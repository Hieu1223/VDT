from fastapi import APIRouter, Depends
from pydantic import BaseModel

from common.enums import UserRole
from gateway.deps import require_roles
from modules.assignment import service

router = APIRouter(prefix="/assignment", tags=["assignment"])


class SetAlgorithmRequest(BaseModel):
    algorithm: str


@router.get("/config", dependencies=[Depends(require_roles(UserRole.ADMIN.value))])
async def get_config():
    config = await service.get_config()
    return {"active_algorithm": config["active_algorithm"], "available_algorithms": await service.list_algorithms()}


@router.put("/config", dependencies=[Depends(require_roles(UserRole.ADMIN.value))])
async def set_config(payload: SetAlgorithmRequest):
    config = await service.set_active_algorithm(payload.algorithm)
    return {"active_algorithm": config["active_algorithm"], "available_algorithms": await service.list_algorithms()}
