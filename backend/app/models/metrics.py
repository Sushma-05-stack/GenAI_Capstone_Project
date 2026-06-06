from beanie import Document as BeanieDocument
from pydantic import Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone


class SystemMetric(BeanieDocument):
    """Periodic system metrics snapshot."""
    total_evaluations: int = 0
    total_queries: int = 0
    total_datasets: int = 0
    active_users: int = 0
    avg_latency_ms: Optional[float] = None
    avg_cost_usd: Optional[float] = None
    avg_faithfulness: Optional[float] = None
    avg_answer_relevancy: Optional[float] = None
    avg_context_precision: Optional[float] = None
    avg_context_recall: Optional[float] = None
    avg_hallucination_risk: Optional[float] = None
    fallback_count: int = 0
    error_count: int = 0
    snapshot_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "system_metrics"
        indexes = ["snapshot_at"]
