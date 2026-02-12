import asyncio
from openrouter_mcp.server import chat_completion
from dotenv import load_dotenv

load_dotenv()

async def solve_puzzle():
    print("🧩 Asking DeepSeek-R1 via MCP...")
    
    puzzle = """
    A farmer has a wolf, a goat, and a cabbage. He must cross a river with a boat that can only hold him and one other item.
    - If left alone, the wolf eats the goat.
    - If left alone, the goat eats the cabbage.
    
    How can he get everything across safely? Explain step by step.
    """
    
    # Using AUTO MODE (no model specified) so it finds an available model
    response = await chat_completion(
        model=None, 
        prompt=puzzle
    )
    
    print("\n--- DeepSeek's Solution ---")
    print(response)

if __name__ == "__main__":
    asyncio.run(solve_puzzle())
