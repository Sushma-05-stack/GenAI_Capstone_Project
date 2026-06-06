"""One-time script to promote a user to admin role."""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()
MONGODB_URL = os.getenv("MONGODB_URL")
DB_NAME = os.getenv("MONGODB_DB_NAME", "rageval")

TARGET_EMAIL = "admin@rageval.com"


async def promote():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DB_NAME]

    result = await db.users.update_one(
        {"email": TARGET_EMAIL},
        {"$set": {"role": "admin", "is_verified": True}},
    )
    print(f"Modified count: {result.modified_count}")

    user = await db.users.find_one({"email": TARGET_EMAIL})
    if user:
        print(f"User {user['email']} role is now: {user['role']}")
    else:
        print("User not found.")
    client.close()


if __name__ == "__main__":
    asyncio.run(promote())
