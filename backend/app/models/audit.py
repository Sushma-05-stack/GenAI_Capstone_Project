from beanie import Document as BeanieDocument, Indexed
from pydantic import Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum


class AuditAction(str, Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"
    PASSWORD_RESET = "password_reset"
    UPLOAD_DOCUMENT = "upload_document"
    DELETE_DOCUMENT = "delete_document"
    CREATE_DATASET = "create_dataset"
    DELETE_DATASET = "delete_dataset"
    RUN_EVALUATION = "run_evaluation"
    QUERY_RAG = "query_rag"
    PROMPT_INJECTION_DETECTED = "prompt_injection_detected"
    ROLE_CHANGED = "role_changed"
    API_KEY_ACCESSED = "api_key_accessed"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    EXPORT_REPORT = "export_report"


class AuditLog(BeanieDocument):
    user_id: Optional[str] = None
    action: AuditAction
    resource: Optional[str] = None  # e.g., dataset_id, document_id
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    details: Dict[str, Any] = {}
    risk_level: str = "low"  # low, medium, high
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "audit_logs"
        indexes = ["user_id", "action", "created_at", "risk_level"]
