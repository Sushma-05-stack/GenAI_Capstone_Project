"""
/rag/query - RAG pipeline endpoint with security checks
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.evaluation import RAGQueryRequest, RAGQueryResponse
from app.services.rag.pipeline import run_rag_query
from app.security.injection import detect_prompt_injection, validate_input
from app.security.audit import log_event
from app.models.audit import AuditAction
from app.core.logging import logger

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post("/query", response_model=RAGQueryResponse)
async def query_rag(
    payload: RAGQueryRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    # Input validation
    valid, err = validate_input(payload.question)
    if not valid:
        raise HTTPException(status_code=400, detail=err)

    # Prompt injection detection
    injected, reason = detect_prompt_injection(payload.question)
    if injected:
        await log_event(
            action=AuditAction.PROMPT_INJECTION_DETECTED,
            user_id=str(current_user.id),
            ip_address=request.client.host,
            details={"reason": reason, "question_preview": payload.question[:100]},
            risk_level="high",
            success=False,
        )
        raise HTTPException(status_code=400, detail=f"Input rejected: {reason}")

    try:
        response = await run_rag_query(
            question=payload.question,
            dataset_id=payload.dataset_id,
            provider=payload.provider or "auto",
            model_name=payload.model_name,
            prompt_version_id=payload.prompt_version_id,
            top_k=payload.top_k,
        )
        await log_event(
            action=AuditAction.QUERY_RAG,
            user_id=str(current_user.id),
            resource=payload.dataset_id,
            details={"model": response.model_used, "latency_ms": response.latency_ms},
        )
        return response
    except Exception as e:
        logger.error("RAG query failed", error=str(e))
        raise HTTPException(status_code=500, detail="RAG query failed. Please try again.")
