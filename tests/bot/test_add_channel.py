from types import SimpleNamespace
from unittest.mock import AsyncMock

from aiogram.enums import ChatMemberStatus

from bot.handlers.channel import get_chat_id

BOT_ID = 999


def make_message(user_status, bot_member):
    async def get_chat_member(chat_id, user_id):
        if user_id == BOT_ID:
            return bot_member
        return SimpleNamespace(status=user_status)

    return SimpleNamespace(
        text="-100123",
        from_user=SimpleNamespace(id=1),
        bot=SimpleNamespace(id=BOT_ID, get_chat_member=get_chat_member),
        answer=AsyncMock(),
    )


def bot_admin(can_invite=True, can_restrict=True):
    return SimpleNamespace(
        status=ChatMemberStatus.ADMINISTRATOR,
        can_invite_users=can_invite,
        can_restrict_members=can_restrict,
    )


async def test_owner_can_add():
    message = make_message(ChatMemberStatus.CREATOR, bot_admin())
    state = AsyncMock()
    await get_chat_id(message, state)
    state.update_data.assert_called_once_with(chat_id=-100123)


async def test_not_admin_cant_add():
    message = make_message(ChatMemberStatus.MEMBER, bot_admin())
    state = AsyncMock()
    await get_chat_id(message, state)
    state.update_data.assert_not_called()


async def test_bot_without_rights():
    message = make_message(ChatMemberStatus.CREATOR, bot_admin(can_restrict=False))
    state = AsyncMock()
    await get_chat_id(message, state)
    state.update_data.assert_not_called()
