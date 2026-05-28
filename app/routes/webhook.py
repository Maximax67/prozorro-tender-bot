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
