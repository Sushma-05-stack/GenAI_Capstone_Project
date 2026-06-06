from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.evaluation import EvalStatus


class EvaluationRunRequest(BaseModel):
    name: str
    dataset_id: str
    model_name: str
    provider: str  # openai | gemini | groq | claude | auto
    prompt_version_id: Optional[str] = None
    top_k: int = 5
    max_questions: Optional[int] = None  # limit for testing


class EvaluationRunOut(BaseModel):
    id: str
    name: str
    dataset_id: str
    owner_id: str
    model_name: str
    provider: str
    status: EvalStatus
    total_questions: int
    completed_questions: int
    avg_faithfulness: Optional[float]
    avg_answer_relevancy: Optional[float]
    avg_context_precision: Optional[float]
    avg_context_recall: Optional[float]
    avg_hallucination_risk: Optional[float]
    avg_latency_ms: Optional[float]
    total_cost_usd: Optional[float]
    langsmith_run_id: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime


class EvaluationResultOut(BaseModel):
    id: str
    run_id: str
    question: str
    answer: str
    ground_truth: Optional[str]
    contexts: List[str]
    faithfulness: Optional[float]
    answer_relevancy: Optional[float]
    context_precision: Optional[float]
    context_recall: Optional[float]
    hallucination_risk: Optional[float]
    retrieval_quality: Optional[float]
    latency_ms: Optional[float]
    cost_usd: Optional[float]
    model_used: str
    provider_used: str
    fallback_used: bool
    langsmith_trace_url: Optional[str]
    created_at: datetime


class EvaluationHistoryResponse(BaseModel):
    runs: List[EvaluationRunOut]
    total: int


class RAGQueryRequest(BaseModel):
    question: str
    dataset_id: str
    model_name: Optional[str] = None
    provider: Optional[str] = "auto"
    prompt_version_id: Optional[str] = None
    top_k: int = 5
    return_contexts: bool = True


class RAGQueryResponse(BaseModel):
    question: str
    answer: str
    contexts: List[str]
    retrieved_chunks: List[Dict[str, Any]]
    model_used: str
    provider_used: str
    fallback_used: bool
    latency_ms: float
    cost_usd: Optional[float]
    langsmith_trace_url: Optional[str]
