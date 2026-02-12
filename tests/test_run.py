import asyncio
import os
from openrouter_mcp.server import list_models, chat_completion

# Mock the env var for the imported module if needed, 
# but we will run this script with the env var set in the exec call.

async def main():
    print("--- 1. Testing list_models ---")
    models = await list_models(limit=3, search="gemini")
    print(models)
    
    print("\n--- 2. Testing chat_completion ---")
    response = await chat_completion(
        model="gemini", # Using alias defined in .env
        prompt="Tell me a very short joke about AI."
    )
    print(f"Response (via alias 'gemini'): {response}")

if __name__ == "__main__":
    asyncio.run(main())
