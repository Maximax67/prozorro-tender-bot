from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.core.logger import logger
from app.core.settings import settings
from app.routes.api import router


async def setup_webhook() -> None:
    if not settings.WEBHOOK_URL:
        logger.warning("WEBHOOK_URL not set, skipping webhook setup")
        return

    from bot.instance import bot

    webhook_url = f"{str(settings.WEBHOOK_URL).rstrip('/')}/webhook"
    webhook_secret = (
        settings.WEBHOOK_SECRET.get_secret_value() if settings.WEBHOOK_SECRET else None
    )

    await bot.set_webhook(
        webhook_url,
        secret_token=webhook_secret,
        allowed_updates=["message", "callback_query"],
        drop_pending_updates=False,
    )
    logger.info(f"Webhook set to {webhook_url}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    if settings.MODE == "webhook":
        await setup_webhook()

    logger.info("App started")
    yield
    logger.info("App shutdown")


app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.include_router(router)
