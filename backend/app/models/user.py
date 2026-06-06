from beanie import Document as BeanieDocument, Indexed
from pydantic import EmailStr, Field
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    EVALUATOR = "evaluator"
    VIEWER = "viewer"


class User(BeanieDocument):
    email: Indexed(EmailStr, unique=True)
    username: Indexed(str, unique=True)
    hashed_password: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.EVALUATOR
    is_active: bool = True
    is_verified: bool = False
    avatar_url: Optional[str] = None
    reset_token: Optional[str] = None
    reset_token_expires: Optional[datetime] = None
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"
        indexes = ["email", "username", "role"]
