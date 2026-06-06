from beanie import Document as BeanieDocument, Indexed
from pydantic import Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone


class PromptVersion(BeanieDocument):
    name: Indexed(str)
    version: str
    content: str  # The prompt template with {context} and {question} placeholders
    description: Optional[str] = None
    owner_id: str
    is_active: bool = True
    tags: List[str] = []
    variables: List[str] = []  # extracted template variables
    metadata: Dict[str, Any] = {}
    # Aggregated performance (filled after eval runs)
    avg_faithfulness: Optional[float] = None
    avg_answer_relevancy: Optional[float] = None
    avg_latency_ms: Optional[float] = None
    eval_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "prompt_versions"
        indexes = ["owner_id", "name", "version", "is_active"]
