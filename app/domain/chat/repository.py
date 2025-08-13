"""
Chat Repository Interface
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from .entities import ChatSession, ChatMessage


class ChatRepository(ABC):
    """Abstract Chat Repository interface"""
    
    @abstractmethod
    async def save_session(self, session: ChatSession) -> ChatSession:
        """Save chat session"""
        pass
    
    @abstractmethod
    async def find_session_by_id(self, session_id: str) -> Optional[ChatSession]:
        """Find chat session by ID"""
        pass
    
    @abstractmethod
    async def find_sessions_by_user_id(self, user_id: str, 
                                     limit: Optional[int] = None,
                                     offset: Optional[int] = None) -> List[ChatSession]:
        """Find chat sessions by user ID"""
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """Delete chat session"""
        pass
    
    @abstractmethod
    async def save_message(self, message: ChatMessage) -> ChatMessage:
        """Save chat message"""
        pass
    
    @abstractmethod
    async def find_messages_by_session_id(self, session_id: str,
                                        limit: Optional[int] = None,
                                        offset: Optional[int] = None) -> List[ChatMessage]:
        """Find messages by session ID"""
        pass
    
    @abstractmethod
    async def find_message_by_id(self, message_id: str) -> Optional[ChatMessage]:
        """Find message by ID"""
        pass
    
    @abstractmethod
    async def update_message_status(self, message_id: str, status: str) -> bool:
        """Update message status"""
        pass
    
    @abstractmethod
    async def get_session_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get chat statistics for user"""
        pass
    
    @abstractmethod
    async def search_sessions(self, user_id: str, query: str) -> List[ChatSession]:
        """Search sessions by content"""
        pass
    
    @abstractmethod
    async def get_active_sessions_count(self, user_id: str) -> int:
        """Get count of active sessions for user"""
        pass
    
    @abstractmethod
    async def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """Clean up old inactive sessions"""
        pass
