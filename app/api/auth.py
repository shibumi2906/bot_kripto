# File: app/api/auth.py

from fastapi import APIRouter, HTTPException, status, Depends, Header
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta
from typing import Optional, Tuple

from app.core.config import settings
from app.core.db import query
from app.core.schemas import UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

# Настройки JWT
JWT_SECRET = settings.JWT_SECRET_KEY
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24 * 7  # 7 дней


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str


def create_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


@router.post("/login", response_model=Token)
async def login(req: LoginRequest):
    """
    Авторизация по username. В ответ — JWT.
    """
    rows = query("SELECT telegram_id FROM users WHERE username = ?", (req.username,))
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный username"
        )
    user_id = rows[0][0]
    token = create_token({"sub": str(user_id), "username": req.username})
    return Token(access_token=token)


async def get_current_user(
    authorization: str = Header(..., alias="Authorization")
) -> Tuple[int, str]:
    """
    Dependency для извлечения и проверки JWT из заголовка Authorization: Bearer <token>.
    Возвращает кортеж (user_id, username).
    """
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Неверная схема авторизации")
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    rows = query(
        "SELECT telegram_id, username FROM users WHERE telegram_id = ?",
        (user_id,)
    )
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return (rows[0][0], rows[0][1])


@router.get("/me", response_model=UserOut)
async def me(current: Tuple[int, str] = Depends(get_current_user)):
    """
    Профиль текущего пользователя по JWT из заголовка.
    """
    user_id, username = current
    return UserOut(id=user_id, username=username)

