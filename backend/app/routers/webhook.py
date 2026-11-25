from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from datetime import datetime, timedelta
from app.database import get_db
from app.models import Transaction, Subscriber, Channel, Author, TransactionStatus
from app.schemas import CryptoBotWebhook
from app.config import settings
from aiogram import Bot
import hmac
import hashlib  
import logging
from hmac import compare_digest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook")

def verify_signature(token: str, body: bytes, signature: str) -> bool:
    secret = hashlib.sha256(token.encode()).digest()
    hmac_hash = hmac.new(secret, body, hashlib.sha256).hexdigest()
    return compare_digest(hmac_hash, signature or "")

@router.post("/cryptobot")
async def cryptobot_webhook(request: Request, data: CryptoBotWebhook, db: AsyncSession = Depends(get_db)):
    body = await request.body()
    signature = request.headers.get("crypto-pay-api-signature", "")
    res = verify_signature(settings.CRYPTOBOT_TOKEN, body, signature)

    if res == False:
        raise HTTPException(403, detail="Invalid signature")

    if data.update_type != "invoice_paid":
        return {"ok": True}
    
    invoice_id = str(data.payload.get("invoice_id"))

    result = await db.execute(
        update(Transaction)
        .where(
            Transaction.cryptobot_invoice_id == invoice_id,
            Transaction.status == TransactionStatus.PENDING.value,
        )
        .values(status=TransactionStatus.PAID.value)
        .returning(Transaction.id, Transaction.channel_id, Transaction.subscriber_telegram_id, Transaction.amount)
    )
    transaction = result.first()

    if not transaction:
        return {"ok": True}

    result2 = await db.execute(select(Channel).where(Channel.id == transaction.channel_id))
    channel = result2.scalar_one_or_none()

    if not channel:
        logger.error("Channel not found for transaction %s", transaction.id)
        await db.rollback()
        return {"ok": True}

    result3 = await db.execute(
        select(Subscriber)
        .where(
            Subscriber.channel_id == transaction.channel_id,
            Subscriber.telegram_id == transaction.subscriber_telegram_id,
        )
        .order_by(Subscriber.expires_at.desc())
        .limit(1)
        .with_for_update()
    )
    subscriber = result3.scalar_one_or_none()

    now = datetime.now()
    period = timedelta(days=channel.period_days)
    if subscriber:
        if subscriber.is_active and subscriber.expires_at > now:
            subscriber.expires_at = subscriber.expires_at + period
        else:
            subscriber.expires_at = now + period
        subscriber.is_active = True
    else:
        db.add(Subscriber(
            channel_id=transaction.channel_id,
            telegram_id=transaction.subscriber_telegram_id,
            expires_at=now + period,
        ))

    await db.execute(
        update(Author)
        .where(Author.id == channel.author_id)
        .values(balance=func.coalesce(Author.balance, 0) + transaction.amount)
    )

    await db.commit()

    bot = Bot(token=settings.BOT_TOKEN)
    try:
        try:
            link = await bot.create_chat_invite_link(
                chat_id=channel.telegram_chat_id,
                member_limit=1
            )
        except Exception as e:
            logger.error("Не удалось создать инвайт-ссылку для транзакции %s: %s", transaction.id, e)
            await bot.send_message(
                transaction.subscriber_telegram_id,
                "✅ Оплата получена, но выдать ссылку на канал не удалось. Обратитесь к автору канала."
            )
            return {"ok": True}

        await bot.send_message(
            transaction.subscriber_telegram_id,
            f"✅ Поздравляю, Подписка активирована!\nСсылка для вступления: {link.invite_link}"
        )
        logger.info("Сообщение отправлено успешно!")
    except Exception as e:
        logger.error("ОШИБКА при отправке: %s", e)
    finally:
        await bot.session.close()

    return {"ok": True}

