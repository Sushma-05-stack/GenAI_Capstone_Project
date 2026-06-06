"""Test every major endpoint to find which one causes 500."""
import json, urllib.request

BASE = "http://localhost:8000/api/v1"

def req(path, method="GET", data=None, token=None, timeout=15):
    headers = {"Content-Type": "application/json"}
    if token: headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    r = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        return 0, str(e)

# Login
status, data = req("/auth/login", "POST", {"email": "admin@rageval.com", "password": "Admin123!"})
print(f"[{status}] POST /auth/login")
if status != 200:
    print(f"  ERROR: {data}")
    exit(1)
token = data["access_token"]

# Test each endpoint
endpoints = [
    ("GET",  "/users/me",                        None),
    ("GET",  "/dashboard/summary",               None),
    ("GET",  "/dashboard/trends?days=30",        None),
    ("GET",  "/dashboard/model-usage",           None),
    ("GET",  "/dashboard/hallucination-report",  None),
    ("GET",  "/datasets/?page_size=10",          None),
    ("GET",  "/prompts/",                        None),
    ("GET",  "/evaluation/history?page_size=10", None),
    ("GET",  "/models/supported",                None),
    ("GET",  "/models/fallback-analytics",       None),
    ("GET",  "/security/stats",                  None),
    ("GET",  "/security/logs?page_size=5",       None),
]

# Get dataset and eval run IDs for deeper tests
_, ds_data = req("/datasets/?page_size=10", token=token)
datasets = ds_data.get("datasets", [])
_, eval_data = req("/evaluation/history?page_size=10", token=token)
runs = eval_data.get("runs", [])

for method, path, data in endpoints:
    status, resp = req(path, method, data, token)
    ok = "✓" if status == 200 else "✗"
    print(f"[{status}] {ok} {method} {path}")
    if status >= 400:
        print(f"      ERROR: {str(resp)[:200]}")

# Test RAG query if dataset exists
if datasets:
    ds_id = datasets[0]["id"]
    print(f"\nTesting RAG query on dataset {ds_id[:16]}...")
    status, resp = req("/rag/query", "POST", {
        "question": "What is RAG?",
        "dataset_id": ds_id,
        "provider": "groq",
        "top_k": 3,
    }, token, timeout=45)
    ok = "✓" if status == 200 else "✗"
    print(f"[{status}] {ok} POST /rag/query")
    if status == 200:
        print(f"      answer: {resp.get('answer','')[:100]}...")
        print(f"      contexts: {len(resp.get('contexts',[]))}")
    else:
        print(f"      ERROR: {str(resp)[:300]}")

# Test eval run detail
if runs:
    run_id = runs[0]["id"]
    status, resp = req(f"/evaluation/{run_id}", token=token)
    ok = "✓" if status == 200 else "✗"
    print(f"\n[{status}] {ok} GET /evaluation/{run_id[:12]}...")

    status2, resp2 = req(f"/evaluation/{run_id}/results", token=token)
    ok2 = "✓" if status2 == 200 else "✗"
    print(f"[{status2}] {ok2} GET /evaluation/{run_id[:12]}.../results")
    if status2 != 200:
        print(f"      ERROR: {str(resp2)[:200]}")

print("\nDone.")
