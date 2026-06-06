"""Diagnose evaluation runs - check why scores are empty."""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

async def diagnose():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
    db = client[os.getenv("MONGODB_DB_NAME", "rageval")]

    # Check evaluation runs
    runs = await db.evaluation_runs.find({}).to_list(20)
    print(f"=== Evaluation Runs ({len(runs)}) ===")
    for r in runs:
        print(f"  id={str(r['_id'])[:16]}  status={r.get('status')}  "
              f"total_q={r.get('total_questions')}  completed_q={r.get('completed_questions')}  "
              f"faithfulness={r.get('avg_faithfulness')}  "
              f"dataset={r.get('dataset_id','')[:16]}")

    # Check evaluation results
    results = await db.evaluation_results.find({}).to_list(10)
    print(f"\n=== Evaluation Results ({len(results)}) ===")
    for r in results:
        print(f"  run_id={r.get('run_id','')[:16]}  "
              f"q={r.get('question','')[:40]}  "
              f"faithfulness={r.get('faithfulness')}  "
              f"relevancy={r.get('answer_relevancy')}  "
              f"answer_len={len(r.get('answer',''))}")

    # Check datasets
    datasets = await db.datasets.find({"is_deleted": {"$ne": True}}).to_list(10)
    print(f"\n=== Datasets ({len(datasets)}) ===")
    for d in datasets:
        qa = d.get('qa_pairs', [])
        print(f"  id={str(d['_id'])[:16]}  name={d.get('name')}  "
              f"qa_count={len(qa)}  status={d.get('status')}")
        if qa:
            print(f"    First QA: q={qa[0].get('question','')[:50]}")

    # Check ChromaDB collections
    try:
        import chromadb
        chroma = chromadb.PersistentClient(path="./chroma_store")
        cols = chroma.list_collections()
        print(f"\n=== ChromaDB Collections ({len(cols)}) ===")
        for c in cols:
            col = chroma.get_collection(c.name)
            print(f"  {c.name}  count={col.count()}")
    except Exception as e:
        print(f"\nChromaDB error: {e}")

    client.close()

asyncio.run(diagnose())
