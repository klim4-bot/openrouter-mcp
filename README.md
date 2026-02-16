# 🤖 OpenRouter MCP Server

An advanced **Model Context Protocol (MCP)** server that connects your AI agent (Claude, Cursor, Cline, etc.) to **OpenRouter's massive ecosystem of models**.

It acts as a "Smart Manager" for your AI, enabling it to delegate tasks to cheaper, faster, or more specialized models automatically.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![Tests](https://img.shields.io/badge/tests-13%20passed-brightgreen.svg)

## ✨ Key Features

- **🧠 Auto-Routing (Smart Fallback)**
  - No need to specify a model manually.
  - Automatically tries available **Free Models** in priority order.
  - Handles rate limits (`429`) and errors by seamlessly switching to the next available model.
  
- **👁️ Vision Support (Multimodal)**
  - Send image URLs directly to models.
  - Automatically routes image requests to vision-capable models.
  
- **🎨 Image Generation (Free)**
  - Built-in `generate_image` tool powered by **Pollinations.ai**.
  - Create high-quality images for free without API keys.

- **🧩 Model Hunter CLI (New)**
  - `python -m openrouter_mcp.model_hunter` で `/models` API から
    無料/低コストモデルを取得して一覧表示。
  - `--free-only` で無料モデルだけ、`--max-prompt` で
    最大プロンプト価格を指定可能。

- **⚡️ Performance & Stability**
  - Reuses HTTP connections (`httpx.AsyncClient`) for lower latency.
  - Caches model lists for 5 minutes to reduce API calls.
  - Robust logging system for easy debugging.

- **🔒 Security Hardened**
  - **Input Validation**: Sanitizes image URLs, clamps image dimensions, and handles empty inputs.
  - **Model Injection Protection**: Prevents arbitrary model execution by validating aliases.
  - **Safe Outputs**: Sanitizes markdown in image generation to prevent injection vulnerabilities.

## 📦 Changelog - Major Refactor

This project has undergone a significant refactoring process guided by AI-driven code analysis. The codebase is now more secure, robust, and performant.

- **Refactored**: Switched from `print` to a structured `logging` system.
- **Refactored**: Implemented a global `httpx.AsyncClient` for connection pooling, improving performance.
- **Feature**: Added a 5-minute in-memory cache for the `list_models` tool.
- **Feature**: Added a `model_hunter` CLI to discover free/low-cost models from the OpenRouter `/models` API.
- **Security**: Hardened the `validate_image_url` function to block localhost and internal IPs.
- **Security**: Made the `generate_image` tool's markdown output safer by removing the user's prompt from the response template.
- **Security**: Improved `OPENROUTER_MODEL_ALIASES` parsing/validation to ignore invalid JSON/非文字列のマッピング。
- **Testing**: Replaced ad-hoc test scripts with a comprehensive test suite using **`pytest`**.
- **Testing**: Implemented **`pytest-mock`** to create an isolated test environment, ensuring tests are reliable and independent of external factors (`.env` files).
- **CI**: All 13 tests are now passing, ensuring code quality and stability.

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/klim4-bot/openrouter-mcp.git
cd openrouter-mcp
```

### 2. Set up Python Environment
We recommend using a virtual environment.

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the environment
source venv/bin/activate
```

### 3. Install Dependencies
Install the package in editable mode, along with testing dependencies.

```bash
# Install main and testing dependencies
pip install -e .
pip install pytest pytest-mock pytest-asyncio
```

### 4. Configure API Keys (`.env`)
Create a file named `.env` in the root directory.

```ini
# Required: Get from https://openrouter.ai/keys
OPENROUTER_API_KEY="sk-or-..."

# Optional
OPENROUTER_DEFAULT_MODEL="google/gemini-2.0-flash-lite-001"
OPENROUTER_MODEL_ALIASES='{"gemini": "google/gemini-pro-vision", "llama-free": "meta-llama/llama-3.3-70b-instruct:free"}'
```

## 🚀 Usage with MCP Clients

_(Configuration examples for Claude Desktop, Cursor, etc. remain the same)_

... (rest of the usage section can be kept as is) ...

## 🔍 Using the Model Hunter CLI

`model_hunter` は OpenRouter の `/models` API から
無料/低コストモデルを一覧化するための小さな CLI です。

仮想環境を有効化した上で、例えば次のように使えます:

```bash
# 無料モデルだけを確認
python -m openrouter_mcp.model_hunter --free-only --limit 10

# プロンプト価格が 0.5 以下のモデルを安い順に 20 件
python -m openrouter_mcp.model_hunter --max-prompt 0.5 --limit 20
```

出力例:

```text
[OpenRouter Model Hunter]

Free models (prompt price = 0):
1. openrouter/aurora-alpha (context: 128000, prompt: 0)
2. openrouter/free (context: 200000, prompt: 0)
...

Total listed: 10 (free: 10)
```

## 🧪 Testing

The project now uses `pytest` for structured testing. To run the full suite:

```bash
# Ensure you are in the virtual environment
# and in the project root directory
pytest
```
This will automatically discover and run all tests in the `tests/` directory.

## 📜 License
MIT License
