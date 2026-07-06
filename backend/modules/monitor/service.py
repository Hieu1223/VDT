from common.presence import presence
from common.ws.manager import manager as ws_manager
from persistence.db import db, serialize_doc


async def monitor_users(online: bool | None = None) -> list[dict]:
    cursor = db.users.find({}, {"password_hash": 0}).sort("created_at", -1)
    users = []
    async for u in cursor:
        u = serialize_doc(u)
        u["online"] = presence.is_online(u["id"])
        u["ws_connected"] = ws_manager.is_online(u["id"])
        users.append(u)
    if online is not None:
        users = [u for u in users if u["online"] == online]
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

    resolved_count = await db.tickets.count_documents({"status": "resolved"})
    resolved_within_sla = await db.tickets.count_documents({"status": "resolved", "sla.resolve_breached": False})
    sla_compliance_rate = round((resolved_within_sla / resolved_count) * 100, 1) if resolved_count else None

    csat_agg = await db.csat_surveys.aggregate([
        {"$match": {"status": "submitted"}},
        {"$group": {"_id": None, "avg_rating": {"$avg": "$rating"}, "count": {"$sum": 1}}},
    ]).to_list(1)
    avg_csat_score = round(csat_agg[0]["avg_rating"], 2) if csat_agg else None
    csat_response_count = csat_agg[0]["count"] if csat_agg else 0

    return {
        "total": total,
        "by_status": by_status,
        "by_priority": by_priority,
        "sla_first_response_breached": first_response_breached,
        "sla_resolve_breached": resolve_breached,
        "currently_locked": locked,
        "sla_compliance_rate": sla_compliance_rate,
        "avg_csat_score": avg_csat_score,
        "csat_response_count": csat_response_count,
    }
