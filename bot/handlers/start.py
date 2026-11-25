from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from bot.services import create_author
import httpx

router = Router()

@router.message(CommandStart())
async def start(message: Message):
    try:
        await create_author(
            telegram_id=message.from_user.id,
            username=message.from_user.username
        )
    except httpx.HTTPError:
        await message.answer("Сервис временно недоступен, попробуйте позже")
        return
    await message.answer(
        "Привет! Я Lockly 🔐\n\n"
        "Команды:\n"
        "/addchannel — добавить канал\n"
        "/dashboard — мой кабинет\n"
        "/subscribe [id канала] — подписаться на канал\n"
        "/mysubscriptions — мои подписки\n"
        "/cancel — отменить ввод"
    )