import asyncio
import os
import json
from openrouter_mcp.server import chat_completion
from dotenv import load_dotenv

load_dotenv()

async def test_image_generation():
    print("🎨 Testing Image Generation capability...")
    
    # Using a model known for image generation capabilities if available
    # Or asking a general model to generate an image (often they return a markdown image link)
    
    # Let's try to find a model that supports this.
    # Currently OpenRouter lists 'stabilityai/stable-diffusion-xl-base-1.0' etc.
    # But usually via a different endpoint or specific request.
    
    # Strategy: Ask a capable model to "generate an image" and see if it returns a URL 
    # (some models like DALL-E 3 via proxy might work this way).
    
    prompt = "Generate an image of a futuristic cyberpunk city with neon lights."
    
    # We'll try the auto-mode first, hoping it picks a capable model, 
    # but for image gen, we might need a specific model ID.
    # Let's try 'google/gemini-2.0-flash-lite-001' as it handles multimodal well.
    
    response = await chat_completion(
        model="google/gemini-2.0-flash-lite-001",
        prompt=prompt
    )
    
    print("\n--- Generation Response ---")
    print(response)

if __name__ == "__main__":
    asyncio.run(test_image_generation())
