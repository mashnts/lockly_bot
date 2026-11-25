from sqlalchemy import select

from app.models import Subscriber
from app.tasks import check_expired_subscriptions
from conftest import create_subscriber


async def is_active(db, sub_id):
    async with db() as session:
        sub = (await session.execute(select(Subscriber).where(Subscriber.id == sub_id))).scalar_one()
        return sub.is_active


async def test_expired(db, channel, bot):
    sub_id = await create_subscriber(db, channel.id, days=-1)
    await check_expired_subscriptions()
    assert bot.banned == [2]
    assert not await is_active(db, sub_id)


async def test_not_expired(db, channel, bot):
    sub_id = await create_subscriber(db, channel.id, days=5)
    await check_expired_subscriptions()
    assert bot.banned == []
    assert await is_active(db, sub_id)


async def test_ban_error(db, channel, bot):
    bot.ban_error = True
    sub_id = await create_subscriber(db, channel.id, days=-1)
    await check_expired_subscriptions()
    assert await is_active(db, sub_id)
