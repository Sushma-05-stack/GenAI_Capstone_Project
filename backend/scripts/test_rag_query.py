"""Test RAG query with the fixed prompt."""
import json, urllib.request, time

BASE = "http://localhost:8000/api/v1"

def req(path, method="GET", data=None, token=None, timeout=30):
    headers = {"Content-Type": "application/json"}
    if token: headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    r = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return json.loads(resp.read())

login = req("/auth/login", "POST", {"email": "admin@rageval.com", "password": "Admin123!"})
token = login["access_token"]

# Get best dataset
datasets = req("/datasets/?page_size=10", token=token)
best = max(datasets["datasets"], key=lambda d: d.get("qa_count", 0))
print(f"Dataset: '{best['name']}' (qa={best['qa_count']})")

# Test queries
queries = [
    "What is RAG and why is it used?",
    "What is hallucination in AI?",
    "How does faithfulness scoring work in RAGAS?",
]

for q in queries:
    print(f"\nQ: {q}")
    result = req("/rag/query", "POST", {
        "question": q,
        "dataset_id": best["id"],
        "provider": "groq",
        "top_k": 3,
    }, token=token, timeout=45)
    print(f"A: {result['answer'][:300]}")
    print(f"   contexts={len(result['contexts'])} | provider={result['provider_used']}/{result['model_used']}")
    print(f"   latency={result['latency_ms']:.0f}ms | fallback={result['fallback_used']}")
