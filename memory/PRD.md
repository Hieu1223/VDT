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
- Native `<input type="date">` pickers used for date-range filters across
  Admin Users/All Tickets/CSAT — could be swapped for a custom calendar
  component for visual consistency (cosmetic, flagged by testing agent).
- Pagination is implemented as in-memory slicing after full query
  materialization (not DB-level skip/limit) — fine at current volumes,
  will need a real DB-level cursor/skip-limit rewrite at scale.
- Least-busy algorithm doesn't consider technician role split (human vs
  virtual) — treats both pools together.
- No email/SMS (by design, WebSocket-only per spec).
- SDK published to a package index — currently local/editable install only.
- Per-technician/per-team business calendars (user explicitly said one
  global calendar is sufficient for now).

## Session 2 (Feb 2026) — Two large feature batches implemented
**Environment note**: RabbitMQ was found completely missing from the
container at the start of this session (fresh pod reset wiped the
`rabbitmq-server` apt package + system user). Reinstalled via apt, recreated
the `helpdesk`/`helpdesk` vhost user with admin permissions, verified
event-bus reconnect. If this recurs, check `rabbitmqctl -n rabbit@localhost
list_users` and re-run `add_user`/`set_permissions` as in this session.

### Batch 1 — presence, business calendar, admin config, lists/CSAT/timeline v1
- Frontend automatic heartbeat (`AuthContext`, every 20s) replaces the old
  manual "Available online" checkbox entirely (removed from
  `AccountSettingsPage` + backend schema) — presence is 100% automatic via
  `common/presence.py` (TTL 45s) + WS connect touch.
- New `/api/calendar` module (admin-only GET/PUT) + Config page UI: global
  business days/hours + holiday list, feeds `business_calendar.py` SLA math.
- New editable Impact×Urgency priority matrix on the Config page
  (`PATCH /api/tickets/config/priority-matrix/{impact}/{urgency}`).
- Ticket list filters: tag, date range, SLA%% slider (Admin All Tickets,
  Technician Queue, Employee My Tickets to varying degrees).
- CSV export (client-side, filter-aware) on All Tickets / Users / CSAT.
- Admin CSAT page v1, Admin Users filters + modal-based Create User,
  Monitor page SLA-compliance/avg-CSAT stat cards, sidebar item counts +
  header route name.
- Virtual Technician SDK v0.2.0 rewrite: new `VirtualTechnician` class
  (`helpdesk_vtech_sdk/agent.py`) — `async with sdk:` context manager,
  `@sdk.on_ticket_assigned`/`sdk.on(kind)` callbacks, automatic 20s
  heartbeat, `edit_message`/`delete_message` parity added to
  `/api/vtech/*`. Smoke-tested live against the backend (context manager,
  heartbeat, queue, run() loop, send/edit/delete message all confirmed).

### Batch 2 — Gantt timeline, dual-range slider, pagination, messenger-style chat, offline reassignment
- **Timeline rebuilt as a TeamUp-style Gantt view**
  (`pages/admin/TimelineCalendar.tsx`): rows = technicians + an
  "Unassigned queue" row, ticket bars span created_at→resolved_at/now,
  week nav (prev/today/next), horizontal zoom (day column width 90-300px),
  clickable legend rows to hide/show a technician's bars, status/priority
  filters, click a bar to open the ticket. Old flat table + raw event log
  kept as a toggleable "Raw Event Log" mode.
- New reusable dual-thumb `RangeSlider` (`components/common/RangeSlider.tsx`,
  Radix UI primitive + plain CSS) — used for CSAT rating range and SLA%%
  filters (replacing two separate native sliders).
- Admin ticket creation simplified: removed the on-behalf-of/requester
  dropdown entirely — admin always creates tickets as themselves.
- Pagination added to Admin All Tickets / Users / CSAT
  (`{items, total, page, page_size}` response shape + shared
  `components/common/Pagination.tsx`).
- Unassigned-queue visibility: `assignee_id=unassigned` filter value on
  `/api/tickets/all`, selectable in the Admin All Tickets handler dropdown.
- New Employee "My CSAT" page (`/csat`) — `GET /api/csat` now also allows
  the employee role, auto-scoped server-side to their own `requester_id`.
- **Bug fix**: sending a chat message with an attachment but no text threw
  a 422 (Pydantic `min_length=1` on content) surfaced as a runtime error in
  the browser — fixed with a `model_validator` requiring text OR at least
  one attachment.
- **Messenger-style file sharing**: picking a file now immediately uploads
  and sends it as its own message (no attach-then-caption-then-send step).
  `MessageBubble` renders images as inline `<img>`, videos as inline
  `<video controls>`, everything else as a downloadable file chip.
- **Offline auto-reassignment**: new `reassignment_loop` background job
  (every 20s) — `get_available_technicians()` now only considers
  currently-online technicians (no more offline fallback);
  `reassign_offline_tickets()` reassigns tickets whose assignee went
  offline to another online technician, or unassigns them (back to the
  unassigned queue) if none are online. Verified live end-to-end by main
  agent via curl (logged in tech.human → auto-assigned → let heartbeat
  TTL expire → confirmed sweep unassigned the ticket, log-verified).

### Testing status
- `testing_agent_v4` run 1 (Batch 1): ended mid-session, no final report
  captured for this specific run (context reset) — Batch 1 items were
  re-covered by Batch 2's regression pass.
- `testing_agent_v4` run 2 (Batch 2 + Batch 1 regression):
  **38/38 backend pytest passing** (`test_helpdesk_v2_batch2.py` new,
  `test_helpdesk_e2e.py` fixed), **100% of tested frontend flows passing**.
  Only note: offline-reassignment was code-reviewed but not live E2E
  tested by the testing agent (time constraints) — closed by main agent
  via a direct curl-based live test after the report (see above).
- Minor cosmetic-only finding: native date pickers instead of a custom
  calendar component (not blocking, left as backlog item above).

## Next action items
- Ask user if virtual technician "full capability parity" needs anything
  beyond current edit/delete message + resolve/reject/escalate/lock set.

## Session 2 continued — DB-level pagination
Converted the in-memory-slice pagination (from Batch 2) to true MongoDB
`skip()`/`limit()` + `count_documents()`:
- `list_users`: `online` filter (in-memory presence set) is now folded
  directly into the Mongo query as `{"id": {"$in"/"$nin": [...]}}` so
  skip/limit still runs at the DB level.
- `list_all_surveys` (CSAT): every filter (status/technician/requester/
  rating range/date range) is already a stored field - fully DB-level now,
  including the per-page ticket-subject enrichment lookup (only runs on
  the current page's rows, not the whole result set).
- `list_all_tickets`: hybrid - all filters except `sla_min_pct` run at the
  DB level with skip/limit; `sla_min_pct` is a derived/business-calendar
  computed value with no stored field, so when it's active the (already
  DB-narrowed-by-other-filters) match set is materialized and
  filtered/paginated in Python as a fallback. This is the correct
  tradeoff - avoids full-collection scans in the common case, only pays
  the in-memory cost when the advanced SLA%% filter is actually used.
- Added supporting indexes (`persistence/db.py::create_indexes`):
  `users.status`, `users.created_at`, `tickets.priority`, `tickets.tags`,
  `tickets.created_at`, `csat_surveys.requester_id/technician_id/status/created_at`.
- Verified via curl: ticket/user/CSAT pagination all return distinct pages
  with correct totals; `online=true/false` filter now DB-level; `sla_min_pct`
  fallback path still correct.
