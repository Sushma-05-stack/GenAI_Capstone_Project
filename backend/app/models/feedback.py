from beanie import Document as BeanieDocument, Indexed
from pydantic import Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum


class FeedbackType(str, Enum):
    RATING = "rating"
    HALLUCINATION_FLAG = "hallucination_flag"
    RETRIEVAL_ISSUE = "retrieval_issue"
    GENERAL = "general"


class Feedback(BeanieDocument):
    result_id: Indexed(str)  # EvaluationResult ID
    run_id: str
    user_id: str
    feedback_type: FeedbackType
    rating: Optional[int] = None  # 1-5
    comment: Optional[str] = None
    is_hallucination: bool = False
    is_retrieval_issue: bool = False
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "feedback"
        indexes = ["result_id", "run_id", "user_id", "feedback_type"]
