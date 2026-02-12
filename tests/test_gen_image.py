import asyncio
from openrouter_mcp.server import generate_image

async def test_gen_image():
    print("🎨 Testing Image Generation (Pollinations)...")
    
    prompt = "A cyberpunk detective cat in neon rain, high quality, detailed"
    response = await generate_image(prompt=prompt)
    
    print("\n--- Response ---")
    print(response)

if __name__ == "__main__":
    asyncio.run(test_gen_image())
