"""
1. Login
2. List all datasets
3. Reindex each dataset's QA pairs into ChromaDB
4. Run a test RAG query
"""
import urllib.request
import json
import time

BASE = "http://localhost:8000/api/v1"


def req(path, method="GET", data=None, token=None, timeout=30):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    r = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return json.loads(resp.read())


def main():
    print("Step 1: Login...")
    login = req("/auth/login", "POST", {"email": "admin@rageval.com", "password": "Admin123!"})
    token = login["access_token"]
    print(f"  Logged in OK")

    print("\nStep 2: List datasets...")
    datasets = req("/datasets/?page_size=50", token=token)
    print(f"  Found {datasets['total']} dataset(s)")

    for ds in datasets["datasets"]:
        print(f"\n  Dataset: '{ds['name']}' (id={ds['id'][:16]}...) qa_count={ds['qa_count']}")
        if ds["qa_count"] > 0:
            print(f"  Reindexing QA pairs into ChromaDB...")
            try:
                result = req(f"/datasets/{ds['id']}/reindex", "POST", token=token)
                print(f"  {result['message']}")
                time.sleep(2)  # give background task time to run
            except Exception as e:
                print(f"  Reindex error: {e}")

    print("\nStep 3: Waiting for indexing to complete (10s)...")
    time.sleep(10)

    # Pick first dataset with QA pairs
    dataset_id = None
    for ds in datasets["datasets"]:
        if ds["qa_count"] > 0:
            dataset_id = ds["id"]
            break

    if not dataset_id:
        print("No datasets with QA pairs found. Create one first.")
        return

    print(f"\nStep 4: Test RAG query against dataset {dataset_id[:16]}...")
    try:
        response = req("/rag/query", "POST", {
            "question": "What is RAG and why is it used?",
            "dataset_id": dataset_id,
            "provider": "auto",
            "top_k": 3,
        }, token=token, timeout=60)

        print(f"\n  Question: {response['question']}")
        print(f"  Answer: {response['answer'][:300]}...")
        print(f"  Provider: {response['provider_used']} / {response['model_used']}")
        print(f"  Fallback used: {response['fallback_used']}")
        print(f"  Contexts retrieved: {len(response['contexts'])}")
        print(f"  Latency: {response['latency_ms']:.0f}ms")
        print(f"\n  RAG Query WORKING!")
    except Exception as e:
        print(f"  RAG query error: {e}")


if __name__ == "__main__":
    main()
