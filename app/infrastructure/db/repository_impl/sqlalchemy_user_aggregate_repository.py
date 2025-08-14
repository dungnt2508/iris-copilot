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
from app.infrastructure.db.models.user import User as UserModel, UserProfile as UserProfileModel, Session as SessionModel, Permission as PermissionModel


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
                profile_model = self._profile_to_model(aggregate.profile)
                existing_profile = await self.session.execute(
                    select(UserProfileModel).where(UserProfileModel.user_id == aggregate.user.id)
                )
                profile_model_result = existing_profile.scalar_one_or_none()
                
                if profile_model_result:
                    # Update existing profile
                    self._update_profile_model(profile_model_result, aggregate.profile)
                else:
                    # Create new profile
                    self.session.add(profile_model)
            
            # 3. Save permissions (if any)
            if aggregate.permissions:
                # Delete existing permissions for this user
                existing_permissions = await self.session.execute(
                    select(PermissionModel).where(PermissionModel.user_id == aggregate.user.id)
                )
                for perm in existing_permissions.scalars():
                    await self.session.delete(perm)
                
                # Add new permissions
                for permission in aggregate.permissions:
                    permission_model = self._permission_to_model(permission)
                    self.session.add(permission_model)
            
            # 4. Save sessions (if any)
            if aggregate.sessions:
                for session in aggregate.sessions:
                    session_model = self._session_to_model(session)
                    existing_session = await self.session.execute(
                        select(SessionModel).where(SessionModel.id == session.id)
                    )
                    session_model_result = existing_session.scalar_one_or_none()
                    
                    if session_model_result:
                        # Update existing session
                        self._update_session_model(session_model_result, session)
                    else:
                        # Create new session
                        self.session.add(session_model)
            
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
        """Convert ORM model to UserAggregate"""
        # 1. Create user entity
        user = self._model_to_user(user_model)
        
        # 2. Create aggregate
        aggregate = UserAggregate(user=user)
        
        # 3. Load profile if exists
        profile_result = await self.session.execute(
            select(UserProfileModel).where(UserProfileModel.user_id == user_model.id)
        )
        profile_model = profile_result.scalar_one_or_none()
        if profile_model:
            aggregate.profile = self._model_to_profile(profile_model)
        
        # 4. Load permissions
        permissions_result = await self.session.execute(
            select(PermissionModel).where(PermissionModel.user_id == user_model.id)
        )
        for perm_model in permissions_result.scalars():
            aggregate.permissions.append(self._model_to_permission(perm_model))
        
        # 5. Load sessions
        sessions_result = await self.session.execute(
            select(SessionModel).where(SessionModel.user_id == user_model.id)
        )
        for session_model in sessions_result.scalars():
            aggregate.sessions.append(self._model_to_session(session_model))
        
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
    
    # Profile conversion methods
    def _profile_to_model(self, profile: UserProfile) -> UserProfileModel:
        """Convert UserProfile entity to ORM model"""
        return UserProfileModel(
            id=profile.id,
            user_id=profile.user_id,
            avatar_url=profile.avatar_url,
            bio=profile.bio,
            location=profile.location,
            website=profile.website,
            company=profile.company,
            job_title=profile.job_title,
            skills=profile.skills,
            preferences=profile.preferences,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )
    
    def _model_to_profile(self, model: UserProfileModel) -> UserProfile:
        """Convert ORM model to UserProfile entity"""
        return UserProfile(
            id=model.id,
            user_id=model.user_id,
            avatar_url=model.avatar_url,
            bio=model.bio,
            location=model.location,
            website=model.website,
            company=model.company,
            job_title=model.job_title,
            skills=model.skills,
            preferences=model.preferences,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _update_profile_model(self, model: UserProfileModel, profile: UserProfile) -> None:
        """Update existing profile model with profile data"""
        model.avatar_url = profile.avatar_url
        model.bio = profile.bio
        model.location = profile.location
        model.website = profile.website
        model.company = profile.company
        model.job_title = profile.job_title
        model.skills = profile.skills
        model.preferences = profile.preferences
        model.updated_at = profile.updated_at
    
    # Permission conversion methods
    def _permission_to_model(self, permission: Permission) -> PermissionModel:
        """Convert Permission entity to ORM model"""
        return PermissionModel(
            id=permission.id,
            user_id=permission.user_id,
            name=permission.name,
            type=permission.type.value,
            scope=permission.scope.value,
            resource=permission.resource,
            conditions=permission.conditions,
            granted_by=permission.granted_by,
            is_active=permission.is_active,
            granted_at=permission.granted_at,
            expires_at=permission.expires_at
        )
    
    def _model_to_permission(self, model: PermissionModel) -> Permission:
        """Convert ORM model to Permission entity"""
        return Permission(
            id=model.id,
            user_id=model.user_id,
            name=model.name,
            type=PermissionType(model.type),
            scope=PermissionScope(model.scope),
            resource=model.resource,
            conditions=model.conditions,
            granted_by=model.granted_by,
            is_active=model.is_active,
            granted_at=model.granted_at,
            expires_at=model.expires_at
        )
    
    # Session conversion methods
    def _session_to_model(self, session: Session) -> SessionModel:
        """Convert Session entity to ORM model"""
        return SessionModel(
            id=session.id,
            user_id=session.user_id,
            token=session.token,
            refresh_token=session.refresh_token,
            device_info=session.device_info,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            is_active=session.is_active,
            expires_at=session.expires_at,
            created_at=session.created_at,
            last_activity=session.last_activity
        )
    
    def _model_to_session(self, model: SessionModel) -> Session:
        """Convert ORM model to Session entity"""
        return Session(
            id=model.id,
            user_id=model.user_id,
            token=model.token,
            refresh_token=model.refresh_token,
            device_info=model.device_info,
            ip_address=model.ip_address,
            user_agent=model.user_agent,
            is_active=model.is_active,
            expires_at=model.expires_at,
            created_at=model.created_at,
            last_activity=model.last_activity
        )
    
    def _update_session_model(self, model: SessionModel, session: Session) -> None:
        """Update existing session model with session data"""
        model.token = session.token
        model.refresh_token = session.refresh_token
        model.device_info = session.device_info
        model.ip_address = session.ip_address
        model.user_agent = session.user_agent
        model.is_active = session.is_active
        model.expires_at = session.expires_at
        model.last_activity = session.last_activity
