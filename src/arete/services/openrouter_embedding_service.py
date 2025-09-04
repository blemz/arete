"""
OpenRouter Embedding Service for Arete Graph-RAG system.

Provides embedding generation using OpenRouter's API with multiple model options.
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
import httpx
from ..config import Settings, get_settings

logger = logging.getLogger(__name__)


class OpenRouterEmbeddingService:
    """OpenRouter-based embedding service."""
    
    # OpenRouter embedding models and their dimensions
    EMBEDDING_MODELS = {
        # OpenAI models via OpenRouter
        "openai/text-embedding-3-large": 3072,
        "openai/text-embedding-3-small": 1536,
        "openai/text-embedding-ada-002": 1536,
        # Other providers available via OpenRouter
        "text-embedding-3-small": 1536,  # Default OpenAI model
        "text-embedding-3-large": 3072,  # Default OpenAI model
    }
    
    def __init__(
        self,
        model_name: str = "openai/text-embedding-3-small",
        api_key: Optional[str] = None,
        settings: Optional[Settings] = None,
        max_batch_size: int = 100,
        base_url: str = "https://openrouter.ai/api/v1"
    ):
        """
        Initialize OpenRouter embedding service.
        
        Args:
            model_name: OpenRouter embedding model name
            api_key: OpenRouter API key (if not provided, uses settings)
            settings: Configuration settings
            max_batch_size: Maximum batch size for embeddings
            base_url: OpenRouter API base URL
        """
        self.settings = settings or get_settings()
        self.model_name = model_name
        self.max_batch_size = max_batch_size
        self.base_url = base_url
        
        # Get API key from parameter or settings
        api_key = api_key or self.settings.openrouter_api_key
        if not api_key:
            raise ValueError("OpenRouter API key is required but not provided")
        
        self.api_key = api_key
        
        # Setup HTTP headers
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/yourusername/arete",  # Optional
            "X-Title": "Arete Philosophy Tutor"  # Optional
        }
        
        # Validate model and get dimensions
        if model_name not in self.EMBEDDING_MODELS:
            logger.warning(f"Unknown OpenRouter model {model_name}, using default dimensions")
            self.dimensions = 1536  # Default
        else:
            self.dimensions = self.EMBEDDING_MODELS[model_name]
        
        logger.info(f"Initialized OpenRouter embedding service with model: {model_name} ({self.dimensions}d)")
    
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
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers=self.headers,
                    json={
                        "model": self.model_name,
                        "input": text,
                        "encoding_format": "float"
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                embedding = result["data"][0]["embedding"]
                logger.debug(f"Generated OpenRouter embedding with {len(embedding)} dimensions")
                return embedding
                
            except httpx.HTTPStatusError as e:
                logger.error(f"OpenRouter HTTP error: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"OpenRouter embedding generation failed: {e}")
                raise
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        embeddings = []
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Process in batches
            for i in range(0, len(texts), self.max_batch_size):
                batch = texts[i:i + self.max_batch_size]
                
                # Filter out empty texts and track indices
                non_empty_batch = []
                indices_map = {}
                
                for idx, text in enumerate(batch):
                    if text.strip():
                        indices_map[len(non_empty_batch)] = idx
                        non_empty_batch.append(text)
                
                if not non_empty_batch:
                    # All texts in batch are empty
                    batch_embeddings = [[0.0] * self.dimensions] * len(batch)
                else:
                    try:
                        response = await client.post(
                            f"{self.base_url}/embeddings",
                            headers=self.headers,
                            json={
                                "model": self.model_name,
                                "input": non_empty_batch,
                                "encoding_format": "float"
                            }
                        )
                        
                        response.raise_for_status()
                        result = response.json()
                        
                        # Create result embeddings for entire batch
                        batch_embeddings = [[0.0] * self.dimensions] * len(batch)
                        
                        # Fill in non-empty embeddings
                        for result_idx, embedding_data in enumerate(result["data"]):
                            original_idx = indices_map[result_idx]
                            batch_embeddings[original_idx] = embedding_data["embedding"]
                        
                        logger.debug(f"Generated {len(non_empty_batch)} OpenRouter embeddings in batch")
                        
                    except httpx.HTTPStatusError as e:
                        logger.error(f"OpenRouter batch HTTP error: {e.response.status_code} - {e.response.text}")
                        # Return zero vectors for failed batch
                        batch_embeddings = [[0.0] * self.dimensions] * len(batch)
                    except Exception as e:
                        logger.error(f"OpenRouter batch embedding generation failed: {e}")
                        # Return zero vectors for failed batch
                        batch_embeddings = [[0.0] * self.dimensions] * len(batch)
                
                embeddings.extend(batch_embeddings)
        
        logger.info(f"Generated {len(embeddings)} total OpenRouter embeddings")
        return embeddings
    
    def get_dimensions(self) -> int:
        """Get embedding dimensions."""
        return self.dimensions
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "provider": "openrouter",
            "model_name": self.model_name,
            "dimensions": self.dimensions,
            "max_batch_size": self.max_batch_size,
            "base_url": self.base_url
        }