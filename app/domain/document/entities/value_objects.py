"""
Document Domain Value Objects
"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any
import hashlib


class DocumentStatus(str, Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class DocumentType(str, Enum):
    """Document type enumeration"""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    HTML = "html"
    CSV = "csv"
    EXCEL = "excel"
    UNKNOWN = "unknown"


class ChunkStatus(str, Enum):
    """Chunk processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    EMBEDDED = "embedded"
    FAILED = "failed"


@dataclass(frozen=True)
class FileMetadata:
    """Value object for file metadata"""
    filename: str
    file_size: int
    content_type: str
    checksum: str
    
    def __post_init__(self):
        if not self.filename:
            raise ValueError("Filename is required")
        if self.file_size <= 0:
            raise ValueError("File size must be positive")
        if not self.content_type:
            raise ValueError("Content type is required")
        if not self.checksum:
            raise ValueError("Checksum is required")
    
    @classmethod
    def create(cls, filename: str, file_size: int, content_type: str, content: bytes) -> "FileMetadata":
        """Factory method to create file metadata"""
        checksum = hashlib.sha256(content).hexdigest()
        return cls(
            filename=filename,
            file_size=file_size,
            content_type=content_type,
            checksum=checksum
        )


@dataclass(frozen=True)
class DocumentContent:
    """Value object for document content"""
    text: str
    language: str = "vi"
    word_count: Optional[int] = None
    
    def __post_init__(self):
        if not self.text or not self.text.strip():
            raise ValueError("Document content cannot be empty")
        if len(self.text) > 10000000:  # 10MB limit
            raise ValueError("Document content too large")
        
        # Calculate word count if not provided
        if self.word_count is None:
            object.__setattr__(self, 'word_count', len(self.text.split()))


@dataclass(frozen=True)
class ProcessingConfig:
    """Value object for document processing configuration"""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_chunks: int = 1000
    embedding_model: str = "text-embedding-ada-002"
    
    def __post_init__(self):
        if self.chunk_size <= 0:
            raise ValueError("Chunk size must be positive")
        if self.chunk_overlap < 0:
            raise ValueError("Chunk overlap cannot be negative")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("Chunk overlap must be less than chunk size")
        if self.max_chunks <= 0:
            raise ValueError("Max chunks must be positive")
