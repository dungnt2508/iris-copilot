"""
Document Repository Interface
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from .entities import Document, DocumentChunk


class DocumentRepository(ABC):
    """Abstract Document Repository interface"""
    
    @abstractmethod
    async def save_document(self, document: Document) -> Document:
        """Save document"""
        pass
    
    @abstractmethod
    async def find_document_by_id(self, document_id: str) -> Optional[Document]:
        """Find document by ID"""
        pass
    
    @abstractmethod
    async def find_documents_by_user_id(self, user_id: str,
                                      limit: Optional[int] = None,
                                      offset: Optional[int] = None,
                                      status: Optional[str] = None) -> List[Document]:
        """Find documents by user ID"""
        pass
    
    @abstractmethod
    async def delete_document(self, document_id: str) -> bool:
        """Delete document"""
        pass
    
    @abstractmethod
    async def save_chunk(self, chunk: DocumentChunk) -> DocumentChunk:
        """Save document chunk"""
        pass
    
    @abstractmethod
    async def find_chunks_by_document_id(self, document_id: str,
                                       limit: Optional[int] = None,
                                       offset: Optional[int] = None) -> List[DocumentChunk]:
        """Find chunks by document ID"""
        pass
    
    @abstractmethod
    async def find_chunk_by_id(self, chunk_id: str) -> Optional[DocumentChunk]:
        """Find chunk by ID"""
        pass
    
    @abstractmethod
    async def update_chunk_status(self, chunk_id: str, status: str) -> bool:
        """Update chunk status"""
        pass
    
    @abstractmethod
    async def find_embedded_chunks(self, limit: Optional[int] = None) -> List[DocumentChunk]:
        """Find all embedded chunks"""
        pass
    
    @abstractmethod
    async def get_document_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get document statistics for user"""
        pass
    
    @abstractmethod
    async def search_documents(self, user_id: str, query: str, 
                             limit: Optional[int] = None) -> List[Document]:
        """Search documents by title or content"""
        pass
    
    @abstractmethod
    async def get_documents_by_status(self, status: str, 
                                    limit: Optional[int] = None) -> List[Document]:
        """Get documents by status"""
        pass
    
    @abstractmethod
    async def get_documents_by_type(self, document_type: str,
                                  limit: Optional[int] = None) -> List[Document]:
        """Get documents by type"""
        pass
    
    @abstractmethod
    async def cleanup_old_documents(self, days_old: int = 90) -> int:
        """Clean up old archived documents"""
        pass
