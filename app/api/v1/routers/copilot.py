"""
Copilot Plugin API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.wiring import get_process_chat_query_use_case, get_db_session, get_search_service, get_llm_service
from app.application.chat.use_cases.process_chat_query import ProcessChatQueryRequest
from app.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/copilot", tags=["Copilot"])


# Request/Response Models
class CopilotChatRequest(BaseModel):
    """Request model for Copilot chat"""
    query: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    use_rag: bool = True
    max_sources: int = 5


class CopilotChatResponse(BaseModel):
    """Response model for Copilot chat"""
    answer: str
    session_id: str
    message_id: str
    sources: List[Dict[str, Any]]
    confidence: float
    processing_time_ms: int
    tokens_used: int
    model_used: str
    timestamp: datetime


class CopilotSearchRequest(BaseModel):
    """Request model for Copilot search"""
    query: str
    search_type: str = "semantic"  # semantic, keyword, hybrid
    limit: int = 10
    threshold: float = 0.7
    filters: Optional[Dict[str, Any]] = None


class CopilotSearchResponse(BaseModel):
    """Response model for Copilot search"""
    results: List[Dict[str, Any]]
    total_count: int
    processing_time_ms: int
    query: str


class CopilotHealthResponse(BaseModel):
    """Response model for Copilot health check"""
    status: str
    version: str
    timestamp: datetime
    services: Dict[str, str]


@router.post("/chat", response_model=CopilotChatResponse)
async def copilot_chat(
    request: CopilotChatRequest,
    use_case = Depends(get_process_chat_query_use_case)
):
    """
    Chat endpoint for Copilot plugin
    Processes user queries with RAG (Retrieval-Augmented Generation)
    """
    try:
        start_time = datetime.utcnow()
        
        # Create use case request
        use_case_request = ProcessChatQueryRequest(
            user_id="copilot_user",  # TODO: Get from authentication
            query=request.query,
            session_id=request.session_id,
            context=request.context,
            use_rag=request.use_rag,
            max_sources=request.max_sources
        )
        
        # Execute use case
        response = await use_case.execute(use_case_request)
        
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return CopilotChatResponse(
            answer=response.answer,
            session_id=response.session_id,
            message_id=response.message_id,
            sources=response.sources,
            confidence=response.confidence,
            processing_time_ms=processing_time,
            tokens_used=response.tokens_used,
            model_used=response.model_used,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in copilot chat: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat request: {str(e)}"
        )


@router.post("/search", response_model=CopilotSearchResponse)
async def copilot_search(
    request: CopilotSearchRequest,
    search_service = Depends(get_search_service)
):
    """
    Search endpoint for Copilot plugin
    Performs semantic, keyword, or hybrid search
    """
    try:
        start_time = datetime.utcnow()
        
        # Create search request
        from app.services.search_service import SearchRequest
        search_request = SearchRequest(
            query=request.query,
            user_id="copilot_user",  # TODO: Get from authentication
            search_type=request.search_type,
            limit=request.limit,
            threshold=request.threshold,
            filters=request.filters
        )
        
        # Execute search
        results = await search_service.search(search_request)
        
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Convert results to dict format
        result_dicts = []
        for result in results:
            result_dicts.append({
                "id": result.id,
                "title": result.title,
                "content": result.content,
                "score": result.score,
                "source_type": result.source_type,
                "source_id": result.source_id,
                "metadata": result.metadata
            })
        
        return CopilotSearchResponse(
            results=result_dicts,
            total_count=len(result_dicts),
            processing_time_ms=processing_time,
            query=request.query
        )
        
    except Exception as e:
        logger.error(f"Error in copilot search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing search: {str(e)}"
        )


@router.get("/health", response_model=CopilotHealthResponse)
async def copilot_health():
    """
    Health check endpoint for Copilot plugin
    """
    try:
        # Check LLM service health
        llm_service = get_llm_service()
        llm_health = await llm_service.health_check()
        
        # Check database health
        async for session in get_db_session():
            try:
                await session.execute("SELECT 1")
                db_status = "healthy"
            except Exception:
                db_status = "unhealthy"
            break
        
        services = {
            "llm": llm_health.get("status", "unknown"),
            "database": db_status,
            "api": "healthy"
        }
        
        return CopilotHealthResponse(
            status="healthy" if all(s == "healthy" for s in services.values()) else "degraded",
            version="1.0.0",
            timestamp=datetime.utcnow(),
            services=services
        )
        
    except Exception as e:
        logger.error(f"Error in copilot health check: {str(e)}")
        return CopilotHealthResponse(
            status="unhealthy",
            version="1.0.0",
            timestamp=datetime.utcnow(),
            services={"error": str(e)}
        )


@router.get("/models")
async def copilot_models():
    """
    Get available models endpoint for Copilot plugin
    """
    try:
        openai_adapter = get_openai_adapter()
        models = await openai_adapter.list_models()
        
        return {
            "models": models,
            "default_chat_model": "gpt-4",
            "default_embedding_model": "text-embedding-ada-002"
        }
        
    except Exception as e:
        logger.error(f"Error getting models: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving models: {str(e)}"
        )


@router.get("/usage")
async def copilot_usage():
    """
    Get usage limits and current usage for Copilot plugin
    """
    try:
        openai_adapter = get_openai_adapter()
        usage_limits = openai_adapter.get_usage_limits()
        
        return {
            "limits": usage_limits,
            "current_usage": {
                "requests_today": 0,  # TODO: Implement usage tracking
                "tokens_today": 0,
                "cost_today": 0.0
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting usage: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving usage: {str(e)}"
        )
