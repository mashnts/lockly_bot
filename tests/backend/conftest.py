from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app import tasks
from app.database import Base, get_db
from app.main import app
from app.models import Author, Channel, Subscriber, Transaction
from app.routers import webhook


@pytest.fixture
async def db():
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest.fixture
async def client(db):
    async def get_test_db():
        async with db() as session:
            yield session

    app.dependency_overrides[get_db] = get_test_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


class FakeBot:
    def __init__(self):
        self.messages = []
        self.banned = []
        self.invite_error = False
        self.ban_error = False
        self.session = SimpleNamespace(close=AsyncMock())

    async def send_message(self, chat_id, text):
        self.messages.append(text)

    async def create_chat_invite_link(self, chat_id, member_limit):
        if self.invite_error:
            raise Exception("error")
        return SimpleNamespace(invite_link="https://t.me/+test")

    async def ban_chat_member(self, chat_id, user_id):
        if self.ban_error:
            raise Exception("error")
        self.banned.append(user_id)

    async def unban_chat_member(self, chat_id, user_id, only_if_banned):
        pass


@pytest.fixture
def bot(monkeypatch, db):
    fake = FakeBot()
    monkeypatch.setattr(webhook, "Bot", lambda token: fake)
    monkeypatch.setattr(tasks, "Bot", lambda token: fake)
    monkeypatch.setattr(tasks, "AsyncSessionLocal", db)
    return fake


@pytest.fixture
async def channel(db):
    async with db() as session:
        author = Author(telegram_id=1, balance=0)
        session.add(author)
        await session.flush()
        channel = Channel(author_id=author.id, telegram_chat_id=-100, title="test", price=5, period_days=30)
        session.add(channel)
        await session.commit()
        return channel


async def create_transaction(db, channel_id, invoice_id, user_id=2):
    async with db() as session:
        session.add(Transaction(
            channel_id=channel_id,
            subscriber_telegram_id=user_id,
            amount=5,
            cryptobot_invoice_id=str(invoice_id),
        ))
        await session.commit()


async def create_subscriber(db, channel_id, days, is_active=True, user_id=2):
    async with db() as session:
        sub = Subscriber(
            channel_id=channel_id,
            telegram_id=user_id,
            expires_at=datetime.now() + timedelta(days=days),
            is_active=is_active,
        )
        session.add(sub)
        await session.commit()
        return sub.id
