from datetime import datetime, timezone

from common.enums import EventDomain, EventType
from common.errors import ConflictError, ForbiddenError, NotFoundError
from common.events import emit_event
from persistence.db import db, new_id, serialize_doc


async def create_survey_for_ticket(bus, ticket: dict) -> dict | None:
    if not ticket.get("assignee_id"):
        return None
    existing = await db.csat_surveys.find_one({"ticket_id": ticket["id"]})
    if existing:
        return serialize_doc(existing)

    survey = {
        "id": new_id(),
        "ticket_id": ticket["id"],
        "technician_id": ticket["assignee_id"],
        "technician_username": ticket.get("assignee_username"),
        "requester_id": ticket["requester_id"],
        "rating": None,
        "comment": None,
        "status": "pending",
        "created_at": datetime.now(timezone.utc),
        "submitted_at": None,
    }
    doc = dict(survey)
    doc["_id"] = survey["id"]
    await db.csat_surveys.insert_one(doc)
    await emit_event(
        bus, EventDomain.CSAT.value, EventType.CSAT_REQUESTED.value,
        {"ticket_id": ticket["id"], "requester_id": ticket["requester_id"]}, ticket_id=ticket["id"],
    )
    return survey


async def get_survey(ticket_id: str) -> dict:
    survey = await db.csat_surveys.find_one({"ticket_id": ticket_id})
    if not survey:
        raise NotFoundError("No CSAT survey exists for this ticket yet")
    return serialize_doc(survey)


async def submit_csat(bus, employee: dict, ticket_id: str, rating: int, comment: str | None) -> dict:
    survey = await get_survey(ticket_id)
    if survey["requester_id"] != employee["id"]:
        raise ForbiddenError("Only the ticket requester can submit this survey")
    if survey["status"] == "submitted":
        raise ConflictError("This survey has already been submitted")

    now = datetime.now(timezone.utc)
    await db.csat_surveys.update_one(
        {"ticket_id": ticket_id},
        {"$set": {"rating": rating, "comment": comment, "status": "submitted", "submitted_at": now}},
    )
    await emit_event(
        bus, EventDomain.CSAT.value, EventType.CSAT_SUBMITTED.value,
        {"ticket_id": ticket_id, "technician_id": survey["technician_id"], "rating": rating}, actor_id=employee["id"], ticket_id=ticket_id,
    )
    return await get_survey(ticket_id)
