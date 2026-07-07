from datetime import datetime, timezone

from common.enums import EventDomain, EventType, UserRole, UserStatus
from common.errors import ConflictError, ForbiddenError, UnauthorizedError
from common.events import emit_event
from common.presence import enrich_online, presence
from common.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from persistence.db import db, new_id, serialize_doc

SELF_REGISTERABLE_ROLES = {UserRole.EMPLOYEE.value, UserRole.TECHNICIAN_HUMAN.value}


async def register_user(bus, payload) -> dict:
    if payload.role not in SELF_REGISTERABLE_ROLES:
        raise ForbiddenError("This role cannot self-register. Contact an administrator.")

    existing = await db.users.find_one({"username": payload.username.lower()})
    if existing:
        raise ConflictError("Username is already taken")

    now = datetime.now(timezone.utc)
    user = {
        "id": new_id(),
        "username": payload.username.lower(),
        "password_hash": hash_password(payload.password),
        "full_name": payload.full_name,
        "email": payload.email,
        "role": payload.role,
        "status": UserStatus.PENDING_ACTIVATION.value,
        "online": False,
        "created_at": now,
        "updated_at": now,
        "last_login_at": None,
    }
    doc = dict(user)
    doc["_id"] = user["id"]
    await db.users.insert_one(doc)

    await emit_event(
        bus, EventDomain.USER.value, EventType.USER_REGISTERED.value,
        {"user_id": user["id"], "username": user["username"], "role": user["role"]},
        actor_id=user["id"],
    )
    user.pop("password_hash")
    return user


async def authenticate_user(bus, username: str, password: str) -> dict:
    user = await db.users.find_one({"username": username.lower()})
    if not user or not verify_password(password, user["password_hash"]):
        raise UnauthorizedError("Invalid username or password")

    if user["status"] != UserStatus.ACTIVE.value:
        raise ForbiddenError(f"account_{user['status']}")

    now = datetime.now(timezone.utc)
    await db.users.update_one({"id": user["id"]}, {"$set": {"last_login_at": now, "updated_at": now}})
    user["last_login_at"] = now
    await presence.touch(user["id"])

    await emit_event(
        bus, EventDomain.USER.value, EventType.USER_ONLINE.value,
        {"user_id": user["id"], "username": user["username"]},
        actor_id=user["id"],
    )

    user = serialize_doc(user)
    user.pop("password_hash")
    return await enrich_online(user)


def issue_tokens(user: dict) -> dict:
    return {
        "access_token": create_access_token(user["id"], user["role"], user["username"]),
        "refresh_token": create_refresh_token(user["id"]),
        "token_type": "bearer",
        "user": user,
    }


async def refresh_access_token(refresh_token: str) -> dict:
    try:
        payload = decode_token(refresh_token)
    except Exception:
        raise UnauthorizedError("Invalid or expired refresh token")
    if payload.get("type") != "refresh":
        raise UnauthorizedError("Invalid token type")

    user = await db.users.find_one({"id": payload["sub"]})
    if not user or user["status"] != UserStatus.ACTIVE.value:
        raise UnauthorizedError("User not found or inactive")
    user = serialize_doc(user)
    user.pop("password_hash")
    return {
        "access_token": create_access_token(user["id"], user["role"], user["username"]),
        "refresh_token": create_refresh_token(user["id"]),
        "token_type": "bearer",
        "user": await enrich_online(user),
    }


async def logout_user(bus, user: dict) -> None:
    await presence.mark_offline(user["id"])
    await emit_event(
        bus, EventDomain.USER.value, EventType.USER_OFFLINE.value,
        {"user_id": user["id"], "username": user["username"]},
        actor_id=user["id"],
    )
