from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.models import User as UserModel
from app.core.schemas import UserCreate, UserOut

router = APIRouter(prefix="/users", tags=["users"])

@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED
)
async def register_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db)  # получаем сессию из зависимости :contentReference[oaicite:2]{index=2}
):
    """
    Регистрирует нового пользователя.
    При конфликте по username возвращает 400 Bad Request.
    """
    new_user = UserModel(username=user.username)
    db.add(new_user)
    try:
        await db.commit()
        await db.refresh(new_user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким именем уже зарегистрирован"
        )
    return new_user



