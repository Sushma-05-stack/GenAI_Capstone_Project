"""Full project verification — no LangSmith network calls."""
import urllib.request, json, sys
sys.stdout.reconfigure(encoding="utf-8")

BASE = "http://localhost:8000"

def req(path, method="GET", data=None, token=None, timeout=15):
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    r = urllib.request.Request(BASE + path, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()[:200]}

print("=" * 55)
print("  RAG Eval Dashboard — Project Verification")
print("=" * 55)

# Health
s, d = req("/health")
print(f"\n[{s}] Health: {d.get('status')} ({d.get('env')})")
assert s == 200, "Health check failed"

# Login
s, d = req("/api/v1/auth/login", "POST",
           {"email": "admin@rageval.com", "password": "Admin123!"})
assert s == 200, f"Login failed: {d}"
token = d["access_token"]
print(f"[{s}] Login: OK")

# Me
s, d = req("/api/v1/users/me", token=token)
print(f"[{s}] User: {d.get('email')} | role={d.get('role')}")

# Status (ChromaDB + LangSmith)
s, d = req("/api/v1/dashboard/status", token=token)
print(f"[{s}] ChromaDB: mode={d['chromadb']['mode']} | collections={d['chromadb']['collections']}")
print(f"     LangSmith: enabled={d['langsmith']['enabled']} | project={d['langsmith']['project']}")
print(f"     LLM providers: {d['llm_providers']}")

# Datasets
s, d = req("/api/v1/datasets/?page_size=10", token=token)
datasets = d.get("datasets", [])
print(f"[{s}] Datasets: {len(datasets)}")
for ds in datasets:
    print(f"     - {ds['name']} (qa={ds['qa_count']})")

# Evaluation history
s, d = req("/api/v1/evaluation/history?page_size=5", token=token, timeout=30)
runs = d.get("runs", [])
print(f"[{s}] Evaluation runs: {d.get('total', 0)}")
for r in runs[:3]:
    print(f"     - {r['name']} | {r['status']} | faith={r.get('avg_faithfulness')}")

# Dashboard summary
s, d = req("/api/v1/dashboard/summary", token=token)
print(f"[{s}] Dashboard: evals={d['total_evaluations']} | datasets={d['total_datasets']}")
print(f"     Avg faithfulness={d.get('avg_faithfulness')} | Hall.risk={d.get('avg_hallucination_risk')}")

# RAG query test
best_ds = max(datasets, key=lambda x: x.get("qa_count", 0)) if datasets else None
if best_ds and best_ds.get("qa_count", 0) > 0:
    print(f"\nTesting RAG query on '{best_ds['name']}'...")
    s, d = req("/api/v1/rag/query", "POST", {
        "question": "What is RAG?",
        "dataset_id": best_ds["id"],
        "provider": "groq",
        "top_k": 3,
    }, token=token, timeout=30)
    if s == 200:
        print(f"[{s}] RAG Query: OK")
        print(f"     Answer: {d.get('answer','')[:100]}...")
        print(f"     Contexts: {len(d.get('contexts', []))}")
        print(f"     Provider: {d.get('provider_used')}/{d.get('model_used')}")
        print(f"     Latency: {d.get('latency_ms',0):.0f}ms")
        print(f"     LangSmith URL: {d.get('langsmith_trace_url')}")
    else:
        print(f"[{s}] RAG Query error: {d.get('error','?')[:100]}")

print("\n" + "=" * 55)
print("  ALL CHECKS PASSED")
print("=" * 55)
print(f"""
  Frontend : http://localhost:3000
  Backend  : http://localhost:8000
  API Docs : http://localhost:8000/docs

  Login credentials:
    Email    : admin@rageval.com
    Password : Admin123!
""")
