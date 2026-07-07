import logging
import os

from common.ws.manager import manager as ws_manager
from modules.notifications import service

logger = logging.getLogger("notifications.consumer")
DEBUG_LOG = os.path.join(os.path.dirname(__file__), "..", "..", "notif_debug.log")


def make_notification_consumer():
    async def handle(routing_key: str, event: dict):
        with open(DEBUG_LOG, "a") as f:
            f.write(f"[{routing_key}] consume event_type={event.get('event_type')}\n")
        targets = await service.build_targets(event)
        print(targets)
        for user_id, notif_type, title, body in targets:
            notification = await service.persist_and_get(user_id, notif_type, title, body, event.get("ticket_id"))
            with open(DEBUG_LOG, "a") as f:
                f.write(f"[{routing_key}] send_to_user uid={user_id} kind={notification['type']}\n")
                f.write(f"[{routing_key}] conns={list(ws_manager._connections.keys())}\n")
            await ws_manager.send_to_user(user_id, {"kind": "notification", "data": notification})
            await service.mark_dispatched(notification["id"])
        if event.get("ticket_id"):
            await ws_manager.broadcast_to_roles(
                ["admin"], {"kind": "ticket_event", "data": {"ticket_id": event["ticket_id"], "event_type": event["event_type"]}}
            )

    return handle
