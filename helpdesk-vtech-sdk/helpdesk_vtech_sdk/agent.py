"""High-level Virtual Technician agent wrapper.

Combines `VTechClient` (REST) + `WSListener` (real-time events) + an
automatic presence heartbeat into a single object usable as an async
context manager, with decorator-based callback registration:

    from helpdesk_vtech_sdk import VirtualTechnician

    sdk = VirtualTechnician(base_url="http://localhost:8001", username="tech.virtual", password="VTech@12345")

    @sdk.on("ticket_assigned")
    async def handle_assignment(event):
        ticket_id = event["data"]["ticket_id"]
        await sdk.acquire_lock(ticket_id)
        await sdk.send_message(ticket_id, "On it!")
        await sdk.resolve(ticket_id, "Fixed.")

    async def main():
        async with sdk:
            await sdk.run()  # blocks: heartbeat loop + WS listener

    asyncio.run(main())

A Virtual Technician can only act on tickets already assigned to it
(resolve/reject/message/lock) and escalate to an upper level for review -
it cannot directly reassign a ticket to another technician, matching the
same permission boundary enforced server-side for the `technician_virtual`
role.
"""
import asyncio
import inspect
import logging
from collections import defaultdict
from typing import Awaitable, Callable, Optional, Union

from helpdesk_vtech_sdk.client import VTechClient
from helpdesk_vtech_sdk.ws_listener import WSListener

logger = logging.getLogger("helpdesk_vtech_sdk.agent")

DEFAULT_HEARTBEAT_INTERVAL_SECONDS = 20.0

Callback = Callable[[dict], Union[Awaitable[None], None]]


class VirtualTechnician:
    """Async context manager wrapping a Virtual Technician's full lifecycle:
    login, presence heartbeat, real-time event callbacks, and every
    technician capability exposed on `VTechClient` (via attribute
    delegation - e.g. `await sdk.resolve(...)`, `await sdk.escalate(...)`)."""

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        heartbeat_interval: float = DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
    ):
        self.client = VTechClient(base_url, username, password)
        self._ws: Optional[WSListener] = None
        self._heartbeat_interval = heartbeat_interval
        self._callbacks: dict[str, list[Callback]] = defaultdict(list)
        self._tasks: list[asyncio.Task] = []
        self._stop_event = asyncio.Event()

    async def __aenter__(self) -> "VirtualTechnician":
        await self.client.connect()
        self._ws = WSListener(self.client.base_url, access_token_provider=lambda: self.client.access_token)
        return self

    async def __aexit__(self, *exc_info) -> None:
        self.stop()
        for task in self._tasks:
            task.cancel()
        await self.client.close()

    def __getattr__(self, name: str):
        """Delegates any undefined attribute/method to the underlying
        VTechClient, so every technician capability (get_queue, resolve,
        reject, escalate, reassign_request, acquire_lock, send_message,
        edit_message, delete_message, upload_attachment, ...) is directly
        callable on the VirtualTechnician instance itself."""
        return getattr(self.client, name)

    # ---- Callback registration ----

    def on(self, event_kind: str) -> Callable[[Callback], Callback]:
        """Registers a callback for a WS event. `event_kind` matches either
        the top-level WS message `kind` (e.g. "ticket_event", "presence") or,
        for `kind == "notification"` messages, the notification's `data.type`
        (e.g. "ticket_assigned", "new_message", "sla_alert", "csat_request",
        "escalation_update", "reassign_update")."""
        def decorator(fn: Callback) -> Callback:
            self._callbacks[event_kind].append(fn)
            return fn
        return decorator

    def on_ticket_assigned(self, fn: Callback) -> Callback:
        self._callbacks["ticket_assigned"].append(fn)
        return fn

    def on_new_message(self, fn: Callback) -> Callback:
        self._callbacks["new_message"].append(fn)
        return fn

    def on_sla_alert(self, fn: Callback) -> Callback:
        self._callbacks["sla_alert"].append(fn)
        return fn

    def on_escalation_update(self, fn: Callback) -> Callback:
        self._callbacks["escalation_update"].append(fn)
        return fn

    async def _dispatch(self, event: dict) -> None:
        kinds = [event.get("kind")]
        if event.get("kind") == "notification":
            kinds.append(event.get("data", {}).get("type"))
        for kind in kinds:
            for fn in self._callbacks.get(kind, []):
                try:
                    result = fn(event)
                    if inspect.isawaitable(result):
                        await result
                except Exception:
                    logger.exception("Error running callback for event kind=%s", kind)

    # ---- Lifecycle ----

    async def _heartbeat_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                await self.client.heartbeat()
            except Exception:
                logger.exception("Heartbeat failed")
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self._heartbeat_interval)
            except asyncio.TimeoutError:
                pass

    async def run(self) -> None:
        """Starts the presence heartbeat loop and blocks on the WebSocket
        event listener, dispatching to registered callbacks. Call `stop()`
        (from a callback or another task) to return."""
        self._stop_event.clear()
        self._tasks.append(asyncio.create_task(self._heartbeat_loop()))
        assert self._ws is not None, "Use 'async with VirtualTechnician(...) as sdk:' before calling run()"
        await self._ws.listen(self._dispatch)

    def stop(self) -> None:
        self._stop_event.set()
        if self._ws:
            self._ws.stop()
