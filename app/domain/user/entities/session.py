"""
User Session Entity
Part of User Aggregate
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import uuid


@dataclass
class Session:
    """
    User Session Entity
    Manages user authentication sessions
    """
    id: str
    user_id: str
    token: str
    refresh_token: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool = True
    expires_at: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    
    @classmethod
    def create_for_user(cls, user_id: str, token: str, refresh_token: Optional[str] = None,
                       device_info: Optional[Dict[str, Any]] = None, 
                       ip_address: Optional[str] = None,
                       user_agent: Optional[str] = None,
                       expires_in_hours: int = 24) -> "Session":
        """Create new session for user"""
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            token=token,
            refresh_token=refresh_token,
            device_info=device_info or {},
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(hours=expires_in_hours),
            last_activity=datetime.utcnow()
        )
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if session is valid (active and not expired)"""
        return self.is_active and not self.is_expired()
    
    def refresh(self, new_token: str, new_refresh_token: Optional[str] = None,
                expires_in_hours: int = 24) -> None:
        """Refresh session with new tokens"""
        self.token = new_token
        if new_refresh_token:
            self.refresh_token = new_refresh_token
        self.expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        self.last_activity = datetime.utcnow()
    
    def update_activity(self) -> None:
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Deactivate session"""
        self.is_active = False
    
    def update_device_info(self, device_info: Dict[str, Any]) -> None:
        """Update device information"""
        self.device_info.update(device_info)
        self.last_activity = datetime.utcnow()
    
    def get_remaining_time(self) -> timedelta:
        """Get remaining time until expiration"""
        return self.expires_at - datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "token": self.token,
            "refresh_token": self.refresh_token,
            "device_info": self.device_info,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "is_active": self.is_active,
            "expires_at": self.expires_at.isoformat(),
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "remaining_time": self.get_remaining_time().total_seconds()
        }
