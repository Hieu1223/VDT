"""Dedicated namespace for the Virtual Technician SDK (helpdesk-vtech-sdk).
Thin wrappers around the same service-layer functions used by the human
Technician web UI, scoped to the `technician_virtual` role so external bot
processes have a stable, documented surface to bind against.
"""
from fastapi import APIRouter, Depends, File, UploadFile

from common.enums import UserRole
from gateway.deps import get_bus, get_current_user, require_roles
from modules.escalation.schemas import CreateEscalationRequest, CreateReassignmentRequest
from modules.escalation import service as escalation_service
from modules.locks import service as lock_service
from modules.messages.schemas import SendMessageRequest
from modules.messages import service as message_service
from modules.tickets.schemas import RejectTicketRequest, ResolveTicketRequest
from modules.tickets import service as ticket_service

router = APIRouter(prefix="/vtech", tags=["vtech-sdk"], dependencies=[Depends(require_roles(UserRole.TECHNICIAN_VIRTUAL.value, UserRole.ADMIN.value))])


@router.get("/queue")
async def queue(vtech: dict = Depends(get_current_user)):
    return await ticket_service.list_queue(vtech)


@router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str, vtech: dict = Depends(get_current_user)):
    return await ticket_service.get_ticket_for_viewer(vtech, ticket_id)


@router.get("/tickets/{ticket_id}/messages")
async def list_messages(ticket_id: str, vtech: dict = Depends(get_current_user)):
    return await message_service.list_messages(vtech, ticket_id)


@router.post("/tickets/{ticket_id}/messages")
async def send_message(ticket_id: str, payload: SendMessageRequest, vtech: dict = Depends(get_current_user), bus=Depends(get_bus)):
    return await message_service.send_message(bus, vtech, ticket_id, payload)


@router.post("/tickets/{ticket_id}/messages/upload")
async def upload_attachment(ticket_id: str, file: UploadFile = File(...), vtech: dict = Depends(get_current_user)):
    return await message_service.save_upload(ticket_id, file)


@router.post("/tickets/{ticket_id}/resolve")
async def resolve(ticket_id: str, payload: ResolveTicketRequest, vtech: dict = Depends(get_current_user), bus=Depends(get_bus)):
    return await ticket_service.resolve_ticket(bus, vtech, ticket_id, payload.resolution_note)


@router.post("/tickets/{ticket_id}/reject")
async def reject(ticket_id: str, payload: RejectTicketRequest, vtech: dict = Depends(get_current_user), bus=Depends(get_bus)):
    return await ticket_service.reject_ticket(bus, vtech, ticket_id, payload.rejection_reason)


@router.post("/tickets/{ticket_id}/escalate")
async def escalate(ticket_id: str, payload: CreateEscalationRequest, vtech: dict = Depends(get_current_user), bus=Depends(get_bus)):
    return await escalation_service.create_escalation(bus, vtech, ticket_id, payload.reason, payload.suggested_target_id)


@router.post("/tickets/{ticket_id}/reassign-request")
async def reassign_request(ticket_id: str, payload: CreateReassignmentRequest, vtech: dict = Depends(get_current_user), bus=Depends(get_bus)):
    return await escalation_service.create_reassignment(bus, vtech, ticket_id, payload.reason, payload.target_technician_id)


@router.post("/tickets/{ticket_id}/lock")
async def acquire_lock(ticket_id: str, vtech: dict = Depends(get_current_user), bus=Depends(get_bus)):
    return await lock_service.acquire_lock(bus, ticket_id, vtech)


@router.post("/tickets/{ticket_id}/lock/refresh")
async def refresh_lock(ticket_id: str, vtech: dict = Depends(get_current_user), bus=Depends(get_bus)):
    return await lock_service.refresh_lock(bus, ticket_id, vtech)


@router.delete("/tickets/{ticket_id}/lock")
async def release_lock(ticket_id: str, vtech: dict = Depends(get_current_user), bus=Depends(get_bus)):
    return await lock_service.release_lock(bus, ticket_id, vtech, force=False)
