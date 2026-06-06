"""
/evaluation/* routes: run evaluations, fetch history and results
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import Optional
from app.api.deps import get_current_user, require_evaluator
from app.models.user import User
from app.models.evaluation import EvaluationRun, EvaluationResult, EvalStatus
from app.schemas.evaluation import (
    EvaluationRunRequest, EvaluationRunOut, EvaluationResultOut, EvaluationHistoryResponse
)
from app.services.evaluation.runner import run_evaluation
from app.security.audit import log_event
from app.models.audit import AuditAction
from datetime import datetime, timezone

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])


def _run_out(r: EvaluationRun) -> EvaluationRunOut:
    return EvaluationRunOut(
        id=str(r.id),
        name=r.name,
        dataset_id=r.dataset_id,
        owner_id=r.owner_id,
        model_name=r.model_name,
        provider=r.provider,
        status=r.status,
        total_questions=r.total_questions,
        completed_questions=r.completed_questions,
        avg_faithfulness=r.avg_faithfulness,
        avg_answer_relevancy=r.avg_answer_relevancy,
        avg_context_precision=r.avg_context_precision,
        avg_context_recall=r.avg_context_recall,
        avg_hallucination_risk=r.avg_hallucination_risk,
        avg_latency_ms=r.avg_latency_ms,
        total_cost_usd=r.total_cost_usd,
        langsmith_run_id=r.langsmith_run_id,
        started_at=r.started_at,
        completed_at=r.completed_at,
        created_at=r.created_at,
    )


@router.post("/run", response_model=EvaluationRunOut, dependencies=[Depends(require_evaluator)])
async def start_evaluation(
    payload: EvaluationRunRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    run = EvaluationRun(
        name=payload.name,
        dataset_id=payload.dataset_id,
        owner_id=str(current_user.id),
        model_name=payload.model_name,
        provider=payload.provider,
        prompt_version_id=payload.prompt_version_id,
        metadata={"max_questions": payload.max_questions, "top_k": payload.top_k},
    )
    await run.insert()
    background_tasks.add_task(run_evaluation, run)

    await log_event(
        action=AuditAction.RUN_EVALUATION,
        user_id=str(current_user.id),
        resource=str(run.id),
        details={"dataset_id": payload.dataset_id, "model": payload.model_name},
    )
    return _run_out(run)


@router.get("/history", response_model=EvaluationHistoryResponse)
async def get_history(
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    dataset_id: Optional[str] = None,
    status: Optional[EvalStatus] = None,
):
    query_filter = {"owner_id": str(current_user.id)}
    if dataset_id:
        query_filter["dataset_id"] = dataset_id
    if status:
        query_filter["status"] = status

    runs = await EvaluationRun.find(query_filter).skip((page - 1) * page_size).limit(page_size).to_list()
    total = await EvaluationRun.find(query_filter).count()
    return EvaluationHistoryResponse(runs=[_run_out(r) for r in runs], total=total)


@router.delete("/{run_id}", dependencies=[Depends(require_evaluator)])
async def delete_run(run_id: str, current_user: User = Depends(get_current_user)):
    run = await EvaluationRun.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    if run.owner_id != str(current_user.id) and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not allowed to delete this run")
    # Delete all per-question results first
    await EvaluationResult.find(EvaluationResult.run_id == run_id).delete()
    await run.delete()
    return {"message": "Evaluation run deleted", "id": run_id}


@router.get("/{run_id}", response_model=EvaluationRunOut)
async def get_run(run_id: str, current_user: User = Depends(get_current_user)):
    run = await EvaluationRun.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    return _run_out(run)


@router.get("/{run_id}/results")
async def get_results(
    run_id: str,
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    results = (
        await EvaluationResult.find(EvaluationResult.run_id == run_id)
        .skip((page - 1) * page_size)
        .limit(page_size)
        .to_list()
    )
    total = await EvaluationResult.find(EvaluationResult.run_id == run_id).count()

    def _result_out(r: EvaluationResult) -> dict:
        return {
            "id": str(r.id),
            "run_id": r.run_id,
            "question": r.question,
            "answer": r.answer,
            "ground_truth": r.ground_truth,
            "contexts": r.contexts,
            "faithfulness": r.faithfulness,
            "answer_relevancy": r.answer_relevancy,
            "context_precision": r.context_precision,
            "context_recall": r.context_recall,
            "hallucination_risk": r.hallucination_risk,
            "retrieval_quality": r.retrieval_quality,
            "latency_ms": r.latency_ms,
            "cost_usd": r.cost_usd,
            "model_used": r.model_used,
            "provider_used": r.provider_used,
            "fallback_used": r.fallback_used,
            "langsmith_trace_url": r.langsmith_trace_url,
            "created_at": r.created_at,
        }

    return {"results": [_result_out(r) for r in results], "total": total, "page": page, "page_size": page_size}
