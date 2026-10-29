from typing import Any

from jose import jwt

from app.core.config import get_settings


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


def token_permissions(payload: dict[str, Any]) -> set[str]:
    perms = payload.get("permissions")
    if isinstance(perms, list):
        return set(str(p) for p in perms)
    return set()
