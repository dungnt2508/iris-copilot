"""
Embedding Repository Implementation with SQLAlchemy
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
import uuid

from app.domain.embedding.repository import EmbeddingRepository
from app.domain.embedding.entities import Embedding, EmbeddingStatus, EmbeddingType
from app.domain.embedding.entities import EmbeddingModel
from app.infrastructure.db.models.embedding import Embedding as EmbeddingModel, EmbeddingModel as EmbeddingModelConfig


class SQLAlchemyEmbeddingRepository(EmbeddingRepository):
    """SQLAlchemy implementation of EmbeddingRepository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save(self, embedding: Embedding) -> Embedding:
        """Save embedding to database"""
        try:
            # Check if embedding exists
            stmt = select(EmbeddingModel).where(EmbeddingModel.id == embedding.id)
            result = await self.session.execute(stmt)
            existing_embedding = result.scalar_one_or_none()
            
            if existing_embedding:
                # Update existing embedding
                await self._update_embedding_model(existing_embedding, embedding)
                await self.session.commit()
                return await self._model_to_embedding(existing_embedding)
            else:
                # Create new embedding
                embedding_model = self._embedding_to_model(embedding)
                self.session.add(embedding_model)
                await self.session.commit()
                await self.session.refresh(embedding_model)
                return await self._model_to_embedding(embedding_model)
                
        except Exception as e:
            await self.session.rollback()
            raise Exception(f"Error saving embedding: {str(e)}")
    
    async def find_by_id(self, embedding_id: uuid.UUID) -> Optional[Embedding]:
        """Find embedding by ID"""
        try:
            stmt = select(EmbeddingModel).where(EmbeddingModel.id == embedding_id)
            result = await self.session.execute(stmt)
            embedding_model = result.scalar_one_or_none()
            
            if embedding_model:
                return await self._model_to_embedding(embedding_model)
            return None
            
        except Exception as e:
            raise Exception(f"Error finding embedding: {str(e)}")
    
    async def find_by_status(self, status: EmbeddingStatus) -> List[Embedding]:
        """Find embeddings by status"""
        try:
            stmt = select(EmbeddingModel).where(EmbeddingModel.status == status.value)
            result = await self.session.execute(stmt)
            embedding_models = result.scalars().all()
            
            return [await self._model_to_embedding(emb) for emb in embedding_models]
            
        except Exception as e:
            raise Exception(f"Error finding embeddings by status: {str(e)}")
    
    async def find_by_type(self, embedding_type: EmbeddingType) -> List[Embedding]:
        """Find embeddings by type"""
        try:
            stmt = select(EmbeddingModel).where(EmbeddingModel.embedding_type == embedding_type.value)
            result = await self.session.execute(stmt)
            embedding_models = result.scalars().all()
            
            return [await self._model_to_embedding(emb) for emb in embedding_models]
            
        except Exception as e:
            raise Exception(f"Error finding embeddings by type: {str(e)}")
    
    async def find_by_model(self, model: str) -> List[Embedding]:
        """Find embeddings by model"""
        try:
            stmt = select(EmbeddingModel).where(EmbeddingModel.model == model)
            result = await self.session.execute(stmt)
            embedding_models = result.scalars().all()
            
            return [await self._model_to_embedding(emb) for emb in embedding_models]
            
        except Exception as e:
            raise Exception(f"Error finding embeddings by model: {str(e)}")
    
    async def delete(self, embedding_id: uuid.UUID) -> bool:
        """Delete embedding by ID"""
        try:
            stmt = delete(EmbeddingModel).where(EmbeddingModel.id == embedding_id)
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            return result.rowcount > 0
            
        except Exception as e:
            await self.session.rollback()
            raise Exception(f"Error deleting embedding: {str(e)}")
    
    async def save_model_config(self, model_config: EmbeddingModel) -> EmbeddingModel:
        """Save embedding model configuration"""
        try:
            # Check if model config exists
            stmt = select(EmbeddingModelConfig).where(EmbeddingModelConfig.id == model_config.id)
            result = await self.session.execute(stmt)
            existing_config = result.scalar_one_or_none()
            
            if existing_config:
                # Update existing config
                await self._update_model_config(existing_config, model_config)
                await self.session.commit()
                return await self._model_to_config(existing_config)
            else:
                # Create new config
                config_model = self._config_to_model(model_config)
                self.session.add(config_model)
                await self.session.commit()
                await self.session.refresh(config_model)
                return await self._model_to_config(config_model)
                
        except Exception as e:
            await self.session.rollback()
            raise Exception(f"Error saving model config: {str(e)}")
    
    async def find_model_config_by_id(self, config_id: uuid.UUID) -> Optional[EmbeddingModel]:
        """Find model configuration by ID"""
        try:
            stmt = select(EmbeddingModelConfig).where(EmbeddingModelConfig.id == config_id)
            result = await self.session.execute(stmt)
            config_model = result.scalar_one_or_none()
            
            if config_model:
                return await self._model_to_config(config_model)
            return None
            
        except Exception as e:
            raise Exception(f"Error finding model config: {str(e)}")
    
    async def find_active_model_configs(self) -> List[EmbeddingModel]:
        """Find all active model configurations"""
        try:
            stmt = select(EmbeddingModelConfig).where(EmbeddingModelConfig.is_active == True)
            result = await self.session.execute(stmt)
            config_models = result.scalars().all()
            
            return [await self._model_to_config(config) for config in config_models]
            
        except Exception as e:
            raise Exception(f"Error finding active model configs: {str(e)}")
    
    # Helper methods for conversion
    def _embedding_to_model(self, embedding: Embedding) -> EmbeddingModel:
        """Convert domain Embedding to SQLAlchemy model"""
        return EmbeddingModel(
            id=embedding.id,
            vector=embedding.vector,
            embedding_metadata=embedding.metadata,
            embedding_type=embedding.embedding_type.value,
            status=embedding.status.value,
            created_at=embedding.created_at,
            updated_at=embedding.updated_at,
            tags=embedding.tags,
            version=embedding.version,
            dimension=embedding.dimension,
            model=embedding.model
        )
    
    async def _update_embedding_model(self, model: EmbeddingModel, embedding: Embedding):
        """Update SQLAlchemy model with domain embedding data"""
        model.vector = embedding.vector
        model.embedding_metadata = embedding.metadata
        model.embedding_type = embedding.embedding_type.value
        model.status = embedding.status.value
        model.updated_at = embedding.updated_at
        model.tags = embedding.tags
        model.version = embedding.version
        model.dimension = embedding.dimension
        model.model = embedding.model
    
    async def _model_to_embedding(self, model: EmbeddingModel) -> Embedding:
        """Convert SQLAlchemy model to domain Embedding"""
        return Embedding(
            id=model.id,
            vector=model.vector,
            metadata=model.embedding_metadata,
            embedding_type=EmbeddingType(model.embedding_type),
            status=EmbeddingStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
            tags=model.tags,
            version=model.version,
            dimension=model.dimension,
            model=model.model
        )
    
    def _config_to_model(self, config: EmbeddingModel) -> EmbeddingModelConfig:
        """Convert domain EmbeddingModel to SQLAlchemy model"""
        return EmbeddingModelConfig(
            id=config.id,
            name=config.name,
            config=config.config,
            created_at=config.created_at,
            updated_at=config.updated_at,
            description=config.description,
            is_active=config.is_active,
            embeddingmodel_metadata=config.metadata
        )
    
    async def _update_model_config(self, model: EmbeddingModelConfig, config: EmbeddingModel):
        """Update SQLAlchemy model with domain config data"""
        model.name = config.name
        model.config = config.config
        model.updated_at = config.updated_at
        model.description = config.description
        model.is_active = config.is_active
        model.embeddingmodel_metadata = config.metadata
    
    async def _model_to_config(self, model: EmbeddingModelConfig) -> EmbeddingModel:
        """Convert SQLAlchemy model to domain EmbeddingModel"""
        return EmbeddingModel(
            id=model.id,
            name=model.name,
            config=model.config,
            created_at=model.created_at,
            updated_at=model.updated_at,
            description=model.description,
            is_active=model.is_active,
            metadata=model.embeddingmodel_metadata
        )
