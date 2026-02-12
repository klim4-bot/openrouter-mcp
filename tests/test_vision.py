import asyncio
from openrouter_mcp.server import chat_completion
from dotenv import load_dotenv

load_dotenv()

async def test_vision():
    print("👁️ Testing VISION capability...")
    
    # Test image: A simple placeholder image (or a reliable public URL)
    # Using a Wikimedia Commons cat image for stability
    img_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/320px-Cat03.jpg"
    
    response = await chat_completion(
        model="gemini", # Explicitly use a vision-capable model
        prompt="Describe this image in detail. What animal is it?",
        image_url=img_url
    )
    
    print("\n--- Vision Response ---")
    print(response)

if __name__ == "__main__":
    asyncio.run(test_vision())
