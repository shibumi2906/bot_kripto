# create_tables.py

import asyncio
from app.core.db import engine, Base

# ВАЖНО: без этого импорта Base.metadata будет пустым
import app.core.models  # noqa: F401

async def main():
    """
    Создаёт все таблицы, описанные в моделях (app/core/models.py).
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("✅ All tables created successfully")

if __name__ == "__main__":
    asyncio.run(main())

