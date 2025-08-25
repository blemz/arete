"""
Simple LLM service for direct provider selection.

This service provides straightforward LLM access with user-controlled provider selection
via environment variables or direct input, without the complexity of intelligent routing.
"""

import logging
from typing import List, Dict, Any, Optional
import os

from arete.services.llm_provider import (
    LLMProviderFactory,
    LLMProvider,
    LLMMessage,
    LLMResponse,
    LLMProviderError,
    ProviderUnavailableError,
    AuthenticationError
)
from arete.config import Settings, get_settings

# Setup logger
logger = logging.getLogger(__name__)


class SimpleLLMService:
    """
    Simple LLM service with direct provider selection.
    
    Provides easy access to LLM providers with user-controlled selection:
    - Environment variable: SELECTED_LLM_PROVIDER
    - Direct method calls with provider parameter
    - Fallback to configured default provider
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize simple LLM service.
        
        Args:
            settings: Application configuration (uses default if None)
        """
        self.settings = settings or get_settings()
        self.factory = LLMProviderFactory(self.settings)
        self._providers: Dict[str, LLMProvider] = {}
        self._initialized_providers: Dict[str, bool] = {}
        
        # Available provider types
        self.available_provider_types = [
            "ollama", "openrouter", "gemini", "anthropic", "openai"
        ]
        
        logger.info("SimpleLLMService initialized")
    
    def get_active_provider_name(self) -> str:
        """
        Get the name of the currently active provider.
        
        Priority order:
        1. Environment variable SELECTED_LLM_PROVIDER
        2. Settings selected_llm_provider
        3. Settings default_llm_provider
        
        Returns:
            Name of active provider
        """
        # Check environment variable first
        env_provider = os.getenv("SELECTED_LLM_PROVIDER", "").lower().strip()
        if env_provider and env_provider in self.available_provider_types:
            return env_provider
        
        # Use settings selection
        return self.settings.active_llm_provider
    
    def get_active_model_name(self) -> str:
        """
        Get the name of the currently active model.
        
        Priority order:
        1. Environment variable SELECTED_LLM_MODEL
        2. Settings selected_llm_model
        3. Empty string (use provider default)
        
        Returns:
            Name of active model or empty string for provider default
        """
        # Check environment variable first
        env_model = os.getenv("SELECTED_LLM_MODEL", "").strip()
        if env_model:
            return env_model
        
        # Use settings selection
        return self.settings.active_llm_model
    
    def set_provider(self, provider_name: str) -> None:
        """
        Set the active provider by name.
        
        Args:
            provider_name: Name of provider to activate
            
        Raises:
            LLMProviderError: If provider name is invalid
        """
        provider_name = provider_name.lower().strip()
        
        if provider_name not in self.available_provider_types:
            raise LLMProviderError(
                f"Invalid provider '{provider_name}'. "
                f"Available: {', '.join(self.available_provider_types)}"
            )
        
        # Update environment variable for session
        os.environ["SELECTED_LLM_PROVIDER"] = provider_name
        logger.info(f"Active provider set to: {provider_name}")
    
    def set_model(self, model_name: str) -> None:
        """
        Set the active model by name.
        
        Args:
            model_name: Name of model to activate
        """
        model_name = model_name.strip()
        
        # Update environment variable for session
        os.environ["SELECTED_LLM_MODEL"] = model_name
        logger.info(f"Active model set to: {model_name}")
    
    def clear_model_selection(self) -> None:
        """Clear model selection to use provider default."""
        os.environ.pop("SELECTED_LLM_MODEL", None)
        logger.info("Model selection cleared, using provider default")
    
    def get_provider(self, provider_name: Optional[str] = None) -> LLMProvider:
        """
        Get a provider instance.
        
        Args:
            provider_name: Specific provider name (uses active if None)
            
        Returns:
            LLM provider instance
            
        Raises:
            LLMProviderError: If provider unavailable or invalid
        """
        provider_name = provider_name or self.get_active_provider_name()
        
        # Create provider if not cached
        if provider_name not in self._providers:
            try:
                provider = self.factory.create_provider(provider_name)
                self._providers[provider_name] = provider
                self._initialized_providers[provider_name] = False
                logger.info(f"Created provider: {provider_name}")
            except Exception as e:
                raise LLMProviderError(f"Failed to create provider '{provider_name}': {e}")
        
        provider = self._providers[provider_name]
        
        # Initialize if not already done
        if not self._initialized_providers.get(provider_name, False):
            try:
                provider.initialize()
                self._initialized_providers[provider_name] = True
                logger.info(f"Initialized provider: {provider_name}")
            except AuthenticationError:
                # Re-raise auth errors with helpful message
                raise AuthenticationError(
                    f"Authentication failed for {provider_name}. "
                    f"Please check your API key configuration.",
                    provider_name
                )
            except Exception as e:
                raise LLMProviderError(f"Failed to initialize provider '{provider_name}': {e}")
        
        return provider
    
    async def generate_response(
        self,
        messages: List[LLMMessage],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate response using specified or active provider.
        
        Args:
            messages: Conversation messages
            provider: Specific provider to use (uses active if None)
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLM response
            
        Raises:
            LLMProviderError: If generation fails
            ProviderUnavailableError: If provider unavailable
        """
        provider_name = provider or self.get_active_provider_name()
        model_name = model or self.get_active_model_name()
        
        try:
            provider_instance = self.get_provider(provider_name)
            
            if not provider_instance.is_available:
                raise ProviderUnavailableError(
                    f"Provider '{provider_name}' is not available. "
                    f"Please check configuration and API keys.",
                    provider_name
                )
            
            # Use settings defaults if not specified
            max_tokens = max_tokens or self.settings.llm_max_tokens
            temperature = temperature or self.settings.llm_temperature
            
            logger.info(f"Generating response with {provider_name}" + 
                       (f" using model {model_name}" if model_name else ""))
            
            response = await provider_instance.generate_response(
                messages=messages,
                model=model_name if model_name else None,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            # Add service metadata
            response.metadata.update({
                "service": "SimpleLLMService",
                "provider_selected_by": "user" if provider else "default",
                "model_selected_by": "user" if model else ("default" if model_name else "provider_default"),
                "active_provider": provider_name,
                "active_model": model_name or "provider_default"
            })
            
            logger.info(f"Generated response: {len(response.content)} chars, {response.usage_tokens} tokens")
            return response
            
        except (ProviderUnavailableError, AuthenticationError):
            # Re-raise these with provider context
            raise
        except Exception as e:
            logger.error(f"Error generating response with {provider_name}: {e}")
            raise LLMProviderError(f"Failed to generate response with {provider_name}: {e}")
    
    def list_available_providers(self) -> List[str]:
        """Get list of available provider types."""
        return self.available_provider_types.copy()
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about current provider configuration.
        
        Returns:
            Dictionary with provider information
        """
        active_provider = self.get_active_provider_name()
        
        # Check which providers have API keys configured
        configured_providers = []
        for provider_type in self.available_provider_types:
            if provider_type == "ollama":
                # Ollama doesn't need API key
                configured_providers.append(provider_type)
            else:
                api_key = getattr(self.settings, f"{provider_type}_api_key", "")
                if api_key and api_key.strip():
                    configured_providers.append(provider_type)
        
        active_model = self.get_active_model_name()
        
        return {
            "active_provider": active_provider,
            "active_model": active_model or "provider_default",
            "available_providers": self.available_provider_types,
            "configured_providers": configured_providers,
            "provider_source": {
                "env_variable": os.getenv("SELECTED_LLM_PROVIDER", ""),
                "settings_selected": self.settings.selected_llm_provider,
                "settings_default": self.settings.default_llm_provider
            },
            "model_source": {
                "env_variable": os.getenv("SELECTED_LLM_MODEL", ""),
                "settings_selected": self.settings.selected_llm_model
            },
            "initialization_status": dict(self._initialized_providers)
        }
    
    def get_provider_health(self, provider_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get health status of a specific provider.
        
        Args:
            provider_name: Provider to check (uses active if None)
            
        Returns:
            Health status information
        """
        provider_name = provider_name or self.get_active_provider_name()
        
        try:
            provider_instance = self.get_provider(provider_name)
            return provider_instance.get_health_status()
        except Exception as e:
            return {
                "provider": provider_name,
                "status": "error",
                "error": str(e),
                "available": False
            }
    
    def cleanup(self) -> None:
        """Cleanup service resources."""
        logger.info("Cleaning up SimpleLLMService")
        
        for provider_name, provider in self._providers.items():
            try:
                if hasattr(provider, 'cleanup'):
                    provider.cleanup()
                logger.info(f"Cleaned up provider: {provider_name}")
            except Exception as e:
                logger.error(f"Error cleaning up provider {provider_name}: {e}")
        
        self._providers.clear()
        self._initialized_providers.clear()
        logger.info("SimpleLLMService cleanup complete")


# Convenience functions
def get_llm_service(settings: Optional[Settings] = None) -> SimpleLLMService:
    """Get a SimpleLLMService instance."""
    return SimpleLLMService(settings)


async def quick_generate(
    prompt: str,
    provider: Optional[str] = None,
    **kwargs
) -> str:
    """
    Quick utility function for simple text generation.
    
    Args:
        prompt: Text prompt
        provider: Provider to use (uses active if None)
        **kwargs: Additional generation parameters
        
    Returns:
        Generated response text
    """
    from arete.services.llm_provider import LLMMessage, MessageRole
    
    service = get_llm_service()
    
    messages = [LLMMessage(role=MessageRole.USER, content=prompt)]
    
    response = await service.generate_response(
        messages=messages,
        provider=provider,
        **kwargs
    )
    
    return response.content


def show_provider_status() -> None:
    """Print current provider status information."""
    service = get_llm_service()
    info = service.get_provider_info()
    
    print("LLM Provider Status")
    print("=" * 50)
    print(f"Active Provider: {info['active_provider']}")
    print(f"Active Model: {info['active_model']}")
    print(f"Available Providers: {', '.join(info['available_providers'])}")
    print(f"Configured Providers: {', '.join(info['configured_providers'])}")
    print()
    print("Provider Configuration Source:")
    print(f"  Environment Variable: {info['provider_source']['env_variable'] or 'Not set'}")
    print(f"  Settings Selected: {info['provider_source']['settings_selected'] or 'Not set'}")
    print(f"  Settings Default: {info['provider_source']['settings_default']}")
    print()
    print("Model Configuration Source:")
    print(f"  Environment Variable: {info['model_source']['env_variable'] or 'Not set'}")
    print(f"  Settings Selected: {info['model_source']['settings_selected'] or 'Not set'}")
    print()
    
    if info['initialization_status']:
        print("Provider Initialization:")
        for provider, initialized in info['initialization_status'].items():
            status = "[OK] Initialized" if initialized else "[--] Not initialized"
            print(f"  {provider}: {status}")


def set_provider_interactive() -> None:
    """Interactive provider selection."""
    service = get_llm_service()
    info = service.get_provider_info()
    
    print("🤖 Select LLM Provider")
    print("=" * 30)
    
    for i, provider in enumerate(info['available_providers'], 1):
        configured = "✅" if provider in info['configured_providers'] else "❌"
        active = "👈 ACTIVE" if provider == info['active_provider'] else ""
        print(f"{i}. {provider} {configured} {active}")
    
    print("\n✅ = Configured with API key")
    print("❌ = Missing API key configuration")
    
    try:
        choice = input(f"\nSelect provider (1-{len(info['available_providers'])}): ").strip()
        index = int(choice) - 1
        
        if 0 <= index < len(info['available_providers']):
            selected_provider = info['available_providers'][index]
            service.set_provider(selected_provider)
            print(f"✅ Provider set to: {selected_provider}")
        else:
            print("❌ Invalid selection")
            
    except (ValueError, KeyboardInterrupt):
        print("\n❌ Selection cancelled")


if __name__ == "__main__":
    # Quick test/demo
    import asyncio
    
    async def demo():
        print("🤖 SimpleLLMService Demo")
        print("=" * 30)
        
        show_provider_status()
        
        # Quick generation example
        try:
            response = await quick_generate("Hello, how are you?")
            print(f"\nResponse: {response}")
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    asyncio.run(demo())