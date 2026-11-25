from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramAPIError
from bot.states import AddChannel
from bot.services import create_channel
import httpx

router = Router()

@router.message(Command("addchannel"))
async def add_channel_start(message: Message, state: FSMContext):
    await state.set_state(AddChannel.waiting_chat_id)
    await message.answer("Перешлите мне любое сообщение из канала или напишите его ID (например: -1001234567890)")

@router.message(AddChannel.waiting_chat_id, ~F.text.startswith("/"))
async def get_chat_id(message: Message, state: FSMContext):
    try:
        chat_id = int(message.text.strip())
    except ValueError:
        await message.answer("Введите число (ID канала, например -1001234567890).")
        return

    try:
        user_member = await message.bot.get_chat_member(chat_id, message.from_user.id)
        bot_member = await message.bot.get_chat_member(chat_id, message.bot.id)
    except TelegramAPIError:
        await message.answer("Не удалось проверить канал. Добавьте бота в канал администратором и попробуйте снова.")
        return

    if user_member.status not in (ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR):
        await message.answer("Добавить канал может только его владелец или администратор.")
        return

    if not (
        bot_member.status == ChatMemberStatus.ADMINISTRATOR
        and getattr(bot_member, "can_invite_users", False)
        and getattr(bot_member, "can_restrict_members", False)
    ):
        await message.answer("Бот должен быть администратором канала с правами приглашать и удалять участников.")
        return

    await state.update_data(chat_id=chat_id)
    await state.set_state(AddChannel.waiting_title)
    await message.answer("Введите название канала:")

@router.message(AddChannel.waiting_title, ~F.text.startswith("/"))
async def get_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AddChannel.waiting_description)
    await message.answer("Введите описание канала (или напишите 'нет'):")

@router.message(AddChannel.waiting_description, ~F.text.startswith("/"))
async def get_description(message: Message, state: FSMContext):
    desc = message.text if message.text.lower() != "нет" else None
    await state.update_data(description=desc)
    await state.set_state(AddChannel.waiting_price)
    await message.answer("Цена подписки в USDT:")

@router.message(AddChannel.waiting_price, ~F.text.startswith("/"))
async def get_price(message: Message, state: FSMContext):
    try:
        price = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer("Введите число (цену в USDT, например 5 или 2.99).")
        return
    if price <= 0:
        await message.answer("Цена должна быть больше нуля.")
        return
    await state.update_data(price=price)
    await state.set_state(AddChannel.waiting_period)
    await message.answer("На сколько дней подписка:")

@router.message(AddChannel.waiting_period, ~F.text.startswith("/"))
async def get_period(message: Message, state: FSMContext):
    try:
        period_days = int(message.text.strip())
    except ValueError:
        await message.answer("Введите целое число (количество дней, например 30).")
        return
    if period_days <= 0:
        await message.answer("Укажите число дней больше нуля.")
        return

    data = await state.get_data()
    await state.clear()

    try:
        channel = await create_channel({
            "author_telegram_id": message.from_user.id,
            "telegram_chat_id": data["chat_id"],
            "title": data["title"],
            "description": data["description"],
            "price": data["price"],
            "period_days": period_days
        })
        await message.answer(
            f"Канал добавлен!\n\n"
            f"Сообщите подписчикам ID канала: {channel['id']}\n\n"
            f"Название: {channel['title']}\n"
            f"Описание: {channel['description'] or '—'}\n"
            f"Цена: {channel['price']} USDT\n"
            f"Длительность подписки: {channel['period_days']} дн."
        )
    except httpx.HTTPError:
        await message.answer("Сервис временно недоступен, попробуйте позже")
    except Exception as e:
        await message.answer(f"Ошибка при добавлении канала: {e}")
