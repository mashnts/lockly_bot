import hashlib
import hmac
import json
from datetime import datetime, timedelta

from sqlalchemy import select

from app.models import Author, Subscriber, Transaction
from conftest import create_subscriber, create_transaction


def make_request(invoice_id, token="cryptobot-test"):
    body = json.dumps({"update_type": "invoice_paid", "payload": {"invoice_id": invoice_id}}).encode()
    secret = hashlib.sha256(token.encode()).digest()
    signature = hmac.new(secret, body, hashlib.sha256).hexdigest()
    return body, {"crypto-pay-api-signature": signature, "content-type": "application/json"}


async def send_webhook(client, invoice_id, token="cryptobot-test"):
    body, headers = make_request(invoice_id, token)
    return await client.post("/webhook/cryptobot", content=body, headers=headers)


async def get_balance(db):
    async with db() as session:
        author = (await session.execute(select(Author))).scalar_one()
        return author.balance


async def get_subscribers(db):
    async with db() as session:
        return (await session.execute(select(Subscriber))).scalars().all()


async def test_wrong_signature(client, db, channel, bot):
    await create_transaction(db, channel.id, 1)
    resp = await send_webhook(client, 1, token="wrong")
    assert resp.status_code == 403
    assert await get_subscribers(db) == []


async def test_payment(client, db, channel, bot):
    await create_transaction(db, channel.id, 1)
    resp = await send_webhook(client, 1)
    assert resp.status_code == 200

    async with db() as session:
        transaction = (await session.execute(select(Transaction))).scalar_one()
    assert transaction.status == "paid"
    assert await get_balance(db) == 5
    assert len(await get_subscribers(db)) == 1
    assert "https://t.me/+test" in bot.messages[0]


async def test_double_webhook(client, db, channel, bot):
    await create_transaction(db, channel.id, 1)
    await send_webhook(client, 1)
    await send_webhook(client, 1)
    assert await get_balance(db) == 5
    assert len(await get_subscribers(db)) == 1
    assert len(bot.messages) == 1


async def test_renewal(client, db, channel, bot):
    await create_subscriber(db, channel.id, days=10)
    await create_transaction(db, channel.id, 1)
    await send_webhook(client, 1)

    subs = await get_subscribers(db)
    assert len(subs) == 1
    assert subs[0].expires_at > datetime.now() + timedelta(days=39)


async def test_invite_error(client, db, channel, bot):
    bot.invite_error = True
    await create_transaction(db, channel.id, 1)
    resp = await send_webhook(client, 1)
    assert resp.status_code == 200
    assert await get_balance(db) == 5
    assert len(await get_subscribers(db)) == 1
    assert "Оплата получена" in bot.messages[0]
