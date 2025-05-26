# File: app/core/db.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
from app.core.logger import logger

# Async engine and session
engine = create_async_engine(
    settings.DATABASE_URL,
    future=True,
    echo=False
)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base declarative class
Base = declarative_base()

# Dependency for FastAPI routes
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            logger.error("Database session rollback due to exception")
            raise
        finally:
            await session.close()
