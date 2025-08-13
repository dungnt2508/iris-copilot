"""
Application Layer - Login Use Case
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from app.domain.user.repository import UserRepository
from app.domain.user.entities.user import User, UserStatus
from app.domain.user.value_objects.email import Email


@dataclass
class LoginRequest:
    email: str
    password: str
    remember_me: bool = False


@dataclass
class LoginResponse:
    user: User
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: datetime | None = None


class LoginError(Exception):
    pass


class InvalidCredentialsError(LoginError):
    pass


class AccountNotActiveError(LoginError):
    pass


class LoginUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        password_service: "PasswordService",
        token_service: "TokenService",
        login_attempts_service: Optional["LoginAttemptsService"] = None,
    ):
        self.user_repo = user_repository
        self.password_service = password_service
        self.token_service = token_service
        self.login_attempts_service = login_attempts_service

    async def execute(self, request: LoginRequest) -> LoginResponse:
        try:
            email = Email(request.email)
        except ValueError as e:
            raise InvalidCredentialsError(f"Invalid email format: {str(e)}")

        if self.login_attempts_service:
            is_blocked = await self.login_attempts_service.is_blocked(email.value)
            if is_blocked:
                raise LoginError("Too many failed login attempts. Please try again later.")

        user = await self.user_repo.find_by_email(email)
        if not user:
            if self.login_attempts_service:
                await self.login_attempts_service.record_failed_attempt(email.value)
            raise InvalidCredentialsError("Invalid email or password")

        is_valid = await self.password_service.verify(
            plain_password=request.password, hashed_password=user.hashed_password
        )
        if not is_valid:
            if self.login_attempts_service:
                await self.login_attempts_service.record_failed_attempt(email.value)
            raise InvalidCredentialsError("Invalid email or password")

        if user.status == UserStatus.SUSPENDED:
            raise AccountNotActiveError("Your account has been suspended. Please contact support.")
        if user.status == UserStatus.INACTIVE:
            raise AccountNotActiveError("Your account is inactive. Please contact support.")
        if user.status == UserStatus.PENDING:
            if user.email_verified:
                user.activate()
            else:
                raise AccountNotActiveError("Please verify your email address before logging in.")

        token_data = await self.token_service.generate_tokens(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
            permissions=user.permissions,
            remember_me=request.remember_me,
        )

        user.update_last_login()
        await self.user_repo.save(user)

        if self.login_attempts_service:
            await self.login_attempts_service.clear_attempts(email.value)

        return LoginResponse(
            user=user,
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token") if request.remember_me else None,
            expires_at=token_data["expires_at"],
        )

    async def validate_token(self, token: str) -> Optional[User]:
        token_data = await self.token_service.verify_token(token)
        if not token_data:
            return None
        user = await self.user_repo.find_by_id(token_data["user_id"])
        if not user or user.status != UserStatus.ACTIVE:
            return None
        return user

    async def refresh_token(self, refresh_token: str) -> LoginResponse:
        token_data = await self.token_service.verify_refresh_token(refresh_token)
        if not token_data:
            raise LoginError("Invalid refresh token")

        user = await self.user_repo.find_by_id(token_data["user_id"])
        if not user or user.status != UserStatus.ACTIVE:
            raise LoginError("User not found or inactive")

        new_token_data = await self.token_service.generate_tokens(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
            permissions=user.permissions,
            remember_me=True,
        )

        return LoginResponse(
            user=user,
            access_token=new_token_data["access_token"],
            refresh_token=new_token_data["refresh_token"],
            expires_at=new_token_data["expires_at"],
        )


