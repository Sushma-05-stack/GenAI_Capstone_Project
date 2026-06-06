import urllib.request, json

BASE = "http://localhost:8000/api/v1"

def req(path, method="GET", data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token: headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    r = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    with urllib.request.urlopen(r, timeout=10) as resp:
        return json.loads(resp.read())

login = req("/auth/login", "POST", {"email": "admin@rageval.com", "password": "Admin123!"})
token = login["access_token"]
dash = req("/dashboard/summary", token=token)

print("Dashboard Summary:")
print(f"  Total Evaluations:  {dash['total_evaluations']}")
print(f"  Completed:          {dash['completed_evaluations']}")
print(f"  Avg Faithfulness:   {dash['avg_faithfulness']}")
print(f"  Avg Relevancy:      {dash['avg_answer_relevancy']}")
print(f"  Avg Hall.Risk:      {dash['avg_hallucination_risk']}")
print(f"  Avg Latency (ms):   {dash['avg_latency_ms']}")
print()

# Check trends
trends = req("/dashboard/trends?days=30", token=token)
print(f"Trend datapoints: {trends['data_points']}")
for t in trends["trends"]:
    print(f"  Run: {t['run_name']}  faith={t['faithfulness']}  rel={t['answer_relevancy']}  hall={t['hallucination_risk']}")
