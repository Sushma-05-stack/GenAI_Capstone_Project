"""
Full fix:
1. Show all datasets with their IDs
2. Add sample QA pairs to any empty dataset
3. Index ALL datasets into ChromaDB using the correct collection names
4. Test a RAG query
"""
import asyncio, os, json, urllib.request, time
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
load_dotenv()

SAMPLE_QA = [
    {"question": "What is RAG?",
     "ground_truth": "RAG stands for Retrieval-Augmented Generation. It retrieves relevant documents and uses them as context for LLM generation, producing accurate, grounded responses."},
    {"question": "What is faithfulness in RAGAS?",
     "ground_truth": "Faithfulness measures whether the generated answer is grounded in the retrieved context, with higher scores meaning the answer stays true to the source material."},
    {"question": "What is hallucination in LLMs?",
     "ground_truth": "Hallucination is when an LLM generates plausible-sounding but factually incorrect content not grounded in its training data or provided context."},
    {"question": "What is context precision?",
     "ground_truth": "Context precision measures whether the retrieved chunks are actually relevant to the question, acting as a signal-to-noise ratio for retrieval quality."},
    {"question": "What is context recall?",
     "ground_truth": "Context recall measures whether all the information needed to answer the question is present in the retrieved context."},
    {"question": "How does RAG reduce hallucination?",
     "ground_truth": "RAG reduces hallucination by grounding LLM responses in retrieved documents. The model is constrained to answer from the provided context rather than relying solely on parametric knowledge."},
    {"question": "What is answer relevancy?",
     "ground_truth": "Answer relevancy measures how relevant the generated answer is to the original question, regardless of whether the answer is factually correct."},
    {"question": "What is ChromaDB?",
     "ground_truth": "ChromaDB is an open-source vector database used to store embeddings and perform semantic similarity search, commonly used in RAG pipelines for document retrieval."},
]


async def fix():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
    db = client[os.getenv("MONGODB_DB_NAME", "rageval")]
    import chromadb
    from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
    ef = DefaultEmbeddingFunction()
    chroma = chromadb.PersistentClient(path="./chroma_store")

    # Step 1: Show datasets
    datasets = await db.datasets.find({"is_deleted": {"$ne": True}}).to_list(50)
    print(f"=== Datasets ({len(datasets)}) ===")

    for ds in datasets:
        ds_id = str(ds["_id"])
        qa = ds.get("qa_pairs", [])
        print(f"\n  '{ds.get('name')}' id={ds_id} qa_count={len(qa)}")

        # Step 2: Seed empty datasets
        if not qa:
            print(f"  → Seeding {len(SAMPLE_QA)} QA pairs...")
            await db.datasets.update_one(
                {"_id": ds["_id"]},
                {"$set": {"qa_pairs": SAMPLE_QA, "qa_count": len(SAMPLE_QA), "status": "ready"}}
            )
            qa = SAMPLE_QA
            print(f"  → Seeded OK")

        # Step 3: Index into ChromaDB
        collection_name = f"dataset_{ds_id}"
        try:
            col = chroma.get_or_create_collection(collection_name, metadata={"hnsw:space": "cosine"})
            if col.count() > 0:
                print(f"  → ChromaDB already has {col.count()} items, deleting and re-indexing...")
                chroma.delete_collection(collection_name)
                col = chroma.get_or_create_collection(collection_name, metadata={"hnsw:space": "cosine"})

            texts, ids, metadatas = [], [], []
            for i, q in enumerate(qa):
                content = f"Q: {q.get('question','')}\nA: {q.get('ground_truth','')}"
                texts.append(content)
                ids.append(f"qa_{ds_id}_{i}")
                metadatas.append({
                    "source": "qa_pair",
                    "dataset_id": ds_id,
                    "question": q.get("question", "")[:200],
                })

            print(f"  → Generating embeddings for {len(texts)} items...")
            embeddings = ef(texts)
            col.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
            print(f"  → ChromaDB indexed: {col.count()} items in '{collection_name}'")

        except Exception as e:
            print(f"  → ChromaDB error: {e}")

    client.close()

    # Step 4: Test RAG query via API
    print("\n=== Testing RAG Query ===")
    BASE = "http://localhost:8000/api/v1"

    def req(path, method="GET", data=None, token=None):
        headers = {"Content-Type": "application/json"}
        if token: headers["Authorization"] = f"Bearer {token}"
        body = json.dumps(data).encode() if data else None
        r = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
        with urllib.request.urlopen(r, timeout=30) as resp:
            return json.loads(resp.read())

    login = req("/auth/login", "POST", {"email": "admin@rageval.com", "password": "Admin123!"})
    token = login["access_token"]

    # Get fresh dataset list (with updated QA)
    time.sleep(2)
    datasets_api = req("/datasets/?page_size=10", token=token)
    ds_list = datasets_api["datasets"]
    best = max(ds_list, key=lambda d: d.get("qa_count", 0))
    print(f"Querying dataset: '{best['name']}' (id={best['id'][:16]}, qa={best['qa_count']})")

    result = req("/rag/query", "POST", {
        "question": "What is RAG and why is it used?",
        "dataset_id": best["id"],
        "provider": "groq",
        "top_k": 3,
    }, token=token)

    print(f"\nQuestion: {result['question']}")
    print(f"Answer:   {result['answer'][:400]}")
    print(f"Provider: {result['provider_used']}/{result['model_used']}")
    print(f"Contexts: {len(result['contexts'])}")
    print(f"Latency:  {result['latency_ms']:.0f}ms")

    if len(result["contexts"]) > 0:
        print(f"\nFirst context: {result['contexts'][0][:150]}...")
        print("\nRAG QUERY WORKING WITH CONTEXT!")
    else:
        print("\nWARNING: Still no contexts retrieved!")


asyncio.run(fix())
