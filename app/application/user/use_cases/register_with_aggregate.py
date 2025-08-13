"""
Register User Use Case with Aggregate
"""
from typing import Optional
from app.domain.user.aggregates import UserAggregate, UserAggregateRepository
from app.domain.user.entities.user import User
from app.services.password_service import PasswordService


class RegisterUserUseCase:
    """
    Register User Use Case
    Uses UserAggregate to ensure data consistency
    """
    
    def __init__(self, user_repository: UserAggregateRepository, password_service: PasswordService):
        self.user_repository = user_repository
        self.password_service = password_service
    
    async def execute(self, email: str, password: str, full_name: str, 
                     username: Optional[str] = None) -> User:
        """
        Execute user registration
        Returns created user
        """
        # 1. Check if user already exists
        existing_aggregate = await self.user_repository.find_aggregate_by_email(email)
        if existing_aggregate:
            raise ValueError("User with this email already exists")
        
        # 2. Hash password
        hashed_password = await self.password_service.hash(password)
        
        # 3. Create empty user for aggregate
        user = User.create_empty()
        aggregate = UserAggregate(user=user)
        
        # 4. Execute business operation on aggregate
        aggregate.register_user(
            email=email,
            password=hashed_password,
            full_name=full_name,
            username=username
        )
        
        # 5. Save to repository (atomic operation)
        saved_aggregate = await self.user_repository.save_aggregate(aggregate)
        
        return saved_aggregate.user
    
    async def execute_with_validation(self, email: str, password: str, full_name: str,
                                    username: Optional[str] = None) -> dict:
        """
        Execute registration with detailed validation
        Returns detailed result
        """
        try:
            # 1. Validate input
            validation_errors = self._validate_input(email, password, full_name)
            if validation_errors:
                return {
                    "success": False,
                    "errors": validation_errors,
                    "user": None
                }
            
            # 2. Check existing user
            existing_aggregate = await self.user_repository.find_aggregate_by_email(email)
            if existing_aggregate:
                return {
                    "success": False,
                    "errors": ["User with this email already exists"],
                    "user": None
                }
            
            # 3. Hash password
            hashed_password = await self.password_service.hash(password)
            
            # 4. Create aggregate and register user
            user = User.create_empty()
            aggregate = UserAggregate(user=user)
            
            aggregate.register_user(
                email=email,
                password=hashed_password,
                full_name=full_name,
                username=username
            )
            
            # 5. Save to repository
            saved_aggregate = await self.user_repository.save_aggregate(aggregate)
            
            return {
                "success": True,
                "errors": [],
                "user": saved_aggregate.user.to_dict(),
                "profile": saved_aggregate.profile.to_dict() if saved_aggregate.profile else None,
                "permissions_count": len(saved_aggregate.permissions)
            }
            
        except Exception as e:
            return {
                "success": False,
                "errors": [str(e)],
                "user": None
            }
    
    def _validate_input(self, email: str, password: str, full_name: str) -> list:
        """Validate registration input"""
        errors = []
        
        # Validate email
        if not email or '@' not in email:
            errors.append("Invalid email format")
        
        # Validate password
        if not password or len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        # Validate full name
        if not full_name or len(full_name.strip()) < 2:
            errors.append("Full name must be at least 2 characters long")
        
        return errors
