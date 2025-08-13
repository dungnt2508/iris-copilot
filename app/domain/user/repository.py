"""
User Entity Repository Interface (Legacy)
For backward compatibility with existing code
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from .entities.user import User
from .value_objects.email import Email


class UserEntityRepository(ABC):
    """
    Repository interface for User entity (legacy)
    This is a port - implementation will be in infrastructure layer
    
    Note: This is legacy interface. For new features, use UserAggregateRepository
    """
    
    @abstractmethod
    async def find_by_id(self, user_id: str) -> Optional[User]:
        """Find user by ID"""
        pass
    
    @abstractmethod
    async def find_by_email(self, email: Email) -> Optional[User]:
        """Find user by email"""
        pass
    
    @abstractmethod
    async def find_by_username(self, username: str) -> Optional[User]:
        """Find user by username"""
        pass
    
    @abstractmethod
    async def save(self, user: User) -> User:
        """Save or update user"""
        pass
    
    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """Delete user by ID"""
        pass
    
    @abstractmethod
    async def list_all(
        self, 
        limit: int = 100, 
        offset: int = 0,
        filters: Optional[dict] = None
    ) -> List[User]:
        """List all users with pagination and filters"""
        pass
    
    @abstractmethod
    async def count(self, filters: Optional[dict] = None) -> int:
        """Count users with optional filters"""
        pass
    
    @abstractmethod
    async def exists_by_email(self, email: Email) -> bool:
        """Check if user exists by email"""
        pass
    
    @abstractmethod
    async def exists_by_username(self, username: str) -> bool:
        """Check if user exists by username"""
        pass
    
    @abstractmethod
    async def find_by_role(self, role: str) -> List[User]:
        """Find all users with specific role"""
        pass
    
    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 50
    ) -> List[User]:
        """Search users by name, email, or username"""
        pass


# Alias for backward compatibility
UserRepository = UserEntityRepository
