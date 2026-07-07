"""FastAPI dependencies: current user, role guards, shared singletons."""
import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from common.enums import UserStatus
from common.presence import enrich_online
from common.security import decode_token
from common.ws.manager import manager as ws_manager
from persistence.db import db, serialize_doc

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> dict:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await db.users.find_one({"id": payload["sub"]})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    user = serialize_doc(user)
    user.pop("password_hash", None)
    if user["status"] != UserStatus.ACTIVE.value:
        raise HTTPException(status_code=403, detail=f"Account is {user['status']}")
    return await enrich_online(user)


def require_roles(*roles: str):
    async def _guard(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="You do not have permission to perform this action")
        return user

    return _guard


def get_bus(request: Request):
    return request.app.state.event_bus


def get_ws_manager():
    return ws_manager
