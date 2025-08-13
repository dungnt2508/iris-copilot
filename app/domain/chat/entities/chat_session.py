"""
Chat Session Entity
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any

from .chat_message import ChatMessage
from .value_objects import MessageRole


@dataclass
class ChatSession:
    """
    Chat Session Entity
    Represents a chat conversation session
    """
    id: str
    user_id: str
    title: str
    messages: List[ChatMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Optional fields
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    max_messages: int = 100  # Limit to prevent memory issues
    
    def __post_init__(self):
        """Validate entity after creation"""
        if not self.id:
            raise ValueError("Session ID is required")
        if not self.user_id:
            raise ValueError("User ID is required")
        if not self.title or not self.title.strip():
            raise ValueError("Session title is required")
    
    @classmethod
    def create(cls, user_id: str, title: str, metadata: Dict[str, Any] = None) -> "ChatSession":
        """Factory method to create a new chat session"""
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            metadata=metadata or {}
        )
    
    def add_message(self, message: ChatMessage) -> None:
        """Add a message to the session"""
        if not message.session_id == self.id:
            raise ValueError("Message session ID must match session ID")
        
        # Check message limit
        if len(self.messages) >= self.max_messages:
            # Remove oldest message to make room
            self.messages.pop(0)
        
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
        
        # Update session title if it's the first user message
        if len(self.messages) == 1 and message.is_user_message():
            self.title = message.content.text[:50] + "..." if len(message.content.text) > 50 else message.content.text
    
    def add_user_message(self, content: str, metadata: Dict[str, Any] = None) -> ChatMessage:
        """Add a user message to the session"""
        message = ChatMessage.create_user_message(
            session_id=self.id,
            content=content,
            metadata=metadata
        )
        self.add_message(message)
        return message
    
    def add_assistant_message(self, content: str, sources: List[Dict[str, Any]] = None,
                            metadata: Dict[str, Any] = None) -> ChatMessage:
        """Add an assistant message to the session"""
        message = ChatMessage.create_assistant_message(
            session_id=self.id,
            content=content,
            sources=sources,
            metadata=metadata
        )
        self.add_message(message)
        return message
    
    def add_system_message(self, content: str) -> ChatMessage:
        """Add a system message to the session"""
        message = ChatMessage.create_system_message(
            session_id=self.id,
            content=content
        )
        self.add_message(message)
        return message
    
    def get_last_message(self) -> Optional[ChatMessage]:
        """Get the last message in the session"""
        return self.messages[-1] if self.messages else None
    
    def get_user_messages(self) -> List[ChatMessage]:
        """Get all user messages in the session"""
        return [msg for msg in self.messages if msg.is_user_message()]
    
    def get_assistant_messages(self) -> List[ChatMessage]:
        """Get all assistant messages in the session"""
        return [msg for msg in self.messages if msg.is_assistant_message()]
    
    def get_conversation_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get conversation history for LLM context"""
        messages = self.messages[-limit:] if limit else self.messages
        return [
            {
                "role": msg.role.value,
                "content": msg.content.text
            }
            for msg in messages
        ]
    
    def get_recent_messages(self, count: int = 10) -> List[ChatMessage]:
        """Get recent messages from the session"""
        return self.messages[-count:] if self.messages else []
    
    def clear_messages(self) -> None:
        """Clear all messages from the session"""
        self.messages.clear()
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Deactivate the session"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """Activate the session"""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def update_title(self, new_title: str) -> None:
        """Update session title"""
        if not new_title or not new_title.strip():
            raise ValueError("Session title cannot be empty")
        self.title = new_title
        self.updated_at = datetime.utcnow()
    
    def update_metadata(self, key: str, value: Any) -> None:
        """Update session metadata"""
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()
    
    def get_message_count(self) -> int:
        """Get total number of messages in session"""
        return len(self.messages)
    
    def get_token_count(self) -> int:
        """Get total tokens used in session"""
        return sum(msg.tokens_used or 0 for msg in self.messages)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "is_active": self.is_active,
            "message_count": self.get_message_count(),
            "token_count": self.get_token_count(),
            "messages": [msg.to_dict() for msg in self.messages]
        }
    
    def is_empty(self) -> bool:
        """Check if session has no messages"""
        return len(self.messages) == 0
    
    def has_user_messages(self) -> bool:
        """Check if session has user messages"""
        return any(msg.is_user_message() for msg in self.messages)
    
    def has_assistant_messages(self) -> bool:
        """Check if session has assistant messages"""
        return any(msg.is_assistant_message() for msg in self.messages)
