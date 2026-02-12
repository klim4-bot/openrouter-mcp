import asyncio
from openrouter_mcp.server import chat_completion
from dotenv import load_dotenv

load_dotenv()

async def test_mcp_vision_real():
    print("👁️ Testing MCP Vision with a food image...")
    
    # Image from Unsplash (usually bot-friendly)
    img_url = "https://images.unsplash.com/photo-1585109649139-366815a0d713?q=80&w=1000&auto=format&fit=crop"
    
    # Let's try explicit model ID for Llama Vision if Gemini is picky about URLs today
    # Or stick to Gemini but with a better URL.
    # We will stick to 'gemini' alias first.
    
    # 1. Ask via MCP (Auto-routing or Explicit Gemini)
    # We rely on auto-routing's intelligence to pick a vision model if we don't specify one,
    # OR we explicitly specify 'gemini' to be safe since we implemented vision priority for it.
    
    print(f"Target Image: {img_url}")
    print("Sending request to OpenRouter MCP...")
    
    response = await chat_completion(
        model="gemini", # Let's use our alias
        prompt="Describe this food in detail. Does it look tasty? Answer in Korean.",
        image_url=img_url
    )
    
    print("\n--- MCP Analysis Result ---")
    print(response)

if __name__ == "__main__":
    asyncio.run(test_mcp_vision_real())
