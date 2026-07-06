import asyncio
import json
import logging
from typing import Awaitable, Callable, Optional

import websockets

from helpdesk_vtech_sdk.exceptions import WebSocketError

logger = logging.getLogger("helpdesk_vtech_sdk.ws_listener")


class WSListener:
    """Connects to the Helpdesk WebSocket endpoint for real-time notification
    events (new messages, assignments, escalation updates, SLA alerts...).

    Example:
        async def on_event(event: dict):
            print("received:", event)

        listener = WSListener(base_url, access_token_provider=lambda: client.access_token)
        await listener.listen(on_event)
    """

    def __init__(self, base_url: str, access_token_provider: Callable[[], Optional[str]], reconnect_delay: float = 3.0):
        self.base_url = base_url.rstrip("/").replace("http", "ws", 1)
        self._token_provider = access_token_provider
        self._reconnect_delay = reconnect_delay
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    async def listen(self, on_event: Callable[[dict], Awaitable[None]]) -> None:
        self._stop = False
        while not self._stop:
            token = self._token_provider()
            if not token:
                raise WebSocketError("No access token available; connect the VTechClient first.")
            url = f"{self.base_url}/api/ws?token={token}"
            try:
                async with websockets.connect(url) as ws:
                    logger.info("WebSocket connected")
                    async for raw in ws:
                        try:
                            await on_event(json.loads(raw))
                        except Exception:
                            logger.exception("Error handling WS event")
            except Exception:
                if self._stop:
                    break
                logger.warning("WebSocket disconnected, retrying in %.1fs", self._reconnect_delay)
                await asyncio.sleep(self._reconnect_delay)
