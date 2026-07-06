from common.ws.manager import manager as ws_manager
from persistence.db import db, serialize_doc


async def monitor_users() -> list[dict]:
    cursor = db.users.find({}, {"password_hash": 0}).sort("created_at", -1)
    users = []
    async for u in cursor:
        u = serialize_doc(u)
        u["ws_connected"] = ws_manager.is_online(u["id"])
        users.append(u)
    return users


async def monitor_tickets() -> dict:
    total = await db.tickets.count_documents({})
    by_status = {}
    async for row in db.tickets.aggregate([{"$group": {"_id": "$status", "count": {"$sum": 1}}}]):
        by_status[row["_id"]] = row["count"]
    by_priority = {}
    async for row in db.tickets.aggregate([{"$group": {"_id": "$priority", "count": {"$sum": 1}}}]):
        by_priority[row["_id"]] = row["count"]

    first_response_breached = await db.tickets.count_documents({"sla.first_response_breached": True})
    resolve_breached = await db.tickets.count_documents({"sla.resolve_breached": True})
    locked = await db.tickets.count_documents({"lock.locked_by": {"$ne": None}})

    return {
        "total": total,
        "by_status": by_status,
        "by_priority": by_priority,
        "sla_first_response_breached": first_response_breached,
        "sla_resolve_breached": resolve_breached,
        "currently_locked": locked,
    }
