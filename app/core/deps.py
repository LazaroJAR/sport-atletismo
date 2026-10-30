from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.core.security import decode_token, token_permissions

bearer_scheme = HTTPBearer(auto_error=True)


async def get_token_payload(
    cred: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> dict:
    try:
        return decode_token(cred.credentials)
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido")


def require_permission(name: str):
    async def _dep(payload: Annotated[dict, Depends(get_token_payload)]) -> dict:
        if name not in token_permissions(payload):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Permisos insuficientes")
        return payload

    return _dep


athletics_read = require_permission("athletics:read")
athletics_write = require_permission("athletics:write")
