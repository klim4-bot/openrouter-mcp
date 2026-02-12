import asyncio
import os
import json
from openrouter_mcp.server import chat_completion
from dotenv import load_dotenv

# Load env to get aliases
load_dotenv()

async def test_free_models():
    aliases_json = os.getenv("OPENROUTER_MODEL_ALIASES", "{}")
    try:
        aliases = json.loads(aliases_json)
    except json.JSONDecodeError:
        print("Error loading aliases.")
        return

    # Filter only keys ending with '-free' that we added
    free_aliases = [k for k in aliases.keys() if k.endswith("-free")]
    
    print(f"🚀 Testing {len(free_aliases)} free models...\n")

    for alias in free_aliases:
        model_id = aliases[alias]
        print(f"Testing: {alias} ({model_id})...", end=" ", flush=True)
        
        try:
            # Simple prompt to test responsiveness
            response = await chat_completion(
                model=alias, 
                prompt="Reply with only the word 'Pong'."
            )
            
            if "Pong" in response or "pong" in response:
                print("✅ Success!")
            else:
                print(f"⚠️ Unexpected response: {response[:50]}...")
                
        except Exception as e:
            print(f"❌ Failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_free_models())
