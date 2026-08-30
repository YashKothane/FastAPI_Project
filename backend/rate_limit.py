from fastapi import HTTPException, status
from cache import redis_client

MAX_ATTEMPTS = 5
WINDOW_SECONDS = 60


def check_and_increment_login_attempts(email: str) -> None:
    key = f"login_attempts:{email.lower()}"

    attempts = redis_client.incr(key)  # creates the key at 1 if it doesn't exist yet

    if attempts == 1:
        # First attempt in this window — start the 60-second clock
        redis_client.expire(key, WINDOW_SECONDS)

    if attempts > MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Try again in a minute.",
        )


def reset_login_attempts(email: str) -> None:
    redis_client.delete(f"login_attempts:{email.lower()}")