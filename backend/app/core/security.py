import random
import time
from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.career import User


bearer_scheme = HTTPBearer(auto_error=False)
captcha_store: dict[str, tuple[str, float]] = {}
rate_limit_store: dict[str, list[float]] = {}


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8")[:72], password_hash.encode("utf-8"))


def create_access_token(user: User, remember_me: bool = False) -> str:
    expires_delta = timedelta(days=30 if remember_me else 1)
    expires_at = datetime.now(timezone.utc) + expires_delta
    payload = {"sub": str(user.id), "email": user.email, "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.") from exc


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication token.")
    payload = decode_token(credentials.credentials)
    user = db.get(User, int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
    return user


def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User | None:
    if credentials is None:
        return None
    try:
        payload = decode_token(credentials.credentials)
        return db.get(User, int(payload["sub"]))
    except HTTPException:
        return None


def create_captcha() -> dict:
    left = random.randint(2, 9)
    right = random.randint(2, 9)
    captcha_id = f"captcha_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
    captcha_store[captcha_id] = (str(left + right), time.time() + 300)
    return {"captcha_id": captcha_id, "question": f"{left} + {right} = ?"}


def verify_captcha(captcha_id: str, answer: str):
    expected = captcha_store.get(captcha_id)
    if not expected:
        raise HTTPException(status_code=400, detail="Captcha expired. Refresh and try again.")
    value, expires_at = expected
    if time.time() > expires_at or answer.strip() != value:
        raise HTTPException(status_code=400, detail="Captcha verification failed.")
    captcha_store.pop(captcha_id, None)


def rate_limit(key: str, limit: int = 8, window_seconds: int = 60):
    now = time.time()
    attempts = [stamp for stamp in rate_limit_store.get(key, []) if now - stamp < window_seconds]
    if len(attempts) >= limit:
        raise HTTPException(status_code=429, detail="Too many attempts. Please wait and try again.")
    attempts.append(now)
    rate_limit_store[key] = attempts
