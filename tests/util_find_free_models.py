import asyncio
import os
import httpx
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"

async def get_free_models():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/models")
        data = response.json()["data"]
        
        free_models = []
        for m in data:
            prompt_price = float(m.get("pricing", {}).get("prompt", 1))
            completion_price = float(m.get("pricing", {}).get("completion", 1))
            
            if prompt_price == 0 and completion_price == 0:
                free_models.append(m["id"])
        
        return free_models

async def main():
    free_models = await get_free_models()
    print("Found free models:")
    for m in free_models:
        print(m)

if __name__ == "__main__":
    asyncio.run(main())
