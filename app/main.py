# File: app/main.py
from fastapi import FastAPI
from app.api import users, signals, portfolio, analytics

app = FastAPI(
    title="Crypto Signals Bot API",
    version="0.1.0",
)

# include routers
app.include_router(users.router)
app.include_router(signals.router)
app.include_router(portfolio.router)
app.include_router(analytics.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
