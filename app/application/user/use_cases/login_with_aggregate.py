"""
Login User Use Case with Aggregate
"""
from typing import Optional, Dict, Any
from app.domain.user.aggregates import UserAggregate, UserAggregateRepository
from app.domain.user.entities.session import Session
from app.services.password_service import PasswordService
from app.services.token_service import TokenService


class LoginUserUseCase:
    """
    Login User Use Case
    Uses UserAggregate to ensure data consistency
    """
    
    def __init__(self, user_repository: UserAggregateRepository, 
                 password_service: PasswordService,
                 token_service: TokenService):
        self.user_repository = user_repository
        self.password_service = password_service
        self.token_service = token_service
    
    async def execute(self, email: str, password: str, 
                     device_info: Optional[Dict[str, Any]] = None,
                     ip_address: Optional[str] = None,
                     user_agent: Optional[str] = None,
                     remember_me: bool = False) -> dict:
        """
        Execute user login
        Returns authentication result with tokens
        """
        # 1. Find user aggregate
        aggregate = await self.user_repository.find_aggregate_by_email(email)
        if not aggregate:
            raise ValueError("Invalid credentials")
        
        # 2. Verify password
        is_valid = await self.password_service.verify(password, aggregate.user.hashed_password)
        if not is_valid:
            raise ValueError("Invalid credentials")
        
        # 3. Check account status
        if not aggregate.user.is_active():
            raise ValueError("Account is not active")
        
        # 4. Execute authentication on aggregate
        session = aggregate.authenticate(
            email=email,
            password=password,
            device_info=device_info,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # 5. Generate tokens
        tokens = await self.token_service.generate_tokens(
            user_id=aggregate.user.id,
            email=aggregate.user.email,
            role=aggregate.user.role.value,
            permissions=[p.name for p in aggregate.permissions if p.is_valid()],
            remember_me=remember_me
        )
        
        # 6. Update session with tokens
        session.token = tokens["access_token"]
        if "refresh_token" in tokens:
            session.refresh_token = tokens["refresh_token"]
        
        # 7. Save to repository
        await self.user_repository.save_aggregate(aggregate)
        
        return {
            "user": aggregate.user.to_dict(),
            "tokens": tokens,
            "session": session.to_dict(),
            "permissions": [p.name for p in aggregate.permissions if p.is_valid()]
        }
    
    async def execute_with_validation(self, email: str, password: str,
                                    device_info: Optional[Dict[str, Any]] = None,
                                    ip_address: Optional[str] = None,
                                    user_agent: Optional[str] = None,
                                    remember_me: bool = False) -> dict:
        """
        Execute login with detailed validation
        Returns detailed result
        """
        try:
            # 1. Validate input
            validation_errors = self._validate_input(email, password)
            if validation_errors:
                return {
                    "success": False,
                    "errors": validation_errors,
                    "user": None,
                    "tokens": None
                }
            
            # 2. Find user aggregate
            aggregate = await self.user_repository.find_aggregate_by_email(email)
            if not aggregate:
                return {
                    "success": False,
                    "errors": ["Invalid credentials"],
                    "user": None,
                    "tokens": None
                }
            
            # 3. Verify password
            is_valid = await self.password_service.verify(password, aggregate.user.hashed_password)
            if not is_valid:
                return {
                    "success": False,
                    "errors": ["Invalid credentials"],
                    "user": None,
                    "tokens": None
                }
            
            # 4. Check account status
            if not aggregate.user.is_active():
                return {
                    "success": False,
                    "errors": ["Account is not active"],
                    "user": None,
                    "tokens": None
                }
            
            # 5. Execute authentication
            session = aggregate.authenticate(
                email=email,
                password=password,
                device_info=device_info,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # 6. Generate tokens
            tokens = await self.token_service.generate_tokens(
                user_id=aggregate.user.id,
                email=aggregate.user.email,
                role=aggregate.user.role.value,
                permissions=[p.name for p in aggregate.permissions if p.is_valid()],
                remember_me=remember_me
            )
            
            # 7. Update session
            session.token = tokens["access_token"]
            if "refresh_token" in tokens:
                session.refresh_token = tokens["refresh_token"]
            
            # 8. Save to repository
            await self.user_repository.save_aggregate(aggregate)
            
            return {
                "success": True,
                "errors": [],
                "user": aggregate.user.to_dict(),
                "tokens": tokens,
                "session": session.to_dict(),
                "permissions": [p.name for p in aggregate.permissions if p.is_valid()],
                "active_sessions_count": len(aggregate.get_active_sessions())
            }
            
        except Exception as e:
            return {
                "success": False,
                "errors": [str(e)],
                "user": None,
                "tokens": None
            }
    
    def _validate_input(self, email: str, password: str) -> list:
        """Validate login input"""
        errors = []
        
        # Validate email
        if not email or '@' not in email:
            errors.append("Invalid email format")
        
        # Validate password
        if not password:
            errors.append("Password is required")
        
        return errors
