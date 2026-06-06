"""Quick API smoke test - verifies all major endpoints are working."""
import urllib.request
import json

BASE = "http://localhost:8000/api/v1"


def req(url, method="GET", data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(r) as resp:
        return json.loads(resp.read())


def main():
    print("=" * 60)
    print("RAG Eval Dashboard - API Smoke Test")
    print("=" * 60)

    # 1. Health
    health = req(f"{BASE.replace('/api/v1', '')}/health")
    print(f"[1] Health: {health['status']} | env: {health['env']}")

    # 2. Login
    login = req(f"{BASE}/auth/login", "POST", {
        "email": "admin@rageval.com",
        "password": "Admin123!"
    })
    token = login["access_token"]
    print(f"[2] Login: token_type={login['token_type']}")

    # 3. Get current user
    me = req(f"{BASE}/users/me", token=token)
    print(f"[3] User: {me['email']} | role={me['role']}")

    # 4. Create dataset with QA pairs
    dataset = req(f"{BASE}/datasets/", "POST", {
        "name": "RAGAS Smoke Test Dataset",
        "description": "Auto-created by test script",
        "tags": ["test", "ragas", "smoke"],
        "qa_pairs": [
            {
                "question": "What is RAG?",
                "ground_truth": "Retrieval-Augmented Generation combines retrieval with LLM generation.",
                "context": []
            },
            {
                "question": "What is faithfulness in RAGAS?",
                "ground_truth": "Faithfulness measures if the answer is grounded in retrieved context.",
                "context": []
            },
            {
                "question": "What is hallucination risk?",
                "ground_truth": "Hallucination risk is 1 minus faithfulness - the probability of fabricated content.",
                "context": []
            }
        ]
    }, token=token)
    dataset_id = dataset["id"]
    print(f"[4] Dataset created: id={dataset_id[:16]}... | qa_count={dataset['qa_count']}")

    # 5. List datasets
    datasets = req(f"{BASE}/datasets/", token=token)
    print(f"[5] Datasets list: total={datasets['total']}")

    # 6. Create a prompt
    prompt = req(f"{BASE}/prompts/", "POST", {
        "name": "Default RAG Prompt",
        "version": "1.0",
        "content": "Answer the question based ONLY on context.\n\nContext:\n{context}\n\nQuestion: {question}\n\nAnswer:",
        "description": "Standard factual RAG prompt",
        "tags": ["default", "factual"]
    }, token=token)
    print(f"[6] Prompt created: {prompt['name']} v{prompt['version']}")

    # 7. Dashboard summary
    dash = req(f"{BASE}/dashboard/summary", token=token)
    print(f"[7] Dashboard: evals={dash['total_evaluations']} | datasets={dash['total_datasets']} | queries={dash['total_queries']}")

    # 8. Supported models
    models = req(f"{BASE}/models/supported", token=token)
    print(f"[8] Supported models: {len(models['models'])} configured")

    # 9. Security stats
    sec = req(f"{BASE}/security/stats", token=token)
    print(f"[9] Security: audit_events={sec['total_audit_events']} | failed_logins={sec['failed_logins']}")

    # 10. Security logs (admin only)
    logs = req(f"{BASE}/security/logs", token=token)
    print(f"[10] Audit logs: {logs['total']} total entries")

    print()
    print("=" * 60)
    print("ALL TESTS PASSED - Backend is fully operational!")
    print(f"Dataset ID for evaluation: {dataset_id}")
    print("=" * 60)


if __name__ == "__main__":
    main()
