from aiogram.types import Update
from fastapi import APIRouter, Header, HTTPException, Request, Response

from app.core.logger import logger
from app.core.settings import settings
from bot.dispatcher import dp
from bot.instance import bot

router = APIRouter(prefix="/webhook", tags=["telegram"])


@router.post("")
async def handle_webhook(
    request: Request,
    x_telegram_token: str = Header(..., alias="X-Telegram-Bot-Api-Secret-Token"),
) -> Response:
    if (
        settings.WEBHOOK_SECRET
        and x_telegram_token != settings.WEBHOOK_SECRET.get_secret_value()
    ):
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        raw = await request.json()
        update = Update.model_validate(raw)
    except Exception as e:
        logger.error(f"Failed to parse update: {e}")
        raise HTTPException(status_code=400, detail="Invalid update")

    try:
        await dp.feed_update(bot, update)
    except Exception as e:
        logger.error(f"Failed to process update: {e}")

    return Response(status_code=200)


def _verify_management_token(authorization: str | None) -> None:
    if settings.WEBHOOK_MANAGE_TOKEN:
        expected = f"Bearer {settings.WEBHOOK_MANAGE_TOKEN.get_secret_value()}"
        if not authorization or authorization != expected:
            raise HTTPException(status_code=401, detail="Unauthorized")


@router.post("/setup", status_code=200)
async def setup_webhook_endpoint(
    authorization: str | None = Header(default=None),
) -> dict[str, str]:
    _verify_management_token(authorization)

    if not settings.WEBHOOK_URL:
        raise HTTPException(
            status_code=400, detail="WEBHOOK_URL is not set in environment"
        )

    webhook_url = f"{str(settings.WEBHOOK_URL).rstrip('/')}/webhook"
    webhook_secret = (
        settings.WEBHOOK_SECRET.get_secret_value() if settings.WEBHOOK_SECRET else None
    )

    try:
        await bot.set_webhook(
            webhook_url,
            secret_token=webhook_secret,
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=False,
        )
        logger.info(f"Webhook explicitly set to {webhook_url}")
        return {"status": "ok", "detail": f"Webhook set to {webhook_url}"}
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/delete", status_code=200)
async def delete_webhook_endpoint(
    authorization: str | None = Header(default=None),
) -> dict[str, str]:
    _verify_management_token(authorization)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook explicitly removed")
        return {
            "status": "ok",
            "detail": "Webhook removed successfully, dropped pending updates",
        }
    except Exception as e:
        logger.error(f"Failed to delete webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))
