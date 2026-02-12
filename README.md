# 🤖 OpenRouter MCP Server

An advanced **Model Context Protocol (MCP)** server that connects your AI agent (Claude, Cursor, Cline, etc.) to **OpenRouter's massive ecosystem of models**.

It acts as a "Smart Manager" for your AI, enabling it to delegate tasks to cheaper, faster, or more specialized models automatically.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)

## ✨ Key Features

- **🧠 Auto-Routing (Smart Fallback)**
  - No need to specify a model manually.
  - Automatically tries available **Free Models** (Llama 3 70B, DeepSeek R1, Gemma 3, etc.) in priority order.
  - Handles rate limits (`429`) and errors (`404`) by seamlessly switching to the next available model.
  
- **👁️ Vision Support (Multimodal)**
  - Send image URLs directly to models.
  - Automatically routes image requests to vision-capable models (e.g., Gemini 2.0 Flash Lite) even in Auto Mode.
  
- **🎨 Image Generation (Free)**
  - Built-in `generate_image` tool powered by **Pollinations.ai**.
  - Create high-quality images for free without API keys.

- **⚡ Streaming & Aliases**
  - Internal streaming logic ensures stability for long responses.
  - Define custom short aliases (e.g., `gpt4`, `sonnet`, `gemini`) for easy access.

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/openrouter-mcp.git
cd openrouter-mcp
```

### 2. Set up Python Environment
We recommend using a virtual environment to keep dependencies clean.

```bash
# Create a virtual environment named 'venv'
python3 -m venv venv

# Activate the environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### 3. Install Dependencies
Install the package in editable mode (allows you to modify code easily).

```bash
pip install -e .
```

### 4. Configure API Keys (`.env`)
Create a file named `.env` in the root directory. **Do not commit this file.**

```ini
# Required: Get your key from https://openrouter.ai/keys
OPENROUTER_API_KEY=sk-or-your-key-here

# Optional: Set a default fallback model
OPENROUTER_DEFAULT_MODEL=google/gemini-2.0-flash-lite-001

# Optional: Define custom aliases for models
OPENROUTER_MODEL_ALIASES={"gemini": "google/gemini-2.0-flash-lite-001", "gpt4": "openai/gpt-4o", "llama-free": "meta-llama/llama-3.3-70b-instruct:free"}
```

## 🚀 Usage with MCP Clients

### Claude Desktop
Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "openrouter": {
      "command": "/path/to/openrouter-mcp/venv/bin/python",
      "args": ["/path/to/openrouter-mcp/src/openrouter_mcp/server.py"],
      "env": {
        "OPENROUTER_API_KEY": "sk-or-...",
        "OPENROUTER_DEFAULT_MODEL": "google/gemini-2.0-flash-lite-001"
      }
    }
  }
}
```

### Cursor / Cline (VS Code)
Add to `.vscode/cline_mcp_settings.json`:

```json
{
  "mcpServers": {
    "openrouter": {
      "command": "/path/to/openrouter-mcp/venv/bin/python",
      "args": ["/path/to/openrouter-mcp/src/openrouter_mcp/server.py"],
      "env": {
        "OPENROUTER_API_KEY": "sk-or-..."
      }
    }
  }
}
```

## 🧰 Available Tools

### 1. `chat_completion` (The Core Tool)
Delegates a task to another LLM.

- **prompt**: The text prompt.
- **model** (Optional): Specific model alias or ID. **If omitted, Auto-Routing kicks in.**
- **image_url** (Optional): URL of an image to analyze (Vision).
- **system_prompt** (Optional): System instructions.

**Example (Auto Mode):**
> "Translate this into Korean." (Automatically picks DeepSeek or Llama)

**Example (Vision):**
> "Describe this image." + [Image URL] (Automatically picks Gemini)

### 2. `generate_image`
Generates an image from text.

- **prompt**: Description of the image.
- **width/height**: Dimensions (default 1024x1024).

**Example:**
> "Draw a cyberpunk cat in neon rain."

### 3. `list_models`
Lists available models on OpenRouter with pricing info.

## 🧪 Testing
Run the included test scripts in `tests/`:

```bash
python tests/test_auto.py       # Test Auto-Routing
python tests/test_vision.py     # Test Vision
python tests/test_gen_image.py  # Test Image Generation
```

## 📜 License
MIT License
