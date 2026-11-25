from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from bot.services import get_channel, create_transaction, check_subscription
from bot.cryptopay import create_invoice 
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton 
import httpx

router = Router()

@router.message(Command("subscribe"))
async def subscribe(message: Message):
    text = message.text.split()

    if len(text) < 2:
        await message.answer(
            "Используйте: /subscribe [ID канала].\n"
            "ID канала можно взять у автора канала или в описании."
        )
        return 
    try:
        channel_id = int(text[1])
    except ValueError:
        await message.answer("Укажите корректный ID канала (число).")
        return
    
    try:
        channel = await get_channel(channel_id)
        if not channel:
            await message.answer("Канал не найден")
            return
        telegram_id = message.from_user.id
        payload = f"{channel_id},{telegram_id}"
        sub = await check_subscription(telegram_id, channel_id)
        if sub and 'id' in sub:
            await message.answer(f"У вас активна подписка на канал '{channel['title']}' до {sub['expires_at'][:10]}")
            return
        try:
            invoice = await create_invoice("USDT", channel['price'], f"Подписка на {channel['title']}", payload, 3600)
        except Exception:
            await message.answer("Не удалось создать счёт для оплаты. Попробуйте позже или обратитесь к автору канала.")
            return
        pay_btn = InlineKeyboardButton(text="Оплатить", url=invoice.bot_invoice_url)
        pay = InlineKeyboardMarkup(inline_keyboard=[[pay_btn]])
        transaction = await create_transaction({
            "channel_id": channel_id,
            "subscriber_telegram_id": telegram_id,
            "amount": channel['price'],
            "cryptobot_invoice_id": str(invoice.invoice_id)
        })
        await message.answer(f"Информация о канале:\nНазвание: {channel['title']}, \nЦена: {channel['price']}", reply_markup=pay)
    except httpx.HTTPError:
        await message.answer("Сервис временно недоступен, попробуйте позже")