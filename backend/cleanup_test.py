import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    c = AsyncIOMotorClient("mongodb://localhost:27017")
    db = c["whatsapp_business_agent"]
    docs = await db["businesses"].find({}).to_list(length=10)
    for d in docs:
        d.pop("_id", None)
        print(d)
    if not docs:
        print("No businesses found in DB")
    c.close()

asyncio.run(main())
