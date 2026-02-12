import asyncio
from openrouter_mcp.server import chat_completion
from dotenv import load_dotenv

load_dotenv()

async def translate_text():
    print("🇯🇵 Translating via MCP (Auto Mode)...")
    
    prompt = "Translate 'hello world mcp' into Japanese. Provide only the translation."
    
    # Auto-routing: let the server find the best available model
    response = await chat_completion(model=None, prompt=prompt)
    
    print("\n--- Translation Result ---")
    print(response)

if __name__ == "__main__":
    asyncio.run(translate_text())
