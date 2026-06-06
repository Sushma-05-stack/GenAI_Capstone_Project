"""
Fix: Set ALL existing users to 'evaluator' role so they can use the app.
Admin users must be explicitly promoted.
Run this once: python fix_roles.py
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()


async def fix():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
    db = client[os.getenv("MONGODB_DB_NAME", "rageval")]

    # Show current state
    users = await db.users.find({}, {"email": 1, "role": 1}).to_list(100)
    print("Current users:")
    for u in users:
        print(f"  {u['email']}  ->  role={u['role']}")

    # Set all viewers to evaluator
    result = await db.users.update_many(
        {"role": "viewer"},
        {"$set": {"role": "evaluator"}}
    )
    print(f"\nUpgraded {result.modified_count} viewer(s) to evaluator")

    # Ensure admin@rageval.com is admin
    r2 = await db.users.update_one(
        {"email": "admin@rageval.com"},
        {"$set": {"role": "admin"}}
    )
    print(f"admin@rageval.com set to admin (modified={r2.modified_count})")

    # Final state
    users = await db.users.find({}, {"email": 1, "role": 1}).to_list(100)
    print("\nFinal user roles:")
    for u in users:
        print(f"  {u['email']}  ->  role={u['role']}")

    client.close()
    print("\nDone. Users must LOG OUT and LOG IN again to get a new token.")


if __name__ == "__main__":
    asyncio.run(fix())
