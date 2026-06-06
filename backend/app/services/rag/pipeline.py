"""
RAG Pipeline — strict document-only answering.
LangSmith tracing is set up but only activates when the key works.
"""
import time
import os
from typing import Optional
from app.services.document.embedder import semantic_search
from app.services.llm.router import route_llm
from app.models.prompt import PromptVersion
from app.schemas.evaluation import RAGQueryResponse
from app.core.config import settings
from app.core.logging import logger

# Disable tracing at import time to avoid blocking startup
# It gets re-enabled per-request if the key is valid
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGSMITH_TRACING"]    = "false"

_ls_key     = (settings.LANGSMITH_API_KEY or "").strip()
_ls_project = (settings.LANGSMITH_PROJECT or "rag-eval-dashboard").strip('"').strip("'")
_ls_endpoint = settings.LANGSMITH_ENDPOINT

# Only mark as enabled if key looks real (non-placeholder)
_LANGSMITH_ENABLED = bool(
    _ls_key
    and len(_ls_key) > 20
    and not _ls_key.startswith("ls__...")
)

if _LANGSMITH_ENABLED:
    logger.info("LangSmith key detected", project=_ls_project)
else:
    logger.info("LangSmith disabled (no valid key)")


STRICT_RAG_PROMPT = """You are a document question-answering assistant.

RULES:
1. Answer ONLY using information from the Context provided below.
2. Do NOT use outside knowledge or prior training data.
3. If the context does not contain enough information, respond:
   "The provided documents do not contain enough information to answer this question."
4. Cite the source number [Source N] that supports your answer.
5. Be concise and accurate.

Context:
{context}

Question: {question}

Answer (based solely on the context above):"""

NO_CONTEXT_RESPONSE = (
    "No documents have been indexed for this dataset yet. "
    "Please upload documents to the dataset first, then ask your question."
)


async def get_prompt_template(prompt_version_id: Optional[str]) -> str:
    if prompt_version_id:
        try:
            p = await PromptVersion.get(prompt_version_id)
            if p and p.content:
                return p.content
        except Exception:
            pass
    return STRICT_RAG_PROMPT


async def run_rag_query(
    question: str,
    dataset_id: str,
    provider: str = "auto",
    model_name: Optional[str] = None,
    prompt_version_id: Optional[str] = None,
    top_k: int = 5,
    query_id: Optional[str] = None,
) -> RAGQueryResponse:
    """
    Full RAG pipeline:
      Question → ChromaDB retrieval → Strict prompt → LLM → Response
    """
    start_time = time.monotonic()
    collection = f"dataset_{dataset_id}"
    trace_url  = None

    # Step 1: Retrieve from ChromaDB
    logger.info("RAG retrieval", question=question[:80], collection=collection, top_k=top_k)
    retrieved = await semantic_search(
        collection_name=collection, query=question, top_k=top_k
    )
    contexts = [r["content"] for r in retrieved]
    logger.info("Retrieved chunks", count=len(contexts))

    # Guard: no documents indexed
    if not contexts:
        total_ms = (time.monotonic() - start_time) * 1000
        logger.warning("Empty ChromaDB collection", collection=collection)
        return RAGQueryResponse(
            question=question,
            answer=NO_CONTEXT_RESPONSE,
            contexts=[],
            retrieved_chunks=[],
            model_used="none",
            provider_used="none",
            fallback_used=False,
            latency_ms=total_ms,
            cost_usd=0.0,
            langsmith_trace_url=None,
        )

    # Step 2: Build strict document-only prompt
    context_block = "\n\n---\n\n".join(
        f"[Source {i+1}]: {ctx}" for i, ctx in enumerate(contexts)
    )
    template    = await get_prompt_template(prompt_version_id)
    prompt_text = template.format(context=context_block, question=question)
    messages    = [
        {
            "role": "system",
            "content": (
                "You are a precise document QA assistant. "
                "Answer ONLY from the provided context. "
                "Never use outside knowledge."
            ),
        },
        {"role": "user", "content": prompt_text},
    ]

    # Step 3: Generate answer
    llm_resp = await route_llm(
        messages=messages,
        provider=provider,
        model_name=model_name,
        query_id=query_id,
    )
    total_ms = (time.monotonic() - start_time) * 1000

    # LangSmith trace URL (no blocking network call)
    if _LANGSMITH_ENABLED:
        trace_url = f"https://smith.langchain.com/projects/{_ls_project}"

    logger.info(
        "RAG query complete",
        model=llm_resp.model,
        provider=llm_resp.provider,
        latency_ms=round(total_ms),
        contexts=len(contexts),
    )

    return RAGQueryResponse(
        question=question,
        answer=llm_resp.content,
        contexts=contexts,
        retrieved_chunks=retrieved,
        model_used=llm_resp.model,
        provider_used=llm_resp.provider,
        fallback_used=llm_resp.fallback_used,
        latency_ms=total_ms,
        cost_usd=llm_resp.cost_usd,
        langsmith_trace_url=trace_url,
    )
