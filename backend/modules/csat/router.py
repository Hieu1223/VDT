from fastapi import APIRouter, Depends, Query

from common.enums import UserRole
from gateway.deps import get_bus, get_current_user, require_roles
from modules.csat import service
from modules.csat.schemas import SubmitCsatRequest

router = APIRouter(prefix="/csat", tags=["csat"])


@router.get("", dependencies=[Depends(require_roles(UserRole.ADMIN.value))])
async def list_all(
    status: str | None = Query(default=None),
    rating_min: int | None = Query(default=None),
    rating_max: int | None = Query(default=None),
    technician_id: str | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
):
    return await service.list_all_surveys(
        status=status, rating_min=rating_min, rating_max=rating_max,
        technician_id=technician_id, date_from=date_from, date_to=date_to,
    )


@router.get("/{ticket_id}")
async def get_survey(ticket_id: str, user: dict = Depends(get_current_user)):
    return await service.get_survey(ticket_id)


@router.post("/{ticket_id}")
async def submit(ticket_id: str, payload: SubmitCsatRequest, user: dict = Depends(get_current_user), bus=Depends(get_bus)):
    return await service.submit_csat(bus, user, ticket_id, payload.rating, payload.comment)
