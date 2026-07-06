from fastapi import APIRouter, Depends, Query

from common.enums import UserRole
from common.errors import NotFoundError
from gateway.deps import get_bus, get_current_user, require_roles
from modules.csat.service import create_survey_for_ticket
from modules.tickets import service
from modules.tickets.schemas import (
    CreateTicketRequest, RejectTicketRequest, ResolveTicketRequest, UpdatePriorityMatrixRequest, UpdateSlaPolicyRequest,
)
from persistence.db import db

router = APIRouter(prefix="/tickets", tags=["tickets"])

TECHNICIAN_OR_ADMIN = [UserRole.TECHNICIAN_HUMAN.value, UserRole.TECHNICIAN_VIRTUAL.value, UserRole.ADMIN.value]


@router.get("/config/priority-matrix")
async def priority_matrix(user: dict = Depends(get_current_user)):
    cursor = db.priority_matrix.find({})
    rows = [{"impact": r["impact"], "urgency": r["urgency"], "priority": r["priority"]} async for r in cursor]
    return rows


@router.patch("/config/priority-matrix/{impact}/{urgency}", dependencies=[Depends(require_roles(UserRole.ADMIN.value))])
async def update_priority_matrix(impact: str, urgency: str, payload: UpdatePriorityMatrixRequest):
    doc_id = f"{impact}_{urgency}"
    await db.priority_matrix.update_one({"id": doc_id}, {"$set": {"priority": payload.priority}})
    row = await db.priority_matrix.find_one({"id": doc_id}, {"_id": 0})
    if not row:
        raise NotFoundError("Unknown impact/urgency combination")
    return row


@router.get("/config/sla-policies")
async def sla_policies(user: dict = Depends(get_current_user)):
    cursor = db.sla_policies.find({})
    return [{"priority": r["priority"], "first_response_minutes": r["first_response_minutes"], "resolve_minutes": r["resolve_minutes"]} async for r in cursor]


@router.patch("/config/sla-policies/{priority}", dependencies=[Depends(require_roles(UserRole.ADMIN.value))])
async def update_sla_policy(priority: str, payload: UpdateSlaPolicyRequest):
    await db.sla_policies.update_one({"id": priority}, {"$set": payload.model_dump()})
    return await db.sla_policies.find_one({"id": priority}, {"_id": 0})


@router.post("", dependencies=[Depends(require_roles(UserRole.EMPLOYEE.value, UserRole.ADMIN.value))])
async def create_ticket(payload: CreateTicketRequest, actor: dict = Depends(get_current_user), bus=Depends(get_bus)):
    return await service.create_ticket(bus, actor, payload)


@router.get("")
async def my_tickets(
    user: dict = Depends(get_current_user),
    tag: str | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
):
    return await service.list_my_tickets(user, tag=tag, date_from=date_from, date_to=date_to)


@router.get("/queue", dependencies=[Depends(require_roles(*TECHNICIAN_OR_ADMIN))])
async def queue(
    technician: dict = Depends(get_current_user),
    tag: str | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    sla_min_pct: float | None = Query(default=None),
):
    return await service.list_queue(technician, tag=tag, date_from=date_from, date_to=date_to, sla_min_pct=sla_min_pct)


@router.get("/all", dependencies=[Depends(require_roles(UserRole.ADMIN.value))])
async def all_tickets(
    status: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    assignee_id: str | None = Query(default=None),
    search: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    sla_min_pct: float | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500),
):
    return await service.list_all_tickets(
        status=status, priority=priority, assignee_id=assignee_id, search=search,
        tag=tag, date_from=date_from, date_to=date_to, sla_min_pct=sla_min_pct,
        page=page, page_size=page_size,
    )


@router.get("/{ticket_id}")
async def get_ticket(ticket_id: str, user: dict = Depends(get_current_user)):
    return await service.get_ticket_for_viewer(user, ticket_id)


@router.post("/{ticket_id}/resolve", dependencies=[Depends(require_roles(*TECHNICIAN_OR_ADMIN))])
async def resolve(ticket_id: str, payload: ResolveTicketRequest, technician: dict = Depends(get_current_user), bus=Depends(get_bus)):
    ticket = await service.resolve_ticket(bus, technician, ticket_id, payload.resolution_note)
    await create_survey_for_ticket(bus, ticket)
    return ticket


@router.post("/{ticket_id}/reject", dependencies=[Depends(require_roles(*TECHNICIAN_OR_ADMIN))])
async def reject(ticket_id: str, payload: RejectTicketRequest, technician: dict = Depends(get_current_user), bus=Depends(get_bus)):
    return await service.reject_ticket(bus, technician, ticket_id, payload.rejection_reason)
