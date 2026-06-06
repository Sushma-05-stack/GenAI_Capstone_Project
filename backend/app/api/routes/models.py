"""
/models/compare - Multi-model benchmarking
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.api.deps import get_current_user, require_evaluator
from app.models.user import User
from app.models.evaluation import EvaluationRun, EvaluationResult
from app.models.fallback import FallbackEvent

router = APIRouter(prefix="/models", tags=["Models"])

SUPPORTED_MODELS = [
    {"provider": "openai", "model": "gpt-4o", "display": "GPT-4o"},
    {"provider": "openai", "model": "gpt-4o-mini", "display": "GPT-4o Mini"},
    {"provider": "gemini", "model": "gemini-1.5-pro", "display": "Gemini 1.5 Pro"},
    {"provider": "gemini", "model": "gemini-1.5-flash", "display": "Gemini 1.5 Flash"},
    {"provider": "groq", "model": "llama3-70b-8192", "display": "Llama3 70B (Groq)"},
    {"provider": "claude", "model": "claude-3-5-sonnet-20241022", "display": "Claude 3.5 Sonnet"},
]


@router.get("/supported")
async def list_supported_models():
    return {"models": SUPPORTED_MODELS}


@router.get("/compare")
async def compare_models(
    run_ids: str,  # comma-separated run IDs
    current_user: User = Depends(get_current_user),
):
    """Compare metrics across multiple evaluation runs (different models)."""
    ids = [rid.strip() for rid in run_ids.split(",") if rid.strip()]
    if not ids:
        raise HTTPException(status_code=400, detail="Provide at least one run_id")

    comparison = []
    for run_id in ids:
        run = await EvaluationRun.get(run_id)
        if not run:
            continue
        comparison.append({
            "run_id": str(run.id),
            "run_name": run.name,
            "provider": run.provider,
            "model": run.model_name,
            "faithfulness": run.avg_faithfulness,
            "answer_relevancy": run.avg_answer_relevancy,
            "context_precision": run.avg_context_precision,
            "context_recall": run.avg_context_recall,
            "hallucination_risk": run.avg_hallucination_risk,
            "retrieval_quality": run.avg_retrieval_quality,
            "avg_latency_ms": run.avg_latency_ms,
            "total_cost_usd": run.total_cost_usd,
            "total_questions": run.total_questions,
            "status": run.status,
        })

    return {"comparison": comparison, "run_count": len(comparison)}


@router.get("/fallback-analytics")
async def fallback_analytics(current_user: User = Depends(get_current_user)):
    """Aggregated fallback stats per provider pair."""
    events = await FallbackEvent.find_all().to_list()

    stats = {}
    for event in events:
        key = f"{event.primary_provider} → {event.fallback_provider}"
        if key not in stats:
            stats[key] = {"count": 0, "reasons": {}, "success_count": 0}
        stats[key]["count"] += 1
        reason = event.reason
        stats[key]["reasons"][reason] = stats[key]["reasons"].get(reason, 0) + 1
        if event.success:
            stats[key]["success_count"] += 1

    result = []
    for pair, data in stats.items():
        result.append({
            "pair": pair,
            "total_events": data["count"],
            "success_rate": round(data["success_count"] / data["count"], 3) if data["count"] else 0,
            "reasons": data["reasons"],
        })

    return {"fallback_analytics": result, "total_events": len(events)}
