# Helpdesk / ITSM System — v2

A full-stack, event-driven helpdesk and IT service management platform with
role-based access, real-time WebSocket notifications, SLA tracking, ticket
lifecycle management, and an admin monitoring suite.

## Stack

| Layer | Choice |
|---|---|
| Frontend | React + TypeScript, hand-written CSS (no Tailwind/Bootstrap) |
| Backend | FastAPI (Python, async) |
| Database | MongoDB (via `motor`) |
| Auth | JWT (PyJWT) + bcrypt |
| Real-time | Native FastAPI WebSockets |
| Event Bus | RabbitMQ topic exchange (`aio-pika`) |
| File storage | Local disk, per-ticket-room folders under `backend/uploads/rooms/{ticket_id}/` |
| Background jobs | asyncio tasks (SLA checker, lock janitor) |
| Virtual Technician SDK | `helpdesk-vtech-sdk` (pip-installable) |

> Note: the original design doc specified DuckDB; this environment is
> natively wired for MongoDB (async driver + hot reload), so MongoDB was
> used instead per an explicit product decision — the rest of the
> architecture (event bus, WS, locking, SLA) is unchanged.

## Local Setup

### 1. RabbitMQ

```bash
docker compose up -d   # starts RabbitMQ on 5672 (AMQP) / 15672 (management UI)
```

Default credentials: `helpdesk` / `helpdesk`. Management UI: http://localhost:15672

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # fill in MONGO_URL, JWT_SECRET, RABBITMQ_URL, seed credentials
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

The backend seeds an admin, human technician, virtual technician, and demo
employee account on first boot — see `backend/gateway/seed.py` and
`/app/memory/test_credentials.md`.

### 3. Frontend

```bash
cd frontend
yarn install
yarn start
```

Set `REACT_APP_BACKEND_URL` in `frontend/.env` to your backend's base URL
(e.g. `http://localhost:8001`).

### 4. Virtual Technician SDK

```bash
pip install -e ./helpdesk-vtech-sdk
```

See `helpdesk-vtech-sdk/README.md` for usage. The SDK wraps `/api/vtech/*`
and is a pure client library — bring your own agent/automation logic.

## Backend Folder Structure

```
backend/
├── gateway/          # FastAPI app, lifespan, router registry, deps
├── common/           # config, enums, errors, security, event bus, ws manager
├── persistence/      # Mongo connection helpers
├── modules/          # one folder per domain: auth, users, tickets, assignment,
│                      # sla, escalation, locks, messages, tags, csat, filters,
│                      # kanban, timeline, monitor, notifications, jobs, vtech
└── uploads/rooms/    # per-ticket file storage, served at /uploads
```

## RabbitMQ Architecture

Exchange `helpdesk.events` (topic). Routing key pattern `<domain>.<EVENT_TYPE>`.

Queues: `notification.queue` (→ WebSocket push, bound to `#`), `sla.queue`,
`assignment.queue` (auto-assignment on `ticket.TICKET_CREATED`),
`escalation.queue`, `vtech.queue` (bound to `#`, ready for external SDK
consumers to bind additional keys).

## Key Flows

- **Auth**: register → `pending_activation` → admin activates → login issues
  JWT access + refresh tokens (JSON body, used by both the web app and the SDK).
- **Tickets**: priority is derived from an impact × urgency matrix, which
  determines the SLA policy (first-response/resolve minutes). New tickets are
  auto-assigned via the pluggable algorithm registry (`round_robin` /
  `least_busy`, admin-configurable at `/admin/config`).
- **Locking**: technicians/admins soft-lock a ticket while its detail page is
  open (TTL 180s, refreshed every 90s, released on unmount). A background
  janitor releases expired locks; admins can force-release.
- **Escalation / Reassignment**: current assignee raises a request → admin
  approves (assigns to target technician) / rejects / returns.
- **SLA**: background asyncio job checks all open tickets every 30s and emits
  near-breach/breach events for first-response and resolve.
- **Notifications**: every domain event is persisted to `events` (Timeline/
  Monitor) and published to RabbitMQ; the `notification.queue` consumer
  fans out to the right users and pushes over WebSocket.

## Seed Credentials

See `/app/memory/test_credentials.md`.
