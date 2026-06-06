"""
1. Reindex all datasets
2. Start a real evaluation run with 2 questions
3. Poll until complete
4. Print scores
"""
import urllib.request, json, time

BASE = "http://localhost:8000/api/v1"

def req(path, method="GET", data=None, token=None, timeout=60):
    headers = {"Content-Type": "application/json"}
    if token: headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    r = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return json.loads(resp.read())

def main():
    # Login
    login = req("/auth/login", "POST", {"email": "admin@rageval.com", "password": "Admin123!"})
    token = login["access_token"]
    print("Logged in as admin")

    # Get datasets
    datasets = req("/datasets/?page_size=10", token=token)
    ds_list = datasets["datasets"]
    print(f"Found {len(ds_list)} datasets")

    # Pick dataset with most QA pairs
    best_ds = max(ds_list, key=lambda d: d["qa_count"])
    print(f"Using dataset: '{best_ds['name']}' ({best_ds['qa_count']} QA pairs)")

    # Reindex
    try:
        r = req(f"/datasets/{best_ds['id']}/reindex", "POST", token=token)
        print(f"Reindex started: {r['message']}")
        time.sleep(5)  # wait for indexing
    except Exception as e:
        print(f"Reindex error (ok if already indexed): {e}")

    # Start evaluation
    eval_run = req("/evaluation/run", "POST", {
        "name": "Auto Test Eval - Groq",
        "dataset_id": best_ds["id"],
        "model_name": "llama-3.3-70b-versatile",
        "provider": "groq",
        "max_questions": 2,  # fast test
    }, token=token)
    run_id = eval_run["id"]
    print(f"\nEvaluation started: {run_id}")
    print("Polling for completion (runs in background)...")

    # Poll
    for attempt in range(40):
        time.sleep(8)
        run = req(f"/evaluation/{run_id}", token=token)
        status = run["status"]
        completed = run["completed_questions"]
        total = run["total_questions"]
        print(f"  [{attempt+1}] status={status} questions={completed}/{total}")

        if status == "completed":
            print(f"\n{'='*50}")
            print("EVALUATION COMPLETE!")
            print(f"  Faithfulness:       {run.get('avg_faithfulness')}")
            print(f"  Answer Relevancy:   {run.get('avg_answer_relevancy')}")
            print(f"  Context Precision:  {run.get('avg_context_precision')}")
            print(f"  Context Recall:     {run.get('avg_context_recall')}")
            print(f"  Hallucination Risk: {run.get('avg_hallucination_risk')}")
            print(f"  Avg Latency:        {run.get('avg_latency_ms')} ms")
            print(f"  Total Cost:         ${run.get('total_cost_usd')}")
            print(f"{'='*50}")

            # Show per-question results
            results = req(f"/evaluation/{run_id}/results", token=token)
            print(f"\nPer-question results ({results['total']} items):")
            for res in results["results"]:
                print(f"  Q: {res['question'][:60]}")
                print(f"  A: {res['answer'][:80]}...")
                print(f"  Faithfulness={res['faithfulness']}  "
                      f"Relevancy={res['answer_relevancy']}  "
                      f"Hall.Risk={res['hallucination_risk']}")
                print()
            break

        elif status == "failed":
            print(f"FAILED: {run.get('error_message')}")
            break
    else:
        print("Timed out waiting for evaluation")

if __name__ == "__main__":
    main()
