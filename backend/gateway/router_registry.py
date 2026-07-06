from fastapi import APIRouter

from modules.assignment.router import router as assignment_router
from modules.auth.router import router as auth_router
from modules.calendar.router import router as calendar_router
from modules.csat.router import router as csat_router
from modules.escalation.router import router as escalation_router
from modules.filters.router import router as filters_router
from modules.kanban.router import router as kanban_router
from modules.locks.router import router as locks_router
from modules.messages.router import router as messages_router
from modules.monitor.router import router as monitor_router
from modules.notifications.router import router as notifications_router
from modules.tags.router import router as tags_router
from modules.tickets.router import router as tickets_router
from modules.timeline.router import router as timeline_router
from modules.users.router import router as users_router
from modules.vtech.router import router as vtech_router

api_router = APIRouter(prefix="/api")

for r in (
    auth_router,
    users_router,
    tickets_router,
    locks_router,
    messages_router,
    tags_router,
    escalation_router,
    assignment_router,
    notifications_router,
    csat_router,
    filters_router,
    kanban_router,
    timeline_router,
    monitor_router,
    vtech_router,
):
    api_router.include_router(r)
