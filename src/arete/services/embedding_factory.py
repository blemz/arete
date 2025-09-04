"""
Embedding Service Factory for Arete Graph-RAG system.

Selects embedding service based on the configured EMBEDDING_PROVIDER variable.
"""

import logging
from typing import Optional, Union
from ..config import Settings, get_settings

logger = logging.getLogger(__name__)


class EmbeddingServiceFactory:
    """Factory for creating appropriate embedding service based on provider configuration."""
    
    @classmethod
    def create_service(
        cls,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        base_url: Optional[str] = None,
        settings: Optional[Settings] = None
    ):
        """
        Create appropriate embedding service based on provider configuration.
        
        Args:
            provider: Embedding provider (overrides settings if provided)
            model_name: Name of embedding model (overrides settings if provided)
            device: Device for sentence-transformers (ignored for cloud providers)
            base_url: Server URL (used for Ollama and OpenRouter)
            settings: Configuration settings
            
        Returns:
            Appropriate embedding service instance
        """
        settings = settings or get_settings()
        provider = provider or settings.embedding_provider
        model_name = model_name or settings.embedding_model
        
        # Normalize provider name for comparison
        provider_lower = provider.lower()
        
        logger.info(f"Creating embedding service - Provider: {provider}, Model: {model_name}")
        
        # Create service based on provider
        if provider_lower == "openai":
            from .openai_embedding_service import OpenAIEmbeddingService
            return OpenAIEmbeddingService(
                model_name=model_name,
                settings=settings,
                max_batch_size=settings.embedding_batch_size
            )
        
        elif provider_lower == "openrouter":
            from .openrouter_embedding_service import OpenRouterEmbeddingService
            return OpenRouterEmbeddingService(
                model_name=model_name,
                base_url=base_url,
                settings=settings,
                max_batch_size=settings.embedding_batch_size
            )
        
        elif provider_lower == "gemini":
            from .gemini_embedding_service import GeminiEmbeddingService
            return GeminiEmbeddingService(
                model_name=model_name,
                settings=settings,
                max_batch_size=settings.embedding_batch_size
            )
        
        elif provider_lower == "anthropic":
            from .anthropic_embedding_service import AnthropicEmbeddingService
            return AnthropicEmbeddingService(
                model_name=model_name,
                settings=settings,
                max_batch_size=min(settings.embedding_batch_size, 10)  # Lower batch size for anthropic
            )
        
        elif provider_lower == "ollama":
            from .ollama_embedding_service import OllamaEmbeddingService
            return OllamaEmbeddingService(
                model_name=model_name,
                base_url=base_url or settings.ollama_base_url,
                settings=settings
            )
        
        elif provider_lower == "sentence-transformers":
            from .embedding_service import EmbeddingService
            return EmbeddingService(
                model_name=model_name,
                device=device or settings.embedding_device,
                settings=settings
            )
        
        else:
            raise ValueError(f"Unknown embedding provider: {provider}. "
                           f"Supported providers: sentence-transformers, ollama, openai, openrouter, gemini, anthropic")
    
    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """Get list of supported embedding providers."""
        return ["sentence-transformers", "ollama", "openai", "openrouter", "gemini", "anthropic"]
    
    @classmethod
    def validate_provider(cls, provider: str) -> bool:
        """Validate if a provider is supported."""
        return provider.lower() in [p.lower() for p in cls.get_supported_providers()]


# Convenience function that matches the existing API
def get_embedding_service(
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    device: Optional[str] = None,
    base_url: Optional[str] = None,
    settings: Optional[Settings] = None
):
    """
    Get appropriate embedding service instance.
    
    This function selects the embedding service based on the configured
    EMBEDDING_PROVIDER or the provider parameter.
    
    Args:
        provider: Embedding provider (overrides settings if provided)
        model_name: Name of embedding model (overrides settings if provided)
        device: Device for sentence-transformers models
        base_url: Server URL for Ollama/OpenRouter models
        settings: Configuration settings
        
    Returns:
        Appropriate embedding service instance
    """
    return EmbeddingServiceFactory.create_service(
        provider=provider,
        model_name=model_name,
        device=device,
        base_url=base_url,
        settings=settings
    )