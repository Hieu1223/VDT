import logging

from common.ws.manager import manager as ws_manager
from modules.notifications import service

logger = logging.getLogger("notifications.consumer")


def make_notification_consumer():
    async def handle(routing_key: str, event: dict):
        targets = await service.build_targets(event)
        for user_id, notif_type, title, body in targets:
            notification = await service.persist_and_get(user_id, notif_type, title, body, event.get("ticket_id"))
            await ws_manager.send_to_user(user_id, {"kind": "notification", "data": notification})
            await service.mark_dispatched(notification["id"])
        if event.get("ticket_id"):
            await ws_manager.broadcast_to_roles(
                ["admin"], {"kind": "ticket_event", "data": {"ticket_id": event["ticket_id"], "event_type": event["event_type"]}}
            )

    return handle
