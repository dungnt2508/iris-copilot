"""
Document Entity
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any

from .document_chunk import DocumentChunk
from .value_objects import DocumentStatus, DocumentType, FileMetadata, DocumentContent, ProcessingConfig


@dataclass
class Document:
    """
    Document Entity
    Represents a document in the system
    """
    id: str
    user_id: str
    title: str
    content: DocumentContent
    file_metadata: FileMetadata
    document_type: DocumentType
    status: DocumentStatus = DocumentStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Optional fields
    chunks: List[DocumentChunk] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_config: ProcessingConfig = field(default_factory=ProcessingConfig)
    version: int = 1
    
    def __post_init__(self):
        """Validate entity after creation"""
        if not self.id:
            raise ValueError("Document ID is required")
        if not self.user_id:
            raise ValueError("User ID is required")
        if not self.title or not self.title.strip():
            raise ValueError("Document title is required")
    
    @classmethod
    def create(cls, user_id: str, title: str, content: str, 
               file_metadata: FileMetadata, document_type: DocumentType,
               metadata: Dict[str, Any] = None) -> "Document":
        """Factory method to create a new document"""
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            content=DocumentContent(text=content),
            file_metadata=file_metadata,
            document_type=document_type,
            metadata=metadata or {}
        )
    
    def add_chunk(self, chunk: DocumentChunk) -> None:
        """Add a chunk to the document"""
        if chunk.document_id != self.id:
            raise ValueError("Chunk document ID must match document ID")
        self.chunks.append(chunk)
        self.updated_at = datetime.utcnow()
    
    def create_chunks(self, chunk_texts: List[str], metadata: Dict[str, Any] = None) -> List[DocumentChunk]:
        """Create chunks from text list"""
        chunks = []
        for i, text in enumerate(chunk_texts):
            chunk = DocumentChunk.create(
                document_id=self.id,
                content=text,
                position=i,
                metadata=metadata or {}
            )
            chunks.append(chunk)
            self.add_chunk(chunk)
        return chunks
    
    def mark_processing(self) -> None:
        """Mark document as processing"""
        self.status = DocumentStatus.PROCESSING
        self.updated_at = datetime.utcnow()
    
    def mark_completed(self) -> None:
        """Mark document as completed"""
        self.status = DocumentStatus.COMPLETED
        self.updated_at = datetime.utcnow()
    
    def mark_failed(self, error_message: str = None) -> None:
        """Mark document as failed"""
        self.status = DocumentStatus.FAILED
        if error_message:
            self.metadata["error"] = error_message
        self.updated_at = datetime.utcnow()
    
    def archive(self) -> None:
        """Archive the document"""
        self.status = DocumentStatus.ARCHIVED
        self.updated_at = datetime.utcnow()
    
    def update_title(self, new_title: str) -> None:
        """Update document title"""
        if not new_title or not new_title.strip():
            raise ValueError("Document title cannot be empty")
        self.title = new_title
        self.updated_at = datetime.utcnow()
    
    def update_metadata(self, key: str, value: Any) -> None:
        """Update document metadata"""
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()
    
    def get_chunk_count(self) -> int:
        """Get total number of chunks"""
        return len(self.chunks)
    
    def get_embedded_chunk_count(self) -> int:
        """Get number of embedded chunks"""
        return sum(1 for chunk in self.chunks if chunk.is_embedded())
    
    def get_failed_chunk_count(self) -> int:
        """Get number of failed chunks"""
        return sum(1 for chunk in self.chunks if chunk.is_failed())
    
    def get_total_tokens(self) -> int:
        """Get total tokens used for embeddings"""
        return sum(chunk.tokens_used or 0 for chunk in self.chunks)
    
    def get_total_word_count(self) -> int:
        """Get total word count across all chunks"""
        return sum(chunk.get_word_count() for chunk in self.chunks)
    
    def get_chunks_by_status(self, status: str) -> List[DocumentChunk]:
        """Get chunks by status"""
        return [chunk for chunk in self.chunks if chunk.status.value == status]
    
    def get_embedded_chunks(self) -> List[DocumentChunk]:
        """Get all embedded chunks"""
        return [chunk for chunk in self.chunks if chunk.is_embedded()]
    
    def get_pending_chunks(self) -> List[DocumentChunk]:
        """Get all pending chunks"""
        return [chunk for chunk in self.chunks if chunk.status.value == "pending"]
    
    def is_completed(self) -> bool:
        """Check if document processing is completed"""
        return self.status == DocumentStatus.COMPLETED
    
    def is_failed(self) -> bool:
        """Check if document processing failed"""
        return self.status == DocumentStatus.FAILED
    
    def is_archived(self) -> bool:
        """Check if document is archived"""
        return self.status == DocumentStatus.ARCHIVED
    
    def has_embeddings(self) -> bool:
        """Check if document has any embedded chunks"""
        return any(chunk.is_embedded() for chunk in self.chunks)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "document_type": self.document_type.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "version": self.version,
            "file_metadata": {
                "filename": self.file_metadata.filename,
                "file_size": self.file_metadata.file_size,
                "content_type": self.file_metadata.content_type,
                "checksum": self.file_metadata.checksum
            },
            "content": {
                "word_count": self.content.word_count,
                "language": self.content.language
            },
            "statistics": {
                "chunk_count": self.get_chunk_count(),
                "embedded_chunk_count": self.get_embedded_chunk_count(),
                "failed_chunk_count": self.get_failed_chunk_count(),
                "total_tokens": self.get_total_tokens(),
                "total_word_count": self.get_total_word_count()
            },
            "chunks": [chunk.to_dict() for chunk in self.chunks]
        }
    
    def to_search_result(self, score: Optional[float] = None) -> Dict[str, Any]:
        """Convert to search result format"""
        result = self.to_dict()
        if score is not None:
            result["score"] = score
        return result
