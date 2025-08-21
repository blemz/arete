"""
Embedding Service Factory for Arete Graph-RAG system.

Automatically selects between sentence-transformers and Ollama
based on the configured model name.
"""

import logging
from typing import Optional, Union
from ..config import Settings, get_settings

logger = logging.getLogger(__name__)


class EmbeddingServiceFactory:
    """Factory for creating appropriate embedding service based on model type."""
    
    # Models that should use Ollama
    OLLAMA_MODELS = {
        "dengcao/qwen3-embedding-8b",
        "dengcao/qwen3-embedding-8b:q8_0", 
        "qwen3-embedding-8b",
        "qwen3-embedding-8b:q8_0",
        # Add more Ollama models here
    }
    
    @classmethod
    def create_service(
        cls,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        base_url: Optional[str] = None,
        settings: Optional[Settings] = None
    ):
        """
        Create appropriate embedding service based on model type.
        
        Args:
            model_name: Name of embedding model
            device: Device for sentence-transformers (ignored for Ollama)
            base_url: Ollama server URL (ignored for sentence-transformers)
            settings: Configuration settings
            
        Returns:
            EmbeddingService or OllamaEmbeddingService instance
        """
        settings = settings or get_settings()
        model_name = model_name or settings.embedding_model
        
        # Normalize model name for comparison
        model_name_lower = model_name.lower()
        
        # Check if this is an Ollama model
        if any(ollama_model in model_name_lower for ollama_model in cls.OLLAMA_MODELS):
            logger.info(f"Using OllamaEmbeddingService for model: {model_name}")
            from .ollama_embedding_service import OllamaEmbeddingService
            return OllamaEmbeddingService(
                model_name=model_name,
                base_url=base_url,
                settings=settings
            )
        else:
            logger.info(f"Using EmbeddingService (sentence-transformers) for model: {model_name}")
            from .embedding_service import EmbeddingService
            return EmbeddingService(
                model_name=model_name,
                device=device,
                settings=settings
            )
    
    @classmethod
    def is_ollama_model(cls, model_name: str) -> bool:
        """Check if a model should use Ollama service."""
        model_name_lower = model_name.lower()
        return any(ollama_model in model_name_lower for ollama_model in cls.OLLAMA_MODELS)


# Convenience function that matches the existing API
def get_embedding_service(
    model_name: Optional[str] = None,
    device: Optional[str] = None,
    base_url: Optional[str] = None,
    settings: Optional[Settings] = None
):
    """
    Get appropriate embedding service instance.
    
    This function automatically selects between sentence-transformers
    and Ollama based on the model name.
    
    Args:
        model_name: Name of embedding model
        device: Device for sentence-transformers models
        base_url: Ollama server URL for Ollama models
        settings: Configuration settings
        
    Returns:
        Appropriate embedding service instance
    """
    return EmbeddingServiceFactory.create_service(
        model_name=model_name,
        device=device,
        base_url=base_url,
        settings=settings
    )