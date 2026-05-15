from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, HTTPException, Request

from app.application.commands.auth.register import RegisterCommand, RegisterHandler
from app.application.commands.auth.login import LoginCommand, LoginHandler
from app.application.commands.auth.refresh_token import RefreshTokenCommand, RefreshTokenHandler
from app.application.commands.auth.logout import LogoutCommand, LogoutHandler
from app.domain.exceptions import AlreadyExistsError, ForbiddenError, TokenTheftError
from app.core.security import get_client_ip
from app.presentation.schemas.auth import (
    RegisterRequest, RegisterResponse,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
)


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=201)
@inject
async def register(
    body: RegisterRequest,
    handler: FromDishka[RegisterHandler],
):
    try:
        cmd = RegisterCommand(
            phone_number=body.phone_number,
            display_name=body.display_name,
            password=body.password,
        )
        user = await handler.handle(cmd)
        return RegisterResponse.from_domain(user)
    except AlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/login", response_model=TokenResponse)
@inject
async def login(
    body: LoginRequest,
    request: Request,
    handler: FromDishka[LoginHandler],
):
    try:
        cmd = LoginCommand(
            phone_number=body.phone_number,
            password=body.password,
            device_id=body.device_id,
            device_name=body.device_name,
            platform=body.platform,
            ip_address=get_client_ip(request),
        )
        tokens = await handler.handle(cmd)
        return TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
        )
    except ForbiddenError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
@inject
async def refresh(
    body: RefreshRequest,
    handler: FromDishka[RefreshTokenHandler],
):
    try:
        cmd = RefreshTokenCommand(
            refresh_token=body.refresh_token,
        )
        tokens = await handler.handle(cmd)
        return TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
        )
    except TokenTheftError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout", status_code=204)
@inject
async def logout(
    body: RefreshRequest,
    handler: FromDishka[LogoutHandler],
):
    cmd = LogoutCommand(
        refresh_token=body.refresh_token,
    )
    await handler.handle(cmd)