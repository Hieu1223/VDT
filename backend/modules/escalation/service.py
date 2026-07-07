from datetime import datetime, timezone

from common.enums import EventDomain, EventType, RequestStatus, RequestType, TicketStatus, UserRole, UserStatus
from common.errors import ConflictError, ForbiddenError, NotFoundError
from common.events import emit_event
from common.presence import presence
from modules.assignment.algorithms import ALGORITHMS
from modules.assignment.service import get_config
from modules.tickets.service import get_ticket_or_404, set_assignee
from persistence.db import db, new_id, serialize_doc

EVENT_MAP = {
    RequestType.ESCALATION: {
        "domain": EventDomain.ESCALATION.value,
        "requested": EventType.ESCALATION_REQUESTED.value,
        "approved": EventType.ESCALATION_APPROVED.value,
        "rejected": EventType.ESCALATION_REJECTED.value,
        "returned": EventType.ESCALATION_RETURNED.value,
    },
    RequestType.REASSIGNMENT: {
        "domain": EventDomain.REASSIGN.value,
        "requested": EventType.REASSIGN_REQUESTED.value,
        "approved": EventType.REASSIGN_APPROVED.value,
        "rejected": EventType.REASSIGN_REJECTED.value,
        "returned": EventType.REASSIGN_RETURNED.value,
    },
}


async def _pick_online_human_technician(exclude_ids: set[str] | None = None) -> dict | None:
    config = await get_config()
    algorithm = ALGORITHMS.get(config.get("active_algorithm", "round_robin"), ALGORITHMS["round_robin"])
    online_ids = await presence.online_ids() - (exclude_ids or set())
    if not online_ids:
        return None
    cursor = db.users.find({
        "role": UserRole.TECHNICIAN_HUMAN.value,
        "status": UserStatus.ACTIVE.value,
        "id": {"$in": list(online_ids)},
    })
    candidates = [t async for t in cursor]
    return await algorithm(candidates, config)


async def _create_request(bus, req_type: RequestType, technician: dict, ticket_id: str, reason: str, target_technician_id: str | None) -> dict:
    ticket = await get_ticket_or_404(ticket_id)
    if ticket.get("assignee_id") != technician["id"]:
        raise ForbiddenError("Only the current assignee can raise this request")
    if ticket.get("request_pending"):
        raise ConflictError("This ticket already has a pending escalation/reassignment request")

    now = datetime.now(timezone.utc)
    request = {
        "id": new_id(),
        "type": req_type.value,
        "ticket_id": ticket_id,
        "requested_by": technician["id"],
        "requested_by_username": technician["username"],
        "reason": reason,
        "target_technician_id": target_technician_id,
        "status": RequestStatus.PENDING.value,
        "reviewed_by": None,
        "review_note": None,
        "created_at": now,
        "reviewed_at": None,
    }
    doc = dict(request)
    doc["_id"] = request["id"]
    await db.requests.insert_one(doc)

    updates = {"request_pending": True, "updated_at": now}
    auto_assigned_human = None
    if req_type == RequestType.ESCALATION and technician["role"] == UserRole.TECHNICIAN_VIRTUAL.value:
        auto_assigned_human = await _pick_online_human_technician(exclude_ids={technician["id"]})
        if auto_assigned_human:
            updates["status"] = TicketStatus.ASSIGNED.value
            updates["previous_status"] = None
            updates["request_pending"] = False
            updates["assignee_id"] = auto_assigned_human["id"]
            updates["assignee_username"] = auto_assigned_human["username"]
        else:
            updates["previous_status"] = ticket["status"]
    elif req_type == RequestType.ESCALATION:
        updates["previous_status"] = ticket["status"]
    await db.tickets.update_one({"id": ticket_id}, {"$set": updates})

    if req_type == RequestType.ESCALATION and technician["role"] == UserRole.TECHNICIAN_VIRTUAL.value:
        await db.requests.update_one(
            {"id": request["id"]},
            {"$set": {"status": RequestStatus.APPROVED.value, "reviewed_by": auto_assigned_human["id"] if auto_assigned_human else None, "review_note": "Auto-escalated to queue", "reviewed_at": now, "target_technician_id": auto_assigned_human["id"] if auto_assigned_human else None}},
        )

    events = EVENT_MAP[req_type]
    await emit_event(
        bus, events["domain"], events["requested"],
        {"ticket_id": ticket_id, "request_id": request["id"], "reason": reason, "requested_by": technician["id"]},
        actor_id=technician["id"], ticket_id=ticket_id,
    )
    return request


async def create_escalation(bus, technician: dict, ticket_id: str, reason: str, suggested_target_id: str | None) -> dict:
    return await _create_request(bus, RequestType.ESCALATION, technician, ticket_id, reason, suggested_target_id)


async def create_reassignment(bus, technician: dict, ticket_id: str, reason: str, target_technician_id: str) -> dict:
    return await _create_request(bus, RequestType.REASSIGNMENT, technician, ticket_id, reason, target_technician_id)


async def _get_pending_request_or_404(request_id: str) -> dict:
    request = await db.requests.find_one({"id": request_id})
    if not request:
        raise NotFoundError("Request not found")
    if request["status"] != RequestStatus.PENDING.value:
        raise ConflictError("Request has already been reviewed")
    return serialize_doc(request)


async def approve_request(bus, admin: dict, request_id: str, target_technician_id: str | None, note: str | None) -> dict:
    request = await _get_pending_request_or_404(request_id)
    req_type = RequestType(request["type"])
    final_target_id = target_technician_id or request.get("target_technician_id")
    if not final_target_id:
        raise ConflictError("A target technician must be specified to approve this request")

    target_user = await db.users.find_one({"id": final_target_id})
    if not target_user:
        raise NotFoundError("Target technician not found")

    now = datetime.now(timezone.utc)
    await set_assignee(bus, request["ticket_id"], serialize_doc(target_user), actor_id=admin["id"])
    await db.tickets.update_one({"id": request["ticket_id"]}, {"$set": {"request_pending": False, "previous_status": None}})
    await db.requests.update_one(
        {"id": request_id},
        {"$set": {"status": RequestStatus.APPROVED.value, "reviewed_by": admin["id"], "review_note": note, "reviewed_at": now, "target_technician_id": final_target_id}},
    )

    events = EVENT_MAP[req_type]
    await emit_event(
        bus, events["domain"], events["approved"],
        {"ticket_id": request["ticket_id"], "request_id": request_id, "target_technician_id": final_target_id, "requested_by": request["requested_by"]},
        actor_id=admin["id"], ticket_id=request["ticket_id"],
    )
    return await db.requests.find_one({"id": request_id}, {"_id": 0})


async def _finalize_without_reassign(bus, admin: dict, request_id: str, note: str | None, final_status: str, event_key: str) -> dict:
    request = await _get_pending_request_or_404(request_id)
    req_type = RequestType(request["type"])
    now = datetime.now(timezone.utc)

    ticket_updates = {"request_pending": False}
    if req_type == RequestType.ESCALATION:
        ticket = await get_ticket_or_404(request["ticket_id"])
        ticket_updates["status"] = ticket.get("previous_status") or TicketStatus.IN_PROGRESS.value
        ticket_updates["previous_status"] = None
    await db.tickets.update_one({"id": request["ticket_id"]}, {"$set": ticket_updates})

    await db.requests.update_one(
        {"id": request_id},
        {"$set": {"status": final_status, "reviewed_by": admin["id"], "review_note": note, "reviewed_at": now}},
    )

    events = EVENT_MAP[req_type]
    await emit_event(
        bus, events["domain"], events[event_key],
        {"ticket_id": request["ticket_id"], "request_id": request_id, "requested_by": request["requested_by"], "note": note},
        actor_id=admin["id"], ticket_id=request["ticket_id"],
    )
    return await db.requests.find_one({"id": request_id}, {"_id": 0})


async def reject_request(bus, admin: dict, request_id: str, note: str | None) -> dict:
    return await _finalize_without_reassign(bus, admin, request_id, note, RequestStatus.REJECTED.value, "rejected")


async def return_request(bus, admin: dict, request_id: str, note: str | None) -> dict:
    return await _finalize_without_reassign(bus, admin, request_id, note, RequestStatus.RETURNED.value, "returned")


async def list_my_requests(technician: dict) -> list[dict]:
    cursor = db.requests.find({"requested_by": technician["id"]}).sort("created_at", -1)
    return [serialize_doc(r) async for r in cursor]


async def list_pending_requests() -> list[dict]:
    cursor = db.requests.find({"status": RequestStatus.PENDING.value}).sort("created_at", 1)
    return [serialize_doc(r) async for r in cursor]
