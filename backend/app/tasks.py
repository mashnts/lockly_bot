from datetime import datetime
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Subscriber, Channel
from app.config import settings
from aiogram import Bot
import logging

logger = logging.getLogger(__name__)

async def check_expired_subscriptions():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Subscriber.id).where(Subscriber.expires_at < datetime.now(), Subscriber.is_active == True))
        expired_ids = result.scalars().all()

    bot = Bot(token=settings.BOT_TOKEN)
    try:
        for subscriber_id in expired_ids:
            async with AsyncSessionLocal() as db:
                sub_result = await db.execute(
                    select(Subscriber)
                    .where(Subscriber.id == subscriber_id)
                    .with_for_update(skip_locked=True)
                )
                subscriber = sub_result.scalar_one_or_none()

                if not subscriber or not subscriber.is_active or subscriber.expires_at >= datetime.now():
                    continue

                channel_result = await db.execute(select(Channel).where(Channel.id == subscriber.channel_id))
                channel = channel_result.scalar_one_or_none()

                if channel:
                    try:
                        await bot.ban_chat_member(channel.telegram_chat_id, subscriber.telegram_id)
                    except Exception as e:
                        logger.error(f"ОШИБКА при бане пользователя {subscriber.telegram_id}: {e}")
                        continue
                    try:
                        await bot.unban_chat_member(channel.telegram_chat_id, subscriber.telegram_id, only_if_banned=True)
                    except Exception as e:
                        logger.error(f"ОШИБКА при разбане пользователя {subscriber.telegram_id}: {e}")

                subscriber.is_active = False
                await db.commit()
    finally:
        await bot.session.close()
