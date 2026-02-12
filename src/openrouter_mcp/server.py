import os
import httpx
import json
import urllib.parse
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Load .env if present (optional, for local dev convenience)
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("OpenRouter MCP")

# --- Configuration Management ---
# Priority: Env Vars > Default Defaults

# 1. API Key (Required)
API_KEY = os.getenv("OPENROUTER_API_KEY")

# 2. Default Model (Optional)
DEFAULT_MODEL = os.getenv("OPENROUTER_DEFAULT_MODEL", "google/gemini-2.0-flash-lite-001")

# 3. Model Aliases (Optional JSON string)
# Users can provide this via env var in MCP settings
ALIASES_JSON = os.getenv("OPENROUTER_MODEL_ALIASES", "{}")

try:
    MODEL_ALIASES = json.loads(ALIASES_JSON)
except json.JSONDecodeError:
    print("Warning: Failed to parse OPENROUTER_MODEL_ALIASES JSON.")
    MODEL_ALIASES = {}

BASE_URL = "https://openrouter.ai/api/v1"

def resolve_model(model_name: str) -> str:
    """Resolve model alias or use default if empty."""
    if not model_name:
        return DEFAULT_MODEL
    return MODEL_ALIASES.get(model_name.lower(), model_name)

@mcp.tool()
async def list_models(limit: int = 10, search: str = None) -> str:
    """
    List available models on OpenRouter.
    Optionally filter by search term and limit results.
    """
    if not API_KEY:
        return "Error: OPENROUTER_API_KEY not found in environment variables."

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/models")
            response.raise_for_status()
            models = response.json()["data"]
            
            # Simple search filter
            if search:
                models = [m for m in models if search.lower() in m["id"].lower()]
            
            # Sort by pricing (cheapest first) just as a heuristic
            models.sort(key=lambda x: float(x["pricing"]["prompt"]) if "pricing" in x else 0)
            
            # Format output
            result = [f"Found {len(models)} models (showing top {limit}):"]
            if MODEL_ALIASES:
                result.append(f"Aliases available: {', '.join(MODEL_ALIASES.keys())}")
                
            for m in models[:limit]:
                price = m.get("pricing", {}).get("prompt", "N/A")
                context = m.get("context_length", "N/A")
                result.append(f"- {m['id']} (Context: {context}, Price: {price})")
                
            return "\n".join(result)
            
        except Exception as e:
            return f"Error fetching models: {str(e)}"

# Prioritized list of aliases to try for auto-selection (best performance first)
AUTO_MODEL_PRIORITY = ["llama-free", "deepseek-free", "gemma-free", "stepfun-free"]

async def try_chat_request(client, model, messages, headers):
    """Helper to execute a single chat request with error handling."""
    full_response = []
    
    payload = {
        "model": model,
        "messages": messages,
        "stream": True
    }
    
    try:
        async with client.stream(
            "POST", 
            f"{BASE_URL}/chat/completions", 
            json=payload, 
            headers=headers, 
            timeout=120.0
        ) as response:
            if response.status_code != 200:
                await response.aread()
                return None, f"API Error {response.status_code}: {response.text}"
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    line = line[6:]
                    if line == "[DONE]":
                        break
                    try:
                        chunk = json.loads(line)
                        if "choices" in chunk and len(chunk["choices"]) > 0:
                            delta = chunk["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                full_response.append(content)
                    except json.JSONDecodeError:
                        continue
                        
        return "".join(full_response), None

    except Exception as e:
        return None, str(e)

@mcp.tool()
async def chat_completion(
    model: str = None, 
    prompt: str = "", 
    image_url: str = None, 
    system_prompt: str = None
) -> str:
    """
    Send a chat completion request to an OpenRouter model.
    - model: Target model alias or ID (auto-selects if omitted).
    - prompt: User text prompt.
    - image_url: Optional URL of an image to analyze.
    - system_prompt: Optional system instruction.
    """
    if not API_KEY:
        return "Error: OPENROUTER_API_KEY not found in environment variables."

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    # Construct user message (Text-only or Multimodal)
    if image_url:
        user_content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_url}}
        ]
    else:
        user_content = prompt

    messages.append({"role": "user", "content": user_content})

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "HTTP-Referer": "https://github.com/openclaw/openrouter-mcp",
        "X-Title": "OpenClaw MCP"
    }

    async with httpx.AsyncClient() as client:
        # 1. If model IS provided, try just that one
        if model:
            target_model = resolve_model(model)
            content, error = await try_chat_request(client, target_model, messages, headers)
            return content if content else error

        # 2. If NO model provided, try auto-fallback chain
        # Note: If image is present, we should prefer vision-capable models.
        # For now, we use the same list, but Gemini (vision) is usually a safe bet.
        print("🤖 Auto-mode: finding best available model...")
        
        # If image is present, prioritize Gemini as it's the best free vision model
        # You might want to define a separate AUTO_VISION_PRIORITY list later.
        candidate_aliases = list(AUTO_MODEL_PRIORITY)
        if image_url and "gemini" not in candidate_aliases:
             candidate_aliases.insert(0, "gemini") # Insert Gemini at top for vision
        
        # Build candidate list
        candidates = []
        for alias in candidate_aliases:
            if alias in MODEL_ALIASES:
                candidates.append((alias, MODEL_ALIASES[alias]))
        
        # Add default model
        candidates.append(("default", DEFAULT_MODEL))

        last_error = "No models available."
        
        for alias, model_id in candidates:
            print(f"🔄 Trying {alias} ({model_id})...")
            content, error = await try_chat_request(client, model_id, messages, headers)
            
            if content:
                return f"[Auto-selected: {alias}]\n{content}"
            else:
                print(f"⚠️ {alias} failed: {error}")
                last_error = error
                
        return f"All auto-models failed. Last error: {last_error}"

@mcp.tool()
async def generate_image(prompt: str, width: int = 1024, height: int = 1024) -> str:
    """
    Generate an image based on a text prompt using Pollinations.ai (Free).
    Returns a Markdown image URL.
    """
    # URL encode the prompt
    encoded_prompt = urllib.parse.quote(prompt)
    
    # Construct the image URL
    # Pollinations API format: https://image.pollinations.ai/prompt/{prompt}?width={width}&height={height}
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"
    
    return f"Here is your generated image:\n\n![{prompt}]({image_url})\n\n(URL: {image_url})"

if __name__ == "__main__":
    mcp.run()
