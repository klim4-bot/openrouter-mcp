import asyncio
from openrouter_mcp.server import chat_completion
from dotenv import load_dotenv

load_dotenv()

async def test_auto_mode():
    print("🤖 Testing AUTO-ROUTING (No model specified)...")
    
    # Intentionally omit the 'model' parameter
    response = await chat_completion(
        prompt="Tell me which model you are. Be brief."
    )
    
    print("\n--- Final Response ---")
    print(response)

if __name__ == "__main__":
    asyncio.run(test_auto_mode())
