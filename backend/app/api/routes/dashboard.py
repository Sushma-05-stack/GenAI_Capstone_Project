"""
/dashboard/* routes: system metrics, trend analytics
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime, timezone, timedelta
from app.api.deps import get_current_user, require_admin
from app.models.user import User
from app.models.evaluation import EvaluationRun, EvaluationResult, EvalStatus
from app.models.dataset import Dataset
from app.models.fallback import FallbackEvent
from app.models.feedback import Feedback

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.post("/reconnect-chroma", dependencies=[Depends(require_admin)])
async def reconnect_chroma():
    """Force ChromaDB client reset — use after updating CHROMA_TENANT in .env."""
    from app.db.chromadb import reset_client, get_chroma_client, get_mode
    reset_client()
    try:
        client = get_chroma_client()
        mode = get_mode()
        cols = len(client.list_collections())
        return {"mode": mode, "collections": cols, "message": f"Reconnected in {mode} mode"}
    except Exception as e:
        return {"error": str(e)}


@router.get("/status")
async def get_status(current_user: User = Depends(get_current_user)):
    """Integration status: ChromaDB mode, LangSmith, LLM providers."""
    from app.db.chromadb import get_chroma_client, get_mode
    from app.core.config import settings

    # ChromaDB
    chroma_mode = "unknown"
    chroma_collections = 0
    try:
        client = get_chroma_client()
        chroma_mode = get_mode()
        chroma_collections = len(client.list_collections())
    except Exception as e:
        chroma_mode = f"error: {str(e)[:80]}"

    # LLM providers configured
    providers = []
    if settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY) > 10:
        providers.append("openai")
    if settings.GROQ_API_KEY and len(settings.GROQ_API_KEY) > 10:
        providers.append("groq")
    if settings.GOOGLE_API_KEY and len(settings.GOOGLE_API_KEY) > 10:
        providers.append("gemini")
    if settings.ANTHROPIC_API_KEY and not settings.ANTHROPIC_API_KEY.startswith("sk-ant-..."):
        providers.append("claude")

    return {
        "chromadb": {
            "mode": chroma_mode,           # "cloud" or "local"
            "collections": chroma_collections,
            "cloud_configured": settings.use_cloud_chroma,
            "tenant": settings.CHROMA_TENANT,
            "database": settings.CHROMA_DATABASE,
        },
        "langsmith": {
            "enabled": settings.langsmith_enabled,
            "project": settings.LANGSMITH_PROJECT.strip('"').strip("'"),
            "endpoint": settings.LANGSMITH_ENDPOINT,
            "dashboard_url": f"https://smith.langchain.com/projects/{settings.LANGSMITH_PROJECT.strip(chr(34)).strip(chr(39))}",
        },
        "llm_providers": providers,
        "primary_llm": providers[0] if providers else "none",
    }


@router.get("/summary")
async def get_summary(current_user: User = Depends(get_current_user)):
    """Main dashboard KPIs."""
    total_evals = await EvaluationRun.find(
        EvaluationRun.owner_id == str(current_user.id)
    ).count()
    total_completed = await EvaluationRun.find(
        EvaluationRun.owner_id == str(current_user.id),
        EvaluationRun.status == EvalStatus.COMPLETED,
    ).count()
    total_datasets = await Dataset.find(
        Dataset.owner_id == str(current_user.id), Dataset.is_deleted == False
    ).count()
    total_queries = await EvaluationResult.find_all().count()
    total_fallbacks = await FallbackEvent.find_all().count()

    # Aggregate metrics from completed runs
    completed_runs = await EvaluationRun.find(
        EvaluationRun.owner_id == str(current_user.id),
        EvaluationRun.status == EvalStatus.COMPLETED,
    ).to_list()

    def safe_avg(lst):
        vals = [v for v in lst if v is not None]
        return round(sum(vals) / len(vals), 4) if vals else None

    avg_faith = safe_avg([r.avg_faithfulness for r in completed_runs])
    avg_rel = safe_avg([r.avg_answer_relevancy for r in completed_runs])
    avg_ctx_prec = safe_avg([r.avg_context_precision for r in completed_runs])
    avg_ctx_rec = safe_avg([r.avg_context_recall for r in completed_runs])
    avg_hall = safe_avg([r.avg_hallucination_risk for r in completed_runs])
    avg_latency = safe_avg([r.avg_latency_ms for r in completed_runs])
    avg_cost = safe_avg([r.total_cost_usd for r in completed_runs])

    return {
        "total_evaluations": total_evals,
        "completed_evaluations": total_completed,
        "total_queries": total_queries,
        "total_datasets": total_datasets,
        "total_fallback_events": total_fallbacks,
        "avg_faithfulness": avg_faith,
        "avg_answer_relevancy": avg_rel,
        "avg_context_precision": avg_ctx_prec,
        "avg_context_recall": avg_ctx_rec,
        "avg_hallucination_risk": avg_hall,
        "avg_latency_ms": avg_latency,
        "avg_cost_usd": avg_cost,
    }


@router.get("/trends")
async def get_trends(
    current_user: User = Depends(get_current_user),
    days: int = Query(30, ge=1, le=365),
):
    """Time-series trend data for RAGAS metrics."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    runs = await EvaluationRun.find(
        EvaluationRun.owner_id == str(current_user.id),
        EvaluationRun.status == EvalStatus.COMPLETED,
        {"completed_at": {"$gte": since}},
    ).sort("+completed_at").to_list()

    trends = [
        {
            "date": r.completed_at.isoformat() if r.completed_at else None,
            "run_name": r.name,
            "model": r.model_name,
            "provider": r.provider,
            "faithfulness": r.avg_faithfulness,
            "answer_relevancy": r.avg_answer_relevancy,
            "context_precision": r.avg_context_precision,
            "context_recall": r.avg_context_recall,
            "hallucination_risk": r.avg_hallucination_risk,
            "latency_ms": r.avg_latency_ms,
            "cost_usd": r.total_cost_usd,
        }
        for r in runs
    ]
    return {"trends": trends, "days": days, "data_points": len(trends)}


@router.get("/model-usage")
async def model_usage(current_user: User = Depends(get_current_user)):
    """Model usage distribution from evaluation runs."""
    runs = await EvaluationRun.find(
        EvaluationRun.owner_id == str(current_user.id)
    ).to_list()

    usage = {}
    for r in runs:
        key = f"{r.provider}/{r.model_name}"
        usage[key] = usage.get(key, 0) + 1

    return {
        "model_usage": [
            {"label": k, "count": v} for k, v in sorted(usage.items(), key=lambda x: -x[1])
        ]
    }


@router.get("/hallucination-report")
async def hallucination_report(
    current_user: User = Depends(get_current_user),
    days: int = Query(30, ge=1, le=365),
):
    """High hallucination risk results."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    # Get user's run IDs
    run_ids = [
        str(r.id)
        for r in await EvaluationRun.find(
            EvaluationRun.owner_id == str(current_user.id)
        ).to_list()
    ]
    high_risk = await EvaluationResult.find(
        {"run_id": {"$in": run_ids}, "hallucination_risk": {"$gte": 0.5}, "created_at": {"$gte": since}}
    ).to_list()

    return {
        "high_risk_count": len(high_risk),
        "threshold": 0.5,
        "results": [
            {
                "id": str(r.id),
                "question": r.question[:100],
                "hallucination_risk": r.hallucination_risk,
                "faithfulness": r.faithfulness,
                "model_used": r.model_used,
                "created_at": r.created_at,
            }
            for r in high_risk
        ],
    }
