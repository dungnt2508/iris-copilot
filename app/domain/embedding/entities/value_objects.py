"""
Embedding Domain Value Objects
"""
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import numpy as np


class EmbeddingStatus(str, Enum):
    """Embedding processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class EmbeddingType(str, Enum):
    """Embedding type enumeration"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    MULTIMODAL = "multimodal"


@dataclass(frozen=True)
class EmbeddingVector:
    """Value object for embedding vector"""
    values: List[float]
    dimension: int
    model: str
    
    def __post_init__(self):
        if not self.values:
            raise ValueError("Embedding values cannot be empty")
        if len(self.values) != self.dimension:
            raise ValueError("Vector dimension must match values length")
        if not self.model:
            raise ValueError("Model name is required")
    
    @classmethod
    def create(cls, values: List[float], model: str) -> "EmbeddingVector":
        """Factory method to create embedding vector"""
        return cls(
            values=values,
            dimension=len(values),
            model=model
        )
    
    def to_numpy(self) -> np.ndarray:
        """Convert to numpy array"""
        return np.array(self.values)
    
    def cosine_similarity(self, other: "EmbeddingVector") -> float:
        """Calculate cosine similarity with another vector"""
        if self.dimension != other.dimension:
            raise ValueError("Vectors must have same dimension")
        
        vec1 = np.array(self.values)
        vec2 = np.array(other.values)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def euclidean_distance(self, other: "EmbeddingVector") -> float:
        """Calculate euclidean distance with another vector"""
        if self.dimension != other.dimension:
            raise ValueError("Vectors must have same dimension")
        
        vec1 = np.array(self.values)
        vec2 = np.array(other.values)
        
        return np.linalg.norm(vec1 - vec2)


@dataclass(frozen=True)
class EmbeddingMetadata:
    """Value object for embedding metadata"""
    source_type: str  # "document_chunk", "user_query", etc.
    source_id: str
    content_preview: str
    tokens_used: Optional[int] = None
    processing_time_ms: Optional[int] = None
    
    def __post_init__(self):
        if not self.source_type:
            raise ValueError("Source type is required")
        if not self.source_id:
            raise ValueError("Source ID is required")
        if not self.content_preview:
            raise ValueError("Content preview is required")


@dataclass(frozen=True)
class ModelConfig:
    """Value object for embedding model configuration"""
    model_name: str
    max_tokens: int = 8192
    temperature: float = 0.0
    batch_size: int = 100
    
    def __post_init__(self):
        if not self.model_name:
            raise ValueError("Model name is required")
        if self.max_tokens <= 0:
            raise ValueError("Max tokens must be positive")
        if self.temperature < 0 or self.temperature > 2:
            raise ValueError("Temperature must be between 0 and 2")
        if self.batch_size <= 0:
            raise ValueError("Batch size must be positive")
