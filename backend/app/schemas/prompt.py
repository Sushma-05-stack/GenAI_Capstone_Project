from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class PromptCreate(BaseModel):
    name: str
    version: str = "1.0"
    content: str
    description: Optional[str] = None
    tags: List[str] = []


class PromptUpdate(BaseModel):
    content: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class PromptOut(BaseModel):
    id: str
    name: str
    version: str
    content: str
    description: Optional[str]
    owner_id: str
    is_active: bool
    tags: List[str]
    avg_faithfulness: Optional[float]
    avg_answer_relevancy: Optional[float]
    avg_latency_ms: Optional[float]
    eval_count: int
    created_at: datetime


class PromptCompareRequest(BaseModel):
    prompt_a_id: str
    prompt_b_id: str
    dataset_id: str
    model_name: str
    provider: str
    max_questions: int = 10


class PromptCompareResult(BaseModel):
    prompt_a: PromptOut
    prompt_b: PromptOut
    accuracy_diff: float
    faithfulness_diff: float
    relevancy_diff: float
    latency_diff_ms: float
    cost_diff_usd: float
    winner: str  # "A" | "B" | "tie"
    details: Dict[str, Any] = {}
