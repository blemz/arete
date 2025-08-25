"""
Multi-provider LLM integration service for Arete Graph-RAG system.

This module provides a unified interface for multiple LLM providers including
Ollama (local), OpenRouter, Google Gemini, and Anthropic Claude with intelligent
routing, failover capabilities, and secure API key management.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Union
import json
import time

from arete.services.base import BaseService, ServiceError, ConfigurationError
from arete.config import Settings

# Setup logger
logger = logging.getLogger(__name__)


class MessageRole(Enum):
    """Message roles for LLM conversations."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class LLMMessage:
    """Represents a message in an LLM conversation."""
    role: MessageRole
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Response from an LLM provider."""
    content: str
    provider: str
    usage_tokens: Optional[int] = None
    model: Optional[str] = None
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# LLM Provider Exceptions
class LLMProviderError(ServiceError):
    """Base exception for LLM provider errors."""
    pass


class ProviderUnavailableError(LLMProviderError):
    """Raised when an LLM provider is unavailable."""
    
    def __init__(self, message: str, provider: str):
        super().__init__(message)
        self.provider = provider


class RateLimitError(LLMProviderError):
    """Raised when rate limits are exceeded."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class AuthenticationError(LLMProviderError):
    """Raised when authentication fails."""
    
    def __init__(self, message: str, provider: str):
        super().__init__(message)
        self.provider = provider


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    Defines the interface that all LLM provider implementations must follow,
    ensuring consistent behavior across different providers.
    """
    
    def __init__(self, name: str):
        """
        Initialize LLM provider.
        
        Args:
            name: Unique name for this provider instance
        """
        self.name = name
        self._initialized = False

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is currently available."""
        pass

    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """Get list of supported models for this provider."""
        pass

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the provider (setup connections, validate config, etc.)."""
        pass

    @abstractmethod
    async def generate_response(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate response from the LLM.
        
        Args:
            messages: Conversation messages
            model: Model to use (if None, uses provider default)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse object with generated content
            
        Raises:
            LLMProviderError: If generation fails
            ProviderUnavailableError: If provider is unavailable
            RateLimitError: If rate limit is exceeded
            AuthenticationError: If authentication fails
        """
        pass

    @abstractmethod
    def get_health_status(self) -> Dict[str, Any]:
        """Get provider health status and diagnostics."""
        pass


class LLMProviderFactory:
    """
    Factory for creating and managing LLM provider instances.
    
    Handles provider registration, creation, and configuration based on
    application settings.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize provider factory.
        
        Args:
            settings: Application configuration
        """
        self.settings = settings
        self._providers: Dict[str, LLMProvider] = {}

    def register_provider(self, name: str, provider: LLMProvider) -> None:
        """
        Register a provider instance.
        
        Args:
            name: Provider name/identifier
            provider: Provider instance to register
        """
        self._providers[name] = provider
        logger.info(f"Registered LLM provider: {name}")

    def get_provider(self, name: str) -> LLMProvider:
        """
        Get a registered provider by name.
        
        Args:
            name: Provider name
            
        Returns:
            Provider instance
            
        Raises:
            LLMProviderError: If provider not found
        """
        if name not in self._providers:
            raise LLMProviderError(f"Provider '{name}' not found")
        return self._providers[name]

    def list_providers(self) -> List[str]:
        """Get list of registered provider names."""
        return list(self._providers.keys())

    def create_provider(self, provider_type: str) -> LLMProvider:
        """
        Create a provider instance by type.
        
        Args:
            provider_type: Type of provider (ollama, openrouter, gemini, anthropic)
            
        Returns:
            Configured provider instance
            
        Raises:
            ConfigurationError: If provider type not supported or config invalid
        """
        provider_type = provider_type.lower()
        
        if provider_type == "ollama":
            from arete.services.ollama_provider import OllamaProvider
            return OllamaProvider(self.settings)
        elif provider_type == "openrouter":
            from arete.services.openrouter_provider import OpenRouterProvider
            return OpenRouterProvider(self.settings)
        elif provider_type == "gemini":
            from arete.services.gemini_provider import GeminiProvider
            return GeminiProvider(self.settings)
        elif provider_type == "anthropic":
            from .anthropic_provider import AnthropicProvider
            return AnthropicProvider(self.settings)
        elif provider_type == "openai":
            from arete.services.openai_provider import OpenAIProvider
            return OpenAIProvider(self.settings)
        else:
            raise ConfigurationError(
                f"Unsupported provider type: {provider_type}. "
                f"Supported types: ollama, openrouter, gemini, anthropic, openai"
            )


class MultiProviderLLMService(BaseService):
    """
    Multi-provider LLM service with intelligent routing and failover.
    
    Coordinates multiple LLM providers, handles failover, load balancing,
    and provides a unified interface for LLM generation.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize multi-provider LLM service.
        
        Args:
            settings: Application configuration
        """
        super().__init__(settings)
        self.settings = settings
        self.factory = LLMProviderFactory(settings)
        self._providers: List[LLMProvider] = []

    def initialize(self) -> None:
        """Initialize the service and all providers."""
        logger.info("Initializing MultiProviderLLMService")
        
        # Initialize all registered providers
        for provider in self._providers:
            try:
                provider.initialize()
                logger.info(f"Initialized provider: {provider.name}")
            except Exception as e:
                logger.error(f"Failed to initialize provider {provider.name}: {e}")
        
        self._is_initialized = True
        logger.info("MultiProviderLLMService initialization complete")

    def add_provider(self, provider: LLMProvider) -> None:
        """
        Add a provider to the service.
        
        Args:
            provider: Provider instance to add
        """
        self._providers.append(provider)
        logger.info(f"Added provider: {provider.name}")

    async def generate_response(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        preferred_provider: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate response using available providers with failover.
        
        Args:
            messages: Conversation messages
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            preferred_provider: Preferred provider name (if available)
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse from first successful provider
            
        Raises:
            LLMProviderError: If all providers fail or none configured
        """
        if not self._providers:
            raise LLMProviderError("No providers configured")
        
        # Use default settings if not provided
        max_tokens = max_tokens or self.settings.llm_max_tokens
        temperature = temperature or self.settings.llm_temperature
        
        # Try preferred provider first if specified and available
        providers_to_try = self._providers.copy()
        if preferred_provider:
            preferred = next((p for p in self._providers if p.name == preferred_provider), None)
            if preferred and preferred.is_available:
                providers_to_try.remove(preferred)
                providers_to_try.insert(0, preferred)
        
        last_error = None
        
        for provider in providers_to_try:
            if not provider.is_available:
                logger.debug(f"Skipping unavailable provider: {provider.name}")
                continue
            
            try:
                logger.debug(f"Attempting generation with provider: {provider.name}")
                
                response = await provider.generate_response(
                    messages=messages,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )
                
                logger.info(f"Successfully generated response with provider: {provider.name}")
                return response
                
            except (ProviderUnavailableError, RateLimitError, AuthenticationError) as e:
                logger.warning(f"Provider {provider.name} failed: {e}")
                last_error = e
                continue
            except Exception as e:
                logger.error(f"Unexpected error from provider {provider.name}: {e}")
                last_error = e
                continue
        
        # If we get here, all providers failed
        error_msg = "All providers failed to generate response"
        if last_error:
            error_msg += f". Last error: {last_error}"
        
        raise LLMProviderError(error_msg)

    async def generate_with_consensus(
        self,
        messages: List[LLMMessage],
        consensus_count: int = 2,
        **kwargs
    ) -> List[LLMResponse]:
        """
        Generate multiple responses for consensus or comparison.
        
        Args:
            messages: Conversation messages
            consensus_count: Number of responses to generate
            **kwargs: Generation parameters
            
        Returns:
            List of responses from different providers
        """
        if consensus_count > len(self._providers):
            raise LLMProviderError(
                f"Requested {consensus_count} responses but only {len(self._providers)} providers available"
            )
        
        available_providers = [p for p in self._providers if p.is_available]
        
        if consensus_count > len(available_providers):
            raise LLMProviderError(
                f"Requested {consensus_count} responses but only {len(available_providers)} providers available"
            )
        
        tasks = []
        for provider in available_providers[:consensus_count]:
            task = self._generate_with_single_provider(provider, messages, **kwargs)
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return successful responses
        successful_responses = []
        for response in responses:
            if isinstance(response, LLMResponse):
                successful_responses.append(response)
            else:
                logger.warning(f"Provider failed during consensus: {response}")
        
        return successful_responses

    async def _generate_with_single_provider(
        self,
        provider: LLMProvider,
        messages: List[LLMMessage],
        **kwargs
    ) -> LLMResponse:
        """Helper method for generating with a single provider."""
        return await provider.generate_response(messages, **kwargs)

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of all providers.
        
        Returns:
            Dictionary with provider health information
        """
        provider_statuses = []
        
        for provider in self._providers:
            try:
                status = provider.get_health_status()
                provider_statuses.append(status)
            except Exception as e:
                provider_statuses.append({
                    "provider": provider.name,
                    "status": "error",
                    "error": str(e)
                })
        
        healthy_count = sum(1 for status in provider_statuses if status.get("status") == "healthy")
        
        return {
            "service": "MultiProviderLLMService",
            "status": "healthy" if healthy_count > 0 else "unhealthy",
            "providers_total": len(self._providers),
            "providers_healthy": healthy_count,
            "providers": provider_statuses
        }

    def cleanup(self) -> None:
        """Cleanup service resources."""
        logger.info("Cleaning up MultiProviderLLMService")
        
        for provider in self._providers:
            try:
                if hasattr(provider, 'cleanup'):
                    provider.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up provider {provider.name}: {e}")
        
        self._providers.clear()
        logger.info("MultiProviderLLMService cleanup complete")


# Factory function for easy service creation
def create_llm_service(settings: Optional[Settings] = None) -> MultiProviderLLMService:
    """
    Create and configure a MultiProviderLLMService instance.
    
    Args:
        settings: Application settings (uses default if None)
        
    Returns:
        Configured LLM service instance
    """
    if settings is None:
        from arete.config import get_settings
        settings = get_settings()
    
    service = MultiProviderLLMService(settings)
    
    # Auto-register providers based on configuration
    llm_config = settings.llm_config
    
    # Register default provider
    try:
        default_provider = service.factory.create_provider(llm_config["default_provider"])
        service.add_provider(default_provider)
        logger.info(f"Registered default provider: {llm_config['default_provider']}")
    except Exception as e:
        logger.error(f"Failed to register default provider: {e}")
    
    return service


# Utility functions for message handling
def create_message(role: MessageRole, content: str, **metadata) -> LLMMessage:
    """Create an LLM message with metadata."""
    return LLMMessage(role=role, content=content, metadata=metadata)


def create_system_message(content: str, **metadata) -> LLMMessage:
    """Create a system message."""
    return LLMMessage(role=MessageRole.SYSTEM, content=content, metadata=metadata)


def create_user_message(content: str, **metadata) -> LLMMessage:
    """Create a user message."""
    return LLMMessage(role=MessageRole.USER, content=content, metadata=metadata)


def create_assistant_message(content: str, **metadata) -> LLMMessage:
    """Create an assistant message."""
    return LLMMessage(role=MessageRole.ASSISTANT, content=content, metadata=metadata)


def messages_to_dict(messages: List[LLMMessage]) -> List[Dict[str, Any]]:
    """Convert LLMMessage list to dictionary format."""
    return [
        {
            "role": msg.role.value,
            "content": msg.content,
            "metadata": msg.metadata
        }
        for msg in messages
    ]


def dict_to_messages(data: List[Dict[str, Any]]) -> List[LLMMessage]:
    """Convert dictionary format to LLMMessage list."""
    return [
        LLMMessage(
            role=MessageRole(item["role"]),
            content=item["content"],
            metadata=item.get("metadata", {})
        )
        for item in data
    ]