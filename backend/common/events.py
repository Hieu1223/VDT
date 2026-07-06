"""Central helper for emitting domain events: persists to the `events`
collection (for Timeline/Monitor/Event log) AND publishes to RabbitMQ.
"""
from datetime import datetime, timezone

from common.event_bus.base import EventBus
from persistence.db import db, new_id


async def emit_event(
    bus: EventBus,
    domain: str,
    event_type: str,
    payload: dict,
    actor_id: str | None = None,
    ticket_id: str | None = None,
) -> dict:
    event = {
        "id": new_id(),
        "domain": domain,
        "event_type": event_type,
        "routing_key": f"{domain}.{event_type}",
        "payload": payload,
        "actor_id": actor_id,
        "ticket_id": ticket_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    event_for_mongo = dict(event)
    event_for_mongo["_id"] = event["id"]
    await db.events.insert_one(event_for_mongo)
    await bus.publish(event["routing_key"], event)
    return event
