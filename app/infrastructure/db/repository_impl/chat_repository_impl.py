"""
Chat Repository Implementation
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload

from app.domain.chat.repository import ChatRepository
from app.domain.chat.entities import ChatSession as ChatSessionEntity, ChatMessage as ChatMessageEntity
from app.domain.chat.entities.value_objects import MessageRole, MessageStatus, MessageContent
from app.infrastructure.db.models.chat import ChatSession, ChatMessage
from app.core.logger import get_logger

logger = get_logger(__name__)


class SQLAlchemyChatRepository(ChatRepository):
    """SQLAlchemy implementation of ChatRepository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save_session(self, session: ChatSessionEntity) -> ChatSessionEntity:
        """Save chat session"""
        try:
            # Convert domain entity to ORM model
            db_session = ChatSession(
                id=session.id,
                user_id=session.user_id,
                title=session.title,
                created_at=session.created_at,
                updated_at=session.updated_at,
                chat_metadata=session.metadata,
                is_active=session.is_active,
                max_messages=session.max_messages
            )
            
            # Add messages if any
            for message in session.messages:
                db_message = ChatMessage(
                    id=message.id,
                    session_id=message.session_id,
                    content=message.content.text,
                    role=message.role.value,
                    status=message.status.value,
                    created_at=message.created_at,
                    updated_at=message.updated_at,
                    message_metadata=message.metadata,
                    sources=message.sources,
                    tokens_used=message.tokens_used,
                    model_used=message.model_used,
                    response_time_ms=message.response_time_ms
                )
                db_session.messages.append(db_message)
            
            self.session.add(db_session)
            await self.session.commit()
            await self.session.refresh(db_session)
            
            return self._to_domain_session(db_session)
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error saving chat session: {str(e)}")
            raise
    
    async def find_session_by_id(self, session_id: str) -> Optional[ChatSessionEntity]:
        """Find chat session by ID"""
        try:
            stmt = select(ChatSession).options(
                selectinload(ChatSession.messages)
            ).where(ChatSession.id == session_id)
            
            result = await self.session.execute(stmt)
            db_session = result.scalar_one_or_none()
            
            if db_session:
                return self._to_domain_session(db_session)
            return None
            
        except Exception as e:
            logger.error(f"Error finding chat session: {str(e)}")
            raise
    
    async def find_sessions_by_user_id(self, user_id: str, 
                                     limit: Optional[int] = None,
                                     offset: Optional[int] = None) -> List[ChatSessionEntity]:
        """Find chat sessions by user ID"""
        try:
            stmt = select(ChatSession).options(
                selectinload(ChatSession.messages)
            ).where(
                and_(
                    ChatSession.user_id == user_id,
                    ChatSession.is_active == True
                )
            ).order_by(desc(ChatSession.updated_at))
            
            if offset:
                stmt = stmt.offset(offset)
            if limit:
                stmt = stmt.limit(limit)
            
            result = await self.session.execute(stmt)
            db_sessions = result.scalars().all()
            
            return [self._to_domain_session(session) for session in db_sessions]
            
        except Exception as e:
            logger.error(f"Error finding chat sessions: {str(e)}")
            raise
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete chat session"""
        try:
            stmt = select(ChatSession).where(ChatSession.id == session_id)
            result = await self.session.execute(stmt)
            db_session = result.scalar_one_or_none()
            
            if db_session:
                await self.session.delete(db_session)
                await self.session.commit()
                return True
            return False
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting chat session: {str(e)}")
            raise
    
    async def save_message(self, message: ChatMessageEntity) -> ChatMessageEntity:
        """Save chat message"""
        try:
            db_message = ChatMessage(
                id=message.id,
                session_id=message.session_id,
                content=message.content.text,
                role=message.role.value,
                status=message.status.value,
                created_at=message.created_at,
                updated_at=message.updated_at,
                message_metadata=message.metadata,
                sources=message.sources,
                tokens_used=message.tokens_used,
                model_used=message.model_used,
                response_time_ms=message.response_time_ms
            )
            
            self.session.add(db_message)
            await self.session.commit()
            await self.session.refresh(db_message)
            
            return self._to_domain_message(db_message)
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error saving chat message: {str(e)}")
            raise
    
    async def find_messages_by_session_id(self, session_id: str,
                                        limit: Optional[int] = None,
                                        offset: Optional[int] = None) -> List[ChatMessageEntity]:
        """Find messages by session ID"""
        try:
            stmt = select(ChatMessage).where(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.created_at)
            
            if offset:
                stmt = stmt.offset(offset)
            if limit:
                stmt = stmt.limit(limit)
            
            result = await self.session.execute(stmt)
            db_messages = result.scalars().all()
            
            return [self._to_domain_message(message) for message in db_messages]
            
        except Exception as e:
            logger.error(f"Error finding chat messages: {str(e)}")
            raise
    
    async def find_message_by_id(self, message_id: str) -> Optional[ChatMessageEntity]:
        """Find message by ID"""
        try:
            stmt = select(ChatMessage).where(ChatMessage.id == message_id)
            result = await self.session.execute(stmt)
            db_message = result.scalar_one_or_none()
            
            if db_message:
                return self._to_domain_message(db_message)
            return None
            
        except Exception as e:
            logger.error(f"Error finding chat message: {str(e)}")
            raise
    
    async def update_message_status(self, message_id: str, status: str) -> bool:
        """Update message status"""
        try:
            stmt = select(ChatMessage).where(ChatMessage.id == message_id)
            result = await self.session.execute(stmt)
            db_message = result.scalar_one_or_none()
            
            if db_message:
                db_message.status = status
                db_message.updated_at = datetime.utcnow()
                await self.session.commit()
                return True
            return False
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating message status: {str(e)}")
            raise
    
    async def get_session_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get chat statistics for user"""
        try:
            # Count sessions
            stmt = select(ChatSession).where(
                and_(
                    ChatSession.user_id == user_id,
                    ChatSession.is_active == True
                )
            )
            result = await self.session.execute(stmt)
            sessions = result.scalars().all()
            
            total_sessions = len(sessions)
            total_messages = sum(len(session.messages) for session in sessions)
            total_tokens = sum(
                sum(msg.tokens_used or 0 for msg in session.messages)
                for session in sessions
            )
            
            return {
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "total_tokens": total_tokens,
                "avg_messages_per_session": total_messages / total_sessions if total_sessions > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting session statistics: {str(e)}")
            raise
    
    async def search_sessions(self, user_id: str, query: str) -> List[ChatSessionEntity]:
        """Search sessions by content"""
        try:
            # Search in session titles and message content
            stmt = select(ChatSession).options(
                selectinload(ChatSession.messages)
            ).where(
                and_(
                    ChatSession.user_id == user_id,
                    ChatSession.is_active == True,
                    ChatSession.title.ilike(f"%{query}%")
                )
            ).order_by(desc(ChatSession.updated_at))
            
            result = await self.session.execute(stmt)
            db_sessions = result.scalars().all()
            
            return [self._to_domain_session(session) for session in db_sessions]
            
        except Exception as e:
            logger.error(f"Error searching sessions: {str(e)}")
            raise
    
    async def get_active_sessions_count(self, user_id: str) -> int:
        """Get count of active sessions for user"""
        try:
            stmt = select(ChatSession).where(
                and_(
                    ChatSession.user_id == user_id,
                    ChatSession.is_active == True
                )
            )
            result = await self.session.execute(stmt)
            return len(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Error getting active sessions count: {str(e)}")
            raise
    
    async def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """Clean up old inactive sessions"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            stmt = select(ChatSession).where(
                and_(
                    ChatSession.is_active == False,
                    ChatSession.updated_at < cutoff_date
                )
            )
            result = await self.session.execute(stmt)
            old_sessions = result.scalars().all()
            
            count = len(old_sessions)
            for session in old_sessions:
                await self.session.delete(session)
            
            await self.session.commit()
            return count
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error cleaning up old sessions: {str(e)}")
            raise
    
    def _to_domain_session(self, db_session: ChatSession) -> ChatSessionEntity:
        """Convert ORM model to domain entity"""
        messages = [self._to_domain_message(msg) for msg in db_session.messages]
        
        return ChatSessionEntity(
            id=str(db_session.id),
            user_id=str(db_session.user_id),
            title=db_session.title,
            messages=messages,
            created_at=db_session.created_at,
            updated_at=db_session.updated_at,
            metadata=db_session.chat_metadata,
            is_active=db_session.is_active,
            max_messages=db_session.max_messages
        )
    
    def _to_domain_message(self, db_message: ChatMessage) -> ChatMessageEntity:
        """Convert ORM model to domain entity"""
        return ChatMessageEntity(
            id=str(db_message.id),
            session_id=str(db_message.session_id),
            content=MessageContent(text=db_message.content),
            role=MessageRole(db_message.role),
            status=MessageStatus(db_message.status),
            created_at=db_message.created_at,
            updated_at=db_message.updated_at,
            metadata=db_message.message_metadata,
            sources=db_message.sources,
            tokens_used=db_message.tokens_used,
            model_used=db_message.model_used,
            response_time_ms=db_message.response_time_ms
        )
