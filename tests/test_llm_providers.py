"""
Test suite for LLM provider abstraction layer.

Tests the unified interface for multiple LLM providers including base abstractions,
provider implementations, and multi-provider coordination capabilities.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from arete.services.llm_provider import (
    LLMProvider,
    LLMResponse,
    LLMProviderError,
    ProviderUnavailableError,
    RateLimitError,
    AuthenticationError,
    LLMMessage,
    MessageRole,
    LLMProviderFactory,
    MultiProviderLLMService
)
from arete.config import Settings


@dataclass
class MockProviderConfig:
    """Mock provider configuration for testing."""
    name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.7


class TestLLMResponse:
    """Test LLMResponse data structure."""
    
    def test_llm_response_creation(self):
        """Test LLMResponse creation with all fields."""
        response = LLMResponse(
            content="Test response content",
            usage_tokens=150,
            provider="test-provider",
            model="test-model",
            finish_reason="stop",
            metadata={"confidence": 0.95}
        )
        
        assert response.content == "Test response content"
        assert response.usage_tokens == 150
        assert response.provider == "test-provider"
        assert response.model == "test-model"
        assert response.finish_reason == "stop"
        assert response.metadata["confidence"] == 0.95

    def test_llm_response_minimal(self):
        """Test LLMResponse creation with minimal required fields."""
        response = LLMResponse(
            content="Minimal response",
            provider="test-provider"
        )
        
        assert response.content == "Minimal response"
        assert response.provider == "test-provider"
        assert response.usage_tokens is None
        assert response.model is None
        assert response.finish_reason is None
        assert response.metadata == {}


class TestLLMMessage:
    """Test LLMMessage data structure."""
    
    def test_llm_message_creation(self):
        """Test LLMMessage creation with role and content."""
        message = LLMMessage(
            role=MessageRole.USER,
            content="Test user message"
        )
        
        assert message.role == MessageRole.USER
        assert message.content == "Test user message"
        assert message.metadata == {}

    def test_llm_message_with_metadata(self):
        """Test LLMMessage with metadata."""
        message = LLMMessage(
            role=MessageRole.ASSISTANT,
            content="Test assistant response",
            metadata={"confidence": 0.9, "citations": ["source1", "source2"]}
        )
        
        assert message.role == MessageRole.ASSISTANT
        assert message.content == "Test assistant response"
        assert message.metadata["confidence"] == 0.9
        assert message.metadata["citations"] == ["source1", "source2"]

    def test_message_role_enum(self):
        """Test MessageRole enum values."""
        assert MessageRole.SYSTEM.value == "system"
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"


class TestLLMProviderExceptions:
    """Test LLM provider exception hierarchy."""
    
    def test_llm_provider_error_base(self):
        """Test base LLMProviderError exception."""
        error = LLMProviderError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_provider_unavailable_error(self):
        """Test ProviderUnavailableError exception."""
        error = ProviderUnavailableError("Provider offline", provider="test-provider")
        assert error.provider == "test-provider"
        assert "Provider offline" in str(error)

    def test_rate_limit_error(self):
        """Test RateLimitError exception."""
        error = RateLimitError("Rate limit exceeded", retry_after=60)
        assert error.retry_after == 60
        assert "Rate limit exceeded" in str(error)

    def test_authentication_error(self):
        """Test AuthenticationError exception."""
        error = AuthenticationError("Invalid API key", provider="test-provider")
        assert error.provider == "test-provider"
        assert "Invalid API key" in str(error)


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""
    
    def __init__(self, config: MockProviderConfig):
        super().__init__(config.name)
        self.config = config
        self._initialized = False
        self._available = True

    @property
    def is_available(self) -> bool:
        return self._available

    @property
    def supported_models(self) -> List[str]:
        return ["mock-model-1", "mock-model-2"]

    def initialize(self) -> None:
        self._initialized = True

    async def generate_response(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> LLMResponse:
        """Mock response generation."""
        if not self._available:
            raise ProviderUnavailableError("Mock provider unavailable", provider=self.name)
        
        if not self._initialized:
            raise LLMProviderError("Provider not initialized")
        
        # Simulate response based on input
        user_message = next((msg.content for msg in messages if msg.role == MessageRole.USER), "")
        response_content = f"Mock response to: {user_message}"
        
        return LLMResponse(
            content=response_content,
            usage_tokens=len(response_content.split()) * 2,  # Simple token estimate
            provider=self.name,
            model=model or "mock-model-1",
            finish_reason="stop"
        )

    def get_health_status(self) -> Dict[str, Any]:
        return {
            "status": "healthy" if self._available else "unhealthy",
            "initialized": self._initialized,
            "provider": self.name
        }


class TestLLMProviderBase:
    """Test base LLM provider functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.provider = MockLLMProvider(MockProviderConfig("mock-provider"))

    def test_provider_initialization(self):
        """Test provider initialization."""
        assert self.provider.name == "mock-provider"
        assert not self.provider._initialized
        
        self.provider.initialize()
        assert self.provider._initialized

    def test_provider_availability_check(self):
        """Test provider availability checking."""
        assert self.provider.is_available
        
        self.provider._available = False
        assert not self.provider.is_available

    def test_supported_models_property(self):
        """Test supported models property."""
        models = self.provider.supported_models
        assert isinstance(models, list)
        assert len(models) > 0
        assert "mock-model-1" in models

    @pytest.mark.asyncio
    async def test_generate_response_success(self):
        """Test successful response generation."""
        self.provider.initialize()
        
        messages = [
            LLMMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
            LLMMessage(role=MessageRole.USER, content="What is philosophy?")
        ]
        
        response = await self.provider.generate_response(messages)
        
        assert isinstance(response, LLMResponse)
        assert response.content == "Mock response to: What is philosophy?"
        assert response.provider == "mock-provider"
        assert response.model == "mock-model-1"
        assert response.usage_tokens > 0

    @pytest.mark.asyncio
    async def test_generate_response_with_parameters(self):
        """Test response generation with custom parameters."""
        self.provider.initialize()
        
        messages = [LLMMessage(role=MessageRole.USER, content="Test message")]
        
        response = await self.provider.generate_response(
            messages,
            model="mock-model-2",
            max_tokens=500,
            temperature=0.9
        )
        
        assert response.model == "mock-model-2"

    @pytest.mark.asyncio
    async def test_generate_response_provider_unavailable(self):
        """Test response generation when provider is unavailable."""
        self.provider.initialize()
        self.provider._available = False
        
        messages = [LLMMessage(role=MessageRole.USER, content="Test")]
        
        with pytest.raises(ProviderUnavailableError) as exc_info:
            await self.provider.generate_response(messages)
        
        assert exc_info.value.provider == "mock-provider"

    @pytest.mark.asyncio
    async def test_generate_response_not_initialized(self):
        """Test response generation when provider is not initialized."""
        messages = [LLMMessage(role=MessageRole.USER, content="Test")]
        
        with pytest.raises(LLMProviderError):
            await self.provider.generate_response(messages)

    def test_health_status(self):
        """Test health status reporting."""
        status = self.provider.get_health_status()
        
        assert isinstance(status, dict)
        assert "status" in status
        assert "initialized" in status
        assert "provider" in status
        assert status["provider"] == "mock-provider"


class TestLLMProviderFactory:
    """Test LLM provider factory functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.settings = Settings()
        self.factory = LLMProviderFactory(self.settings)

    def test_factory_initialization(self):
        """Test factory initialization."""
        assert self.factory.settings == self.settings
        assert isinstance(self.factory._providers, dict)

    def test_register_provider(self):
        """Test provider registration."""
        provider = MockLLMProvider(MockProviderConfig("test-provider"))
        
        self.factory.register_provider("test", provider)
        
        assert "test" in self.factory._providers
        assert self.factory._providers["test"] == provider

    def test_get_provider_exists(self):
        """Test getting registered provider."""
        provider = MockLLMProvider(MockProviderConfig("test-provider"))
        self.factory.register_provider("test", provider)
        
        retrieved = self.factory.get_provider("test")
        assert retrieved == provider

    def test_get_provider_not_exists(self):
        """Test getting non-existent provider."""
        with pytest.raises(LLMProviderError, match="Provider 'nonexistent' not found"):
            self.factory.get_provider("nonexistent")

    def test_list_providers(self):
        """Test listing registered providers."""
        provider1 = MockLLMProvider(MockProviderConfig("provider1"))
        provider2 = MockLLMProvider(MockProviderConfig("provider2"))
        
        self.factory.register_provider("p1", provider1)
        self.factory.register_provider("p2", provider2)
        
        providers = self.factory.list_providers()
        assert len(providers) == 2
        assert "p1" in providers
        assert "p2" in providers

    @patch('arete.services.ollama_provider.OllamaProvider')
    def test_create_ollama_provider(self, mock_ollama):
        """Test creating Ollama provider."""
        mock_instance = Mock()
        mock_ollama.return_value = mock_instance
        
        provider = self.factory.create_provider("ollama")
        
        assert provider == mock_instance
        mock_ollama.assert_called_once_with(self.settings)

    @patch('arete.services.openrouter_provider.OpenRouterProvider')
    def test_create_openrouter_provider(self, mock_openrouter):
        """Test creating OpenRouter provider."""
        mock_instance = Mock()
        mock_openrouter.return_value = mock_instance
        
        provider = self.factory.create_provider("openrouter")
        
        assert provider == mock_instance
        mock_openrouter.assert_called_once_with(self.settings)


class TestMultiProviderLLMService:
    """Test multi-provider LLM service coordination."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.settings = Settings()
        self.service = MultiProviderLLMService(self.settings)

    def test_service_initialization(self):
        """Test service initialization."""
        assert self.service.settings == self.settings
        assert isinstance(self.service.factory, LLMProviderFactory)
        assert isinstance(self.service._providers, list)

    def test_add_provider(self):
        """Test adding provider to service."""
        provider = MockLLMProvider(MockProviderConfig("test-provider"))
        
        self.service.add_provider(provider)
        
        assert len(self.service._providers) == 1
        assert self.service._providers[0] == provider

    def test_add_multiple_providers(self):
        """Test adding multiple providers."""
        provider1 = MockLLMProvider(MockProviderConfig("provider1"))
        provider2 = MockLLMProvider(MockProviderConfig("provider2"))
        
        self.service.add_provider(provider1)
        self.service.add_provider(provider2)
        
        assert len(self.service._providers) == 2

    @pytest.mark.asyncio
    async def test_generate_with_single_provider(self):
        """Test response generation with single provider."""
        provider = MockLLMProvider(MockProviderConfig("test-provider"))
        provider.initialize()
        
        self.service.add_provider(provider)
        
        messages = [LLMMessage(role=MessageRole.USER, content="Test question")]
        
        response = await self.service.generate_response(messages)
        
        assert isinstance(response, LLMResponse)
        assert response.provider == "test-provider"
        assert "Test question" in response.content

    @pytest.mark.asyncio
    async def test_generate_with_provider_failover(self):
        """Test failover to secondary provider when primary fails."""
        # Primary provider that will fail
        primary = MockLLMProvider(MockProviderConfig("primary"))
        primary.initialize()
        primary._available = False
        
        # Secondary provider that will succeed
        secondary = MockLLMProvider(MockProviderConfig("secondary"))
        secondary.initialize()
        
        self.service.add_provider(primary)
        self.service.add_provider(secondary)
        
        messages = [LLMMessage(role=MessageRole.USER, content="Test question")]
        
        response = await self.service.generate_response(messages)
        
        assert response.provider == "secondary"

    @pytest.mark.asyncio
    async def test_generate_all_providers_fail(self):
        """Test when all providers fail."""
        provider1 = MockLLMProvider(MockProviderConfig("provider1"))
        provider1.initialize()
        provider1._available = False
        
        provider2 = MockLLMProvider(MockProviderConfig("provider2"))
        provider2.initialize()
        provider2._available = False
        
        self.service.add_provider(provider1)
        self.service.add_provider(provider2)
        
        messages = [LLMMessage(role=MessageRole.USER, content="Test question")]
        
        with pytest.raises(LLMProviderError, match="All providers failed"):
            await self.service.generate_response(messages)

    @pytest.mark.asyncio
    async def test_generate_no_providers(self):
        """Test generation with no providers configured."""
        messages = [LLMMessage(role=MessageRole.USER, content="Test question")]
        
        with pytest.raises(LLMProviderError, match="No providers configured"):
            await self.service.generate_response(messages)

    def test_get_health_status(self):
        """Test health status aggregation."""
        provider1 = MockLLMProvider(MockProviderConfig("provider1"))
        provider2 = MockLLMProvider(MockProviderConfig("provider2"))
        
        provider1.initialize()
        provider2.initialize()
        provider2._available = False
        
        self.service.add_provider(provider1)
        self.service.add_provider(provider2)
        
        status = self.service.get_health_status()
        
        assert isinstance(status, dict)
        assert "providers" in status
        assert len(status["providers"]) == 2
        assert status["providers"][0]["provider"] == "provider1"
        assert status["providers"][0]["status"] == "healthy"
        assert status["providers"][1]["provider"] == "provider2"
        assert status["providers"][1]["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_provider_selection_strategy(self):
        """Test provider selection strategy (first available)."""
        # This test verifies current simple strategy of using first available provider
        provider1 = MockLLMProvider(MockProviderConfig("provider1"))
        provider2 = MockLLMProvider(MockProviderConfig("provider2"))
        
        provider1.initialize()
        provider2.initialize()
        
        self.service.add_provider(provider1)
        self.service.add_provider(provider2)
        
        messages = [LLMMessage(role=MessageRole.USER, content="Test")]
        
        response = await self.service.generate_response(messages)
        
        # Should use first provider (provider1)
        assert response.provider == "provider1"


# Integration tests for provider coordination
class TestProviderIntegration:
    """Integration tests for provider coordination and error handling."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_conversation(self):
        """Test end-to-end conversation flow."""
        provider = MockLLMProvider(MockProviderConfig("test-provider"))
        provider.initialize()
        
        service = MultiProviderLLMService(Settings())
        service.add_provider(provider)
        
        # Multi-turn conversation
        messages = [
            LLMMessage(role=MessageRole.SYSTEM, content="You are a philosophy tutor."),
            LLMMessage(role=MessageRole.USER, content="What is Plato's theory of Forms?")
        ]
        
        response = await service.generate_response(messages)
        
        assert isinstance(response, LLMResponse)
        assert response.provider == "test-provider"
        assert "theory of Forms" in response.content
        
        # Continue conversation
        messages.append(LLMMessage(role=MessageRole.ASSISTANT, content=response.content))
        messages.append(LLMMessage(role=MessageRole.USER, content="Can you give an example?"))
        
        response2 = await service.generate_response(messages)
        assert isinstance(response2, LLMResponse)

    @pytest.mark.asyncio
    async def test_provider_error_recovery(self):
        """Test error recovery and provider switching."""
        # Provider that fails after first call
        failing_provider = MockLLMProvider(MockProviderConfig("failing"))
        failing_provider.initialize()
        
        # Reliable backup provider
        backup_provider = MockLLMProvider(MockProviderConfig("backup"))
        backup_provider.initialize()
        
        service = MultiProviderLLMService(Settings())
        service.add_provider(failing_provider)
        service.add_provider(backup_provider)
        
        messages = [LLMMessage(role=MessageRole.USER, content="First question")]
        
        # First call succeeds with primary provider
        response1 = await service.generate_response(messages)
        assert response1.provider == "failing"
        
        # Make primary provider fail
        failing_provider._available = False
        
        # Second call should failover to backup
        response2 = await service.generate_response(messages)
        assert response2.provider == "backup"