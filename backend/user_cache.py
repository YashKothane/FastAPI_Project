
import json
from cache import redis_client

CACHE_TTL_SECONDS = 300  # 5 minutes


def _cache_key(email: str) -> str:
    return f"user:{email.lower()}"


def get_cached_user(email: str) -> dict | None:
    cached = redis_client.get(_cache_key(email))
    if cached:
        return json.loads(cached)
    return None


def set_cached_user(email: str, user_data: dict) -> None:
    redis_client.set(_cache_key(email), json.dumps(user_data), ex=CACHE_TTL_SECONDS)


def invalidate_cached_user(email: str) -> None:
    redis_client.delete(_cache_key(email))