from beanie import Document as BeanieDocument, Indexed
from pydantic import Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    INDEXED = "indexed"
    ERROR = "error"


class Document(BeanieDocument):
    dataset_id: Indexed(str)
    owner_id: str
    filename: str
    file_type: str  # pdf, docx, txt, csv
    file_size: int  # bytes
    storage_path: str
    status: DocumentStatus = DocumentStatus.UPLOADED
    chunk_count: int = 0
    chroma_collection: Optional[str] = None
    metadata: Dict[str, Any] = {}
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "documents"
        indexes = ["dataset_id", "owner_id", "status"]


class Chunk(BeanieDocument):
    document_id: Indexed(str)
    dataset_id: str
    content: str
    chunk_index: int
    chroma_id: str  # ID in ChromaDB
    embedding_model: str = "text-embedding-3-small"
    token_count: int = 0
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "chunks"
        indexes = ["document_id", "dataset_id", "chroma_id"]
