"""
Application Layer - Register Use Case
"""
from dataclasses import dataclass
from typing import Optional

from app.domain.user.repository import UserRepository
from app.domain.user.entities.user import User, UserRole
from app.domain.user.value_objects.email import Email
from app.domain.user.value_objects.password import Password


@dataclass
class RegisterRequest:
    email: str
    username: str
    full_name: str
    password: str
    password_confirm: str
    phone: Optional[str] = None
    department: Optional[str] = None


@dataclass
class RegisterResponse:
    user: User
    verification_token: Optional[str] = None
    message: str = "Registration successful"


class RegisterError(Exception):
    pass


class EmailAlreadyExistsError(RegisterError):
    pass


class UsernameAlreadyExistsError(RegisterError):
    pass


class PasswordMismatchError(RegisterError):
    pass


class RegisterUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        password_service: "PasswordService",
        email_service: Optional["EmailService"] = None,
        default_role: UserRole = UserRole.USER,
    ):
        self.user_repo = user_repository
        self.password_service = password_service
        self.email_service = email_service
        self.default_role = default_role

    async def execute(self, request: RegisterRequest) -> RegisterResponse:
        try:
            email = Email(request.email)
        except ValueError as e:
            raise RegisterError(f"Invalid email: {str(e)}")

        if request.password != request.password_confirm:
            raise PasswordMismatchError("Passwords do not match")

        try:
            password = Password(request.password)
        except ValueError as e:
            raise RegisterError(f"Invalid password: {str(e)}")

        if not request.username:
            raise RegisterError("Username is required")
        if len(request.username) < 3:
            raise RegisterError("Username must be at least 3 characters")
        if len(request.username) > 50:
            raise RegisterError("Username cannot exceed 50 characters")
        if not request.username.replace("_", "").replace("-", "").isalnum():
            raise RegisterError(
                "Username can only contain letters, numbers, underscore and hyphen"
            )

        if not request.full_name:
            raise RegisterError("Full name is required")
        if len(request.full_name) < 2:
            raise RegisterError("Full name must be at least 2 characters")
        if len(request.full_name) > 100:
            raise RegisterError("Full name cannot exceed 100 characters")

        if await self.user_repo.exists_by_email(email):
            raise EmailAlreadyExistsError(f"Email {email.value} is already registered")

        if await self.user_repo.exists_by_username(request.username.lower()):
            raise UsernameAlreadyExistsError(f"Username {request.username} is already taken")

        hashed_password = await self.password_service.hash(password.value)

        user = User.create(
            email=email.value,
            username=request.username,
            full_name=request.full_name,
            hashed_password=hashed_password,
            role=self.default_role,
        )

        if request.phone:
            user.phone = request.phone
        if request.department:
            user.department = request.department

        user.metadata["password_strength"] = password.calculate_strength()

        saved_user = await self.user_repo.save(user)

        verification_token = None
        if self.email_service:
            verification_token = await self.email_service.send_verification_email(
                email=saved_user.email,
                username=saved_user.username,
                user_id=saved_user.id,
            )

        message = "Registration successful"
        if verification_token:
            message += ". Please check your email to verify your account."

        return RegisterResponse(
            user=saved_user,
            verification_token=verification_token,
            message=message,
        )

    async def verify_email(self, token: str) -> User:
        if not self.email_service:
            raise RegisterError("Email service not configured")

        user_id = await self.email_service.verify_token(token)
        if not user_id:
            raise RegisterError("Invalid or expired verification token")

        user = await self.user_repo.find_by_id(user_id)
        if not user:
            raise RegisterError("User not found")

        user.activate()
        return await self.user_repo.save(user)

    async def resend_verification(self, email: str) -> str:
        if not self.email_service:
            raise RegisterError("Email service not configured")

        try:
            email_obj = Email(email)
        except ValueError as e:
            raise RegisterError(f"Invalid email: {str(e)}")

        user = await self.user_repo.find_by_email(email_obj)
        if not user:
            raise RegisterError("User not found")
        if user.email_verified:
            raise RegisterError("Email already verified")

        verification_token = await self.email_service.send_verification_email(
            email=user.email, username=user.username, user_id=user.id
        )
        return verification_token


