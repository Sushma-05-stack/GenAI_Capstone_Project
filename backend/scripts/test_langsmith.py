"""Test LangSmith connection and create a test trace."""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()

api_key  = os.getenv("LANGSMITH_API_KEY", "")
project  = os.getenv("LANGSMITH_PROJECT", "rag-eval-dashboard").strip('"').strip("'")
endpoint = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

print(f"Key     : {api_key[:20]}...")
print(f"Project : {project}")
print(f"Endpoint: {endpoint}")
print()

# Test 1: direct HTTP check
import urllib.request, json
req = urllib.request.Request(
    f"{endpoint}/api/v1/workspaces",
    headers={"x-api-key": api_key}
)
try:
    with urllib.request.urlopen(req, timeout=10) as r:
        ws = json.loads(r.read())
        print(f"LangSmith workspaces: {len(ws)}")
        for w in ws[:3]:
            print(f"  - {w.get('name', w.get('id','?'))}")
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.read().decode()[:200]}")
except Exception as e:
    print(f"Connection error: {e}")

# Test 2: create a real trace using langsmith SDK
print()
print("Creating test trace via SDK...")
try:
    from langsmith import Client, traceable

    client = Client(api_url=endpoint, api_key=api_key)

    # Set env vars
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"]    = api_key
    os.environ["LANGCHAIN_PROJECT"]    = project
    os.environ["LANGCHAIN_ENDPOINT"]   = endpoint

    @traceable(name="test_rag_trace", project_name=project, run_type="chain")
    def test_chain(question: str) -> dict:
        return {"answer": f"Test answer for: {question}", "contexts": 3}

    result = test_chain("What is RAG?")
    print(f"Trace created! Result: {result}")
    print(f"Check LangSmith: https://smith.langchain.com/projects/{project}")

except Exception as e:
    print(f"SDK trace failed: {e}")

    # Test 3: create run manually via client
    print()
    print("Trying manual run creation...")
    try:
        import uuid
        run_id = str(uuid.uuid4())
        client.create_run(
            id=run_id,
            name="manual_test_trace",
            run_type="chain",
            project_name=project,
            inputs={"question": "What is RAG?"},
        )
        client.update_run(
            run_id,
            outputs={"answer": "RAG is Retrieval-Augmented Generation"},
        )
        print(f"Manual trace created: {run_id}")
        print(f"View at: https://smith.langchain.com/projects/{project}")
    except Exception as e2:
        print(f"Manual trace also failed: {e2}")
