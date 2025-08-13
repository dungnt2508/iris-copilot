# Clean Architecture & DDD - User Module Implementation Guide

## Tổng quan
Hướng dẫn step-by-step tạo các file cho User module theo Clean Architecture, từ Domain → Application → Infrastructure → API.

## Step 1: Domain Layer (Core Business Logic)

### 1.1. Tạo User Entity
**File:** `app/domain/user/entities/user.py`

```python
@dataclass
class User:
    id: str
    email: str
    username: str
    full_name: str
    hashed_password: str
    role: UserRole
    status: UserStatus
    # ... other fields
    
    @classmethod
    def create(cls, email: str, username: str, ...) -> "User":
        # Factory method - business rule để tạo user mới
        return cls(id=str(uuid4()), ...)
    
    def can_access(self, resource: str, action: str = "read") -> bool:
        # Business rule - kiểm tra quyền truy cập
        if self.status != UserStatus.ACTIVE:
            return False
        # ... logic kiểm tra permission
    
    def activate(self) -> None:
        # Business rule - kích hoạt tài khoản
        if self.status == UserStatus.SUSPENDED:
            raise ValueError("Suspended accounts must be unsuspended by admin")
        self.status = UserStatus.ACTIVE
        self.email_verified = True
```

**Nguyên tắc:**
- Chỉ chứa business rules và behavior
- Không import framework (FastAPI, SQLAlchemy)
- Không chứa logic persistence/HTTP

### 1.2. Tạo Value Objects
**File:** `app/domain/user/value_objects/email.py`

```python
class Email:
    def __init__(self, value: str):
        if not self._is_valid(value):
            raise ValueError("Invalid email format")
        self.value = value.lower()
    
    @staticmethod
    def _is_valid(email: str) -> bool:
        # Business rule validation
        return "@" in email and "." in email.split("@")[1]
```

**File:** `app/domain/user/value_objects/password.py`

```python
class Password:
    def __init__(self, value: str):
        if len(value) < 8:
            raise ValueError("Password too short")
        self.value = value
    
    def calculate_strength(self) -> int:
        # Business rule - tính độ mạnh password
        return len([c for c in self.value if c.isupper()]) + \
               len([c for c in self.value if c.isdigit()])
```

### 1.3. Tạo Repository Interface
**File:** `app/domain/user/repository.py`

```python
class UserRepository(ABC):
    @abstractmethod
    async def find_by_id(self, user_id: str) -> Optional[User]:
        pass
    
    @abstractmethod
    async def find_by_email(self, email: Email) -> Optional[User]:
        pass
    
    @abstractmethod
    async def save(self, user: User) -> User:
        pass
    
    @abstractmethod
    async def exists_by_email(self, email: Email) -> bool:
        pass
```

**Nguyên tắc:**
- Chỉ định nghĩa interface (contract)
- Không chứa implementation
- Domain không biết về database/ORM

## Step 2: Application Layer (Use Cases)

### 2.1. Tạo Login Use Case
**File:** `app/application/user/use_cases/login.py`

```python
class LoginUseCase:
    def __init__(
        self,
        user_repository: UserRepository,  # Dependency injection
        password_service: "PasswordService",
        token_service: "TokenService",
    ):
        self.user_repo = user_repository
        self.password_service = password_service
        self.token_service = token_service
    
    async def execute(self, request: LoginRequest) -> LoginResponse:
        # 1. Validate input
        email = Email(request.email)
        
        # 2. Find user
        user = await self.user_repo.find_by_email(email)
        if not user:
            raise InvalidCredentialsError()
        
        # 3. Verify password
        is_valid = await self.password_service.verify(
            request.password, user.hashed_password
        )
        if not is_valid:
            raise InvalidCredentialsError()
        
        # 4. Check status
        if user.status != UserStatus.ACTIVE:
            raise AccountNotActiveError()
        
        # 5. Generate tokens
        token_data = await self.token_service.generate_tokens(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
            permissions=user.permissions,
        )
        
        # 6. Update last login
        user.update_last_login()
        await self.user_repo.save(user)
        
        return LoginResponse(
            user=user,
            access_token=token_data["access_token"],
            expires_at=token_data["expires_at"],
        )
```

**Nguyên tắc:**
- Chỉ orchestration (gọi domain + services)
- Không chứa business rules
- Nhận dependencies qua constructor

### 2.2. Tạo Register Use Case
**File:** `app/application/user/use_cases/register.py`

```python
class RegisterUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        password_service: "PasswordService",
        email_service: Optional["EmailService"] = None,
    ):
        self.user_repo = user_repository
        self.password_service = password_service
        self.email_service = email_service
    
    async def execute(self, request: RegisterRequest) -> RegisterResponse:
        # 1. Validate input
        email = Email(request.email)
        password = Password(request.password)
        
        # 2. Check if exists
        if await self.user_repo.exists_by_email(email):
            raise EmailAlreadyExistsError()
        
        # 3. Hash password
        hashed_password = await self.password_service.hash(password.value)
        
        # 4. Create user (domain factory)
        user = User.create(
            email=email.value,
            username=request.username,
            full_name=request.full_name,
            hashed_password=hashed_password,
            role=UserRole.USER,
        )
        
        # 5. Save user
        saved_user = await self.user_repo.save(user)
        
        # 6. Send verification email (optional)
        verification_token = None
        if self.email_service:
            verification_token = await self.email_service.send_verification_email(
                email=saved_user.email,
                user_id=saved_user.id,
            )
        
        return RegisterResponse(
            user=saved_user,
            verification_token=verification_token,
            message="Registration successful",
        )
```

## Step 3: Infrastructure Layer (Implementation)

### 3.1. Tạo Database Models
**File:** `app/infrastructure/db/models/user.py`

```python
class UserModel(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    # ... other fields
```

### 3.2. Tạo Repository Implementation
**File:** `app/infrastructure/db/repository_impl/user_repository_impl.py`

```python
class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def find_by_id(self, user_id: str) -> Optional[User]:
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        user_model = result.scalar_one_or_none()
        if not user_model:
            return None
        
        # Map ORM model to Domain entity
        return self._to_domain(user_model)
    
    async def find_by_email(self, email: Email) -> Optional[User]:
        result = await self.session.execute(
            select(UserModel).where(UserModel.email == email.value.lower())
        )
        user_model = result.scalar_one_or_none()
        if not user_model:
            return None
        
        return self._to_domain(user_model)
    
    async def save(self, user: User) -> User:
        # Check if exists
        existing = await self.session.execute(
            select(UserModel).where(UserModel.id == user.id)
        )
        user_model = existing.scalar_one_or_none()
        
        if user_model:
            # Update existing
            self._update_model(user_model, user)
        else:
            # Create new
            user_model = self._to_model(user)
            self.session.add(user_model)
        
        await self.session.commit()
        return user
    
    def _to_domain(self, model: UserModel) -> User:
        """Map ORM model to Domain entity"""
        return User(
            id=model.id,
            email=model.email,
            username=model.username,
            full_name=model.full_name,
            hashed_password=model.hashed_password,
            role=UserRole(model.role),
            status=UserStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
            # ... map other fields
        )
    
    def _to_model(self, user: User) -> UserModel:
        """Map Domain entity to ORM model"""
        return UserModel(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            hashed_password=user.hashed_password,
            role=user.role.value,
            status=user.status.value,
            created_at=user.created_at,
            updated_at=user.updated_at,
            # ... map other fields
        )
```

## Step 4: API Layer (Controllers)

### 4.1. Tạo Schemas
**File:** `app/api/v1/schemas/auth.py`

```python
class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    full_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=8)
    password_confirm: str = Field(min_length=8)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
```

### 4.2. Tạo Dependencies
**File:** `app/api/v1/dependencies.py`

```python
async def get_current_user(
    authorization: Optional[str] = Header(None),
    token_service: TokenService = Depends(get_token_service),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split(" ", 1)[1]
    token_data = await token_service.verify_token(token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await user_repo.find_by_id(token_data["user_id"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

def require_permissions(*permissions: str):
    async def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role == UserRole.ADMIN:
            return current_user
        missing = [p for p in permissions if p not in current_user.permissions]
        if missing:
            raise HTTPException(status_code=403, detail="Missing permissions")
        return current_user
    return _dependency
```

### 4.3. Tạo Router
**File:** `app/api/v1/routers/auth.py`

```python
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
        expires_in=1800,
        refresh_token=result.refresh_token,
    )

@router.get("/me", response_model=MeResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return MeResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        role=current_user.role.value,
        permissions=current_user.permissions,
        status=current_user.status.value,
    )
```

## Step 5: Wiring (Composition Root)

### 5.1. Tạo Wiring Module
**File:** `app/wiring.py`

```python
def provide_user_repository() -> UserRepository:
    # TODO: Replace with DB implementation
    return InMemoryUserRepository()

def provide_token_service() -> TokenService:
    return TokenService(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
        access_token_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )

def provide_password_service() -> PasswordService:
    return PasswordService()
```

## Tóm tắt Flow

### Request Flow:
1. **API Layer** nhận request → gọi **Use Case**
2. **Use Case** orchestrate → gọi **Domain entities** + **Repository interface**
3. **Repository implementation** (Infrastructure) → thực hiện persistence
4. **Domain entities** → chứa business rules
5. **Response** → trả về qua API Layer

### Dependency Flow:
```
API → Application → Domain ← Infrastructure
```

## Lợi ích của Clean Architecture

- **Domain không phụ thuộc framework**: Có thể thay đổi framework mà không ảnh hưởng business logic
- **Business rules tập trung**: Tất cả business logic nằm ở Domain layer
- **Infrastructure có thể thay đổi**: Có thể đổi database từ PostgreSQL sang MongoDB mà không ảnh hưởng Domain
- **Test dễ dàng**: Có thể mock dependencies để test từng layer riêng biệt
- **Separation of Concerns**: Mỗi layer có trách nhiệm rõ ràng
- **Maintainability**: Code dễ bảo trì và mở rộng