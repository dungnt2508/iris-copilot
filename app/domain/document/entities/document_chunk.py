"""
Document Chunk Entity
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

from .value_objects import ChunkStatus


@dataclass
class DocumentChunk:
    """
    Document Chunk Entity
    Represents a chunk of text from a document
    """
    id: str
    document_id: str
    content: str
    position: int
    status: ChunkStatus = ChunkStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Optional fields
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tokens_used: Optional[int] = None
    embedding_model: Optional[str] = None
    
    def __post_init__(self):
        """Validate entity after creation"""
        if not self.id:
            raise ValueError("Chunk ID is required")
        if not self.document_id:
            raise ValueError("Document ID is required")
        if not self.content or not self.content.strip():
            raise ValueError("Chunk content cannot be empty")
        if self.position < 0:
            raise ValueError("Position must be non-negative")
    
    @classmethod
    def create(cls, document_id: str, content: str, position: int, 
               metadata: Dict[str, Any] = None) -> "DocumentChunk":
        """Factory method to create a new document chunk"""
        return cls(
            id=str(uuid.uuid4()),
            document_id=document_id,
            content=content,
            position=position,
            metadata=metadata or {}
        )
    
    def mark_processing(self) -> None:
        """Mark chunk as processing"""
        self.status = ChunkStatus.PROCESSING
        self.updated_at = datetime.utcnow()
    
    def mark_embedded(self, embedding: List[float], model: str, tokens_used: Optional[int] = None) -> None:
        """Mark chunk as embedded"""
        self.status = ChunkStatus.EMBEDDED
        self.embedding = embedding
        self.embedding_model = model
        self.tokens_used = tokens_used
        self.updated_at = datetime.utcnow()
    
    def mark_failed(self, error_message: str = None) -> None:
        """Mark chunk as failed"""
        self.status = ChunkStatus.FAILED
        if error_message:
            self.metadata["error"] = error_message
        self.updated_at = datetime.utcnow()
    
    def update_metadata(self, key: str, value: Any) -> None:
        """Update chunk metadata"""
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()
    
    def get_word_count(self) -> int:
        """Get word count of chunk content"""
        return len(self.content.split())
    
    def get_character_count(self) -> int:
        """Get character count of chunk content"""
        return len(self.content)
    
    def is_embedded(self) -> bool:
        """Check if chunk has been embedded"""
        return self.status == ChunkStatus.EMBEDDED and self.embedding is not None
    
    def is_failed(self) -> bool:
        """Check if chunk processing failed"""
        return self.status == ChunkStatus.FAILED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "content": self.content,
            "position": self.position,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "tokens_used": self.tokens_used,
            "embedding_model": self.embedding_model,
            "word_count": self.get_word_count(),
            "character_count": self.get_character_count(),
            "has_embedding": self.is_embedded()
        }
    
    def to_search_result(self, score: Optional[float] = None) -> Dict[str, Any]:
        """Convert to search result format"""
        result = self.to_dict()
        if score is not None:
            result["score"] = score
        return result
