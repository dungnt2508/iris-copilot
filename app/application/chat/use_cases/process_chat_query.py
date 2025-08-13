"""
Process Chat Query Use Case
"""
import time
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from app.domain.chat.repository import ChatRepository
from app.domain.document.repository import DocumentRepository
from app.domain.embedding.repository import EmbeddingRepository
from app.services.llm_service import LLMService
from app.services.search_service import SearchService
from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ProcessChatQueryRequest:
    """Request for processing chat query"""
    user_id: str
    query: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    use_rag: bool = True
    max_sources: int = 5


@dataclass
class ProcessChatQueryResponse:
    """Response from processing chat query"""
    answer: str
    session_id: str
    message_id: str
    sources: List[Dict[str, Any]]
    confidence: float
    processing_time_ms: int
    tokens_used: int
    model_used: str


class ProcessChatQueryUseCase:
    """Use case for processing chat queries with RAG"""
    
    def __init__(self,
                 chat_repository: ChatRepository,
                 document_repository: DocumentRepository,
                 embedding_repository: EmbeddingRepository,
                 llm_service: LLMService,
                 search_service: SearchService):
        self.chat_repo = chat_repository
        self.document_repo = document_repository
        self.embedding_repo = embedding_repository
        self.llm_service = llm_service
        self.search_service = search_service
    
    async def execute(self, request: ProcessChatQueryRequest) -> ProcessChatQueryResponse:
        """Execute the use case"""
        start_time = time.time()
        
        try:
            # 1. Get or create chat session
            session = await self._get_or_create_session(request.user_id, request.session_id)
            
            # 2. Add user message to session
            user_message = session.add_user_message(
                content=request.query,
                metadata=request.context or {}
            )
            
            # 3. Save user message
            await self.chat_repo.save_message(user_message)
            
            # 4. Process query based on mode
            if request.use_rag:
                response = await self._process_rag_query(request, session)
            else:
                response = await self._process_simple_query(request, session)
            
            # 5. Add assistant message to session
            assistant_message = session.add_assistant_message(
                content=response.answer,
                sources=response.sources,
                metadata={
                    "confidence": response.confidence,
                    "tokens_used": response.tokens_used,
                    "model_used": response.model_used,
                    "processing_time_ms": response.processing_time_ms
                }
            )
            
            # 6. Save assistant message and session
            await self.chat_repo.save_message(assistant_message)
            await self.chat_repo.save_session(session)
            
            # 7. Calculate total processing time
            total_processing_time = int((time.time() - start_time) * 1000)
            
            return ProcessChatQueryResponse(
                answer=response.answer,
                session_id=session.id,
                message_id=assistant_message.id,
                sources=response.sources,
                confidence=response.confidence,
                processing_time_ms=total_processing_time,
                tokens_used=response.tokens_used,
                model_used=response.model_used
            )
            
        except Exception as e:
            logger.error(f"Error processing chat query: {str(e)}")
            raise
    
    async def _get_or_create_session(self, user_id: str, session_id: Optional[str] = None) -> "ChatSession":
        """Get existing session or create new one"""
        if session_id:
            session = await self.chat_repo.find_session_by_id(session_id)
            if session and session.user_id == user_id:
                return session
        
        # Create new session
        from app.domain.chat.entities import ChatSession
        session = ChatSession.create(
            user_id=user_id,
            title=f"Chat session - {time.strftime('%Y-%m-%d %H:%M')}",
            metadata={"created_from": "chat_query"}
        )
        
        return session
    
    async def _process_rag_query(self, request: ProcessChatQueryRequest, session: "ChatSession") -> "ProcessChatQueryResponse":
        """Process query using RAG (Retrieval-Augmented Generation)"""
        
        # 1. Generate embedding for user query
        query_embedding = await self.llm_service.generate_embedding(request.query)
        
        # 2. Search for relevant documents
        search_results = await self.search_service.semantic_search(
            query_embedding=query_embedding,
            user_id=request.user_id,
            limit=request.max_sources,
            threshold=0.7
        )
        
        # 3. Prepare context from search results
        relevant_documents = []
        for result in search_results:
            relevant_documents.append({
                "title": result.get("title", "Unknown"),
                "content": result.get("content", ""),
                "score": result.get("score", 0),
                "source_type": result.get("source_type", "document"),
                "source_id": result.get("source_id", "")
            })
        
        # 4. Generate RAG response
        llm_response = await self.llm_service.generate_rag_response(
            user_query=request.query,
            relevant_documents=relevant_documents,
            system_prompt="Bạn là một trợ lý AI hữu ích, chuyên về việc trả lời câu hỏi dựa trên tài liệu được cung cấp. Hãy trả lời một cách chính xác và chi tiết."
        )
        
        # 5. Calculate confidence based on search results
        confidence = self._calculate_confidence(relevant_documents, llm_response)
        
        return ProcessChatQueryResponse(
            answer=llm_response.content,
            session_id=session.id,
            message_id="",  # Will be set later
            sources=relevant_documents,
            confidence=confidence,
            processing_time_ms=llm_response.processing_time_ms,
            tokens_used=llm_response.tokens_used,
            model_used=llm_response.model_used
        )
    
    async def _process_simple_query(self, request: ProcessChatQueryRequest, session: "ChatSession") -> "ProcessChatQueryResponse":
        """Process query using simple chat (no RAG)"""
        
        # Get conversation history
        conversation_history = session.get_conversation_history(limit=10)
        
        # Generate chat response
        llm_response = await self.llm_service.generate_chat_response(
            user_message=request.query,
            conversation_history=conversation_history,
            system_prompt="Bạn là một trợ lý AI hữu ích và thân thiện."
        )
        
        return ProcessChatQueryResponse(
            answer=llm_response.content,
            session_id=session.id,
            message_id="",  # Will be set later
            sources=[],
            confidence=0.8,  # Default confidence for simple chat
            processing_time_ms=llm_response.processing_time_ms,
            tokens_used=llm_response.tokens_used,
            model_used=llm_response.model_used
        )
    
    def _calculate_confidence(self, relevant_documents: List[Dict[str, Any]], 
                            llm_response: "LLMResponse") -> float:
        """Calculate confidence score based on search results and response"""
        if not relevant_documents:
            return 0.3  # Low confidence if no relevant documents
        
        # Calculate average relevance score
        avg_score = sum(doc.get("score", 0) for doc in relevant_documents) / len(relevant_documents)
        
        # Base confidence on relevance score
        confidence = min(avg_score * 1.2, 0.95)  # Cap at 0.95
        
        # Adjust based on number of sources
        if len(relevant_documents) >= 3:
            confidence += 0.05
        elif len(relevant_documents) == 0:
            confidence -= 0.2
        
        return max(confidence, 0.1)  # Minimum confidence of 0.1
