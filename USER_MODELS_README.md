# User Domain Models

## Tổng quan

Đây là các SQLAlchemy models cho domain User được tạo theo kiến trúc Clean Architecture và Domain-Driven Design (DDD). Các models này map trực tiếp với domain entities và đảm bảo tính nhất quán của dữ liệu.

## Các Models

### 1. User Model
**File:** `app/infrastructure/db/models/user.py`

Model chính cho User entity với các trường:

```python
class User(Base):
    __tablename__ = "users"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # Basic information
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Status and role
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), nullable=False)
    status: Mapped[UserStatus] = mapped_column(SQLEnum(UserStatus), nullable=False)
    
    # Contact information
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Verification and metadata
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    permissions: Mapped[List[str]] = mapped_column(JSON, default=list)
    user_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
```

### 2. UserProfile Model
**File:** `app/infrastructure/db/models/user.py`

Model cho UserProfile entity:

```python
class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # Foreign key to User
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    
    # Profile information
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    company: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    job_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Skills and preferences
    skills: Mapped[List[str]] = mapped_column(JSON, default=list)
    preferences: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 3. Session Model
**File:** `app/infrastructure/db/models/user.py`

Model cho Session entity:

```python
class Session(Base):
    __tablename__ = "sessions"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # Foreign key to User
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    
    # Session tokens
    token: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, unique=True)
    
    # Session metadata
    device_info: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Session status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_activity: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 4. Permission Model
**File:** `app/infrastructure/db/models/user.py`

Model cho Permission entity:

```python
class Permission(Base):
    __tablename__ = "permissions"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # Foreign key to User
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    
    # Permission details
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    type: Mapped[PermissionType] = mapped_column(SQLEnum(PermissionType), nullable=False)
    scope: Mapped[PermissionScope] = mapped_column(SQLEnum(PermissionScope), nullable=False)
    resource: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Permission conditions and metadata
    conditions: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    granted_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Permission status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    granted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
```

## Relationships

Các models có các relationships sau:

1. **User -> UserProfile**: One-to-One relationship
2. **User -> Session**: One-to-Many relationship  
3. **User -> Permission**: One-to-Many relationship

```python
# Trong User model
profile: Mapped[Optional["UserProfile"]] = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
sessions: Mapped[List["Session"]] = relationship("Session", back_populates="user", cascade="all, delete-orphan")
permissions_rel: Mapped[List["Permission"]] = relationship("Permission", back_populates="user", cascade="all, delete-orphan")
```

## Repository Implementation

Các models này được sử dụng trong `SQLAlchemyUserAggregateRepository` để:

1. **Lưu trữ dữ liệu**: Chuyển đổi từ domain entities sang SQLAlchemy models
2. **Truy xuất dữ liệu**: Chuyển đổi từ SQLAlchemy models sang domain entities
3. **Quản lý relationships**: Đảm bảo tính nhất quán của dữ liệu

## Cách sử dụng

### 1. Tạo User Aggregate

```python
from app.domain.user.aggregates.user_aggregate import UserAggregate
from app.domain.user.entities.user import User, UserRole

# Tạo user
user = User.create(
    email="user@example.com",
    username="username",
    full_name="Full Name",
    hashed_password="hashed_password",
    role=UserRole.USER
)

# Tạo aggregate
aggregate = UserAggregate(user=user)
```

### 2. Sử dụng Repository

```python
from app.infrastructure.db.repository_impl.sqlalchemy_user_aggregate_repository import SQLAlchemyUserAggregateRepository

# Lưu aggregate
repo = SQLAlchemyUserAggregateRepository(session)
saved_aggregate = await repo.save_aggregate(aggregate)

# Tìm aggregate
found_aggregate = await repo.find_aggregate_by_email("user@example.com")
```

### 3. Test Models

Chạy script test để kiểm tra:

```bash
python test_user_models.py
```

## Database Schema

Các bảng được tạo:

1. **users**: Bảng chính cho user
2. **user_profiles**: Thông tin profile của user
3. **sessions**: Sessions đăng nhập của user
4. **permissions**: Quyền hạn của user

## Lưu ý

1. **Cascade Delete**: Khi xóa user, tất cả profile, sessions, và permissions sẽ bị xóa theo
2. **Indexes**: Email, username, và token có indexes để tối ưu truy vấn
3. **JSON Fields**: Skills, preferences, device_info, conditions, và metadata sử dụng JSON field
4. **Timestamps**: Tất cả models đều có created_at và updated_at
5. **UUID**: Tất cả primary keys sử dụng UUID string

## Migration

Để tạo database tables:

```python
from app.infrastructure.db.base import init_db

await init_db()
```

Điều này sẽ tạo tất cả tables cho tất cả models đã được import.
