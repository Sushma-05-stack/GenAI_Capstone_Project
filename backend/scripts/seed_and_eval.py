"""
Seed RAG Evaluation Benchmark Dataset with rich QA pairs and run evaluation.
"""
import asyncio, os, json, urllib.request, time
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
load_dotenv()

BASE = "http://localhost:8000/api/v1"

RICH_QA = [
    {
        "question": "What is Retrieval-Augmented Generation?",
        "ground_truth": "Retrieval-Augmented Generation (RAG) is a technique that combines information retrieval with large language model generation. It retrieves relevant documents from a knowledge base and uses them as context to generate accurate, grounded responses.",
    },
    {
        "question": "What is faithfulness in RAGAS?",
        "ground_truth": "Faithfulness in RAGAS measures whether the generated answer is factually grounded in the provided context. A high faithfulness score means the answer does not contain information that contradicts or goes beyond the retrieved context.",
    },
    {
        "question": "How does context precision differ from context recall?",
        "ground_truth": "Context precision measures whether retrieved chunks are relevant to the question, while context recall measures whether all information needed to answer the question is present in the retrieved context.",
    },
    {
        "question": "What is hallucination risk?",
        "ground_truth": "Hallucination risk is the probability that a model generates content not grounded in the provided context. It is calculated as 1 minus the faithfulness score.",
    },
    {
        "question": "What is answer relevancy in RAGAS?",
        "ground_truth": "Answer relevancy measures how relevant the generated answer is to the original question, using embedding similarity between the question and answer.",
    },
]


def http(path, method="GET", data=None, token=None, timeout=30):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    r = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return json.loads(resp.read())


async def main():
    # Login
    login = http("/auth/login", "POST", {"email": "admin@rageval.com", "password": "Admin123!"})
    token = login["access_token"]
    print("Logged in")

    # Seed benchmark dataset
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
    db = client[os.getenv("MONGODB_DB_NAME", "rageval")]

    bench = await db.datasets.find_one({"name": "RAG Evaluation Benchmark Dataset"})
    if bench and len(bench.get("qa_pairs", [])) == 0:
        await db.datasets.update_one(
            {"_id": bench["_id"]},
            {"$set": {"qa_pairs": RICH_QA, "qa_count": len(RICH_QA)}}
        )
        print(f"Seeded {len(RICH_QA)} QA pairs into benchmark dataset")

        # Re-index into ChromaDB
        ds_id = str(bench["_id"])
        import chromadb
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
        chroma = chromadb.PersistentClient(path="./chroma_store")
        ef = DefaultEmbeddingFunction()
        try:
            chroma.delete_collection(f"dataset_{ds_id}")
        except Exception:
            pass
        col = chroma.get_or_create_collection(f"dataset_{ds_id}", metadata={"hnsw:space": "cosine"})
        texts = [f"Q: {q['question']}\nA: {q['ground_truth']}" for q in RICH_QA]
        ids   = [f"qa_{ds_id}_{i}" for i in range(len(RICH_QA))]
        metas = [{"source": "qa_pair", "dataset_id": ds_id} for _ in RICH_QA]
        col.upsert(ids=ids, embeddings=ef(texts), documents=texts, metadatas=metas)
        print(f"ChromaDB indexed: {col.count()} items")

    client.close()

    # Start evaluation on the best dataset
    datasets = http("/datasets/?page_size=10", token=token)
    best = max(datasets["datasets"], key=lambda d: d.get("qa_count", 0))
    print(f"\nRunning evaluation on '{best['name']}' ({best['qa_count']} QA pairs)...")

    run = http("/evaluation/run", "POST", {
        "name": "Build Eval — Groq + RAGAS",
        "dataset_id": best["id"],
        "model_name": "llama-3.3-70b-versatile",
        "provider": "groq",
        "max_questions": 3,
    }, token=token)
    run_id = run["id"]
    print(f"Run started: {run_id}")

    for attempt in range(30):
        time.sleep(10)
        run = http(f"/evaluation/{run_id}", token=token)
        print(f"  [{attempt+1}] {run['status']} — {run['completed_questions']}/{run['total_questions']}")
        if run["status"] == "completed":
            print(f"\nResults:")
            print(f"  Faithfulness:       {run.get('avg_faithfulness')}")
            print(f"  Answer Relevancy:   {run.get('avg_answer_relevancy')}")
            print(f"  Context Precision:  {run.get('avg_context_precision')}")
            print(f"  Context Recall:     {run.get('avg_context_recall')}")
            print(f"  Hallucination Risk: {run.get('avg_hallucination_risk')}")
            print(f"  Avg Latency:        {run.get('avg_latency_ms'):.0f}ms")
            break
        elif run["status"] == "failed":
            print(f"FAILED: {run.get('error_message')}")
            break

if __name__ == "__main__":
    asyncio.run(main())
