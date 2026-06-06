from beanie import Document as BeanieDocument, Indexed
from pydantic import Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum


class EvalStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class EvaluationRun(BeanieDocument):
    name: str
    dataset_id: Indexed(str)
    owner_id: str
    prompt_version_id: Optional[str] = None
    model_name: str
    provider: str
    status: EvalStatus = EvalStatus.PENDING
    total_questions: int = 0
    completed_questions: int = 0
    # Aggregate scores
    avg_faithfulness: Optional[float] = None
    avg_answer_relevancy: Optional[float] = None
    avg_context_precision: Optional[float] = None
    avg_context_recall: Optional[float] = None
    avg_hallucination_risk: Optional[float] = None
    avg_retrieval_quality: Optional[float] = None
    avg_latency_ms: Optional[float] = None
    total_cost_usd: Optional[float] = None
    langsmith_run_id: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "evaluation_runs"
        indexes = ["dataset_id", "owner_id", "status", "model_name"]


class EvaluationResult(BeanieDocument):
    run_id: Indexed(str)
    question: str
    answer: str
    ground_truth: Optional[str] = None
    contexts: List[str] = []
    retrieved_chunks: List[Dict[str, Any]] = []
    # RAGAS metrics
    faithfulness: Optional[float] = None
    answer_relevancy: Optional[float] = None
    context_precision: Optional[float] = None
    context_recall: Optional[float] = None
    hallucination_risk: Optional[float] = None
    retrieval_quality: Optional[float] = None
    # Perf
    latency_ms: Optional[float] = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: Optional[float] = None
    model_used: str = ""
    provider_used: str = ""
    fallback_used: bool = False
    langsmith_trace_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "evaluation_results"
        indexes = ["run_id", "faithfulness", "hallucination_risk"]
