"""
Google Gemini Embedding Service for Arete Graph-RAG system.

Provides embedding generation using Google's Gemini API.
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
import httpx
from ..config import Settings, get_settings

logger = logging.getLogger(__name__)


class GeminiEmbeddingService:
    """Google Gemini-based embedding service."""
    
    # Gemini embedding models and their dimensions
    EMBEDDING_MODELS = {
        "text-embedding-004": 768,
        "embedding-001": 768,
        "models/embedding-001": 768,
        "models/text-embedding-004": 768,
    }
    
    def __init__(
        self,
        model_name: str = "text-embedding-004",
        api_key: Optional[str] = None,
        settings: Optional[Settings] = None,
        max_batch_size: int = 100,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    ):
        """
        Initialize Gemini embedding service.
        
        Args:
            model_name: Gemini embedding model name
            api_key: Gemini API key (if not provided, uses settings)
            settings: Configuration settings
            max_batch_size: Maximum batch size for embeddings
            base_url: Gemini API base URL
        """
        self.settings = settings or get_settings()
        self.model_name = model_name
        self.max_batch_size = max_batch_size
        self.base_url = base_url
        
        # Get API key from parameter or settings
        api_key = api_key or self.settings.gemini_api_key
        if not api_key:
            raise ValueError("Gemini API key is required but not provided")
        
        self.api_key = api_key
        
        # Ensure model name has models/ prefix for API calls
        if not self.model_name.startswith("models/"):
            self.api_model_name = f"models/{self.model_name}"
        else:
            self.api_model_name = self.model_name
        
        # Validate model and get dimensions
        if model_name not in self.EMBEDDING_MODELS and self.api_model_name not in self.EMBEDDING_MODELS:
            logger.warning(f"Unknown Gemini model {model_name}, using default dimensions")
            self.dimensions = 768  # Default
        else:
            self.dimensions = self.EMBEDDING_MODELS.get(model_name, 
                                                       self.EMBEDDING_MODELS.get(self.api_model_name, 768))
        
        logger.info(f"Initialized Gemini embedding service with model: {model_name} ({self.dimensions}d)")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        if not text.strip():
            logger.warning("Empty text provided, returning zero vector")
            return [0.0] * self.dimensions
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                url = f"{self.base_url}/{self.api_model_name}:embedContent"
                
                response = await client.post(
                    url,
                    headers={
                        "Content-Type": "application/json",
                    },
                    params={"key": self.api_key},
                    json={
                        "model": self.api_model_name,
                        "content": {
                            "parts": [{"text": text}]
                        }
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                embedding = result["embedding"]["values"]
                logger.debug(f"Generated Gemini embedding with {len(embedding)} dimensions")
                return embedding
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Gemini HTTP error: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Gemini embedding generation failed: {e}")
                raise
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Note: Gemini API doesn't support batch embedding requests,
        so we make individual requests with concurrency control.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Use semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(10)  # Max 10 concurrent requests
        
        async def generate_single(text: str) -> List[float]:
            async with semaphore:
                try:
                    return await self.generate_embedding(text)
                except Exception as e:
                    logger.error(f"Failed to generate embedding for text: {e}")
                    return [0.0] * self.dimensions
        
        # Generate embeddings concurrently
        tasks = [generate_single(text) for text in texts]
        embeddings = await asyncio.gather(*tasks, return_exceptions=False)
        
        # Convert any exception results to zero vectors
        final_embeddings = []
        for embedding in embeddings:
            if isinstance(embedding, list):
                final_embeddings.append(embedding)
            else:
                logger.warning(f"Got non-list embedding result: {type(embedding)}")
                final_embeddings.append([0.0] * self.dimensions)
        
        logger.info(f"Generated {len(final_embeddings)} total Gemini embeddings")
        return final_embeddings
    
    def get_dimensions(self) -> int:
        """Get embedding dimensions."""
        return self.dimensions
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "provider": "gemini",
            "model_name": self.model_name,
            "api_model_name": self.api_model_name,
            "dimensions": self.dimensions,
            "max_batch_size": self.max_batch_size,
            "base_url": self.base_url
        }