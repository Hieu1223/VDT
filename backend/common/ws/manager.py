"""In-memory WebSocket connection registry, keyed by user id."""

import json
import logging
from typing import Any, Dict, Set
from fastapi import WebSocket

logger = logging.getLogger("ws_manager")


def _json_default(obj: Any) -> Any:
    return obj.isoformat() if hasattr(obj, "isoformat") else str(obj)


class ConnectionManager:
    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._roles: Dict[str, str] = {}

    async def connect(self, user_id: str, role: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(user_id, set()).add(websocket)
        self._roles[user_id] = role

    def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        sockets = self._connections.get(user_id)
        if sockets and websocket in sockets:
            sockets.discard(websocket)
            if not sockets:
                self._connections.pop(user_id, None)

    def is_online(self, user_id: str) -> bool:
        return bool(self._connections.get(user_id))

    async def _send(self, ws: WebSocket, message: dict) -> None:
        await ws.send_text(
            json.dumps(message, ensure_ascii=False, default=_json_default)
        )

    async def send_to_user(self, user_id: str, message: dict) -> None:
        for ws in list(self._connections.get(user_id, [])):
            try:
                await self._send(ws, message)
            except Exception:
                logger.exception("Failed to push WS message to user %s", user_id)

    async def send_to_users(self, user_ids, message: dict) -> None:
        for uid in set(user_ids):
            await self.send_to_user(uid, message)

    async def broadcast_to_roles(self, roles, message: dict) -> None:
        role_set = set(roles)
        for uid, role in list(self._roles.items()):
            if role in role_set:
                await self.send_to_user(uid, message)


manager = ConnectionManager()
