from datetime import datetime, timezone

from common.enums import EventDomain, EventType, TECHNICIAN_ROLES, UserStatus
from common.errors import ConflictError, NotFoundError, AppError
from common.events import emit_event
from common.presence import presence
from common.security import hash_password, verify_password
from persistence.db import db, new_id, serialize_doc

ADMIN_ASSIGNABLE_STATUS_EVENTS = {
    UserStatus.ACTIVE.value: EventType.USER_ACTIVATED.value,
    UserStatus.SUSPENDED.value: EventType.USER_SUSPENDED.value,
    UserStatus.DEACTIVATED.value: EventType.USER_DEACTIVATED.value,
}


def _clean(user: dict) -> dict:
    user = serialize_doc(user)
    user.pop("password_hash", None)
    return user


async def _clean_online(user: dict) -> dict:
    user = _clean(user)
    user["online"] = await presence.is_online(user["id"])
    return user


async def update_profile(user: dict, payload) -> dict:
    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if not updates:
        return user
    updates["updated_at"] = datetime.now(timezone.utc)
    await db.users.update_one({"id": user["id"]}, {"$set": updates})
    fresh = await db.users.find_one({"id": user["id"]})
    return await _clean_online(fresh)


async def change_password(user: dict, payload) -> None:
    full = await db.users.find_one({"id": user["id"]})
    if not verify_password(payload.current_password, full["password_hash"]):
        raise AppError("Current password is incorrect")
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"password_hash": hash_password(payload.new_password), "updated_at": datetime.now(timezone.utc)}},
    )


async def heartbeat(user_id: str) -> bool:
    """Records a presence heartbeat. Returns True if the user just came online."""
    return await presence.touch(user_id)


async def list_users(
    role: str | None = None,
    status: str | None = None,
    search: str | None = None,
    online: bool | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    query: dict = {}
    if role:
        query["role"] = role
    if status:
        query["status"] = status
    if search:
        query["$or"] = [
            {"username": {"$regex": search, "$options": "i"}},
            {"full_name": {"$regex": search, "$options": "i"}},
        ]
    if date_from or date_to:
        date_query: dict = {}
        if date_from:
            date_query["$gte"] = datetime.fromisoformat(date_from)
        if date_to:
            date_query["$lte"] = datetime.fromisoformat(date_to)
        query["created_at"] = date_query
    if online is not None:
        # Presence lives in Redis - fold the currently-online id set into
        # the Mongo query so skip/limit still happens at the DB level.
        _online_ids = list(await presence.online_ids())
        query["id"] = {"$in": _online_ids} if online else {"$nin": _online_ids}

    total = await db.users.count_documents(query)
    skip = (page - 1) * page_size
    cursor = db.users.find(query).sort("created_at", -1).skip(skip).limit(page_size)
    users = [_clean(u) async for u in cursor]
    return {"items": users, "total": total, "page": page, "page_size": page_size}


async def list_technicians() -> list[dict]:
    cursor = db.users.find({"role": {"$in": list(TECHNICIAN_ROLES)}, "status": UserStatus.ACTIVE.value})
    return [await _clean_online(u) async for u in cursor]


async def admin_create_user(bus, admin: dict, payload) -> dict:
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
        "status": UserStatus.ACTIVE.value,
        "created_at": now,
        "updated_at": now,
        "last_login_at": None,
    }
    doc = dict(user)
    doc["_id"] = user["id"]
    await db.users.insert_one(doc)
    await emit_event(
        bus, EventDomain.USER.value, EventType.USER_ACTIVATED.value,
        {"user_id": user["id"], "username": user["username"], "role": user["role"], "created_by_admin": admin["id"]},
        actor_id=admin["id"],
    )
    return await _clean_online(user)


async def update_user_status(bus, admin: dict, user_id: str, new_status: str) -> dict:
    target = await db.users.find_one({"id": user_id})
    if not target:
        raise NotFoundError("User not found")
    if new_status not in ADMIN_ASSIGNABLE_STATUS_EVENTS:
        raise AppError("Invalid status")

    await db.users.update_one(
        {"id": user_id}, {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc)}}
    )
    event_type = ADMIN_ASSIGNABLE_STATUS_EVENTS[new_status]
    await emit_event(
        bus, EventDomain.USER.value, event_type,
        {"user_id": user_id, "username": target["username"], "status": new_status, "reviewed_by": admin["id"]},
        actor_id=admin["id"],
    )
    fresh = await db.users.find_one({"id": user_id})
    return await _clean_online(fresh)
