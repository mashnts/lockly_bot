from datetime import datetime as dt_parse
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from bot.services import get_my_subscriptions
import httpx

router = Router()

@router.message(Command("mysubscriptions"))
async def my_subscriptions(message: Message):
    try:
        subs = await get_my_subscriptions(message.from_user.id)
    except httpx.HTTPError:
        await message.answer("Сервис временно недоступен, попробуйте позже")
        return

    if not subs:
        await message.answer("У вас нет активных подписок на текущее время")
        return
    
    text = "Ваши активные подписки:\n\n"

    for sub in subs:
        raw = sub["expires_at"][:10]
        try:
            dt = dt_parse.strptime(raw, "%Y-%m-%d")
            date_str = dt.strftime("%d.%m.%Y")
        except (ValueError, TypeError):
            date_str = raw
        text += f"🔷 {sub['channel_title']}\n   Активна до: {date_str}\n\n"

    await message.answer(text)