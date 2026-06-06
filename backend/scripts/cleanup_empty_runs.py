"""Remove evaluation runs that completed with 0 questions (no real data)."""
import asyncio, os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
load_dotenv()

async def cleanup():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
    db = client[os.getenv("MONGODB_DB_NAME", "rageval")]

    # Delete runs that completed with 0 questions (bogus runs)
    result = await db.evaluation_runs.delete_many({
        "status": "completed",
        "total_questions": 0
    })
    print(f"Deleted {result.deleted_count} empty evaluation run(s)")

    # Show remaining runs
    runs = await db.evaluation_runs.find({}).to_list(20)
    print(f"\nRemaining runs ({len(runs)}):")
    for r in runs:
        print(f"  '{r.get('name')}' status={r.get('status')} "
              f"q={r.get('total_questions')} faithfulness={r.get('avg_faithfulness')}")

    client.close()

asyncio.run(cleanup())
