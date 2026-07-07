import logging

from common.enums import TECHNICIAN_ROLES, UserStatus
from common.presence import presence
from modules.assignment.algorithms import ALGORITHMS
from modules.tickets.service import get_ticket_or_404, set_assignee, unassign_ticket
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


async def get_available_technicians(exclude_ids: set[str] | None = None) -> list[dict]:
    """Only technicians who are currently online (Redis-backed presence) are
    eligible for (re)assignment - there is no fallback to offline staff, per
    product requirement. Tickets with no eligible online technician stay
    (or fall back into) the unassigned queue."""
    online_ids = await presence.online_ids() - (exclude_ids or set())
    if not online_ids:
        return []
    cursor = db.users.find({"role": {"$in": list(TECHNICIAN_ROLES)}, "status": UserStatus.ACTIVE.value, "id": {"$in": list(online_ids)}})
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
        logger.warning("No online technician available to assign ticket %s - left unassigned", ticket_id)
        return ticket
    return await set_assignee(bus, ticket_id, chosen)


async def reassign_offline_tickets(bus) -> int:
    """Periodic sweep: any open ticket whose current assignee has gone
    offline gets reassigned to another online technician, or - if none are
    online - unassigned (falls back into the unassigned queue)."""
    from common.enums import OPEN_TICKET_STATUSES

    online_ids = await presence.online_ids()
    config = await get_config()
    algorithm = ALGORITHMS.get(config["active_algorithm"], ALGORITHMS["round_robin"])
    moved = 0

    cursor = db.tickets.find({"status": {"$in": list(OPEN_TICKET_STATUSES)}, "assignee_id": {"$ne": None}})
    async for ticket in cursor:
        if ticket["assignee_id"] in online_ids:
            continue
        candidates = await get_available_technicians(exclude_ids={ticket["assignee_id"]})
        chosen = await algorithm(candidates, config)
        if chosen:
            await set_assignee(bus, ticket["id"], chosen)
            logger.info("Reassigned ticket %s from offline technician to %s", ticket["id"], chosen["username"])
        else:
            await unassign_ticket(bus, ticket["id"])
            logger.info("Ticket %s unassigned - no online technician available", ticket["id"])
        moved += 1
    return moved
