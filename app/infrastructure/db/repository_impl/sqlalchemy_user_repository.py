"""
SQLAlchemy User Repository Implementation
"""
from typing import Optional, List
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.user.repository import UserRepository
from app.domain.user.entities.user import User, UserRole, UserStatus
from app.domain.user.value_objects.email import Email
from app.infrastructure.db.models.user import UserModel


class SQLAlchemyUserRepository(UserRepository):
    """
    SQLAlchemy implementation of UserRepository
    Maps between UserModel (ORM) and User (Domain Entity)
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def find_by_id(self, user_id: str) -> Optional[User]:
        """Find user by ID"""
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        user_model = result.scalar_one_or_none()
        if not user_model:
            return None
        
        return self._to_domain(user_model)
    
    async def find_by_email(self, email: Email) -> Optional[User]:
        """Find user by email"""
        result = await self.session.execute(
            select(UserModel).where(UserModel.email == email.value.lower())
        )
        user_model = result.scalar_one_or_none()
        if not user_model:
            return None
        
        return self._to_domain(user_model)
    
    async def find_by_username(self, username: str) -> Optional[User]:
        """Find user by username"""
        result = await self.session.execute(
            select(UserModel).where(UserModel.username == username.lower())
        )
        user_model = result.scalar_one_or_none()
        if not user_model:
            return None
        
        return self._to_domain(user_model)
    
    async def save(self, user: User) -> User:
        """Save or update user"""
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
        await self.session.refresh(user_model)
        
        return self._to_domain(user_model)
    
    async def delete(self, user_id: str) -> bool:
        """Delete user by ID"""
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        user_model = result.scalar_one_or_none()
        if not user_model:
            return False
        
        await self.session.delete(user_model)
        await self.session.commit()
        return True
    
    async def list_all(
        self, limit: int = 100, offset: int = 0, filters: Optional[dict] = None
    ) -> List[User]:
        """List all users with pagination and filters"""
        query = select(UserModel)
        
        # Apply filters
        if filters:
            if filters.get("role"):
                query = query.where(UserModel.role == filters["role"])
            if filters.get("status"):
                query = query.where(UserModel.status == filters["status"])
        
        # Apply pagination
        query = query.offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        user_models = result.scalars().all()
        
        return [self._to_domain(model) for model in user_models]
    
    async def count(self, filters: Optional[dict] = None) -> int:
        """Count users with optional filters"""
        query = select(UserModel)
        
        if filters:
            if filters.get("role"):
                query = query.where(UserModel.role == filters["role"])
            if filters.get("status"):
                query = query.where(UserModel.status == filters["status"])
        
        result = await self.session.execute(query)
        return len(result.scalars().all())
    
    async def exists_by_email(self, email: Email) -> bool:
        """Check if user exists by email"""
        result = await self.session.execute(
            select(UserModel.id).where(UserModel.email == email.value.lower())
        )
        return result.scalar_one_or_none() is not None
    
    async def exists_by_username(self, username: str) -> bool:
        """Check if user exists by username"""
        result = await self.session.execute(
            select(UserModel.id).where(UserModel.username == username.lower())
        )
        return result.scalar_one_or_none() is not None
    
    async def find_by_role(self, role: str) -> List[User]:
        """Find all users with specific role"""
        result = await self.session.execute(
            select(UserModel).where(UserModel.role == role)
        )
        user_models = result.scalars().all()
        return [self._to_domain(model) for model in user_models]
    
    async def search(self, query: str, limit: int = 50) -> List[User]:
        """Search users by name, email, or username"""
        search_term = f"%{query.lower()}%"
        result = await self.session.execute(
            select(UserModel).where(
                (UserModel.email.ilike(search_term)) |
                (UserModel.username.ilike(search_term)) |
                (UserModel.full_name.ilike(search_term))
            ).limit(limit)
        )
        user_models = result.scalars().all()
        return [self._to_domain(model) for model in user_models]
    
    def _to_domain(self, model: UserModel) -> User:
        """Map ORM model to Domain entity"""
        # Handle invalid role values
        try:
            role = UserRole(model.role)
        except ValueError:
            # Default to USER if role is invalid
            role = UserRole.USER
        
        # Handle invalid status values
        try:
            status = UserStatus(model.status)
        except ValueError:
            # Default to PENDING if status is invalid
            status = UserStatus.PENDING
        
        return User(
            id=model.id,
            email=model.email,
            username=model.username,
            full_name=model.full_name,
            hashed_password=model.hashed_password,
            role=role,
            status=status,
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_login=model.last_login,
            email_verified=model.email_verified,
            phone=model.phone,
            department=model.department,
            permissions=model.permissions or [],
            metadata=model.user_metadata or {},
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
            last_login=user.last_login,
            email_verified=user.email_verified,
            phone=user.phone,
            department=user.department,
            permissions=user.permissions,
            user_metadata=user.metadata,
        )
    
    def _update_model(self, model: UserModel, user: User) -> None:
        """Update existing model with user data"""
        model.email = user.email
        model.username = user.username
        model.full_name = user.full_name
        model.hashed_password = user.hashed_password
        model.role = user.role.value
        model.status = user.status.value
        model.updated_at = user.updated_at
        model.last_login = user.last_login
        model.email_verified = user.email_verified
        model.phone = user.phone
        model.department = user.department
        model.permissions = user.permissions
        model.user_metadata = user.metadata
