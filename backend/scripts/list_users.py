"""List all users and reset passwords."""
import asyncio, os, sys
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
    db = client[os.getenv("MONGODB_DB_NAME", "rageval")]

    users = await db.users.find({}, {"email": 1, "username": 1, "role": 1, "is_active": 1}).to_list(50)
    print(f"Users ({len(users)}):")
    for u in users:
        print(f"  {u['email']:35}  role={u.get('role','?'):12}  active={u.get('is_active',True)}")

    # Reset ALL user passwords to Admin123! and set active
    import bcrypt
    new_hash = bcrypt.hashpw(b"Admin123!", bcrypt.gensalt()).decode()
    result = await db.users.update_many(
        {},
        {"$set": {"hashed_password": new_hash, "is_active": True}}
    )
    print(f"\nReset {result.modified_count} user password(s) to: Admin123!")

    # Make first user admin
    if users:
        await db.users.update_one(
            {"_id": users[0]["_id"]},
            {"$set": {"role": "admin"}}
        )
        print(f"Set {users[0]['email']} as admin")

    client.close()
    print("\nYou can now login with any email above using password: Admin123!")

asyncio.run(main())
