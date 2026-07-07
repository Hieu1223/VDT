from datetime import datetime, timezone

from common.enums import NotificationType, UserRole, UserStatus
from persistence.db import db, new_id, serialize_doc


async def _admin_ids() -> list[str]:
    cursor = db.users.find(
        {"role": UserRole.ADMIN.value, "status": UserStatus.ACTIVE.value}, {"id": 1}
    )
    return [u["id"] async for u in cursor]


async def _technician_ids() -> list[str]:
    cursor = db.users.find(
        {
            "role": {
                "$in": [
                    UserRole.TECHNICIAN_HUMAN.value,
                    UserRole.TECHNICIAN_VIRTUAL.value,
                ]
            },
            "status": UserStatus.ACTIVE.value,
        },
        {"id": 1},
    )
    return [u["id"] async for u in cursor]


async def build_targets(event: dict) -> list[tuple[str, str, str, str]]:
    """Returns list of (user_id, type, title, body) to notify for this event."""
    domain, event_type, payload = event["domain"], event["event_type"], event["payload"]
    out: list[tuple[str, str, str, str]] = []

    if event_type == "USER_REGISTERED":
        for admin_id in await _admin_ids():
            out.append(
                (
                    admin_id,
                    NotificationType.USER_LIFECYCLE.value,
                    "New user awaiting activation",
                    f"{payload.get('username')} registered and needs activation.",
                )
            )

    elif event_type in ("USER_ACTIVATED", "USER_SUSPENDED", "USER_DEACTIVATED"):
        uid = payload.get("user_id")
        if uid:
            out.append(
                (
                    uid,
                    NotificationType.USER_LIFECYCLE.value,
                    "Account status updated",
                    f"Your account is now {payload.get('status')}.",
                )
            )

    elif event_type == "TICKET_CREATED":
        for admin_id in await _admin_ids():
            out.append(
                (
                    admin_id,
                    NotificationType.TICKET_CREATED.value,
                    "New ticket created",
                    f"Ticket '{payload.get('subject')}' was created by {payload.get('requester_username', 'a user')}.",
                )
            )
        for tech_id in await _technician_ids():
            out.append(
                (
                    tech_id,
                    NotificationType.TICKET_CREATED.value,
                    "New ticket available",
                    f"New ticket '{payload.get('subject')}' is awaiting pickup.",
                )
            )

    elif event_type == "TICKET_ASSIGNED":
        assignee_id = payload.get("assignee_id")
        if assignee_id:
            out.append(
                (
                    assignee_id,
                    NotificationType.TICKET_ASSIGNED.value,
                    "Ticket assigned to you",
                    f"Ticket assigned to you by the system.",
                )
            )

    elif event_type == "TICKET_RESOLVED":
        requester_id = payload.get("requester_id")
        if requester_id:
            out.append(
                (
                    requester_id,
                    NotificationType.TICKET_STATUS_CHANGED.value,
                    "Your ticket was resolved",
                    "Please rate your experience with our technician.",
                )
            )

    elif event_type == "TICKET_REJECTED":
        requester_id = payload.get("requester_id")
        if requester_id:
            out.append(
                (
                    requester_id,
                    NotificationType.TICKET_STATUS_CHANGED.value,
                    "Your ticket was rejected",
                    payload.get("rejection_reason", ""),
                )
            )

    elif event_type == "TICKET_UNASSIGNED":
        for admin_id in await _admin_ids():
            out.append(
                (
                    admin_id,
                    NotificationType.TICKET_ASSIGNED.value,
                    "Ticket unassigned",
                    f"Ticket {payload.get('ticket_id')} was unassigned: {payload.get('reason', '')}.",
                )
            )

    elif event_type == "MESSAGE_SENT":
        sender_id = payload.get("sender_id")
        for candidate in (payload.get("requester_id"), payload.get("assignee_id")):
            if candidate and candidate != sender_id:
                out.append(
                    (
                        candidate,
                        NotificationType.NEW_MESSAGE.value,
                        f"New message from {payload.get('sender_username')}",
                        payload.get("content", "")[:140],
                    )
                )

    elif event_type == "MESSAGE_EDITED":
        sender_id = payload.get("sender_id")
        for candidate in (payload.get("requester_id"), payload.get("assignee_id")):
            if candidate and candidate != sender_id:
                out.append(
                    (
                        candidate,
                        NotificationType.MESSAGE_EDITED.value,
                        f"Message edited by {payload.get('sender_username')}",
                        "A message in this ticket was updated.",
                    )
                )

    elif event_type == "MESSAGE_DELETED":
        sender_id = payload.get("sender_id")
        for candidate in (payload.get("requester_id"), payload.get("assignee_id")):
            if candidate and candidate != sender_id:
                out.append(
                    (
                        candidate,
                        NotificationType.MESSAGE_DELETED.value,
                        f"Message deleted by {payload.get('sender_username')}",
                        "A message in this ticket was removed.",
                    )
                )

    elif event_type in ("ESCALATION_REQUESTED", "REASSIGN_REQUESTED"):
        for admin_id in await _admin_ids():
            out.append(
                (
                    admin_id,
                    NotificationType.ESCALATION_UPDATE.value,
                    "New request awaiting review",
                    payload.get("reason", ""),
                )
            )

    elif event_type in (
        "ESCALATION_APPROVED",
        "ESCALATION_REJECTED",
        "ESCALATION_RETURNED",
    ):
        requested_by = payload.get("requested_by")
        if requested_by:
            out.append(
                (
                    requested_by,
                    NotificationType.ESCALATION_UPDATE.value,
                    f"Your escalation was {event_type.split('_')[-1].lower()}",
                    payload.get("note", "") or "",
                )
            )
        target = payload.get("target_technician_id")
        if target:
            out.append(
                (
                    target,
                    NotificationType.TICKET_ASSIGNED.value,
                    "Escalated ticket assigned to you",
                    "An admin approved an escalation and assigned the ticket to you.",
                )
            )

    elif event_type in ("REASSIGN_APPROVED", "REASSIGN_REJECTED", "REASSIGN_RETURNED"):
        requested_by = payload.get("requested_by")
        if requested_by:
            out.append(
                (
                    requested_by,
                    NotificationType.REASSIGN_UPDATE.value,
                    f"Your reassignment request was {event_type.split('_')[-1].lower()}",
                    payload.get("note", "") or "",
                )
            )
        target = payload.get("target_technician_id")
        if target:
            out.append(
                (
                    target,
                    NotificationType.TICKET_ASSIGNED.value,
                    "Ticket reassigned to you",
                    "An admin approved a reassignment and assigned the ticket to you.",
                )
            )

    elif event_type in (
        "SLA_NEAR_BREACH_FIRST_RESPONSE",
        "SLA_BREACHED_FIRST_RESPONSE",
        "SLA_NEAR_BREACH_RESOLVE",
        "SLA_BREACHED_RESOLVE",
    ):
        assignee_id = payload.get("assignee_id")
        title = "SLA breach warning" if "NEAR_BREACH" in event_type else "SLA BREACHED"
        recipients = set(await _admin_ids())
        if assignee_id:
            recipients.add(assignee_id)
        for uid in recipients:
            out.append(
                (
                    uid,
                    NotificationType.SLA_ALERT.value,
                    title,
                    f"Ticket {payload.get('ticket_id')} - {event_type}",
                )
            )

    elif event_type == "CSAT_REQUESTED":
        requester_id = payload.get("requester_id")
        if requester_id:
            out.append(
                (
                    requester_id,
                    NotificationType.CSAT_REQUEST.value,
                    "Rate your support experience",
                    "Your ticket was resolved - let us know how we did.",
                )
            )

    return out


async def persist_and_get(
    user_id: str, notif_type: str, title: str, body: str, ticket_id: str | None
) -> dict:
    now = datetime.now(timezone.utc)
    notification = {
        "id": new_id(),
        "user_id": user_id,
        "type": notif_type,
        "title": title,
        "body": body,
        "ticket_id": ticket_id,
        "read_at": None,
        "dispatched": False,
        "created_at": now,
    }
    doc = dict(notification)
    doc["_id"] = notification["id"]
    await db.notifications.insert_one(doc)
    return notification


async def mark_dispatched(notification_id: str) -> None:
    await db.notifications.update_one(
        {"id": notification_id}, {"$set": {"dispatched": True}}
    )


async def list_my_notifications(user_id: str) -> list[dict]:
    cursor = (
        db.notifications.find({"user_id": user_id}).sort("created_at", -1).limit(100)
    )
    return [serialize_doc(n) async for n in cursor]


async def mark_read(user_id: str, notification_id: str) -> None:
    await db.notifications.update_one(
        {"id": notification_id, "user_id": user_id},
        {"$set": {"read_at": datetime.now(timezone.utc)}},
    )


async def mark_all_read(user_id: str) -> None:
    await db.notifications.update_many(
        {"user_id": user_id, "read_at": None},
        {"$set": {"read_at": datetime.now(timezone.utc)}},
    )
