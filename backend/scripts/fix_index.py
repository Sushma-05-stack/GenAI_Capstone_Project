"""Check ChromaDB state and reindex all datasets."""
import asyncio, os, sys
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
load_dotenv()

async def fix():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
    db = client[os.getenv("MONGODB_DB_NAME", "rageval")]

    # Check ChromaDB
    import chromadb
    chroma = chromadb.PersistentClient(path="./chroma_store")
    cols = chroma.list_collections()
    print("=== ChromaDB Collections ===")
    for c in cols:
        col = chroma.get_collection(c.name)
        print(f"  {c.name}  count={col.count()}")

    # Get all datasets with QA pairs
    datasets = await db.datasets.find({"is_deleted": {"$ne": True}}).to_list(50)
    print(f"\n=== Datasets ({len(datasets)}) ===")

    for ds in datasets:
        ds_id = str(ds["_id"])
        qa = ds.get("qa_pairs", [])
        print(f"\n  '{ds.get('name')}' (id={ds_id[:16]}) qa_count={len(qa)}")

        if not qa:
            print("  → No QA pairs, skipping")
            continue

        collection_name = f"dataset_{ds_id}"
        try:
            col = chroma.get_or_create_collection(collection_name, metadata={"hnsw:space": "cosine"})
            current_count = col.count()
            print(f"  → ChromaDB count={current_count}")

            if current_count == 0:
                print(f"  → Indexing {len(qa)} QA pairs...")
                # Build texts and IDs
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

                # Use ChromaDB's built-in ONNX embeddings
                from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
                ef = DefaultEmbeddingFunction()
                embeddings = ef(texts)

                col.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
                print(f"  → Indexed {len(texts)} items. New count={col.count()}")
            else:
                print(f"  → Already indexed ({current_count} items)")

        except Exception as e:
            print(f"  → Error: {e}")

    client.close()
    print("\nDone! Try RAG query again.")

asyncio.run(fix())
