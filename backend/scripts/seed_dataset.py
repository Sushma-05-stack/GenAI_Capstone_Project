"""
Seed QA pairs into all empty datasets and re-run failed/empty evaluations.
Run: python seed_dataset.py
"""
import asyncio, os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
load_dotenv()

SAMPLE_QA = [
    {
        "question": "What is Retrieval-Augmented Generation (RAG)?",
        "ground_truth": "RAG is a technique that combines information retrieval with LLM generation. It retrieves relevant documents from a knowledge base and uses them as context to generate accurate, grounded responses.",
        "context": [],
    },
    {
        "question": "What are the main benefits of using RAG over fine-tuning?",
        "ground_truth": "RAG keeps the knowledge base up-to-date without retraining, is more cost-effective, provides source attribution, and reduces hallucination by grounding answers in retrieved documents.",
        "context": [],
    },
    {
        "question": "What is faithfulness in RAGAS evaluation?",
        "ground_truth": "Faithfulness measures whether the generated answer is factually grounded in the provided context. A high faithfulness score means the answer does not contain information that contradicts or goes beyond the retrieved context.",
        "context": [],
    },
    {
        "question": "How does context precision differ from context recall?",
        "ground_truth": "Context precision measures whether retrieved chunks are relevant to the question (signal-to-noise ratio), while context recall measures whether all information needed to answer the question is present in the retrieved context.",
        "context": [],
    },
    {
        "question": "What is hallucination risk in LLMs?",
        "ground_truth": "Hallucination risk is the probability that a model generates plausible-sounding but factually incorrect information not grounded in the provided context. It is calculated as 1 minus the faithfulness score.",
        "context": [],
    },
]


async def seed():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
    db = client[os.getenv("MONGODB_DB_NAME", "rageval")]

    datasets = await db.datasets.find({"is_deleted": {"$ne": True}}).to_list(50)
    print(f"Found {len(datasets)} dataset(s)")

    for ds in datasets:
        ds_id = str(ds["_id"])
        current_qa = ds.get("qa_pairs", [])
        name = ds.get("name", "")
        print(f"\n  Dataset: '{name}' | current QA pairs: {len(current_qa)}")

        if len(current_qa) == 0:
            result = await db.datasets.update_one(
                {"_id": ds["_id"]},
                {"$set": {"qa_pairs": SAMPLE_QA, "qa_count": len(SAMPLE_QA), "status": "ready"}}
            )
            print(f"  → Seeded {len(SAMPLE_QA)} QA pairs (modified={result.modified_count})")
        else:
            print(f"  → Already has QA pairs, skipping")

    # Show evaluation run status
    runs = await db.evaluation_runs.find({}).to_list(20)
    print(f"\n=== Evaluation Runs ({len(runs)}) ===")
    for r in runs:
        print(f"  '{r.get('name','')}' status={r.get('status')} "
              f"total_q={r.get('total_questions',0)} "
              f"faithfulness={r.get('avg_faithfulness')}")

    client.close()
    print("\nDone! Now run a NEW evaluation from the Evaluations page.")
    print("Existing completed-with-0-questions runs won't auto-update.")
    print("Create a new evaluation run to get scores.")


asyncio.run(seed())
