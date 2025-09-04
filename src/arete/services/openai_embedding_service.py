"""
OpenAI Embedding Service for Arete Graph-RAG system.

Provides embedding generation using OpenAI's API.
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
import openai
from openai import AsyncOpenAI
from ..config import Settings, get_settings

logger = logging.getLogger(__name__)


class OpenAIEmbeddingService:
    """OpenAI-based embedding service."""
    
    # OpenAI embedding models and their dimensions
    EMBEDDING_MODELS = {
        "text-embedding-3-large": 3072,
        "text-embedding-3-small": 1536, 
        "text-embedding-ada-002": 1536,
    }
    
    def __init__(
        self,
        model_name: str = "text-embedding-3-small",
        api_key: Optional[str] = None,
        settings: Optional[Settings] = None,
        max_batch_size: int = 100
    ):
        """
        Initialize OpenAI embedding service.
        
        Args:
            model_name: OpenAI embedding model name
            api_key: OpenAI API key (if not provided, uses settings)
            settings: Configuration settings
            max_batch_size: Maximum batch size for embeddings
        """
        self.settings = settings or get_settings()
        self.model_name = model_name
        self.max_batch_size = max_batch_size
        
        # Get API key from parameter or settings
        api_key = api_key or self.settings.openai_api_key
        if not api_key:
            raise ValueError("OpenAI API key is required but not provided")
        
        # Initialize OpenAI client
        self.client = AsyncOpenAI(api_key=api_key)
        
        # Validate model and get dimensions
        if model_name not in self.EMBEDDING_MODELS:
            logger.warning(f"Unknown OpenAI model {model_name}, using default dimensions")
            self.dimensions = 1536  # Default
        else:
            self.dimensions = self.EMBEDDING_MODELS[model_name]
        
        logger.info(f"Initialized OpenAI embedding service with model: {model_name} ({self.dimensions}d)")
    
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
        
        try:
            response = await self.client.embeddings.create(
                model=self.model_name,
                input=text,
                encoding_format="float"
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Generated OpenAI embedding with {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"OpenAI embedding generation failed: {e}")
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
                    response = await self.client.embeddings.create(
                        model=self.model_name,
                        input=non_empty_batch,
                        encoding_format="float"
                    )
                    
                    # Create result embeddings for entire batch
                    batch_embeddings = [[0.0] * self.dimensions] * len(batch)
                    
                    # Fill in non-empty embeddings
                    for result_idx, embedding_data in enumerate(response.data):
                        original_idx = indices_map[result_idx]
                        batch_embeddings[original_idx] = embedding_data.embedding
                    
                    logger.debug(f"Generated {len(non_empty_batch)} OpenAI embeddings in batch")
                    
                except Exception as e:
                    logger.error(f"OpenAI batch embedding generation failed: {e}")
                    # Return zero vectors for failed batch
                    batch_embeddings = [[0.0] * self.dimensions] * len(batch)
            
            embeddings.extend(batch_embeddings)
        
        logger.info(f"Generated {len(embeddings)} total OpenAI embeddings")
        return embeddings
    
    def get_dimensions(self) -> int:
        """Get embedding dimensions."""
        return self.dimensions
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "provider": "openai",
            "model_name": self.model_name,
            "dimensions": self.dimensions,
            "max_batch_size": self.max_batch_size
        }