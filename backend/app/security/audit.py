"""
Audit logging service.
"""
from typing import Optional, Dict, Any
from app.models.audit import AuditLog, AuditAction
from app.core.logging import logger


async def log_event(
    action: AuditAction,
    user_id: Optional[str] = None,
    resource: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    success: bool = True,
    details: Dict[str, Any] = {},
    risk_level: str = "low",
):
    """Write an audit log entry to MongoDB."""
    try:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            details=details,
            risk_level=risk_level,
        )
        await entry.insert()
    except Exception as e:
        # Audit logging must never crash the application
        logger.error("Audit log write failed", error=str(e), action=str(action))
