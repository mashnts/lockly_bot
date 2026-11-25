import httpx
from bot.config import settings

TIMEOUT = 10
HEADERS = {"X-Internal-Token": settings.INTERNAL_API_TOKEN}

async def create_author(telegram_id: int, username: str | None):
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            f"{settings.BACKEND_URL}/authors/",
            json={"telegram_id": telegram_id, "username": username},
            headers=HEADERS,
        )
        resp.raise_for_status()
        return resp.json()
    
async def create_channel(data: dict):
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(f"{settings.BACKEND_URL}/channels/", json=data, headers=HEADERS)
        resp.raise_for_status()
        return resp.json()
    

async def get_author(telegram_id: int):
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(f"{settings.BACKEND_URL}/authors/{telegram_id}", headers=HEADERS)
        resp.raise_for_status()
        return resp.json()
    

async def get_channel(channel_id: int):
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(f"{settings.BACKEND_URL}/channels/{channel_id}", headers=HEADERS)
        resp.raise_for_status()
        return resp.json()
    

async def create_transaction(data: dict):
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(f"{settings.BACKEND_URL}/transactions/", json=data, headers=HEADERS)
        resp.raise_for_status()
        return resp.json()
    

async def get_my_subscriptions(telegram_id: int):
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(f"{settings.BACKEND_URL}/subscribers/{telegram_id}", headers=HEADERS)
        resp.raise_for_status()
        return resp.json()
        
async def check_subscription(telegram_id: int, channel_id: int):
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(f"{settings.BACKEND_URL}/subscribers/check", params={"channel_id": channel_id, "telegram_id": telegram_id}, headers=HEADERS)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()