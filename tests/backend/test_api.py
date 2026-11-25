from conftest import create_subscriber

TOKEN = {"X-Internal-Token": "internal-test"}


async def test_no_token(client):
    assert (await client.get("/authors/1")).status_code == 403
    assert (await client.get("/channels/1")).status_code == 403
    assert (await client.get("/channels/1/subscribers")).status_code == 403
    assert (await client.get("/subscribers/1")).status_code == 403
    assert (await client.get("/transactions/invoice/1")).status_code == 403


async def test_wrong_token(client):
    resp = await client.get("/authors/1", headers={"X-Internal-Token": "wrong"})
    assert resp.status_code == 403


async def test_create_author(client):
    resp1 = await client.post("/authors/", json={"telegram_id": 10}, headers=TOKEN)
    resp2 = await client.post("/authors/", json={"telegram_id": 10}, headers=TOKEN)
    assert resp1.status_code == 200
    assert resp1.json()["id"] == resp2.json()["id"]


async def test_check_subscription(client, db, channel):
    await create_subscriber(db, channel.id, days=5)
    resp = await client.get("/subscribers/check", params={"channel_id": channel.id, "telegram_id": 2}, headers=TOKEN)
    assert resp.status_code == 200


async def test_check_subscription_duplicates(client, db, channel):
    await create_subscriber(db, channel.id, days=5)
    await create_subscriber(db, channel.id, days=20)
    resp = await client.get("/subscribers/check", params={"channel_id": channel.id, "telegram_id": 2}, headers=TOKEN)
    assert resp.status_code == 200
