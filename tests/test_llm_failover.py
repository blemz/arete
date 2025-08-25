"""
Test suite for LLM provider failover and load balancing.

Tests the multi-provider LLM service's ability to handle provider failures,
route requests intelligently, and maintain reliability across providers.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio
from typing import List, Dict, Any

from arete.services.llm_provider import (
    MultiProviderLLMService,
    LLMProviderFactory,
    LLMProvider,
    LLMMessage,
    LLMResponse,
    MessageRole,
    LLMProviderError,
    ProviderUnavailableError,
    RateLimitError,
    AuthenticationError
)
from arete.config import Settings


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""
    
    def __init__(self, name: str, is_available: bool = True, should_fail: bool = False):
        super().__init__(name)
        self._is_available = is_available
        self._should_fail = should_fail
        self._initialized = False
        self._models = ["mock-model-1", "mock-model-2"]
        
    @property
    def is_available(self) -> bool:
        return self._is_available
    
    @property
    def supported_models(self) -> List[str]:
        return self._models
    
    def initialize(self) -> None:
        self._initialized = True
    
    async def generate_response(
        self,
        messages: List[LLMMessage],
        model: str = None,
        max_tokens: int = None,
        temperature: float = None,
        **kwargs
    ) -> LLMResponse:
        if self._should_fail:
            raise LLMProviderError(f"Mock failure from {self.name}")
        
        return LLMResponse(
            content=f"Mock response from {self.name}",
            provider=self.name,
            model=model or "mock-model-1",
            usage_tokens=50
        )
    
    def get_health_status(self) -> Dict[str, Any]:
        return {
            "provider": self.name,
            "status": "healthy" if self._is_available else "unhealthy",
            "initialized": self._initialized
        }


class TestMultiProviderLLMService:
    """Test multi-provider LLM service functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.settings = Settings(
            llm_max_tokens=1000,
            llm_temperature=0.7,
            llm_timeout=30
        )
        self.service = MultiProviderLLMService(self.settings)
        
        # Create mock providers
        self.provider_a = MockLLMProvider("provider_a", is_available=True)
        self.provider_b = MockLLMProvider("provider_b", is_available=True)
        self.provider_c = MockLLMProvider("provider_c", is_available=False)
        
    def test_service_initialization(self):
        """Test service initialization."""
        assert self.service.settings == self.settings
        assert self.service.factory is not None
        assert len(self.service._providers) == 0
        assert not self.service._is_initialized
    
    def test_add_provider(self):
        """Test adding providers to service."""
        self.service.add_provider(self.provider_a)
        assert len(self.service._providers) == 1
        assert self.provider_a in self.service._providers
    
    def test_service_initialization_with_providers(self):
        """Test service initialization with providers."""
        self.service.add_provider(self.provider_a)
        self.service.add_provider(self.provider_b)
        
        self.service.initialize()
        
        assert self.service._is_initialized
        assert self.provider_a._initialized
        assert self.provider_b._initialized
    
    @pytest.mark.asyncio
    async def test_generate_response_no_providers(self):
        """Test response generation with no providers configured."""
        messages = [
            LLMMessage(role=MessageRole.USER, content="Hello")
        ]
        
        with pytest.raises(LLMProviderError, match="No providers configured"):
            await self.service.generate_response(messages)
    
    @pytest.mark.asyncio
    async def test_generate_response_single_provider(self):
        """Test response generation with single available provider."""
        self.service.add_provider(self.provider_a)
        self.service.initialize()
        
        messages = [
            LLMMessage(role=MessageRole.USER, content="Hello")
        ]
        
        response = await self.service.generate_response(messages)
        
        assert response.content == "Mock response from provider_a"
        assert response.provider == "provider_a"
        assert response.usage_tokens == 50
    
    @pytest.mark.asyncio
    async def test_generate_response_preferred_provider(self):
        """Test response generation with preferred provider."""
        self.service.add_provider(self.provider_a)
        self.service.add_provider(self.provider_b)
        self.service.initialize()
        
        messages = [
            LLMMessage(role=MessageRole.USER, content="Hello")
        ]
        
        # Test with preferred provider
        response = await self.service.generate_response(
            messages, 
            preferred_provider="provider_b"
        )
        
        assert response.content == "Mock response from provider_b"
        assert response.provider == "provider_b"
    
    @pytest.mark.asyncio
    async def test_generate_response_provider_failover(self):
        """Test failover when first provider fails."""
        # Create failing and working providers
        failing_provider = MockLLMProvider("failing", is_available=True, should_fail=True)
        working_provider = MockLLMProvider("working", is_available=True, should_fail=False)
        
        self.service.add_provider(failing_provider)
        self.service.add_provider(working_provider)
        self.service.initialize()
        
        messages = [
            LLMMessage(role=MessageRole.USER, content="Hello")
        ]
        
        response = await self.service.generate_response(messages)
        
        # Should get response from working provider after failing provider fails
        assert response.content == "Mock response from working"
        assert response.provider == "working"
    
    @pytest.mark.asyncio
    async def test_generate_response_all_providers_fail(self):
        """Test behavior when all providers fail."""
        failing_a = MockLLMProvider("failing_a", is_available=True, should_fail=True)
        failing_b = MockLLMProvider("failing_b", is_available=True, should_fail=True)
        
        self.service.add_provider(failing_a)
        self.service.add_provider(failing_b)
        self.service.initialize()
        
        messages = [
            LLMMessage(role=MessageRole.USER, content="Hello")
        ]
        
        with pytest.raises(LLMProviderError, match="All providers failed to generate response"):
            await self.service.generate_response(messages)
    
    @pytest.mark.asyncio
    async def test_generate_response_unavailable_providers_skipped(self):
        """Test that unavailable providers are skipped."""
        self.service.add_provider(self.provider_c)  # unavailable
        self.service.add_provider(self.provider_a)  # available
        self.service.initialize()
        
        messages = [
            LLMMessage(role=MessageRole.USER, content="Hello")
        ]
        
        response = await self.service.generate_response(messages)
        
        # Should skip unavailable provider and use available one
        assert response.content == "Mock response from provider_a"
        assert response.provider == "provider_a"
    
    @pytest.mark.asyncio
    async def test_generate_with_consensus(self):
        """Test generating multiple responses for consensus."""
        self.service.add_provider(self.provider_a)
        self.service.add_provider(self.provider_b)
        self.service.initialize()
        
        messages = [
            LLMMessage(role=MessageRole.USER, content="Hello")
        ]
        
        responses = await self.service.generate_with_consensus(
            messages, 
            consensus_count=2
        )
        
        assert len(responses) == 2
        assert responses[0].provider != responses[1].provider
        assert all(isinstance(r, LLMResponse) for r in responses)
    
    @pytest.mark.asyncio
    async def test_generate_with_consensus_insufficient_providers(self):
        """Test consensus generation with insufficient providers."""
        self.service.add_provider(self.provider_a)
        self.service.initialize()
        
        messages = [
            LLMMessage(role=MessageRole.USER, content="Hello")
        ]
        
        with pytest.raises(LLMProviderError, match="only 1 providers available"):
            await self.service.generate_with_consensus(messages, consensus_count=3)
    
    @pytest.mark.asyncio
    async def test_generate_with_consensus_unavailable_providers(self):
        """Test consensus generation accounting for unavailable providers."""
        self.service.add_provider(self.provider_a)  # available
        self.service.add_provider(self.provider_c)  # unavailable
        self.service.initialize()
        
        messages = [
            LLMMessage(role=MessageRole.USER, content="Hello")
        ]
        
        with pytest.raises(LLMProviderError, match="only 1 providers available"):
            await self.service.generate_with_consensus(messages, consensus_count=2)
    
    def test_get_health_status(self):
        """Test health status reporting."""
        self.service.add_provider(self.provider_a)  # healthy
        self.service.add_provider(self.provider_c)  # unhealthy
        self.service.initialize()
        
        status = self.service.get_health_status()
        
        assert status["service"] == "MultiProviderLLMService"
        assert status["status"] == "healthy"  # at least one provider is healthy
        assert status["providers_total"] == 2
        assert status["providers_healthy"] == 1
        assert len(status["providers"]) == 2
    
    def test_get_health_status_all_unhealthy(self):
        """Test health status when all providers are unhealthy."""
        # Create all unhealthy providers
        unhealthy_a = MockLLMProvider("unhealthy_a", is_available=False)
        unhealthy_b = MockLLMProvider("unhealthy_b", is_available=False)
        
        self.service.add_provider(unhealthy_a)
        self.service.add_provider(unhealthy_b)
        self.service.initialize()
        
        status = self.service.get_health_status()
        
        assert status["status"] == "unhealthy"
        assert status["providers_healthy"] == 0
    
    def test_cleanup(self):
        """Test service cleanup."""
        self.service.add_provider(self.provider_a)
        self.service.add_provider(self.provider_b)
        self.service.initialize()
        
        assert len(self.service._providers) == 2
        
        self.service.cleanup()
        
        assert len(self.service._providers) == 0


class TestLLMProviderFactory:
    """Test LLM provider factory functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.settings = Settings()
        self.factory = LLMProviderFactory(self.settings)
    
    def test_factory_initialization(self):
        """Test factory initialization."""
        assert self.factory.settings == self.settings
        assert len(self.factory._providers) == 0
    
    def test_register_provider(self):
        """Test provider registration."""
        provider = MockLLMProvider("test_provider")
        
        self.factory.register_provider("test", provider)
        
        assert "test" in self.factory._providers
        assert self.factory._providers["test"] == provider
    
    def test_get_provider(self):
        """Test getting registered provider."""
        provider = MockLLMProvider("test_provider")
        self.factory.register_provider("test", provider)
        
        retrieved = self.factory.get_provider("test")
        assert retrieved == provider
    
    def test_get_provider_not_found(self):
        """Test getting non-existent provider."""
        with pytest.raises(LLMProviderError, match="Provider 'nonexistent' not found"):
            self.factory.get_provider("nonexistent")
    
    def test_list_providers(self):
        """Test listing registered providers."""
        provider_a = MockLLMProvider("provider_a")
        provider_b = MockLLMProvider("provider_b")
        
        self.factory.register_provider("a", provider_a)
        self.factory.register_provider("b", provider_b)
        
        providers = self.factory.list_providers()
        assert set(providers) == {"a", "b"}
    
    @patch('arete.services.ollama_provider.OllamaProvider')
    def test_create_ollama_provider(self, mock_ollama):
        """Test creating Ollama provider."""
        mock_instance = Mock()
        mock_ollama.return_value = mock_instance
        
        provider = self.factory.create_provider("ollama")
        
        mock_ollama.assert_called_once_with(self.settings)
        assert provider == mock_instance
    
    @patch('arete.services.openrouter_provider.OpenRouterProvider')
    def test_create_openrouter_provider(self, mock_openrouter):
        """Test creating OpenRouter provider."""
        mock_instance = Mock()
        mock_openrouter.return_value = mock_instance
        
        provider = self.factory.create_provider("openrouter")
        
        mock_openrouter.assert_called_once_with(self.settings)
        assert provider == mock_instance
    
    @patch('arete.services.gemini_provider.GeminiProvider')
    def test_create_gemini_provider(self, mock_gemini):
        """Test creating Gemini provider."""
        mock_instance = Mock()
        mock_gemini.return_value = mock_instance
        
        provider = self.factory.create_provider("gemini")
        
        mock_gemini.assert_called_once_with(self.settings)
        assert provider == mock_instance
    
    @patch('arete.services.anthropic_provider.AnthropicProvider')
    def test_create_anthropic_provider(self, mock_anthropic):
        """Test creating Anthropic provider."""
        mock_instance = Mock()
        mock_anthropic.return_value = mock_instance
        
        provider = self.factory.create_provider("anthropic")
        
        mock_anthropic.assert_called_once_with(self.settings)
        assert provider == mock_instance
    
    @patch('arete.services.openai_provider.OpenAIProvider')
    def test_create_openai_provider(self, mock_openai):
        """Test creating OpenAI provider."""
        mock_instance = Mock()
        mock_openai.return_value = mock_instance
        
        provider = self.factory.create_provider("openai")
        
        mock_openai.assert_called_once_with(self.settings)
        assert provider == mock_instance
    
    def test_create_unsupported_provider(self):
        """Test creating unsupported provider type."""
        with pytest.raises(Exception, match="Unsupported provider type"):
            self.factory.create_provider("unsupported")


class TestProviderRouting:
    """Test intelligent provider routing and load balancing."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.settings = Settings()
        self.service = MultiProviderLLMService(self.settings)
        
        # Create providers with different characteristics
        self.fast_provider = MockLLMProvider("fast", is_available=True)
        self.slow_provider = MockLLMProvider("slow", is_available=True)
        self.premium_provider = MockLLMProvider("premium", is_available=True)
    
    @pytest.mark.asyncio
    async def test_provider_priority_ordering(self):
        """Test that providers are tried in priority order."""
        # Add providers in specific order
        self.service.add_provider(self.slow_provider)   # First in list
        self.service.add_provider(self.fast_provider)   # Second in list
        self.service.initialize()
        
        messages = [
            LLMMessage(role=MessageRole.USER, content="Hello")
        ]
        
        response = await self.service.generate_response(messages)
        
        # Should use first available provider (slow_provider)
        assert response.provider == "slow"
    
    @pytest.mark.asyncio
    async def test_preferred_provider_priority(self):
        """Test that preferred provider is prioritized."""
        self.service.add_provider(self.fast_provider)
        self.service.add_provider(self.premium_provider)
        self.service.initialize()
        
        messages = [
            LLMMessage(role=MessageRole.USER, content="Hello")
        ]
        
        response = await self.service.generate_response(
            messages,
            preferred_provider="premium"
        )
        
        # Should use preferred provider even though it's not first
        assert response.provider == "premium"
    
    @pytest.mark.asyncio
    async def test_preferred_provider_unavailable_fallback(self):
        """Test fallback when preferred provider is unavailable."""
        unavailable_provider = MockLLMProvider("unavailable", is_available=False)
        
        self.service.add_provider(unavailable_provider)
        self.service.add_provider(self.fast_provider)
        self.service.initialize()
        
        messages = [
            LLMMessage(role=MessageRole.USER, content="Hello")
        ]
        
        response = await self.service.generate_response(
            messages,
            preferred_provider="unavailable"
        )
        
        # Should fallback to available provider
        assert response.provider == "fast"


class TestErrorHandling:
    """Test error handling and recovery scenarios."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.settings = Settings()
        self.service = MultiProviderLLMService(self.settings)
    
    @pytest.mark.asyncio
    async def test_rate_limit_error_handling(self):
        """Test handling of rate limit errors."""
        # Create provider that raises rate limit error
        rate_limited_provider = MockLLMProvider("rate_limited", is_available=True)
        working_provider = MockLLMProvider("working", is_available=True)
        
        # Mock the rate limited provider to raise RateLimitError
        async def raise_rate_limit(*args, **kwargs):
            raise RateLimitError("Rate limit exceeded", retry_after=60)
        
        rate_limited_provider.generate_response = raise_rate_limit
        
        self.service.add_provider(rate_limited_provider)
        self.service.add_provider(working_provider)
        self.service.initialize()
        
        messages = [
            LLMMessage(role=MessageRole.USER, content="Hello")
        ]
        
        response = await self.service.generate_response(messages)
        
        # Should fallback to working provider
        assert response.provider == "working"
    
    @pytest.mark.asyncio
    async def test_authentication_error_handling(self):
        """Test handling of authentication errors."""
        # Create provider that raises authentication error
        auth_failed_provider = MockLLMProvider("auth_failed", is_available=True)
        working_provider = MockLLMProvider("working", is_available=True)
        
        # Mock the auth failed provider to raise AuthenticationError
        async def raise_auth_error(*args, **kwargs):
            raise AuthenticationError("Invalid API key", "auth_failed")
        
        auth_failed_provider.generate_response = raise_auth_error
        
        self.service.add_provider(auth_failed_provider)
        self.service.add_provider(working_provider)
        self.service.initialize()
        
        messages = [
            LLMMessage(role=MessageRole.USER, content="Hello")
        ]
        
        response = await self.service.generate_response(messages)
        
        # Should fallback to working provider
        assert response.provider == "working"
    
    @pytest.mark.asyncio
    async def test_provider_unavailable_error_handling(self):
        """Test handling of provider unavailable errors."""
        # Create provider that raises unavailable error
        unavailable_provider = MockLLMProvider("unavailable_provider", is_available=True)
        working_provider = MockLLMProvider("working", is_available=True)
        
        # Mock the unavailable provider to raise ProviderUnavailableError
        async def raise_unavailable_error(*args, **kwargs):
            raise ProviderUnavailableError("Service temporarily unavailable", "unavailable_provider")
        
        unavailable_provider.generate_response = raise_unavailable_error
        
        self.service.add_provider(unavailable_provider)
        self.service.add_provider(working_provider)
        self.service.initialize()
        
        messages = [
            LLMMessage(role=MessageRole.USER, content="Hello")
        ]
        
        response = await self.service.generate_response(messages)
        
        # Should fallback to working provider
        assert response.provider == "working"


class TestServiceIntegration:
    """Test full service integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_create_llm_service_factory_function(self):
        """Test the create_llm_service factory function."""
        from arete.services.llm_provider import create_llm_service
        
        # Test with custom settings
        settings = Settings(
            default_llm_provider="ollama",
            llm_max_tokens=2000
        )
        
        with patch('arete.services.llm_provider.MultiProviderLLMService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            # Mock the factory and provider creation
            mock_factory = Mock()
            mock_service.factory = mock_factory
            mock_provider = Mock()
            mock_factory.create_provider.return_value = mock_provider
            
            service = create_llm_service(settings)
            
            # Should create service with settings
            mock_service_class.assert_called_once_with(settings)
            
            # Should try to create default provider
            mock_factory.create_provider.assert_called_once_with("ollama")
            mock_service.add_provider.assert_called_once_with(mock_provider)
    
    @pytest.mark.asyncio
    async def test_end_to_end_philosophical_conversation(self):
        """Test end-to-end philosophical conversation scenario."""
        service = MultiProviderLLMService(Settings())
        
        # Create mock provider for philosophy
        philosophy_provider = MockLLMProvider("philosophy_ai", is_available=True)
        
        # Override generate_response to provide philosophical content
        async def philosophical_response(messages, **kwargs):
            if "Aristotle" in messages[-1].content:
                return LLMResponse(
                    content="Aristotle's concept of eudaimonia refers to human flourishing or well-being...",
                    provider="philosophy_ai",
                    model="philosophy-gpt-4",
                    usage_tokens=150,
                    metadata={"philosophical_accuracy": 0.95}
                )
            return LLMResponse(
                content="I can help with philosophical questions.",
                provider="philosophy_ai",
                model="philosophy-gpt-4",
                usage_tokens=25
            )
        
        philosophy_provider.generate_response = philosophical_response
        
        service.add_provider(philosophy_provider)
        service.initialize()
        
        # Test philosophical conversation
        messages = [
            LLMMessage(role=MessageRole.SYSTEM, content="You are a philosophy tutor."),
            LLMMessage(role=MessageRole.USER, content="What is Aristotle's concept of eudaimonia?")
        ]
        
        response = await service.generate_response(messages)
        
        assert "Aristotle" in response.content
        assert "eudaimonia" in response.content
        assert response.provider == "philosophy_ai"
        assert response.usage_tokens == 150
        assert response.metadata.get("philosophical_accuracy") == 0.95