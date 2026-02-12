import pytest
import os
import json
from unittest.mock import MagicMock, AsyncMock

# Import server components once at the top
import openrouter_mcp.server

# --- Pytest Fixture to Isolate Environment ---

@pytest.fixture(autouse=True)
def isolated_env(mocker):
    """
    This fixture automatically runs for every test. It mocks the configuration
    variables directly within the imported server module, bypassing import-time
    evaluation issues.
    """
    # 1. Prevent dotenv from running and reading the real .env file
    mocker.patch('dotenv.load_dotenv', return_value=None)

    # 2. Define the exact configuration for our tests
    test_default_model = 'test/default-model'
    test_aliases = {
        "llama-free": "meta-llama/llama-3-8b:free",
        "deepseek-free": "deepseek/deepseek-coder-v2-lite",
        "gemini": "google/gemini-pro-vision"
    }

    # 3. Patch the variables directly in the already-imported server module
    mocker.patch.object(openrouter_mcp.server, 'DEFAULT_MODEL', test_default_model)
    mocker.patch.object(openrouter_mcp.server, 'MODEL_ALIASES', test_aliases)
    mocker.patch.object(openrouter_mcp.server, 'API_KEY', 'test-key')

    # Also yield the test data for use in tests if needed
    yield {
        "default_model": test_default_model,
        "aliases": test_aliases
    }

# Now we can import the functions without worrying about when they were loaded
from openrouter_mcp.server import (
    resolve_model,
    validate_image_url,
    list_models,
    chat_completion,
    generate_image,
    http_client,
    model_cache
)


# --- Test Suite ---

def test_resolve_model():
    """Tests the model alias resolution logic with a perfectly isolated environment."""
    assert resolve_model('llama-free') == "meta-llama/llama-3-8b:free"
    assert resolve_model('DEEPSEEK-FREE') == "deepseek/deepseek-coder-v2-lite"
    assert resolve_model('unknown-alias') == "test/default-model"
    assert resolve_model(None) == "test/default-model"
    assert resolve_model('') == "test/default-model"

def test_validate_image_url():
    """Tests the security checks for image URLs."""
    assert validate_image_url("https://example.com/image.jpg") is True
    assert validate_image_url("http://sub.example.org/path") is True
    assert validate_image_url("ftp://example.com/image.jpg") is False
    assert validate_image_url("https://localhost/image.png") is False
    assert validate_image_url("http://127.0.0.1/path") is False
    assert validate_image_url("https://192.168.1.10/some/path") is False
    assert validate_image_url(None) is False
    assert validate_image_url("not a url") is False

@pytest.mark.asyncio
async def test_list_models_caching(mocker):
    """Tests that the model list is fetched and then cached."""
    model_cache["expiry"] = 0
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": [{"id": "model1"}]}
    mock_response.raise_for_status = MagicMock()

    mock_get = AsyncMock(return_value=mock_response)
    mocker.patch.object(http_client, 'get', new=mock_get)

    await list_models()
    mock_get.assert_called_once()
    await list_models()
    mock_get.assert_called_once()

@pytest.mark.asyncio
async def test_chat_completion_auto_mode_vision(mocker):
    """Tests that vision model is prioritized in auto-mode with an image."""
    mock_try_request = AsyncMock(return_value=(None, "Mock error"))
    mocker.patch('openrouter_mcp.server.try_chat_request', new=mock_try_request)

    await chat_completion(prompt="describe this", image_url="https://example.com/image.jpg")
    
    first_call_args = mock_try_request.call_args_list[0].args
    assert first_call_args[0] == "google/gemini-pro-vision"

@pytest.mark.asyncio
async def test_chat_completion_empty_prompt_error():
    result = await chat_completion(prompt="")
    assert "Error: Prompt cannot be empty" in result

@pytest.mark.asyncio
async def test_generate_image_empty_prompt_error():
    result = await generate_image(prompt="")
    assert "Error: Prompt cannot be empty" in result

@pytest.mark.asyncio
async def test_generate_image_safe_alt_text():
    result = await generate_image(prompt="a cat closing a [bracket]")
    assert "![Generated Image]" in result
    assert "a cat closing a [bracket]" not in result
