from fastapi import APIRouter, Depends

from common.enums import UserRole
from gateway.deps import get_bus, get_current_user, require_roles
from modules.escalation import service
from modules.escalation.schemas import CreateEscalationRequest, CreateReassignmentRequest, ReviewRequestPayload

router = APIRouter(tags=["escalation"])

TECHNICIAN_OR_ADMIN = [UserRole.TECHNICIAN_HUMAN.value, UserRole.TECHNICIAN_VIRTUAL.value, UserRole.ADMIN.value]


@router.post("/tickets/{ticket_id}/escalate", dependencies=[Depends(require_roles(*TECHNICIAN_OR_ADMIN))])
async def escalate(ticket_id: str, payload: CreateEscalationRequest, technician: dict = Depends(get_current_user), bus=Depends(get_bus)):
    return await service.create_escalation(bus, technician, ticket_id, payload.reason, payload.suggested_target_id)


@router.post("/tickets/{ticket_id}/reassign-request", dependencies=[Depends(require_roles(*TECHNICIAN_OR_ADMIN))])
async def reassign_request(ticket_id: str, payload: CreateReassignmentRequest, technician: dict = Depends(get_current_user), bus=Depends(get_bus)):
    return await service.create_reassignment(bus, technician, ticket_id, payload.reason, payload.target_technician_id)


@router.get("/requests/mine", dependencies=[Depends(require_roles(*TECHNICIAN_OR_ADMIN))])
async def my_requests(technician: dict = Depends(get_current_user)):
    return await service.list_my_requests(technician)


@router.get("/requests/pending", dependencies=[Depends(require_roles(UserRole.ADMIN.value))])
async def pending_requests():
    return await service.list_pending_requests()


@router.post("/requests/{request_id}/approve", dependencies=[Depends(require_roles(UserRole.ADMIN.value))])
async def approve(request_id: str, payload: ReviewRequestPayload, admin: dict = Depends(get_current_user), bus=Depends(get_bus)):
    return await service.approve_request(bus, admin, request_id, payload.target_technician_id, payload.note)


@router.post("/requests/{request_id}/reject", dependencies=[Depends(require_roles(UserRole.ADMIN.value))])
async def reject(request_id: str, payload: ReviewRequestPayload, admin: dict = Depends(get_current_user), bus=Depends(get_bus)):
    return await service.reject_request(bus, admin, request_id, payload.note)


@router.post("/requests/{request_id}/return", dependencies=[Depends(require_roles(UserRole.ADMIN.value))])
async def return_to_requester(request_id: str, payload: ReviewRequestPayload, admin: dict = Depends(get_current_user), bus=Depends(get_bus)):
    return await service.return_request(bus, admin, request_id, payload.note)
