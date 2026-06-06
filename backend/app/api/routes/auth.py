"""
/auth/* routes: register, login, refresh, reset password, logout
"""
import secrets
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, status, Request, Depends
from app.schemas.auth import (
    RegisterRequest, LoginRequest, TokenResponse,
    RefreshRequest, PasswordResetRequest, PasswordResetConfirm
)
from app.models.user import User
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token
)
from app.core.config import settings
from app.security.audit import log_event
from app.models.audit import AuditAction

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, request: Request):
    if await User.find_one(User.email == payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if await User.find_one(User.username == payload.username):
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    await user.insert()
    await log_event(
        action=AuditAction.REGISTER,
        user_id=str(user.id),
        ip_address=request.client.host,
        details={"email": payload.email},
    )
    return {"message": "Registration successful", "user_id": str(user.id)}


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request):
    user = await User.find_one(User.email == payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        await log_event(
            action=AuditAction.LOGIN,
            ip_address=request.client.host,
            success=False,
            details={"email": payload.email},
            risk_level="medium",
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    user.last_login = datetime.now(timezone.utc)
    await user.save()

    access_token = create_access_token(
        str(user.id), extra={"role": user.role, "email": user.email}
    )
    refresh_token = create_refresh_token(str(user.id))

    await log_event(
        action=AuditAction.LOGIN,
        user_id=str(user.id),
        ip_address=request.client.host,
        success=True,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshRequest):
    token_data = decode_token(payload.refresh_token)
    if not token_data or token_data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = await User.get(token_data["sub"])
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")

    access_token = create_access_token(
        str(user.id), extra={"role": user.role, "email": user.email}
    )
    new_refresh = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/password-reset/request")
async def request_password_reset(payload: PasswordResetRequest):
    user = await User.find_one(User.email == payload.email)
    # Always return OK to prevent email enumeration
    if user:
        token = secrets.token_urlsafe(32)
        user.reset_token = token
        user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        await user.save()
        # In production, send this token via email service
        # For now we return it directly (dev only)
    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/password-reset/confirm")
async def confirm_password_reset(payload: PasswordResetConfirm):
    user = await User.find_one(User.reset_token == payload.token)
    if not user or not user.reset_token_expires:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    if user.reset_token_expires < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Reset token has expired")

    user.hashed_password = hash_password(payload.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    await user.save()

    await log_event(action=AuditAction.PASSWORD_RESET, user_id=str(user.id))
    return {"message": "Password updated successfully"}
