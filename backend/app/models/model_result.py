from beanie import Document as BeanieDocument, Indexed
from pydantic import Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone


class ModelResult(BeanieDocument):
    """Aggregated per-model benchmark results."""
    run_id: Indexed(str)
    provider: str
    model_name: str
    avg_faithfulness: Optional[float] = None
    avg_answer_relevancy: Optional[float] = None
    avg_context_precision: Optional[float] = None
    avg_context_recall: Optional[float] = None
    avg_hallucination_risk: Optional[float] = None
    avg_latency_ms: Optional[float] = None
    total_cost_usd: Optional[float] = None
    success_rate: Optional[float] = None
    failure_rate: Optional[float] = None
    fallback_rate: Optional[float] = None
    total_queries: int = 0
    user_rating: Optional[float] = None  # avg user feedback rating
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "model_results"
        indexes = ["run_id", "provider", "model_name"]
