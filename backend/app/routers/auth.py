import hmac
import hashlib
import json
from urllib.parse import unquote, parse_qsl
from fastapi import HTTPException
from app.config import settings
from app.models import Subscriber, Author

def validate_init_data(init_data: str) -> dict:
    parsed = dict(parse_qsl(unquote(init_data), keep_blank_values=True))

    received_hash = parsed.pop("hash", None)

    if not received_hash:
        raise HTTPException(status_code=400, detail="Missing hash")
    
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))

    secret_key = hmac.new(b"WebAppData", settings.BOT_TOKEN.encode(), hashlib.sha256).digest()

    expected_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(expected_hash, received_hash):
        raise HTTPException(status_code=401, detail="Invalid initData")
    
    user_data = parsed.get("user")
    if not user_data:
        raise HTTPException(status_code=400, detail="No user data")
    
    return json.loads(user_data)

def get_user_roles(telegram_id: int):
    result = db.execute(select())