"""
OpenAI Adapter - External integration adapter for OpenAI API
"""
import asyncio
import time
from typing import List, Dict, Any, Optional
import openai
from openai import AsyncOpenAI

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class OpenAIAdapter:
    """Adapter for OpenAI integration"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.openai_api_key
        self.base_url = base_url or settings.openai_base_url
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        # Initialize OpenAI client
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        # Default models
        self.default_chat_model = "gpt-4"
        self.default_embedding_model = "text-embedding-ada-002"
        
        logger.info(f"OpenAI adapter initialized with base URL: {self.base_url}")
    
    async def generate_completion(self, messages: List[Dict[str, str]], 
                                model: str = None,
                                temperature: float = 0.7,
                                max_tokens: Optional[int] = None,
                                **kwargs) -> Dict[str, Any]:
        """Generate chat completion"""
        start_time = time.time()
        
        try:
            response = await self.client.chat.completions.create(
                model=model or self.default_chat_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return {
                "content": response.choices[0].message.content,
                "model": response.model,
                "tokens_used": response.usage.total_tokens,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "processing_time_ms": processing_time,
                "metadata": {
                    "finish_reason": response.choices[0].finish_reason,
                    "response_id": response.id
                }
            }
            
        except Exception as e:
            logger.error(f"OpenAI completion error: {str(e)}")
            raise
    
    async def generate_embedding(self, text: str, model: str = None) -> List[float]:
        """Generate embedding for text"""
        try:
            response = await self.client.embeddings.create(
                model=model or self.default_embedding_model,
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"OpenAI embedding error: {str(e)}")
            raise
    
    async def generate_embeddings_batch(self, texts: List[str], 
                                      model: str = None,
                                      batch_size: int = 100) -> List[List[float]]:
        """Generate embeddings for multiple texts with batching"""
        try:
            all_embeddings = []
            
            # Process in batches
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                response = await self.client.embeddings.create(
                    model=model or self.default_embedding_model,
                    input=batch
                )
                
                batch_embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(batch_embeddings)
                
                # Small delay to avoid rate limiting
                if i + batch_size < len(texts):
                    await asyncio.sleep(0.1)
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"OpenAI batch embedding error: {str(e)}")
            raise
    
    async def generate_image(self, prompt: str,
                           size: str = "1024x1024",
                           quality: str = "standard",
                           style: str = "vivid") -> str:
        """Generate image using DALL-E"""
        try:
            response = await self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality=quality,
                style=style,
                n=1
            )
            
            return response.data[0].url
            
        except Exception as e:
            logger.error(f"OpenAI image generation error: {str(e)}")
            raise
    
    async def transcribe_audio(self, audio_file_path: str,
                             language: Optional[str] = None) -> str:
        """Transcribe audio file"""
        try:
            with open(audio_file_path, "rb") as audio_file:
                response = await self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language
                )
            
            return response.text
            
        except Exception as e:
            logger.error(f"OpenAI transcription error: {str(e)}")
            raise
    
    async def moderate_content(self, text: str) -> Dict[str, Any]:
        """Moderate content using OpenAI moderation"""
        try:
            response = await self.client.moderations.create(
                input=text
            )
            
            result = response.results[0]
            
            return {
                "flagged": result.flagged,
                "categories": result.categories.model_dump(),
                "category_scores": result.category_scores.model_dump()
            }
            
        except Exception as e:
            logger.error(f"OpenAI moderation error: {str(e)}")
            raise
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models"""
        try:
            response = await self.client.models.list()
            
            return [
                {
                    "id": model.id,
                    "object": model.object,
                    "created": model.created,
                    "owned_by": model.owned_by
                }
                for model in response.data
            ]
            
        except Exception as e:
            logger.error(f"OpenAI list models error: {str(e)}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Check OpenAI API health"""
        try:
            start_time = time.time()
            
            # Test with a simple completion
            response = await self.generate_completion(
                messages=[{"role": "user", "content": "Hello"}],
                model="gpt-3.5-turbo",
                max_tokens=5
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return {
                "status": "healthy",
                "response_time_ms": processing_time,
                "model": response["model"],
                "tokens_used": response["tokens_used"]
            }
            
        except Exception as e:
            logger.error(f"OpenAI health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def get_usage_limits(self) -> Dict[str, Any]:
        """Get API usage limits and current usage"""
        # Note: This would require additional API calls to get actual usage
        return {
            "rate_limits": {
                "requests_per_minute": 3500,
                "tokens_per_minute": 90000
            },
            "model_limits": {
                "gpt-4": {
                    "max_tokens": 8192,
                    "max_input_tokens": 8192
                },
                "gpt-3.5-turbo": {
                    "max_tokens": 4096,
                    "max_input_tokens": 4096
                }
            }
        }
