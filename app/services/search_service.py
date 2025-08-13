"""
Search Service - Orchestration layer for search operations
"""
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from app.domain.document.repository import DocumentRepository
from app.domain.embedding.repository import EmbeddingRepository
from app.services.llm_service import LLMService
from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SearchRequest:
    """Request for search operation"""
    query: str
    user_id: str
    search_type: str = "semantic"  # "semantic", "keyword", "hybrid"
    limit: int = 10
    threshold: float = 0.7
    filters: Optional[Dict[str, Any]] = None


@dataclass
class SearchResult:
    """Search result"""
    id: str
    title: str
    content: str
    score: float
    source_type: str
    source_id: str
    metadata: Dict[str, Any]


class SearchService:
    """Service for orchestrating search operations"""
    
    def __init__(self,
                 document_repository: DocumentRepository,
                 embedding_repository: EmbeddingRepository,
                 llm_service: LLMService):
        self.document_repo = document_repository
        self.embedding_repo = embedding_repository
        self.llm_service = llm_service
    
    async def search(self, request: SearchRequest) -> List[SearchResult]:
        """Perform search based on request type"""
        start_time = time.time()
        
        try:
            if request.search_type == "semantic":
                results = await self.semantic_search(
                    query=request.query,
                    user_id=request.user_id,
                    limit=request.limit,
                    threshold=request.threshold,
                    filters=request.filters
                )
            elif request.search_type == "keyword":
                results = await self.keyword_search(
                    query=request.query,
                    user_id=request.user_id,
                    limit=request.limit,
                    filters=request.filters
                )
            elif request.search_type == "hybrid":
                results = await self.hybrid_search(
                    query=request.query,
                    user_id=request.user_id,
                    limit=request.limit,
                    threshold=request.threshold,
                    filters=request.filters
                )
            else:
                raise ValueError(f"Unsupported search type: {request.search_type}")
            
            processing_time = int((time.time() - start_time) * 1000)
            logger.info(f"Search completed in {processing_time}ms, found {len(results)} results")
            
            return results
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            raise
    
    async def semantic_search(self, query: str, user_id: str, 
                            limit: int = 10, threshold: float = 0.7,
                            filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Perform semantic search using embeddings"""
        try:
            # 1. Generate embedding for query
            query_embedding = await self.llm_service.generate_embedding(query)
            
            # 2. Search for similar embeddings
            similar_embeddings = await self.embedding_repo.search_similar_embeddings(
                query_vector=query_embedding,
                limit=limit * 2,  # Get more results for filtering
                threshold=threshold
            )
            
            # 3. Get document chunks for similar embeddings
            results = []
            for embedding_data in similar_embeddings:
                if embedding_data.get("score", 0) >= threshold:
                    chunk_id = embedding_data.get("metadata", {}).get("source_id")
                    if chunk_id:
                        chunk = await self.document_repo.find_chunk_by_id(chunk_id)
                        if chunk and chunk.document_id:
                            document = await self.document_repo.find_document_by_id(chunk.document_id)
                            if document and document.user_id == user_id:
                                # Apply filters if provided
                                if self._apply_filters(document, filters):
                                    results.append(SearchResult(
                                        id=chunk.id,
                                        title=document.title,
                                        content=chunk.content,
                                        score=embedding_data.get("score", 0),
                                        source_type="document_chunk",
                                        source_id=chunk.id,
                                        metadata={
                                            "document_id": document.id,
                                            "chunk_position": chunk.position,
                                            "document_type": document.document_type.value
                                        }
                                    ))
            
            # 4. Sort by score and limit results
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Semantic search error: {str(e)}")
            raise
    
    async def keyword_search(self, query: str, user_id: str,
                           limit: int = 10,
                           filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Perform keyword-based search"""
        try:
            # Search documents by title and content
            documents = await self.document_repo.search_documents(
                user_id=user_id,
                query=query,
                limit=limit
            )
            
            results = []
            for document in documents:
                # Apply filters if provided
                if self._apply_filters(document, filters):
                    # Simple keyword matching score
                    score = self._calculate_keyword_score(query, document.title, document.content.text)
                    
                    if score > 0:
                        results.append(SearchResult(
                            id=document.id,
                            title=document.title,
                            content=document.content.text[:500] + "...",  # Truncate content
                            score=score,
                            source_type="document",
                            source_id=document.id,
                            metadata={
                                "document_type": document.document_type.value,
                                "word_count": document.content.word_count
                            }
                        ))
            
            # Sort by score and limit results
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Keyword search error: {str(e)}")
            raise
    
    async def hybrid_search(self, query: str, user_id: str,
                          limit: int = 10, threshold: float = 0.7,
                          filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Perform hybrid search combining semantic and keyword search"""
        try:
            # Perform both searches
            semantic_results = await self.semantic_search(
                query=query,
                user_id=user_id,
                limit=limit,
                threshold=threshold,
                filters=filters
            )
            
            keyword_results = await self.keyword_search(
                query=query,
                user_id=user_id,
                limit=limit,
                filters=filters
            )
            
            # Combine and deduplicate results
            combined_results = self._combine_search_results(
                semantic_results, keyword_results, limit
            )
            
            return combined_results
            
        except Exception as e:
            logger.error(f"Hybrid search error: {str(e)}")
            raise
    
    async def search_by_embedding(self, query_embedding: List[float], user_id: str,
                                limit: int = 10, threshold: float = 0.7) -> List[SearchResult]:
        """Search using pre-computed embedding"""
        try:
            # Search for similar embeddings
            similar_embeddings = await self.embedding_repo.search_similar_embeddings(
                query_vector=query_embedding,
                limit=limit * 2,
                threshold=threshold
            )
            
            # Get document chunks for similar embeddings
            results = []
            for embedding_data in similar_embeddings:
                if embedding_data.get("score", 0) >= threshold:
                    chunk_id = embedding_data.get("metadata", {}).get("source_id")
                    if chunk_id:
                        chunk = await self.document_repo.find_chunk_by_id(chunk_id)
                        if chunk and chunk.document_id:
                            document = await self.document_repo.find_document_by_id(chunk.document_id)
                            if document and document.user_id == user_id:
                                results.append(SearchResult(
                                    id=chunk.id,
                                    title=document.title,
                                    content=chunk.content,
                                    score=embedding_data.get("score", 0),
                                    source_type="document_chunk",
                                    source_id=chunk.id,
                                    metadata={
                                        "document_id": document.id,
                                        "chunk_position": chunk.position
                                    }
                                ))
            
            # Sort by score and limit results
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Search by embedding error: {str(e)}")
            raise
    
    def _apply_filters(self, document: "Document", filters: Optional[Dict[str, Any]]) -> bool:
        """Apply filters to document"""
        if not filters:
            return True
        
        # Filter by document type
        if "document_type" in filters:
            if document.document_type.value != filters["document_type"]:
                return False
        
        # Filter by date range
        if "date_from" in filters:
            if document.created_at < filters["date_from"]:
                return False
        
        if "date_to" in filters:
            if document.created_at > filters["date_to"]:
                return False
        
        # Filter by metadata
        if "metadata" in filters:
            for key, value in filters["metadata"].items():
                if document.metadata.get(key) != value:
                    return False
        
        return True
    
    def _calculate_keyword_score(self, query: str, title: str, content: str) -> float:
        """Calculate keyword matching score"""
        query_lower = query.lower()
        title_lower = title.lower()
        content_lower = content.lower()
        
        # Title matching (higher weight)
        title_score = 0
        for word in query_lower.split():
            if word in title_lower:
                title_score += 2.0
        
        # Content matching
        content_score = 0
        for word in query_lower.split():
            content_score += content_lower.count(word)
        
        # Normalize scores
        total_score = (title_score * 0.7) + (content_score * 0.3)
        return min(total_score / 10.0, 1.0)  # Normalize to 0-1 range
    
    def _combine_search_results(self, semantic_results: List[SearchResult],
                              keyword_results: List[SearchResult],
                              limit: int) -> List[SearchResult]:
        """Combine and deduplicate search results"""
        # Create a map to track unique results
        result_map = {}
        
        # Add semantic results with higher weight
        for result in semantic_results:
            key = result.source_id
            if key not in result_map:
                result_map[key] = result
            else:
                # If already exists, take the higher score
                if result.score > result_map[key].score:
                    result_map[key] = result
        
        # Add keyword results
        for result in keyword_results:
            key = result.source_id
            if key not in result_map:
                result_map[key] = result
            else:
                # Combine scores for hybrid approach
                existing_score = result_map[key].score
                new_score = result.score
                combined_score = (existing_score * 0.7) + (new_score * 0.3)
                result_map[key] = SearchResult(
                    id=result.id,
                    title=result.title,
                    content=result.content,
                    score=combined_score,
                    source_type=result.source_type,
                    source_id=result.source_id,
                    metadata=result.metadata
                )
        
        # Convert back to list and sort
        combined_results = list(result_map.values())
        combined_results.sort(key=lambda x: x.score, reverse=True)
        
        return combined_results[:limit]
