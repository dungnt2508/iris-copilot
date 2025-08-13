"""
Embedding Entity
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any

from .value_objects import EmbeddingStatus, EmbeddingType, EmbeddingVector, EmbeddingMetadata


@dataclass
class Embedding:
    """
    Embedding Entity
    Represents an embedding in the system
    """
    id: str
    vector: EmbeddingVector
    metadata: EmbeddingMetadata
    embedding_type: EmbeddingType = EmbeddingType.TEXT
    status: EmbeddingStatus = EmbeddingStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Optional fields
    tags: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    
    def __post_init__(self):
        """Validate entity after creation"""
        if not self.id:
            raise ValueError("Embedding ID is required")
    
    @classmethod
    def create(cls, vector: EmbeddingVector, metadata: EmbeddingMetadata,
               embedding_type: EmbeddingType = EmbeddingType.TEXT,
               tags: Dict[str, Any] = None) -> "Embedding":
        """Factory method to create a new embedding"""
        return cls(
            id=str(uuid.uuid4()),
            vector=vector,
            metadata=metadata,
            embedding_type=embedding_type,
            tags=tags or {}
        )
    
    def mark_processing(self) -> None:
        """Mark embedding as processing"""
        self.status = EmbeddingStatus.PROCESSING
        self.updated_at = datetime.utcnow()
    
    def mark_completed(self) -> None:
        """Mark embedding as completed"""
        self.status = EmbeddingStatus.COMPLETED
        self.updated_at = datetime.utcnow()
    
    def mark_failed(self, error_message: str = None) -> None:
        """Mark embedding as failed"""
        self.status = EmbeddingStatus.FAILED
        if error_message:
            self.tags["error"] = error_message
        self.updated_at = datetime.utcnow()
    
    def update_tags(self, key: str, value: Any) -> None:
        """Update embedding tags"""
        self.tags[key] = value
        self.updated_at = datetime.utcnow()
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.vector.dimension
    
    def get_model(self) -> str:
        """Get embedding model name"""
        return self.vector.model
    
    def is_completed(self) -> bool:
        """Check if embedding processing is completed"""
        return self.status == EmbeddingStatus.COMPLETED
    
    def is_failed(self) -> bool:
        """Check if embedding processing failed"""
        return self.status == EmbeddingStatus.FAILED
    
    def is_text_embedding(self) -> bool:
        """Check if embedding is text type"""
        return self.embedding_type == EmbeddingType.TEXT
    
    def is_image_embedding(self) -> bool:
        """Check if embedding is image type"""
        return self.embedding_type == EmbeddingType.IMAGE
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "embedding_type": self.embedding_type.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "vector": {
                "dimension": self.vector.dimension,
                "model": self.vector.model,
                "values": self.vector.values
            },
            "metadata": {
                "source_type": self.metadata.source_type,
                "source_id": self.metadata.source_id,
                "content_preview": self.metadata.content_preview,
                "tokens_used": self.metadata.tokens_used,
                "processing_time_ms": self.metadata.processing_time_ms
            },
            "tags": self.tags
        }
    
    def to_search_result(self, score: Optional[float] = None) -> Dict[str, Any]:
        """Convert to search result format"""
        result = self.to_dict()
        if score is not None:
            result["score"] = score
        return result
