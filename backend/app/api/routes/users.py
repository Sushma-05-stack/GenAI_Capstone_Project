"""
/users/* routes: profile, management, RBAC
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.deps import get_current_user, require_admin
from app.models.user import User, UserRole
from app.schemas.user import UserOut, UserUpdate, UserRoleUpdate, UserListResponse
from app.security.audit import log_event
from app.models.audit import AuditAction
from datetime import datetime, timezone

router = APIRouter(prefix="/users", tags=["Users"])


def _user_to_out(u: User) -> UserOut:
    return UserOut(
        id=str(u.id),
        email=u.email,
        username=u.username,
        full_name=u.full_name,
        role=u.role,
        is_active=u.is_active,
        last_login=u.last_login,
        created_at=u.created_at,
    )


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return _user_to_out(current_user)


@router.put("/me", response_model=UserOut)
async def update_me(payload: UserUpdate, current_user: User = Depends(get_current_user)):
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    if payload.avatar_url is not None:
        current_user.avatar_url = payload.avatar_url
    current_user.updated_at = datetime.now(timezone.utc)
    await current_user.save()
    return _user_to_out(current_user)


@router.get("/", response_model=UserListResponse, dependencies=[Depends(require_admin)])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: UserRole = None,
):
    query = User.find(User.is_active == True)
    if role:
        query = User.find(User.role == role)
    total = await query.count()
    users = await query.skip((page - 1) * page_size).limit(page_size).to_list()
    return UserListResponse(
        users=[_user_to_out(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.put("/{user_id}/role", response_model=UserOut, dependencies=[Depends(require_admin)])
async def update_user_role(
    user_id: str,
    payload: UserRoleUpdate,
    current_user: User = Depends(get_current_user),
):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    old_role = user.role
    user.role = payload.role
    user.updated_at = datetime.now(timezone.utc)
    await user.save()
    await log_event(
        action=AuditAction.ROLE_CHANGED,
        user_id=str(current_user.id),
        resource=user_id,
        details={"old_role": old_role, "new_role": payload.role},
        risk_level="high",
    )
    return _user_to_out(user)


@router.delete("/{user_id}", dependencies=[Depends(require_admin)])
async def deactivate_user(user_id: str, current_user: User = Depends(get_current_user)):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    user.updated_at = datetime.now(timezone.utc)
    await user.save()
    return {"message": "User deactivated"}
