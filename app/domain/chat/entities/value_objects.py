"""
Chat Domain Value Objects
"""
from enum import Enum
from typing import Optional
from dataclasses import dataclass
from datetime import datetime


class MessageRole(str, Enum):
    """Message role enumeration"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageStatus(str, Enum):
    """Message status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class MessageContent:
    """Value object for message content"""
    text: str
    content_type: str = "text"
    
    def __post_init__(self):
        if not self.text or not self.text.strip():
            raise ValueError("Message content cannot be empty")
        if len(self.text) > 10000:  # 10KB limit
            raise ValueError("Message content too long")


@dataclass(frozen=True)
class ChatContext:
    """Value object for chat context"""
    session_id: str
    user_id: str
    metadata: dict = None
    
    def __post_init__(self):
        if not self.session_id:
            raise ValueError("Session ID is required")
        if not self.user_id:
            raise ValueError("User ID is required")
        if self.metadata is None:
            object.__setattr__(self, 'metadata', {})
