import os
import httpx
import json
import urllib.parse
import logging
import time
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# --- Pre-computation & Setup ---
# 1. Load environment variables
load_dotenv()

# 2. Setup Logging
# Use LOG_LEVEL from env, default to INFO.
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("OpenRouterMCP")

# 3. Initialize MCP Server
mcp = FastMCP("OpenRouter MCP")

# --- Configuration & Globals ---
API_KEY = os.getenv("OPENROUTER_API_KEY")
DEFAULT_MODEL = os.getenv("OPENROUTER_DEFAULT_MODEL", "google/gemini-2.0-flash-lite-001")
ALIASES_JSON = os.getenv("OPENROUTER_MODEL_ALIASES", "{}")
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", 120.0))

# Parse and normalize model aliases from env
try:
    raw_aliases = json.loads(ALIASES_JSON)
    if not isinstance(raw_aliases, dict):
        raise ValueError("OPENROUTER_MODEL_ALIASES must be a JSON object")
except (json.JSONDecodeError, ValueError) as e:
    logger.warning("Failed to parse OPENROUTER_MODEL_ALIASES (%s). No aliases will be used.", e)
    MODEL_ALIASES: dict[str, str] = {}
else:
    MODEL_ALIASES = {}
    for k, v in raw_aliases.items():
        # Only keep clean string->string mappings and normalize keys
        if not isinstance(k, str) or not isinstance(v, str):
            logger.warning("Ignoring non-string alias mapping: %r -> %r", k, v)
            continue
        MODEL_ALIASES[k.lower()] = v

logger.info("Loaded %d model aliases.", len(MODEL_ALIASES))

# 4. Global HTTP Client for performance (connection pooling)
http_client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT)

# 5. In-memory cache for model list
model_cache = {"models": [], "expiry": 0}
MODEL_CACHE_TTL_SECONDS = 300  # 5 minutes

BASE_URL = "https://openrouter.ai/api/v1"

# --- Helper Functions ---

def resolve_model(model_name: str) -> str:
    """Safely resolve a model alias to a model ID, falling back to default."""
    if not model_name:
        return DEFAULT_MODEL
    
    alias_lower = model_name.lower()
    resolved_model = MODEL_ALIASES.get(alias_lower)
    
    if resolved_model:
        return resolved_model
    else:
        logger.warning(f"Unknown model alias '{model_name}' requested. Falling back to default.")
        return DEFAULT_MODEL

def validate_image_url(url: str) -> bool:
    """Basic validation for image URL scheme."""
    if not url: return False
    try:
        parsed = urllib.parse.urlparse(url)
        # Allow only public, web-accessible schemes
        if parsed.scheme not in ('http', 'https'):
            return False
        # Disallow localhost or internal-looking IPs for security
        if parsed.hostname in ('localhost', '127.0.0.1') or (parsed.hostname and parsed.hostname.startswith('192.168.')):
            return False
        return True
    except ValueError:
        return False

def validate_dimensions(width: int, height: int) -> tuple[int, int]:
    """Validate and clamp image dimensions to a safe range."""
    MAX_DIM, MIN_DIM = 2048, 128
    return max(MIN_DIM, min(MAX_DIM, width)), max(MIN_DIM, min(MAX_DIM, height))

def sanitize_markdown(text: str) -> str:
    """Simple sanitization for alt-text in markdown."""
    return text.replace("[", "\\[").replace("]", "\\]")

# --- Core API Logic ---

@mcp.tool()
async def list_models(limit: int = 10, search: str = None) -> str:
    """List available models on OpenRouter, with caching."""
    if not API_KEY:
        return "Error: OPENROUTER_API_KEY is not set."
    
    # Clamp limit to a safe range
    safe_limit = max(1, min(100, limit))

    try:
        # Check cache first
        if time.time() < model_cache["expiry"]:
            logger.info("Returning cached model list.")
            models = model_cache["models"]
        else:
            logger.info("Fetching fresh model list from OpenRouter.")
            response = await http_client.get(f"{BASE_URL}/models")
            response.raise_for_status()
            data = response.json()
            if "data" not in data:
                return "Error: Invalid response from OpenRouter API."
            models = data["data"]
            # Update cache
            model_cache["models"] = models
            model_cache["expiry"] = time.time() + MODEL_CACHE_TTL_SECONDS
        
        if search:
            models = [m for m in models if search.lower() in m["id"].lower()]
        
        models.sort(key=lambda x: float(x.get("pricing", {}).get("prompt", 'inf')))
        
        result = [f"Found {len(models)} models (showing top {safe_limit}):"]
        if MODEL_ALIASES:
            result.append(f"Aliases: {', '.join(MODEL_ALIASES.keys())}")
        
        for m in models[:safe_limit]:
            price = m.get("pricing", {}).get("prompt", "N/A")
            context = m.get("context_length", "N/A")
            result.append(f"- {m['id']} (Context: {context}, Price: {price})")
            
        return "\n".join(result)
        
    except httpx.HTTPStatusError as e:
        logger.error(f"API Error fetching models: {e.response.status_code}")
        return f"API Error {e.response.status_code} while fetching models."
    except Exception as e:
        logger.error(f"Unexpected error fetching models: {e}", exc_info=True)
        return "An unexpected error occurred while fetching models."

async def try_chat_request(model: str, messages: list) -> tuple[str | None, str | None]:
    """Helper to execute a single chat request with the global client."""
    full_response = []
    payload = {"model": model, "messages": messages, "stream": True}
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "HTTP-Referer": "https://github.com/klim4-bot/openrouter-mcp",
        "X-Title": "OpenClaw-MCP"
    }
    
    try:
        async with http_client.stream("POST", f"{BASE_URL}/chat/completions", json=payload, headers=headers) as response:
            if response.status_code != 200:
                # Read the body to avoid connection leaks
                error_body = await response.aread()
                logger.warning(f"API request to {model} failed with status {response.status_code}: {error_body.decode()}")
                return None, f"API Error {response.status_code}."
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    line = line[6:]
                    if line == "[DONE]": break
                    try:
                        chunk = json.loads(line)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        # Handle both content and reasoning fields for compatibility
                        content = delta.get("content") or delta.get("reasoning")
                        if content:
                            full_response.append(content)
                    except (json.JSONDecodeError, IndexError):
                        logger.warning(f"Could not parse stream chunk: {line}")
                        continue
                        
        return "".join(full_response), None

    except httpx.TimeoutException:
        logger.warning(f"Request to {model} timed out.")
        return None, "Request timed out."
    except Exception as e:
        logger.error(f"Unexpected error during chat request to {model}: {e}", exc_info=True)
        return None, "An unexpected error occurred."

def get_candidates_for_auto_mode(image_present: bool) -> list:
    """Builds a prioritized list of model candidates for auto-mode."""
    AUTO_MODEL_PRIORITY = ["llama-free", "deepseek-free", "gemma-free", "stepfun-free"]
    candidate_aliases = list(AUTO_MODEL_PRIORITY)
    
    if image_present and "gemini" not in candidate_aliases:
        candidate_aliases.insert(0, "gemini")
    
    candidates = [(alias, MODEL_ALIASES[alias]) for alias in candidate_aliases if alias in MODEL_ALIASES]
    candidates.append(("default", DEFAULT_MODEL))
    return candidates

@mcp.tool()
async def chat_completion(model: str = None, prompt: str = "", image_url: str = None, system_prompt: str = None) -> str:
    """Send a chat completion request to an OpenRouter model."""
    if not API_KEY: return "Error: OPENROUTER_API_KEY is not set."
    if not prompt and not image_url: return "Error: Prompt cannot be empty without an image."
    if image_url and not validate_image_url(image_url): return "Error: Invalid or disallowed image URL."

    messages = []
    if system_prompt: messages.append({"role": "system", "content": system_prompt})

    user_content = [{"type": "text", "text": prompt}]
    if image_url: user_content.append({"type": "image_url", "image_url": {"url": image_url}})
    messages.append({"role": "user", "content": user_content if image_url else prompt})

    if model:
        target_model = resolve_model(model)
        content, error = await try_chat_request(target_model, messages)
        return content if content is not None else error

    logger.info("🤖 Auto-mode: finding best available model...")
    candidates = get_candidates_for_auto_mode(image_url is not None)
    last_error = "No models available or all failed."
    
    for alias, model_id in candidates:
        logger.info(f"🔄 Trying {alias} ({model_id})...")
        content, error = await try_chat_request(model_id, messages)
        if content is not None:
            return f"[Auto-selected: {alias}]\n{content}"
        else:
            logger.warning(f"⚠️ {alias} failed: {error}")
            last_error = error
            
    return f"All auto-models failed. Last error: {last_error}"

@mcp.tool()
async def generate_image(prompt: str, width: int = 1024, height: int = 1024) -> str:
    """Generate an image using Pollinations.ai."""
    if not prompt: return "Error: Prompt cannot be empty."
    
    width, height = validate_dimensions(width, height)
    encoded_prompt = urllib.parse.quote(prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"
    
    # Use a generic, safe alt-text instead of the user's prompt
    return f"![Generated Image]({image_url})\n\n(URL: {image_url})"

if __name__ == "__main__":
    if not API_KEY:
        logger.critical("FATAL: OPENROUTER_API_KEY is not set. The server will not start.")
    else:
        mcp.run()
