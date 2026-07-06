# helpdesk-vtech-sdk

Async Python SDK for building **Virtual Technician** agents that connect to
the Helpdesk / ITSM platform. Wraps every `/api/vtech/*` endpoint with an
async `httpx` client, handles JWT login/refresh/retry automatically, and
provides a WebSocket listener for real-time events.

This package contains **no agent logic** — it is purely a client library.
Bring your own automation/AI logic and call these methods from it.

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

## Usage

```python
import asyncio
from helpdesk_vtech_sdk import VTechClient, WSListener

async def main():
    async with VTechClient(base_url="http://localhost:8001", username="tech.virtual", password="VTech@12345") as client:
        # Pull actionable tickets
        tickets = await client.get_queue()
        for ticket in tickets:
            print(ticket.id, ticket.subject, ticket.status)

        if tickets:
            ticket_id = tickets[0].id
            await client.acquire_lock(ticket_id)
            await client.send_message(ticket_id, "Working on it...")
            await client.resolve(ticket_id, "Fixed - reseated RAM.")
            await client.release_lock(ticket_id)

        # Listen for real-time events (new messages, assignments, SLA alerts...)
        listener = WSListener(client.base_url, access_token_provider=lambda: client.access_token)

        async def on_event(event: dict):
            print("event:", event)

        await listener.listen(on_event)  # runs until listener.stop() is called

asyncio.run(main())
```

## API surface

| Method | Endpoint |
|---|---|
| `get_queue()` | `GET /api/vtech/queue` |
| `get_ticket(id)` | `GET /api/vtech/tickets/{id}` |
| `list_messages(id)` | `GET /api/vtech/tickets/{id}/messages` |
| `send_message(id, content, ...)` | `POST /api/vtech/tickets/{id}/messages` |
| `upload_attachment(id, file_path)` | `POST /api/vtech/tickets/{id}/messages/upload` |
| `resolve(id, resolution_note)` | `POST /api/vtech/tickets/{id}/resolve` |
| `reject(id, rejection_reason)` | `POST /api/vtech/tickets/{id}/reject` |
| `escalate(id, reason, ...)` | `POST /api/vtech/tickets/{id}/escalate` |
| `reassign_request(id, reason, target_id)` | `POST /api/vtech/tickets/{id}/reassign-request` |
| `acquire_lock(id)` / `refresh_lock(id)` / `release_lock(id)` | `/api/vtech/tickets/{id}/lock` |

## Exceptions

- `AuthenticationError` — login or refresh failed
- `ApiError(status_code, detail)` — any non-2xx response from the API
- `WebSocketError` — WS listener misconfigured or unrecoverable

## License

MIT
