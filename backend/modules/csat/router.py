from fastapi import APIRouter, Depends, Query

from common.enums import UserRole
from common.errors import ForbiddenError
from gateway.deps import get_bus, get_current_user
from modules.csat import service
from modules.csat.schemas import SubmitCsatRequest

router = APIRouter(prefix="/csat", tags=["csat"])


@router.get("")
async def list_all(
    user: dict = Depends(get_current_user),
    status: str | None = Query(default=None),
    rating_min: int | None = Query(default=None),
    rating_max: int | None = Query(default=None),
    technician_id: str | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
):
    # Employees may only ever see their own surveys (as the ticket requester).
    # Admins can see every survey and filter by technician.
    requester_id = user["id"] if user["role"] == UserRole.EMPLOYEE.value else None
    if user["role"] not in (UserRole.EMPLOYEE.value, UserRole.ADMIN.value):
        raise ForbiddenError("Only employees and admins can list CSAT surveys")
    return await service.list_all_surveys(
        status=status, rating_min=rating_min, rating_max=rating_max,
        technician_id=technician_id, requester_id=requester_id, date_from=date_from, date_to=date_to,
        page=page, page_size=page_size,
    )


@router.get("/{ticket_id}")
async def get_survey(ticket_id: str, user: dict = Depends(get_current_user)):
    return await service.get_survey(ticket_id)


@router.post("/{ticket_id}")
async def submit(ticket_id: str, payload: SubmitCsatRequest, user: dict = Depends(get_current_user), bus=Depends(get_bus)):
    return await service.submit_csat(bus, user, ticket_id, payload.rating, payload.comment)
