# File: app/main.py

from fastapi import FastAPI
from app.api.users import router as users_router
from app.api.auth import router as auth_router
from app.api.subscription import router as subscription_router
from app.api.payments import router as payments_router
from app.api.signals import router as signals_router
from app.api.portfolio import router as portfolio_router
from app.api.analytics import router as analytics_router
from app.api.news import router as news_router
from app.api.sentiment import router as sentiment_router

from app.tasks.scheduler import start_scheduler

app = FastAPI(
    title="Crypto Signals Bot API",
    version="0.1.0",
)

# Include all API routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(subscription_router)
app.include_router(payments_router)
app.include_router(signals_router)
app.include_router(portfolio_router)
app.include_router(analytics_router)
app.include_router(news_router)
app.include_router(sentiment_router)


@app.on_event("startup")
def on_startup():
    """
    Запускаем планировщик фоновых задач при старте приложения.
    """
    start_scheduler()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

