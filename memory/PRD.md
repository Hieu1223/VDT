# Helpdesk / ITSM System — v2 — PRD

## Original problem statement
Full-stack, event-driven helpdesk/ITSM platform. Roles: Employee, Technician
(Human/Virtual), Admin. Ticket lifecycle with priority matrix + SLA, TTL-based
locking, tag management. Assignment via pluggable algorithm registry.
Escalation/reassignment request-review flows. Per-ticket chat with file
uploads. Real-time WebSocket notifications backed by a RabbitMQ topic
exchange. SLA near-breach/breach tracking (technician/admin only). CSAT
surveys post-resolution. Admin suite: Kanban, Timeline/event log, User &
Ticket monitor, Queue vs All Tickets, assignment config. Pip-installable
`helpdesk-vtech-sdk` for external Virtual Technician agents (SDK only, no
agent logic). Stack requested: React+TS, plain CSS (no framework), FastAPI,
DuckDB, JWT+bcrypt, native WebSockets, RabbitMQ/aio-pika, local disk uploads,
asyncio background jobs, Docker Compose (RabbitMQ only).

## User-approved deviations (via ask_human at kickoff)
1. **Database: MongoDB instead of DuckDB** — this sandbox is natively wired
   for MongoDB (async `motor`, hot reload); user approved the switch.
2. **RabbitMQ**: no Docker daemon available in this sandbox → installed
   `rabbitmq-server` natively via apt, supervised by supervisor. A
   `docker-compose.yml` is still provided for the user's own local/prod use.
3. **Frontend**: React + TypeScript, hand-written CSS only (reset.css +
   CSS variables + per-component .css files), no Tailwind/shadcn — confirmed.
4. **Phasing**: Phases 1–7 (full core app) delivered first; Phase 8 (SDK) and
   Phase 9 (final polish) folded into the same first pass given time.
5. Seed credentials auto-generated, documented in `/app/memory/test_credentials.md`.

## Architecture
- **Backend** (`/app/backend`): modular FastAPI app under `gateway/` (main,
  deps, middleware, router registry, seed) + `common/` (config, enums,
  errors, security/JWT, RabbitMQ event bus, WS connection manager) +
  `persistence/db.py` (Mongo, UUID-string `_id`s to avoid ObjectId
  serialization entirely) + `modules/{auth,users,tickets,assignment,sla,
  escalation,locks,messages,tags,csat,filters,kanban,timeline,monitor,
  notifications,jobs,vtech}`. Entry point `server.py` re-exports
  `gateway.main:app` so supervisor's `uvicorn server:app` keeps working.
- **Event bus**: `RabbitEventBus` (aio-pika) declares `helpdesk.events`
  topic exchange + 5 queues (`notification`, `sla`, `assignment`,
  `escalation`, `vtech`) at startup. `common/events.py::emit_event()` is the
  single call site used by every module — persists to Mongo `events`
  collection (Timeline/Monitor) AND publishes to RabbitMQ.
- **Frontend** (`/app/frontend`): CRA + TypeScript (tsconfig.json added,
  `react-app-env.d.ts`, `global.d.ts` for CSS module declarations), plain
  CSS with design tokens in `styles/variables.css`, AuthContext +
  NotificationContext (WebSocket), role-gated routing via `ProtectedRoute`,
  `AppShell` sidebar/topbar layout.
- **SDK** (`/app/helpdesk-vtech-sdk`): pip-installable, `VTechClient`
  (httpx, auto 401-retry), `WSListener` (websockets), Pydantic models,
  custom exceptions. Installed with `pip install -e .` and smoke-tested.

## What's been implemented (as of Feb 2026, initial build)
- Auth: register (pending_activation) → admin activate/suspend/deactivate →
  JWT login/refresh/logout/me. Roles: employee, technician_human,
  technician_virtual, admin.
- Tickets: create (impact×urgency → priority → SLA due dates), list mine,
  queue (technician actionable), all (admin browse+filters), resolve,
  reject, get-by-id (SLA block hidden from employees).
- Auto-assignment: round_robin / least_busy pluggable registry, admin
  config endpoint, triggered via `assignment.queue` consumer on
  `ticket.TICKET_CREATED`.
- Locking: acquire/refresh/release/force-release, TTL 180s, background
  janitor loop every 30s.
- Messaging: send/edit/delete, reply-preview, file upload to
  `uploads/rooms/{ticket_id}/`, served via `/uploads` StaticFiles mount.
- Tags: master list CRUD (admin) + attach/detach on tickets.
- Escalation/Reassignment: request → admin approve (assign target)/reject/
  return-to-requester.
- Notifications: WebSocket push (`/api/ws?token=`) + persisted list +
  read/read-all, bell UI with live badge + shake animation.
- SLA: background checker every 30s, near-breach (80%) + breach events for
  first-response and resolve, admin-tunable policies.
- CSAT: auto-created on resolve, employee submits 1-5 rating + comment.
- Admin suite: Kanban (7 status columns), Timeline (event log), All Tickets
  (filterable table), Users (create/activate/suspend/deactivate), Tags,
  Monitor (live stats + pending escalation/reassignment review + user
  monitor), Config (algorithm switch + SLA policy editor).
- Frontend pages: all 17 routes from the spec, role-gated.
- Virtual Technician SDK: full package, installed, smoke-tested against
  the live backend (login + get_queue).

## Seed data
Admin, human technician, virtual technician, demo employee — see
`/app/memory/test_credentials.md`. Priority matrix (9 impact×urgency
combos) + SLA policies (P1-P4) seeded idempotently on every backend boot.

## Known deferred / P1-P2 backlog
- Attachment previews (images) in chat — currently link-only.
- Pagination on ticket lists / timeline (currently capped, e.g. limit=200).
- Least-busy algorithm doesn't consider technician role split (human vs
  virtual) — treats both pools together.
- No email/SMS (by design, WebSocket-only per spec).
- SDK published to a package index — currently local/editable install only.

## Next action items
- Run full end-to-end testing pass (backend + frontend + WS + RabbitMQ
  consumers) via testing subagent, fix any reported issues.
- Consider adding image thumbnail previews in ChatRoom for uploaded images.
- Consider pagination/infinite-scroll for AllTicketsPage and TimelinePage
  once ticket volume grows.
