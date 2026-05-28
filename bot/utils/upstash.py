import httpx

from app.core.logger import logger
from app.core.settings import settings

LAST_TENDER_KEY = "prozorro:last_tender_id"


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.UPSTASH_REDIS_REST_TOKEN.get_secret_value()}",
        "Content-Type": "application/json",
    }


async def get_last_tender_id() -> str | None:
    url = settings.UPSTASH_REDIS_REST_URL.rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                headers=_headers(),
                json=["GET", LAST_TENDER_KEY],
            )
            response.raise_for_status()
            data = response.json()
            result = data.get("result")
            return str(result) if result is not None else None
    except Exception as e:
        logger.error(f"Upstash GET failed: {e}")
        return None


async def set_last_tender_id(tender_id: str) -> bool:
    url = settings.UPSTASH_REDIS_REST_URL.rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                headers=_headers(),
                json=["SET", LAST_TENDER_KEY, tender_id],
            )
            response.raise_for_status()
            return True
    except Exception as e:
        logger.error(f"Upstash SET failed: {e}")
        return False
