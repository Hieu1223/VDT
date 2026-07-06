import logging

from common.enums import TECHNICIAN_ROLES, UserStatus
from modules.assignment.algorithms import ALGORITHMS
from modules.tickets.service import get_ticket_or_404, set_assignee
from persistence.db import db

logger = logging.getLogger("assignment")

DEFAULT_CONFIG = {"id": "config", "_id": "config", "active_algorithm": "round_robin", "round_robin_cursor": 0}


async def get_config() -> dict:
    config = await db.assignment_config.find_one({"id": "config"})
    if not config:
        await db.assignment_config.insert_one(dict(DEFAULT_CONFIG))
        config = dict(DEFAULT_CONFIG)
    return config


async def set_active_algorithm(name: str) -> dict:
    if name not in ALGORITHMS:
        raise ValueError(f"Unknown algorithm '{name}'. Available: {list(ALGORITHMS.keys())}")
    await get_config()
    await db.assignment_config.update_one({"id": "config"}, {"$set": {"active_algorithm": name}})
    return await get_config()


async def list_algorithms() -> list[str]:
    return list(ALGORITHMS.keys())


async def get_available_technicians() -> list[dict]:
    cursor = db.users.find({"role": {"$in": list(TECHNICIAN_ROLES)}, "status": UserStatus.ACTIVE.value, "online": True})
    online = [t async for t in cursor]
    if online:
        return online
    cursor = db.users.find({"role": {"$in": list(TECHNICIAN_ROLES)}, "status": UserStatus.ACTIVE.value})
    return [t async for t in cursor]


async def assign_ticket_automatically(bus, ticket_id: str) -> dict | None:
    ticket = await get_ticket_or_404(ticket_id)
    if ticket.get("assignee_id"):
        return ticket
    config = await get_config()
    algorithm = ALGORITHMS.get(config["active_algorithm"], ALGORITHMS["round_robin"])
    candidates = await get_available_technicians()
    chosen = await algorithm(candidates, config)
    if not chosen:
        logger.warning("No technician available to assign ticket %s", ticket_id)
        return ticket
    return await set_assignee(bus, ticket_id, chosen)
