from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.dataset import DatasetStatus


class QAPairIn(BaseModel):
    question: str
    ground_truth: str
    context: Optional[List[str]] = []
    metadata: Dict[str, Any] = {}


class DatasetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    tags: List[str] = []
    qa_pairs: Optional[List[QAPairIn]] = []


class DatasetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class DatasetOut(BaseModel):
    id: str
    name: str
    description: Optional[str]
    owner_id: str
    version: str
    status: DatasetStatus
    file_count: int
    qa_count: int
    tags: List[str]
    created_at: datetime
    updated_at: datetime


class DatasetListResponse(BaseModel):
    datasets: List[DatasetOut]
    total: int
    page: int
    page_size: int
