"""
User Entity - Core business object
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import uuid4


class UserRole(str, Enum):
    """User roles in the system"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    GUEST = "guest"


class UserStatus(str, Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


@dataclass
class User:
    """
    User entity with business logic
    Pure domain model - no framework dependencies
    """
    id: str
    email: str
    username: str
    full_name: str
    hashed_password: str
    role: UserRole
    status: UserStatus
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    email_verified: bool = False
    phone: Optional[str] = None
    department: Optional[str] = None
    permissions: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    
    @classmethod
    def create(
        cls,
        email: str,
        username: str,
        full_name: str,
        hashed_password: str,
        role: UserRole = UserRole.USER,
    ) -> "User":
        """Factory method to create a new user"""
        now = datetime.utcnow()
        return cls(
            id=str(uuid4()),
            email=email.lower(),
            username=username.lower(),
            full_name=full_name,
            hashed_password=hashed_password,
            role=role,
            status=UserStatus.PENDING,
            created_at=now,
            updated_at=now,
            permissions=cls._get_default_permissions(role),
        )
    
    @classmethod
    def create_empty(cls) -> "User":
        """Factory method to create an empty user for aggregate initialization"""
        now = datetime.utcnow()
        return cls(
            id=str(uuid4()),
            email="",
            username="",
            full_name="",
            hashed_password="",
            role=UserRole.USER,
            status=UserStatus.PENDING,
            created_at=now,
            updated_at=now,
            permissions=[],
        )
    
    @staticmethod
    def _get_default_permissions(role: UserRole) -> List[str]:
        """Get default permissions based on role"""
        base_permissions = ["read:public", "read:profile"]
        
        role_permissions = {
            UserRole.GUEST: [],
            UserRole.VIEWER: ["read:documents", "read:analytics"],
            UserRole.USER: [
                "read:documents", 
                "write:documents", 
                "read:analytics",
                "use:chat"
            ],
            UserRole.ADMIN: [
                "read:all", 
                "write:all", 
                "delete:all", 
                "manage:users",
                "manage:system"
            ],
        }
        
        return base_permissions + role_permissions.get(role, [])
    
    def can_access(self, resource: str, action: str = "read") -> bool:
        """
        Business rule: Check if user can access a resource
        """
        if self.status != UserStatus.ACTIVE:
            return False
        
        if self.role == UserRole.ADMIN:
            return True
        
        permission = f"{action}:{resource}"
        
        # Check specific permission
        if permission in self.permissions:
            return True
        
        # Check wildcard permissions
        if f"{action}:all" in self.permissions:
            return True
        
        if f"*:{resource}" in self.permissions:
            return True
        
        return False
    
    def can_manage_user(self, target_user: "User") -> bool:
        """
        Business rule: Check if can manage another user
        """
        if self.status != UserStatus.ACTIVE:
            return False
        
        # Admins can manage everyone
        if self.role == UserRole.ADMIN:
            return True
        
        # Users can only manage themselves
        return self.id == target_user.id
    
    def update_role(self, new_role: UserRole, updated_by: "User") -> None:
        """
        Business rule: Update user role
        """
        if not updated_by.can_manage_user(self):
            raise PermissionError(
                f"User {updated_by.username} cannot update role for {self.username}"
            )
        
        if self.id == updated_by.id and new_role != self.role:
            raise ValueError("Users cannot change their own role")
        
        self.role = new_role
        self.permissions = self._get_default_permissions(new_role)
        self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """
        Business rule: Activate user account
        """
        if self.status == UserStatus.SUSPENDED:
            raise ValueError("Suspended accounts must be unsuspended by admin")
        
        self.status = UserStatus.ACTIVE
        self.email_verified = True
        self.updated_at = datetime.utcnow()
    
    def suspend(self, reason: str, suspended_by: "User") -> None:
        """
        Business rule: Suspend user account
        """
        if not suspended_by.can_manage_user(self):
            raise PermissionError(
                f"User {suspended_by.username} cannot suspend {self.username}"
            )
        
        if self.id == suspended_by.id:
            raise ValueError("Users cannot suspend themselves")
        
        self.status = UserStatus.SUSPENDED
        self.metadata["suspension_reason"] = reason
        self.metadata["suspended_by"] = suspended_by.id
        self.metadata["suspended_at"] = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow()
    
    def update_last_login(self) -> None:
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def is_active(self) -> bool:
        """Check if user account is active"""
        return self.status == UserStatus.ACTIVE
    
    def verify_password(self, plain_password: str) -> bool:
        """
        Verify plain password against hashed password
        This is a placeholder - in real implementation, use PasswordService
        """
        # For testing purposes, we'll do a simple comparison
        # In production, this should use proper password hashing
        return plain_password == self.hashed_password
    
    def add_permission(self, permission: str, granted_by: "User") -> None:
        """
        Business rule: Add a permission to user
        """
        if not granted_by.role == UserRole.ADMIN:
            raise PermissionError("Only admins can grant permissions")
        
        if permission not in self.permissions:
            self.permissions.append(permission)
            self.updated_at = datetime.utcnow()
    
    def remove_permission(self, permission: str, revoked_by: "User") -> None:
        """
        Business rule: Remove a permission from user
        """
        if not revoked_by.role == UserRole.ADMIN:
            raise PermissionError("Only admins can revoke permissions")
        
        if permission in self.permissions:
            self.permissions.remove(permission)
            self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert to dictionary (for serialization)"""
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
            "role": self.role.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "email_verified": self.email_verified,
            "phone": self.phone,
            "department": self.department,
            "permissions": self.permissions,
        }
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)