from fastapi import APIRouter, Depends, Query

from common.enums import UserRole
from gateway.deps import get_bus, get_current_user, require_roles
from modules.csat.service import create_survey_for_ticket
from modules.tickets import service
from modules.tickets.schemas import CreateTicketRequest, RejectTicketRequest, ResolveTicketRequest, UpdateSlaPolicyRequest
from persistence.db import db

router = APIRouter(prefix="/tickets", tags=["tickets"])

TECHNICIAN_OR_ADMIN = [UserRole.TECHNICIAN_HUMAN.value, UserRole.TECHNICIAN_VIRTUAL.value, UserRole.ADMIN.value]


@router.get("/config/priority-matrix")
async def priority_matrix(user: dict = Depends(get_current_user)):
    cursor = db.priority_matrix.find({})
    rows = [{"impact": r["impact"], "urgency": r["urgency"], "priority": r["priority"]} async for r in cursor]
    return rows


@router.get("/config/sla-policies")
async def sla_policies(user: dict = Depends(get_current_user)):
    cursor = db.sla_policies.find({})
    return [{"priority": r["priority"], "first_response_minutes": r["first_response_minutes"], "resolve_minutes": r["resolve_minutes"]} async for r in cursor]


@router.patch("/config/sla-policies/{priority}", dependencies=[Depends(require_roles(UserRole.ADMIN.value))])
async def update_sla_policy(priority: str, payload: UpdateSlaPolicyRequest):
    await db.sla_policies.update_one({"id": priority}, {"$set": payload.model_dump()})
    return await db.sla_policies.find_one({"id": priority}, {"_id": 0})


@router.post("", dependencies=[Depends(require_roles(UserRole.EMPLOYEE.value))])
async def create_ticket(payload: CreateTicketRequest, requester: dict = Depends(get_current_user), bus=Depends(get_bus)):
    return await service.create_ticket(bus, requester, payload)


@router.get("")
async def my_tickets(user: dict = Depends(get_current_user)):
    return await service.list_my_tickets(user)


@router.get("/queue", dependencies=[Depends(require_roles(*TECHNICIAN_OR_ADMIN))])
async def queue(technician: dict = Depends(get_current_user)):
    return await service.list_queue(technician)


@router.get("/all", dependencies=[Depends(require_roles(UserRole.ADMIN.value))])
async def all_tickets(status: str | None = Query(default=None), priority: str | None = Query(default=None), assignee_id: str | None = Query(default=None), search: str | None = Query(default=None)):
    return await service.list_all_tickets(status=status, priority=priority, assignee_id=assignee_id, search=search)


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
