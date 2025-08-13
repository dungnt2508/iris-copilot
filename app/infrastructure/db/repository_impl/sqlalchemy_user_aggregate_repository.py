"""
SQLAlchemy User Aggregate Repository Implementation
"""
from typing import Optional, List
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.user.aggregates import UserAggregate, UserAggregateRepository
from app.domain.user.entities.user import User, UserRole, UserStatus
from app.domain.user.entities.user_profile import UserProfile
from app.domain.user.entities.session import Session
from app.domain.user.entities.permission import Permission, PermissionType, PermissionScope
from app.domain.user.value_objects.email import Email
from app.infrastructure.db.models.user import UserModel


class SQLAlchemyUserAggregateRepository(UserAggregateRepository):
    """
    SQLAlchemy implementation of UserAggregate repository
    Maps between ORM models and Domain aggregates
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save_aggregate(self, aggregate: UserAggregate) -> UserAggregate:
        """Save entire user aggregate atomically"""
        try:
            # 1. Save user
            user_model = self._user_to_model(aggregate.user)
            
            # Check if user exists
            existing_user = await self.session.execute(
                select(UserModel).where(UserModel.id == aggregate.user.id)
            )
            user_model_result = existing_user.scalar_one_or_none()
            
            if user_model_result:
                # Update existing user
                self._update_user_model(user_model_result, aggregate.user)
            else:
                # Create new user
                self.session.add(user_model)
            
            # 2. Save profile (if exists)
            if aggregate.profile:
                # Note: In real implementation, you'd have a ProfileModel
                # For now, we'll store profile data in user metadata
                profile_data = aggregate.profile.to_dict()
                user_model.user_metadata = user_model.user_metadata or {}
                user_model.user_metadata["profile"] = profile_data
            
            # 3. Save permissions (if any)
            # Note: In real implementation, you'd have a PermissionModel
            # For now, we'll store permissions in user metadata
            permissions_data = [p.to_dict() for p in aggregate.permissions]
            user_model.user_metadata = user_model.user_metadata or {}
            user_model.user_metadata["permissions"] = permissions_data
            
            # 4. Save sessions (if any)
            # Note: In real implementation, you'd have a SessionModel
            # For now, we'll store sessions in user metadata
            sessions_data = [s.to_dict() for s in aggregate.sessions]
            user_model.user_metadata = user_model.user_metadata or {}
            user_model.user_metadata["sessions"] = sessions_data
            
            # 5. Commit transaction
            await self.session.commit()
            await self.session.refresh(user_model)
            
            # 6. Return updated aggregate
            return await self._model_to_aggregate(user_model)
            
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def find_aggregate_by_id(self, user_id: str) -> Optional[UserAggregate]:
        """Find user aggregate by ID"""
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        user_model = result.scalar_one_or_none()
        
        if not user_model:
            return None
        
        return await self._model_to_aggregate(user_model)
    
    async def find_aggregate_by_email(self, email: str) -> Optional[UserAggregate]:
        """Find user aggregate by email"""
        result = await self.session.execute(
            select(UserModel).where(UserModel.email == email.lower())
        )
        user_model = result.scalar_one_or_none()
        
        if not user_model:
            return None
        
        return await self._model_to_aggregate(user_model)
    
    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email"""
        result = await self.session.execute(
            select(UserModel.id).where(UserModel.email == email.lower())
        )
        return result.scalar_one_or_none() is not None
    
    async def _model_to_aggregate(self, user_model: UserModel) -> UserAggregate:
        """Convert ORM model to Domain aggregate"""
        # 1. Convert user
        user = self._model_to_user(user_model)
        
        # 2. Create aggregate
        aggregate = UserAggregate(user=user)
        
        # 3. Add profile if exists
        if user_model.user_metadata and "profile" in user_model.user_metadata:
            profile_data = user_model.user_metadata["profile"]
            aggregate.profile = UserProfile(
                id=profile_data["id"],
                user_id=profile_data["user_id"],
                avatar_url=profile_data.get("avatar_url"),
                bio=profile_data.get("bio"),
                location=profile_data.get("location"),
                website=profile_data.get("website"),
                company=profile_data.get("company"),
                job_title=profile_data.get("job_title"),
                skills=profile_data.get("skills", []),
                preferences=profile_data.get("preferences", {}),
                created_at=datetime.fromisoformat(profile_data["created_at"]),
                updated_at=datetime.fromisoformat(profile_data["updated_at"])
            )
        
        # 4. Add permissions if exist
        if user_model.user_metadata and "permissions" in user_model.user_metadata:
            permissions_data = user_model.user_metadata["permissions"]
            for perm_data in permissions_data:
                permission = Permission(
                    id=perm_data["id"],
                    user_id=perm_data["user_id"],
                    name=perm_data["name"],
                    type=PermissionType(perm_data["type"]),
                    scope=PermissionScope(perm_data["scope"]),
                    resource=perm_data.get("resource"),
                    conditions=perm_data.get("conditions", {}),
                    granted_at=datetime.fromisoformat(perm_data["granted_at"]),
                    granted_by=perm_data.get("granted_by"),
                    expires_at=datetime.fromisoformat(perm_data["expires_at"]) if perm_data.get("expires_at") else None,
                    is_active=perm_data["is_active"]
                )
                aggregate.permissions.append(permission)
        
        # 5. Add sessions if exist
        if user_model.user_metadata and "sessions" in user_model.user_metadata:
            sessions_data = user_model.user_metadata["sessions"]
            for session_data in sessions_data:
                session = Session(
                    id=session_data["id"],
                    user_id=session_data["user_id"],
                    token=session_data["token"],
                    refresh_token=session_data.get("refresh_token"),
                    device_info=session_data.get("device_info"),
                    ip_address=session_data.get("ip_address"),
                    user_agent=session_data.get("user_agent"),
                    is_active=session_data["is_active"],
                    expires_at=datetime.fromisoformat(session_data["expires_at"]),
                    created_at=datetime.fromisoformat(session_data["created_at"]),
                    last_activity=datetime.fromisoformat(session_data["last_activity"])
                )
                aggregate.sessions.append(session)
        
        return aggregate
    
    def _model_to_user(self, model: UserModel) -> User:
        """Convert ORM model to User entity"""
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
            last_login=model.last_login,
            email_verified=model.email_verified,
            phone=model.phone,
            department=model.department,
            permissions=model.permissions or [],
            metadata=model.user_metadata or {}
        )
    
    def _user_to_model(self, user: User) -> UserModel:
        """Convert User entity to ORM model"""
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
            user_metadata=user.metadata
        )
    
    def _update_user_model(self, model: UserModel, user: User) -> None:
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
