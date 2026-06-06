from beanie import Document as BeanieDocument, Indexed
from pydantic import Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum


class FallbackReason(str, Enum):
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    PROVIDER_ERROR = "provider_error"
    CONTEXT_LENGTH = "context_length"
    CONTENT_FILTER = "content_filter"
    UNKNOWN = "unknown"


class FallbackEvent(BeanieDocument):
    query_id: Optional[str] = None
    primary_provider: str
    primary_model: str
    fallback_provider: str
    fallback_model: str
    reason: FallbackReason
    error_message: Optional[str] = None
    latency_before_fallback_ms: Optional[float] = None
    latency_after_fallback_ms: Optional[float] = None
    success: bool = True
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "fallback_events"
        indexes = ["primary_provider", "fallback_provider", "reason", "created_at"]
