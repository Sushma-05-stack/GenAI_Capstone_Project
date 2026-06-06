from beanie import Document as BeanieDocument, Indexed
from pydantic import Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum


class DatasetStatus(str, Enum):
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class QAPair(BeanieDocument):
    question: str
    ground_truth: str
    context: Optional[List[str]] = []
    metadata: Dict[str, Any] = {}


class Dataset(BeanieDocument):
    name: Indexed(str)
    description: Optional[str] = None
    owner_id: str
    version: str = "1.0"
    status: DatasetStatus = DatasetStatus.PROCESSING
    file_count: int = 0
    qa_count: int = 0
    tags: List[str] = []
    qa_pairs: List[Dict[str, Any]] = []  # embedded QA pairs for small sets
    metadata: Dict[str, Any] = {}
    is_deleted: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "datasets"
        indexes = ["owner_id", "name", "status", "is_deleted"]
