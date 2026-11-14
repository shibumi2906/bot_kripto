"""Read-only credential checks. Never return token values or raw exception text."""
import httpx
from openai import OpenAI

from app.core.config import settings


def check_credentials() -> dict:
    result = {}
    if not settings.OPENAI_API_KEY:
        result["openai"] = {"status": "not_configured"}
    else:
        try:
            with OpenAI(api_key=settings.OPENAI_API_KEY, max_retries=0, timeout=15) as client:
                model = client.models.retrieve(settings.OPENAI_MODEL)
            result["openai"] = {
                "status": "accessible", "model": model.id,
                "billing_eligibility": "not_verified",
            }
        except Exception as exc:
            result["openai"] = {"status": "failed", "error_type": type(exc).__name__}
    if not settings.TELEGRAM_BOT_TOKEN:
        result["telegram"] = {"status": "not_configured"}
    else:
        try:
            response = httpx.get(
                "https://api.telegram.org/bot" + settings.TELEGRAM_BOT_TOKEN + "/getMe",
                timeout=15,
            )
            result["telegram"] = {
                "status": "valid" if response.json().get("ok") else "rejected",
            }
        except Exception as exc:
            result["telegram"] = {"status": "failed", "error_type": type(exc).__name__}
    return result
