from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat

from app.core.settings import settings
from bot.instance import bot

commands = [
    BotCommand(command="start", description="Показати список команд"),
    BotCommand(command="check", description="Перевірити нові закупівлі зараз"),
    BotCommand(command="status", description="Переглянути останній оброблений тендер"),
]


async def set_chat_commands() -> None:
    await bot.set_my_commands(
        commands=commands, scope=BotCommandScopeChat(chat_id=settings.CHAT_ID)
    )
