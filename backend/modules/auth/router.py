from fastapi import APIRouter, Depends

from gateway.deps import get_bus, get_current_user
from modules.auth import service
from modules.auth.schemas import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic)
async def register(payload: RegisterRequest, bus=Depends(get_bus)):
    return await service.register_user(bus, payload)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, bus=Depends(get_bus)):
    user = await service.authenticate_user(bus, payload.username, payload.password)
    return service.issue_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest):
    return await service.refresh_access_token(payload.refresh_token)


@router.post("/logout")
async def logout(bus=Depends(get_bus), user: dict = Depends(get_current_user)):
    await service.logout_user(bus, user)
    return {"detail": "logged out"}


@router.get("/me", response_model=UserPublic)
async def me(user: dict = Depends(get_current_user)):
    return user
