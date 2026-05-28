from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.core.logger import logger
from app.core.settings import settings
from bot.utils.tender_checker import check_new_tenders
from bot.utils.upstash import get_last_tender_id

router = Router()

ADMIN_FILTER = F.chat.id == settings.CHAT_ID


@router.message(Command("start"), ADMIN_FILTER)
async def start_handler(message: Message) -> None:
    await message.answer(
        "✅ <b>Бот моніторингу закупівель Prozorro активний</b>\n\n"
        "Команди:\n"
        "/check — перевірити нові закупівлі зараз\n"
        "/status — переглянути останній оброблений тендер"
    )


@router.message(Command("check"), ADMIN_FILTER)
async def check_handler(message: Message) -> None:
    status_msg = await message.answer("⏳ Перевірка нових закупівель...")
    try:
        count = await check_new_tenders()
        if count == 0:
            await status_msg.edit_text("✅ Нових закупівель не знайдено")
        else:
            await status_msg.edit_text(f"✅ Оброблено <b>{count}</b> нових закупівель")
    except Exception as e:
        logger.error(f"Manual check failed: {e}")
        await status_msg.edit_text(f"❌ Помилка під час перевірки:\n<code>{e}</code>")


@router.message(Command("status"), ADMIN_FILTER)
async def status_handler(message: Message) -> None:
    last_id = await get_last_tender_id()
    if last_id:
        await message.answer(
            f"📋 Останній оброблений тендер:\n<code>{last_id}</code>\n\n"
            f"🔗 https://prozorro.gov.ua/tender/{last_id}"
        )
    else:
        await message.answer("ℹ️ Ще не оброблено жодного тендера")
