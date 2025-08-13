"""
LLM Service - Orchestration layer for Language Model operations
"""
import asyncio
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from app.adapters.openai_adapter import OpenAIAdapter
from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class LLMRequest:
    """Request for LLM operation"""
    prompt: str
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    system_message: Optional[str] = None
    context: Optional[List[Dict[str, str]]] = None


@dataclass
class LLMResponse:
    """Response from LLM operation"""
    content: str
    model_used: str
    tokens_used: int
    processing_time_ms: int
    metadata: Dict[str, Any]


class LLMService:
    """Service for orchestrating LLM operations"""
    
    def __init__(self, openai_adapter: OpenAIAdapter):
        self.openai_adapter = openai_adapter
        self.default_model = "gpt-4"
        self.default_temperature = 0.7
    
    async def generate_completion(self, request: LLMRequest) -> LLMResponse:
        """Generate text completion using LLM"""
        start_time = time.time()
        
        try:
            # Prepare messages
            messages = []
            
            # Add system message if provided
            if request.system_message:
                messages.append({
                    "role": "system",
                    "content": request.system_message
                })
            
            # Add context messages if provided
            if request.context:
                messages.extend(request.context)
            
            # Add user prompt
            messages.append({
                "role": "user",
                "content": request.prompt
            })
            
            # Generate completion
            response = await self.openai_adapter.generate_completion(
                messages=messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return LLMResponse(
                content=response["content"],
                model_used=request.model,
                tokens_used=response.get("tokens_used", 0),
                processing_time_ms=processing_time,
                metadata=response.get("metadata", {})
            )
            
        except Exception as e:
            logger.error(f"Error generating completion: {str(e)}")
            raise
    
    async def generate_chat_response(self, user_message: str, 
                                   conversation_history: List[Dict[str, str]] = None,
                                   system_prompt: str = None,
                                   model: str = None) -> LLMResponse:
        """Generate chat response for conversation"""
        request = LLMRequest(
            prompt=user_message,
            model=model or self.default_model,
            temperature=0.7,
            system_message=system_prompt,
            context=conversation_history
        )
        
        return await self.generate_completion(request)
    
    async def generate_rag_response(self, user_query: str,
                                  relevant_documents: List[Dict[str, Any]],
                                  system_prompt: str = None,
                                  model: str = None) -> LLMResponse:
        """Generate RAG (Retrieval-Augmented Generation) response"""
        
        # Build context from relevant documents
        context = self._build_document_context(relevant_documents)
        
        # Create enhanced prompt
        enhanced_prompt = f"""
Dựa trên các tài liệu sau đây, hãy trả lời câu hỏi của người dùng một cách chính xác và chi tiết:

TÀI LIỆU THAM KHẢO:
{context}

CÂU HỎI: {user_query}

Hãy trả lời dựa trên thông tin trong tài liệu. Nếu không tìm thấy thông tin phù hợp, hãy nói rõ điều đó.
"""
        
        request = LLMRequest(
            prompt=enhanced_prompt,
            model=model or self.default_model,
            temperature=0.3,  # Lower temperature for more factual responses
            system_message=system_prompt or "Bạn là một trợ lý AI hữu ích, chuyên về việc trả lời câu hỏi dựa trên tài liệu được cung cấp."
        )
        
        return await self.generate_completion(request)
    
    async def generate_summary(self, text: str, 
                             max_length: int = 200,
                             model: str = None) -> LLMResponse:
        """Generate summary of text"""
        prompt = f"""
Hãy tóm tắt đoạn văn bản sau đây trong khoảng {max_length} từ:

{text}

Tóm tắt:
"""
        
        request = LLMRequest(
            prompt=prompt,
            model=model or self.default_model,
            temperature=0.3,
            max_tokens=max_length * 2  # Approximate token count
        )
        
        return await self.generate_completion(request)
    
    async def generate_embedding(self, text: str, model: str = "text-embedding-ada-002") -> List[float]:
        """Generate embedding for text"""
        try:
            embedding = await self.openai_adapter.generate_embedding(text, model)
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    async def generate_embeddings_batch(self, texts: List[str], 
                                      model: str = "text-embedding-ada-002") -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        try:
            embeddings = await self.openai_adapter.generate_embeddings_batch(texts, model)
            return embeddings
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            raise
    
    def _build_document_context(self, documents: List[Dict[str, Any]]) -> str:
        """Build context string from relevant documents"""
        context_parts = []
        
        for i, doc in enumerate(documents, 1):
            title = doc.get("title", f"Tài liệu {i}")
            content = doc.get("content", "")
            score = doc.get("score", 0)
            
            context_parts.append(f"""
{i}. {title} (Độ liên quan: {score:.2f})
Nội dung: {content}
---""")
        
        return "\n".join(context_parts)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check LLM service health"""
        try:
            # Simple test with a short prompt
            request = LLMRequest(
                prompt="Hello",
                model=self.default_model,
                max_tokens=10
            )
            
            response = await self.generate_completion(request)
            
            return {
                "status": "healthy",
                "model": self.default_model,
                "response_time_ms": response.processing_time_ms,
                "tokens_used": response.tokens_used
            }
            
        except Exception as e:
            logger.error(f"LLM service health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
