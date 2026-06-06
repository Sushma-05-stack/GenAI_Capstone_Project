"""Quick health + login + RAG test."""
import urllib.request, json, sys
sys.stdout.reconfigure(encoding='utf-8')

BASE = "http://localhost:8000"

def req(path, method="GET", data=None, token=None, timeout=20):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    r = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return resp.status, json.loads(resp.read())

# 1. Health
status, data = req("/health")
print(f"[{status}] Health: {data['status']} | env: {data['env']}")

# 2. Login
status, data = req("/api/v1/auth/login", "POST", {"email": "admin@rageval.com", "password": "Admin123!"})
token = data["access_token"]
print(f"[{status}] Login: OK (token: {token[:20]}...)")

# 3. LangSmith status
status, data = req("/api/v1/dashboard/status", token=token)
print(f"[{status}] LangSmith enabled: {data['langsmith']['enabled']}")
print(f"       project: {data['langsmith']['project']}")
print(f"       URL: {data['langsmith']['dashboard_url']}")
print(f"       ChromaDB mode: {data['chromadb']['mode']} ({data['chromadb']['collections']} collections)")
print(f"       LLM providers: {data['llm_providers']}")

# 4. Datasets
status, data = req("/api/v1/datasets/?page_size=10", token=token)
datasets = data["datasets"]
print(f"\n[{status}] Datasets: {len(datasets)}")
for d in datasets:
    print(f"   - {d['name']} (qa={d['qa_count']})")

print("\nAll OK! Login credentials:")
print("  Email:    admin@rageval.com")
print("  Password: Admin123!")
print(f"\nFrontend: http://localhost:3000")
print(f"Backend:  http://localhost:8000")
print(f"API Docs: http://localhost:8000/docs")
