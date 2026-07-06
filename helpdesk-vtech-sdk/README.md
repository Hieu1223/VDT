# helpdesk-vtech-sdk

Async Python SDK for building **Virtual Technician** agents that connect to
the Helpdesk / ITSM platform. Wraps every `/api/vtech/*` endpoint with an
async `httpx` client, handles JWT login/refresh/retry automatically, keeps
the account "online" via an automatic presence heartbeat, and provides a
WebSocket listener with decorator-based callbacks for real-time events.

This package contains **no AI/automation logic** — it is purely a client
library. Bring your own automation/AI logic and call these methods from it.

A Virtual Technician can only act on tickets already assigned to it
(resolve, reject, message, lock) and escalate to an upper level for admin
review - it cannot directly reassign a ticket to another technician. This
mirrors the permission boundary enforced server-side for the
`technician_virtual` role.

## Install

```bash
# From PyPI (once published)
pip install helpdesk-vtech-sdk

# From local path during development
pip install -e ./helpdesk-vtech-sdk
```

## Requirements

A Virtual Technician account must already exist on the Helpdesk backend
(role `technician_virtual`, status `active`). Admins create these via
the Admin → Users page or `POST /api/users`.

## Usage: `VirtualTechnician` (recommended)

The `VirtualTechnician` class is an async context manager that bundles
login, an automatic 20s presence heartbeat, and a WebSocket event loop with
decorator-based callbacks. Every `VTechClient` method (see API surface
below) is directly callable on the instance:

```python
import asyncio
from helpdesk_vtech_sdk import VirtualTechnician

sdk = VirtualTechnician(base_url="http://localhost:8001", username="tech.virtual", password="VTech@12345")

@sdk.on_ticket_assigned
async def handle_assignment(event):
    ticket_id = event["data"]["ticket_id"]
    await sdk.acquire_lock(ticket_id)
    await sdk.send_message(ticket_id, "On it!")
    await sdk.resolve(ticket_id, "Fixed - reseated RAM.")
    await sdk.release_lock(ticket_id)

@sdk.on_new_message
async def handle_message(event):
    print("new message on ticket", event["data"]["ticket_id"])

# Generic callback keyed by any WS event kind / notification type
@sdk.on("sla_alert")
async def handle_sla_alert(event):
    print("SLA at risk:", event["data"])

async def main():
    async with sdk:
        await sdk.run()  # blocks: heartbeat loop + WS listener; call sdk.stop() to exit

asyncio.run(main())
```

## Usage: low-level `VTechClient` (no callbacks/heartbeat)

```python
import asyncio
from helpdesk_vtech_sdk import VTechClient, WSListener

async def main():
    async with VTechClient(base_url="http://localhost:8001", username="tech.virtual", password="VTech@12345") as client:
        tickets = await client.get_queue()
        for ticket in tickets:
            print(ticket.id, ticket.subject, ticket.status)

        if tickets:
            ticket_id = tickets[0].id
            await client.acquire_lock(ticket_id)
            await client.send_message(ticket_id, "Working on it...")
            await client.resolve(ticket_id, "Fixed - reseated RAM.")
            await client.release_lock(ticket_id)

        listener = WSListener(client.base_url, access_token_provider=lambda: client.access_token)

        async def on_event(event: dict):
            print("event:", event)

        await listener.listen(on_event)  # runs until listener.stop() is called

asyncio.run(main())
```

## API surface

| Method | Endpoint |
|---|---|
| `heartbeat()` | `POST /api/users/me/heartbeat` |
| `get_queue()` | `GET /api/vtech/queue` |
| `get_ticket(id)` | `GET /api/vtech/tickets/{id}` |
| `list_messages(id)` | `GET /api/vtech/tickets/{id}/messages` |
| `send_message(id, content, ...)` | `POST /api/vtech/tickets/{id}/messages` |
| `edit_message(id, message_id, content)` | `PATCH /api/vtech/tickets/{id}/messages/{message_id}` |
| `delete_message(id, message_id)` | `DELETE /api/vtech/tickets/{id}/messages/{message_id}` |
| `upload_attachment(id, file_path)` | `POST /api/vtech/tickets/{id}/messages/upload` |
| `resolve(id, resolution_note)` | `POST /api/vtech/tickets/{id}/resolve` |
| `reject(id, rejection_reason)` | `POST /api/vtech/tickets/{id}/reject` |
| `escalate(id, reason, ...)` | `POST /api/vtech/tickets/{id}/escalate` |
| `reassign_request(id, reason, target_id)` | `POST /api/vtech/tickets/{id}/reassign-request` |
| `acquire_lock(id)` / `refresh_lock(id)` / `release_lock(id)` | `/api/vtech/tickets/{id}/lock` |

`VirtualTechnician` additionally exposes `on(event_kind)`, `on_ticket_assigned`,
`on_new_message`, `on_sla_alert`, `on_escalation_update`, `run()`, and `stop()`.

## Exceptions

- `AuthenticationError` — login or refresh failed
- `ApiError(status_code, detail)` — any non-2xx response from the API
- `WebSocketError` — WS listener misconfigured or unrecoverable

## License

MIT
