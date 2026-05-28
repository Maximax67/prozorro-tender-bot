import asyncio

from app.core.logger import logger
from app.core.settings import settings
from bot.dispatcher import dp
from bot.instance import bot
from bot.utils.tender_checker import check_new_tenders


async def periodic_check(interval_seconds: int = 3600) -> None:
    logger.info("Periodic check task started")
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            logger.info("Running periodic tender check")
            count = await check_new_tenders()
            logger.info(f"Periodic check done: {count} new tenders processed")
        except Exception as e:
            logger.error(f"Periodic check error: {e}")


async def main() -> None:
    if settings.WEBHOOK_URL:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook removed, switching to polling")

    check_task = asyncio.create_task(periodic_check())

    try:
        logger.info("Starting polling...")
        await dp.start_polling(bot)
    finally:
        check_task.cancel()
        try:
            await check_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    asyncio.run(main())
