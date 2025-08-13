"""
User Permission Entity
Part of User Aggregate
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum
import uuid


class PermissionType(Enum):
    """Permission types"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


class PermissionScope(Enum):
    """Permission scopes"""
    DOCUMENTS = "documents"
    USERS = "users"
    CHAT = "chat"
    ANALYTICS = "analytics"
    SYSTEM = "system"


@dataclass
class Permission:
    """
    User Permission Entity
    Defines user permissions and access rights
    """
    id: str
    user_id: str
    name: str
    type: PermissionType
    scope: PermissionScope
    resource: Optional[str] = None
    conditions: dict = field(default_factory=dict)
    granted_at: datetime = field(default_factory=datetime.utcnow)
    granted_by: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True
    
    @classmethod
    def create(cls, user_id: str, name: str, type: PermissionType, 
               scope: PermissionScope, resource: Optional[str] = None,
               granted_by: Optional[str] = None) -> "Permission":
        """Create new permission"""
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            type=type,
            scope=scope,
            resource=resource,
            granted_by=granted_by
        )
    
    def is_expired(self) -> bool:
        """Check if permission is expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if permission is valid (active and not expired)"""
        return self.is_active and not self.is_expired()
    
    def deactivate(self) -> None:
        """Deactivate permission"""
        self.is_active = False
    
    def extend(self, days: int) -> None:
        """Extend permission expiration"""
        if self.expires_at:
            self.expires_at = self.expires_at.replace(
                day=self.expires_at.day + days
            )
        else:
            self.expires_at = datetime.utcnow().replace(
                day=datetime.utcnow().day + days
            )
    
    def matches(self, required_name: str, required_type: PermissionType, 
                required_scope: PermissionScope, resource: Optional[str] = None) -> bool:
        """Check if permission matches required criteria"""
        if not self.is_valid():
            return False
        
        # Check name, type, and scope
        if (self.name != required_name or 
            self.type != required_type or 
            self.scope != required_scope):
            return False
        
        # Check resource if specified
        if resource and self.resource and self.resource != resource:
            return False
        
        return True
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "type": self.type.value,
            "scope": self.scope.value,
            "resource": self.resource,
            "conditions": self.conditions,
            "granted_at": self.granted_at.isoformat(),
            "granted_by": self.granted_by,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
            "is_valid": self.is_valid()
        }


# Predefined permissions
class Permissions:
    """Predefined permission constants"""
    
    # Document permissions
    READ_DOCUMENTS = "read:documents"
    WRITE_DOCUMENTS = "write:documents"
    DELETE_DOCUMENTS = "delete:documents"
    UPLOAD_DOCUMENTS = "upload:documents"
    
    # User permissions
    READ_USERS = "read:users"
    WRITE_USERS = "write:users"
    DELETE_USERS = "delete:users"
    MANAGE_USERS = "manage:users"
    
    # Chat permissions
    USE_CHAT = "use:chat"
    MANAGE_CHAT = "manage:chat"
    
    # Analytics permissions
    VIEW_ANALYTICS = "view:analytics"
    EXPORT_ANALYTICS = "export:analytics"
    
    # System permissions
    SYSTEM_ADMIN = "system:admin"
    CONFIG_SYSTEM = "config:system"


def get_default_permissions(role: str) -> List[Permission]:
    """Get default permissions for user role"""
    permissions = []
    
    if role == "admin":
        # Admin gets all permissions
        for permission_name in [
            Permissions.READ_DOCUMENTS, Permissions.WRITE_DOCUMENTS,
            Permissions.DELETE_DOCUMENTS, Permissions.UPLOAD_DOCUMENTS,
            Permissions.READ_USERS, Permissions.WRITE_USERS,
            Permissions.DELETE_USERS, Permissions.MANAGE_USERS,
            Permissions.USE_CHAT, Permissions.MANAGE_CHAT,
            Permissions.VIEW_ANALYTICS, Permissions.EXPORT_ANALYTICS,
            Permissions.SYSTEM_ADMIN, Permissions.CONFIG_SYSTEM
        ]:
            permissions.append(Permission.create(
                user_id="",  # Will be set when creating user
                name=permission_name,
                type=PermissionType.ADMIN if "admin" in permission_name else PermissionType.READ,
                scope=PermissionScope.SYSTEM if "system" in permission_name else PermissionScope.DOCUMENTS
            ))
    
    elif role == "manager":
        # Manager gets most permissions except system admin
        for permission_name in [
            Permissions.READ_DOCUMENTS, Permissions.WRITE_DOCUMENTS,
            Permissions.DELETE_DOCUMENTS, Permissions.UPLOAD_DOCUMENTS,
            Permissions.READ_USERS, Permissions.WRITE_USERS,
            Permissions.USE_CHAT, Permissions.MANAGE_CHAT,
            Permissions.VIEW_ANALYTICS, Permissions.EXPORT_ANALYTICS
        ]:
            permissions.append(Permission.create(
                user_id="",
                name=permission_name,
                type=PermissionType.WRITE if "write" in permission_name or "manage" in permission_name else PermissionType.READ,
                scope=PermissionScope.DOCUMENTS
            ))
    
    else:  # user role
        # Regular user gets basic permissions
        for permission_name in [
            Permissions.READ_DOCUMENTS, Permissions.UPLOAD_DOCUMENTS,
            Permissions.USE_CHAT
        ]:
            permissions.append(Permission.create(
                user_id="",
                name=permission_name,
                type=PermissionType.READ,
                scope=PermissionScope.DOCUMENTS
            ))
    
    return permissions
