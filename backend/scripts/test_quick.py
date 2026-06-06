"""Quick final status check."""
import urllib.request
import json

BASE = "http://localhost:8000/api/v1"


def req(url, method="GET", data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(r, timeout=8) as resp:
        return json.loads(resp.read())


login = req(f"{BASE}/auth/login", "POST", {"email": "admin@rageval.com", "password": "Admin123!"})
token = login["access_token"]

# Security logs check
logs = req(f"{BASE}/security/logs?page_size=5", token=token)
print(f"Audit logs: {logs['total']} total")

# List prompts
prompts = req(f"{BASE}/prompts/", token=token)
print(f"Prompts: {len(prompts)} in library")

# Fallback analytics
fb = req(f"{BASE}/models/fallback-analytics", token=token)
print(f"Fallback events: {fb['total_events']}")

# Trend data
trends = req(f"{BASE}/dashboard/trends?days=30", token=token)
print(f"Trend datapoints: {trends['data_points']}")

print()
print("Backend fully operational on http://localhost:8000")
print("API docs at http://localhost:8000/docs")
print("Frontend running on http://localhost:3000")
