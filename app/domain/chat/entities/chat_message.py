"""
Chat Message Entity
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

from .value_objects import MessageRole, MessageStatus, MessageContent


@dataclass
class ChatMessage:
    """
    Chat Message Entity
    Represents a single message in a chat conversation
    """
    id: str
    session_id: str
    content: MessageContent
    role: MessageRole
    status: MessageStatus = MessageStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Optional fields
    metadata: Dict[str, Any] = field(default_factory=dict)
    sources: List[Dict[str, Any]] = field(default_factory=list)
    tokens_used: Optional[int] = None
    model_used: Optional[str] = None
    response_time_ms: Optional[int] = None
    
    def __post_init__(self):
        """Validate entity after creation"""
        if not self.id:
            raise ValueError("Message ID is required")
        if not self.session_id:
            raise ValueError("Session ID is required")
    
    @classmethod
    def create_user_message(cls, session_id: str, content: str, metadata: Dict[str, Any] = None) -> "ChatMessage":
        """Factory method to create a user message"""
        return cls(
            id=str(uuid.uuid4()),
            session_id=session_id,
            content=MessageContent(text=content),
            role=MessageRole.USER,
            metadata=metadata or {}
        )
    
    @classmethod
    def create_assistant_message(cls, session_id: str, content: str, 
                               sources: List[Dict[str, Any]] = None,
                               metadata: Dict[str, Any] = None) -> "ChatMessage":
        """Factory method to create an assistant message"""
        return cls(
            id=str(uuid.uuid4()),
            session_id=session_id,
            content=MessageContent(text=content),
            role=MessageRole.ASSISTANT,
            status=MessageStatus.COMPLETED,
            sources=sources or [],
            metadata=metadata or {}
        )
    
    @classmethod
    def create_system_message(cls, session_id: str, content: str) -> "ChatMessage":
        """Factory method to create a system message"""
        return cls(
            id=str(uuid.uuid4()),
            session_id=session_id,
            content=MessageContent(text=content),
            role=MessageRole.SYSTEM,
            status=MessageStatus.COMPLETED
        )
    
    def mark_processing(self) -> None:
        """Mark message as processing"""
        self.status = MessageStatus.PROCESSING
        self.updated_at = datetime.utcnow()
    
    def mark_completed(self, tokens_used: Optional[int] = None, 
                      model_used: Optional[str] = None,
                      response_time_ms: Optional[int] = None) -> None:
        """Mark message as completed"""
        self.status = MessageStatus.COMPLETED
        self.tokens_used = tokens_used
        self.model_used = model_used
        self.response_time_ms = response_time_ms
        self.updated_at = datetime.utcnow()
    
    def mark_failed(self, error_message: str = None) -> None:
        """Mark message as failed"""
        self.status = MessageStatus.FAILED
        if error_message:
            self.metadata["error"] = error_message
        self.updated_at = datetime.utcnow()
    
    def add_source(self, source: Dict[str, Any]) -> None:
        """Add a source reference to the message"""
        if not source.get("id") or not source.get("title"):
            raise ValueError("Source must have id and title")
        self.sources.append(source)
        self.updated_at = datetime.utcnow()
    
    def update_metadata(self, key: str, value: Any) -> None:
        """Update message metadata"""
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "content": self.content.text,
            "role": self.role.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "sources": self.sources,
            "tokens_used": self.tokens_used,
            "model_used": self.model_used,
            "response_time_ms": self.response_time_ms
        }
    
    def is_user_message(self) -> bool:
        """Check if message is from user"""
        return self.role == MessageRole.USER
    
    def is_assistant_message(self) -> bool:
        """Check if message is from assistant"""
        return self.role == MessageRole.ASSISTANT
    
    def is_system_message(self) -> bool:
        """Check if message is system message"""
        return self.role == MessageRole.SYSTEM
    
    def is_completed(self) -> bool:
        """Check if message processing is completed"""
        return self.status == MessageStatus.COMPLETED
    
    def is_failed(self) -> bool:
        """Check if message processing failed"""
        return self.status == MessageStatus.FAILED
