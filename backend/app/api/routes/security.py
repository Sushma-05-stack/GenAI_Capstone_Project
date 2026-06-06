"""
/security/logs - Audit log viewer (admin only)
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.api.deps import require_admin, get_current_user
from app.models.user import User
from app.models.audit import AuditLog, AuditAction

router = APIRouter(prefix="/security", tags=["Security"])


@router.get("/logs", dependencies=[Depends(require_admin)])
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    action: Optional[AuditAction] = None,
    risk_level: Optional[str] = None,
    user_id: Optional[str] = None,
):
    filters = {}
    if action:
        filters["action"] = action
    if risk_level:
        filters["risk_level"] = risk_level
    if user_id:
        filters["user_id"] = user_id

    logs = (
        await AuditLog.find(filters)
        .sort("-created_at")
        .skip((page - 1) * page_size)
        .limit(page_size)
        .to_list()
    )
    total = await AuditLog.find(filters).count()

    return {
        "logs": [
            {
                "id": str(log.id),
                "user_id": log.user_id,
                "action": log.action,
                "resource": log.resource,
                "ip_address": log.ip_address,
                "success": log.success,
                "risk_level": log.risk_level,
                "details": log.details,
                "created_at": log.created_at,
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/stats", dependencies=[Depends(require_admin)])
async def security_stats():
    """Security event summary."""
    from datetime import timedelta, datetime, timezone
    since_24h = datetime.now(timezone.utc) - timedelta(hours=24)

    total_events = await AuditLog.find_all().count()
    high_risk = await AuditLog.find(AuditLog.risk_level == "high").count()
    failed_logins = await AuditLog.find(
        {"action": AuditAction.LOGIN, "success": False}
    ).count()
    injection_attempts = await AuditLog.find(
        AuditLog.action == AuditAction.PROMPT_INJECTION_DETECTED
    ).count()
    events_24h = await AuditLog.find({"created_at": {"$gte": since_24h}}).count()

    return {
        "total_audit_events": total_events,
        "high_risk_events": high_risk,
        "failed_logins": failed_logins,
        "injection_attempts": injection_attempts,
        "events_last_24h": events_24h,
    }
