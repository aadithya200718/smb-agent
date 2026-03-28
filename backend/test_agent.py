import asyncio
from app.agent.graph import run_agent
from app.core.vector_db import VectorDB

async def main():
    try:
        await VectorDB.connect()
    except Exception as e:
        print(f"Warning: Could not connect to Qdrant ({e}) - proceeding without memory")
        
    result = await run_agent(
        message="I want 2 veg biryanis",
        user_phone="+919876543210",
        business_id="BIZ001",
    )
    
    print("\n========== RESULT ==========")
    print("Intent:", result.get("current_intent", "Unknown"))
    
    # Safely print response avoiding charmap errors on Windows with emojis
    safe_response = result.get("response", "").encode("ascii", "ignore").decode("ascii")
    print("Response:", safe_response)
    print("============================\n")

asyncio.run(main())