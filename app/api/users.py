# app/api/users.py

from fastapi import APIRouter, HTTPException, status
import sqlite3
from typing import Any, Tuple

from app.core.db import query, execute
from app.core.schemas import UserCreate, UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(user: UserCreate):
    """
    Регистрирует нового пользователя.
    При конфликте по username возвращает 400 Bad Request.
    """
    # 1) Проверяем, что username ещё не занят
    existing: list[Tuple[Any, ...]] = query(
        "SELECT telegram_id, username FROM users WHERE username = ?",
        (user.username,),
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким именем уже зарегистрирован",
        )

    # 2) Вставляем нового пользователя
    try:
        execute(
            "INSERT INTO users (username, is_premium, premium_expires_at) VALUES (?, 0, NULL)",
            (user.username,),
        )
    except sqlite3.IntegrityError as e:
        # На всякий случай ловим ошибки уникальности
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ошибка при регистрации пользователя",
        )

    # 3) Достаём свежесозданного пользователя
    row = query(
        "SELECT telegram_id, username FROM users WHERE username = ?",
        (user.username,),
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось получить данные зарегистрированного пользователя",
        )

    telegram_id, username = row[0]
    return UserOut(id=telegram_id, username=username)




