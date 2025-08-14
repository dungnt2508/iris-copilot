"""
Document Repository Implementation with SQLAlchemy
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
import uuid

from app.domain.document.repository import DocumentRepository
from app.domain.document.entities import Document, DocumentStatus, DocumentType
from app.domain.document.entities import DocumentChunk, ChunkStatus
from app.infrastructure.db.models.document import Document as DocumentModel, DocumentChunk as DocumentChunkModel


class SQLAlchemyDocumentRepository(DocumentRepository):
    """SQLAlchemy implementation of DocumentRepository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save(self, document: Document) -> Document:
        """Save document to database"""
        try:
            # Check if document exists
            stmt = select(DocumentModel).where(DocumentModel.id == document.id)
            result = await self.session.execute(stmt)
            existing_doc = result.scalar_one_or_none()
            
            if existing_doc:
                # Update existing document
                await self._update_document_model(existing_doc, document)
                await self.session.commit()
                return await self._model_to_document(existing_doc)
            else:
                # Create new document
                doc_model = self._document_to_model(document)
                self.session.add(doc_model)
                await self.session.commit()
                await self.session.refresh(doc_model)
                return await self._model_to_document(doc_model)
                
        except Exception as e:
            await self.session.rollback()
            raise Exception(f"Error saving document: {str(e)}")
    
    async def find_by_id(self, document_id: uuid.UUID) -> Optional[Document]:
        """Find document by ID"""
        try:
            stmt = select(DocumentModel).where(DocumentModel.id == document_id)
            result = await self.session.execute(stmt)
            doc_model = result.scalar_one_or_none()
            
            if doc_model:
                return await self._model_to_document(doc_model)
            return None
            
        except Exception as e:
            raise Exception(f"Error finding document: {str(e)}")
    
    async def find_by_user_id(self, user_id: uuid.UUID) -> List[Document]:
        """Find documents by user ID"""
        try:
            stmt = select(DocumentModel).where(DocumentModel.user_id == user_id)
            result = await self.session.execute(stmt)
            doc_models = result.scalars().all()
            
            return [await self._model_to_document(doc) for doc in doc_models]
            
        except Exception as e:
            raise Exception(f"Error finding documents by user: {str(e)}")
    
    async def find_by_status(self, status: DocumentStatus) -> List[Document]:
        """Find documents by status"""
        try:
            stmt = select(DocumentModel).where(DocumentModel.status == status.value)
            result = await self.session.execute(stmt)
            doc_models = result.scalars().all()
            
            return [await self._model_to_document(doc) for doc in doc_models]
            
        except Exception as e:
            raise Exception(f"Error finding documents by status: {str(e)}")
    
    async def delete(self, document_id: uuid.UUID) -> bool:
        """Delete document by ID"""
        try:
            stmt = delete(DocumentModel).where(DocumentModel.id == document_id)
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            return result.rowcount > 0
            
        except Exception as e:
            await self.session.rollback()
            raise Exception(f"Error deleting document: {str(e)}")
    
    async def save_chunk(self, chunk: DocumentChunk) -> DocumentChunk:
        """Save document chunk"""
        try:
            # Check if chunk exists
            stmt = select(DocumentChunkModel).where(DocumentChunkModel.id == chunk.id)
            result = await self.session.execute(stmt)
            existing_chunk = result.scalar_one_or_none()
            
            if existing_chunk:
                # Update existing chunk
                await self._update_chunk_model(existing_chunk, chunk)
                await self.session.commit()
                return await self._model_to_chunk(existing_chunk)
            else:
                # Create new chunk
                chunk_model = self._chunk_to_model(chunk)
                self.session.add(chunk_model)
                await self.session.commit()
                await self.session.refresh(chunk_model)
                return await self._model_to_chunk(chunk_model)
                
        except Exception as e:
            await self.session.rollback()
            raise Exception(f"Error saving chunk: {str(e)}")
    
    async def find_chunks_by_document_id(self, document_id: uuid.UUID) -> List[DocumentChunk]:
        """Find chunks by document ID"""
        try:
            stmt = select(DocumentChunkModel).where(DocumentChunkModel.document_id == document_id)
            result = await self.session.execute(stmt)
            chunk_models = result.scalars().all()
            
            return [await self._model_to_chunk(chunk) for chunk in chunk_models]
            
        except Exception as e:
            raise Exception(f"Error finding chunks: {str(e)}")
    
    # Helper methods for conversion
    def _document_to_model(self, document: Document) -> DocumentModel:
        """Convert domain Document to SQLAlchemy model"""
        return DocumentModel(
            id=document.id,
            user_id=document.user_id,
            title=document.title,
            content=document.content,
            file_path=document.file_path,
            file_size=document.file_size,
            file_type=document.file_type.value,
            status=document.status.value,
            document_type=document.document_type.value,
            created_at=document.created_at,
            updated_at=document.updated_at,
            document_metadata=document.metadata,
            processing_config=document.processing_config,
            version=document.version
        )
    
    async def _update_document_model(self, model: DocumentModel, document: Document):
        """Update SQLAlchemy model with domain document data"""
        model.title = document.title
        model.content = document.content
        model.file_path = document.file_path
        model.file_size = document.file_size
        model.file_type = document.file_type.value
        model.status = document.status.value
        model.document_type = document.document_type.value
        model.updated_at = document.updated_at
        model.document_metadata = document.metadata
        model.processing_config = document.processing_config
        model.version = document.version
    
    async def _model_to_document(self, model: DocumentModel) -> Document:
        """Convert SQLAlchemy model to domain Document"""
        return Document(
            id=model.id,
            user_id=model.user_id,
            title=model.title,
            content=model.content,
            file_path=model.file_path,
            file_size=model.file_size,
            file_type=DocumentType(model.file_type),
            status=DocumentStatus(model.status),
            document_type=DocumentType(model.document_type),
            created_at=model.created_at,
            updated_at=model.updated_at,
            metadata=model.document_metadata,
            processing_config=model.processing_config,
            version=model.version
        )
    
    def _chunk_to_model(self, chunk: DocumentChunk) -> DocumentChunkModel:
        """Convert domain DocumentChunk to SQLAlchemy model"""
        return DocumentChunkModel(
            id=chunk.id,
            document_id=chunk.document_id,
            content=chunk.content,
            chunk_index=chunk.chunk_index,
            start_position=chunk.start_position,
            end_position=chunk.end_position,
            status=chunk.status.value,
            created_at=chunk.created_at,
            updated_at=chunk.updated_at,
            embedding=chunk.embedding,
            chunk_metadata=chunk.metadata,
            tokens_used=chunk.tokens_used,
            embedding_model=chunk.embedding_model
        )
    
    async def _update_chunk_model(self, model: DocumentChunkModel, chunk: DocumentChunk):
        """Update SQLAlchemy model with domain chunk data"""
        model.content = chunk.content
        model.chunk_index = chunk.chunk_index
        model.start_position = chunk.start_position
        model.end_position = chunk.end_position
        model.status = chunk.status.value
        model.updated_at = chunk.updated_at
        model.embedding = chunk.embedding
        model.chunk_metadata = chunk.metadata
        model.tokens_used = chunk.tokens_used
        model.embedding_model = chunk.embedding_model
    
    async def _model_to_chunk(self, model: DocumentChunkModel) -> DocumentChunk:
        """Convert SQLAlchemy model to domain DocumentChunk"""
        return DocumentChunk(
            id=model.id,
            document_id=model.document_id,
            content=model.content,
            chunk_index=model.chunk_index,
            start_position=model.start_position,
            end_position=model.end_position,
            status=ChunkStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
            embedding=model.embedding,
            metadata=model.chunk_metadata,
            tokens_used=model.tokens_used,
            embedding_model=model.embedding_model
        )
