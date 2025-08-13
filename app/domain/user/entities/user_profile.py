"""
User Profile Entity
Part of User Aggregate
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
import uuid


@dataclass
class UserProfile:
    """
    User Profile Entity
    Contains user's profile information
    """
    id: str
    user_id: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    skills: list = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    @classmethod
    def create_for_user(cls, user_id: str) -> "UserProfile":
        """Create default profile for new user"""
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            preferences={
                "theme": "light",
                "language": "vi",
                "notifications": {
                    "email": True,
                    "push": True
                }
            }
        )
    
    def update_basic_info(self, bio: Optional[str] = None, location: Optional[str] = None, 
                         website: Optional[str] = None, company: Optional[str] = None, 
                         job_title: Optional[str] = None) -> None:
        """Update basic profile information"""
        if bio is not None:
            self.bio = bio
        if location is not None:
            self.location = location
        if website is not None:
            self.website = website
        if company is not None:
            self.company = company
        if job_title is not None:
            self.job_title = job_title
        
        self.updated_at = datetime.utcnow()
    
    def update_avatar(self, avatar_url: str) -> None:
        """Update user avatar"""
        self.avatar_url = avatar_url
        self.updated_at = datetime.utcnow()
    
    def add_skill(self, skill: str) -> None:
        """Add skill to user profile"""
        if skill not in self.skills:
            self.skills.append(skill)
            self.updated_at = datetime.utcnow()
    
    def remove_skill(self, skill: str) -> None:
        """Remove skill from user profile"""
        if skill in self.skills:
            self.skills.remove(skill)
            self.updated_at = datetime.utcnow()
    
    def update_preferences(self, preferences: Dict[str, Any]) -> None:
        """Update user preferences"""
        self.preferences.update(preferences)
        self.updated_at = datetime.utcnow()
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get specific preference value"""
        return self.preferences.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "location": self.location,
            "website": self.website,
            "company": self.company,
            "job_title": self.job_title,
            "skills": self.skills,
            "preferences": self.preferences,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
