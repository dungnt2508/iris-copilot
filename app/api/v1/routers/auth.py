from fastapi import APIRouter, Depends, HTTPException, status
from app.api.v1.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    TokenResponse,
    MeResponse,
)
from app.api.v1.dependencies import (
    get_token_service,
    get_current_user,
    get_user_repository,
)
from app.services.password_service import PasswordService
from app.services.token_service import TokenService
from app.domain.user.repository import UserRepository
from app.application.user.use_cases.register import RegisterUseCase
from app.application.user.use_cases.login import LoginUseCase


router = APIRouter(tags=["Auth"])


@router.post("/register", response_model=RegisterResponse)
async def register_user(
    payload: RegisterRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    password_service: PasswordService = Depends(PasswordService),
):
    use_case = RegisterUseCase(
        user_repository=user_repo,
        password_service=password_service,
    )
    result = await use_case.execute(payload)
    return RegisterResponse(
        user_id=result.user.id,
        email=result.user.email,
        username=result.user.username,
        full_name=result.user.full_name,
        message=result.message,
    )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    payload: LoginRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    password_service: PasswordService = Depends(PasswordService),
    token_service: TokenService = Depends(get_token_service),
):
    use_case = LoginUseCase(
        user_repository=user_repo,
        password_service=password_service,
        token_service=token_service,
    )
    result = await use_case.execute(payload)
    return TokenResponse(
        access_token=result.access_token,
        expires_in=1800,  # TODO: align with settings.ACCESS_TOKEN_EXPIRE_MINUTES
        refresh_token=result.refresh_token,
    )


@router.get("/me", response_model=MeResponse)
async def get_me(
    user_repo: UserRepository = Depends(get_user_repository),
    token_service: TokenService = Depends(get_token_service),
    current_user=Depends(get_current_user),
):
    return MeResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        role=current_user.role.value,
        permissions=current_user.permissions,
        status=current_user.status.value,
    )


