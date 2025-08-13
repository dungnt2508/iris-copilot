"""
Embedding Model Entity
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any

from .value_objects import ModelConfig


@dataclass
class EmbeddingModel:
    """
    Embedding Model Entity
    Represents an embedding model configuration
    """
    id: str
    name: str
    config: ModelConfig
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Optional fields
    description: Optional[str] = None
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate entity after creation"""
        if not self.id:
            raise ValueError("Model ID is required")
        if not self.name:
            raise ValueError("Model name is required")
    
    @classmethod
    def create(cls, name: str, config: ModelConfig, description: str = None) -> "EmbeddingModel":
        """Factory method to create a new embedding model"""
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            config=config,
            description=description
        )
    
    def activate(self) -> None:
        """Activate the model"""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Deactivate the model"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def update_config(self, new_config: ModelConfig) -> None:
        """Update model configuration"""
        self.config = new_config
        self.updated_at = datetime.utcnow()
    
    def update_metadata(self, key: str, value: Any) -> None:
        """Update model metadata"""
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()
    
    def get_max_tokens(self) -> int:
        """Get maximum tokens for the model"""
        return self.config.max_tokens
    
    def get_batch_size(self) -> int:
        """Get batch size for the model"""
        return self.config.batch_size
    
    def get_temperature(self) -> float:
        """Get temperature for the model"""
        return self.config.temperature
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "config": {
                "model_name": self.config.model_name,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "batch_size": self.config.batch_size
            },
            "metadata": self.metadata
        }
