from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from bot.services import get_author
import httpx

router = Router()

@router.message(Command("dashboard"))
async def dashboard(message: Message):
    try:
        author = await get_author(message.from_user.id)
    except httpx.HTTPError:
        await message.answer("Сервис временно недоступен, попробуйте позже")
        return
    await message.answer(
        f"Твой кабинет:\n\n"
        f"Баланс: {author['balance']} USDT\n"
        f"ID: {author['id']}"
    )
