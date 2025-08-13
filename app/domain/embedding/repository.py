"""
Embedding Repository Interface
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from .entities import Embedding, EmbeddingModel


class EmbeddingRepository(ABC):
    """Abstract Embedding Repository interface"""
    
    @abstractmethod
    async def save_embedding(self, embedding: Embedding) -> Embedding:
        """Save embedding"""
        pass
    
    @abstractmethod
    async def find_embedding_by_id(self, embedding_id: str) -> Optional[Embedding]:
        """Find embedding by ID"""
        pass
    
    @abstractmethod
    async def find_embeddings_by_source(self, source_type: str, source_id: str) -> List[Embedding]:
        """Find embeddings by source"""
        pass
    
    @abstractmethod
    async def delete_embedding(self, embedding_id: str) -> bool:
        """Delete embedding"""
        pass
    
    @abstractmethod
    async def save_model(self, model: EmbeddingModel) -> EmbeddingModel:
        """Save embedding model"""
        pass
    
    @abstractmethod
    async def find_model_by_id(self, model_id: str) -> Optional[EmbeddingModel]:
        """Find embedding model by ID"""
        pass
    
    @abstractmethod
    async def find_model_by_name(self, name: str) -> Optional[EmbeddingModel]:
        """Find embedding model by name"""
        pass
    
    @abstractmethod
    async def find_active_models(self) -> List[EmbeddingModel]:
        """Find all active embedding models"""
        pass
    
    @abstractmethod
    async def delete_model(self, model_id: str) -> bool:
        """Delete embedding model"""
        pass
    
    @abstractmethod
    async def search_similar_embeddings(self, query_vector: List[float], 
                                      limit: int = 10,
                                      threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Search for similar embeddings using vector similarity"""
        pass
    
    @abstractmethod
    async def get_embedding_statistics(self) -> Dict[str, Any]:
        """Get embedding statistics"""
        pass
    
    @abstractmethod
    async def cleanup_old_embeddings(self, days_old: int = 90) -> int:
        """Clean up old embeddings"""
        pass
