"""
Test suite for OpenRouter LLM provider integration.

Tests the OpenRouter provider implementation including API key management,
model selection, rate limiting, and error handling for cloud-based LLM access.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any
import json
import httpx

from arete.services.openrouter_provider import OpenRouterProvider
from arete.services.llm_provider import (
    LLMMessage,
    LLMResponse,
    MessageRole,
    LLMProviderError,
    ProviderUnavailableError,
    RateLimitError,
    AuthenticationError
)
from arete.config import Settings


class TestOpenRouterProvider:
    """Test OpenRouter provider functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.settings = Settings(
            openrouter_api_key="test-api-key-12345",
            llm_max_tokens=4000,
            llm_temperature=0.7,
            llm_timeout=30
        )
        self.provider = OpenRouterProvider(self.settings)

    def test_provider_initialization(self):
        """Test provider initialization with settings."""
        assert self.provider.name == "openrouter"
        assert self.provider.settings == self.settings
        assert self.provider.api_key == "test-api-key-12345"
        assert self.provider.base_url == "https://openrouter.ai/api/v1"
        assert not self.provider._initialized

    def test_provider_initialization_no_api_key(self):
        """Test provider initialization without API key."""
        settings = Settings(openrouter_api_key="")
        
        with pytest.raises(AuthenticationError, match="OpenRouter API key not provided"):
            OpenRouterProvider(settings)

    def test_provider_properties(self):
        """Test provider property access."""
        assert self.provider.timeout == 30
        assert self.provider.max_tokens == 4000
        assert self.provider.temperature == 0.7

    @patch('arete.services.openrouter_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_initialize_success(self, mock_client_class):
        """Test successful provider initialization."""
        mock_client = Mock()
        
        # Mock models response
        models_response = Mock()
        models_response.status_code = 200
        models_response.json.return_value = {
            "data": [
                {
                    "id": "anthropic/claude-3-haiku",
                    "name": "Claude 3 Haiku",
                    "context_length": 200000,
                    "pricing": {"prompt": "0.00025", "completion": "0.00125"}
                },
                {
                    "id": "openai/gpt-4-turbo",
                    "name": "GPT-4 Turbo", 
                    "context_length": 128000,
                    "pricing": {"prompt": "0.01", "completion": "0.03"}
                }
            ]
        }
        
        mock_client.get = AsyncMock(return_value=models_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        self.provider.initialize()
        assert self.provider._initialized

    @patch('arete.services.openrouter_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_initialize_api_error(self, mock_client_class):
        """Test initialization when API returns error."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Invalid API key"
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with pytest.raises(AuthenticationError, match="OpenRouter API authentication failed"):
            self.provider.initialize()

    @patch('arete.services.openrouter_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_initialize_network_error(self, mock_client_class):
        """Test initialization when network error occurs."""
        mock_client = Mock()
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with pytest.raises(ProviderUnavailableError, match="OpenRouter API unavailable"):
            self.provider.initialize()

    def test_is_available_property_not_initialized(self):
        """Test is_available property when not initialized."""
        assert not self.provider.is_available

    def test_is_available_property_initialized(self):
        """Test is_available property when initialized."""
        self.provider._initialized = True
        assert self.provider.is_available

    @patch('arete.services.openrouter_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_get_available_models_success(self, mock_client_class):
        """Test getting available models from OpenRouter API."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "anthropic/claude-3-haiku",
                    "name": "Claude 3 Haiku",
                    "context_length": 200000
                },
                {
                    "id": "openai/gpt-4-turbo",
                    "name": "GPT-4 Turbo",
                    "context_length": 128000
                },
                {
                    "id": "meta-llama/llama-3-8b-instruct",
                    "name": "Llama 3 8B Instruct",
                    "context_length": 8192
                }
            ]
        }
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        models = await self.provider._get_available_models()
        
        assert len(models) == 3
        assert "anthropic/claude-3-haiku" in models
        assert "openai/gpt-4-turbo" in models
        assert "meta-llama/llama-3-8b-instruct" in models

    def test_supported_models_property_not_initialized(self):
        """Test supported_models property when not initialized."""
        models = self.provider.supported_models
        assert isinstance(models, list)
        assert len(models) >= 0

    def test_supported_models_property_initialized(self):
        """Test supported_models property when initialized."""
        self.provider._initialized = True
        self.provider._available_models = ["anthropic/claude-3-haiku", "openai/gpt-4-turbo"]
        
        models = self.provider.supported_models
        assert models == ["anthropic/claude-3-haiku", "openai/gpt-4-turbo"]

    @patch('arete.services.openrouter_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_response_success(self, mock_client_class):
        """Test successful response generation."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Plato's Theory of Forms is a philosophical doctrine that suggests there exists a realm of perfect, immutable Forms or Ideas that serve as the true reality behind the physical world we perceive."
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 45,
                "completion_tokens": 38,
                "total_tokens": 83
            },
            "model": "anthropic/claude-3-haiku"
        }
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        self.provider._initialized = True
        
        messages = [
            LLMMessage(role=MessageRole.SYSTEM, content="You are a philosophy tutor."),
            LLMMessage(role=MessageRole.USER, content="Explain Plato's Theory of Forms.")
        ]
        
        response = await self.provider.generate_response(messages, model="anthropic/claude-3-haiku")
        
        assert isinstance(response, LLMResponse)
        assert "Theory of Forms" in response.content
        assert response.provider == "openrouter"
        assert response.model == "anthropic/claude-3-haiku"
        assert response.usage_tokens == 83
        assert response.finish_reason == "stop"

    @patch('arete.services.openrouter_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_response_with_streaming(self, mock_client_class):
        """Test response generation with streaming."""
        mock_client = Mock()
        
        # Mock streaming responses
        stream_data = [
            'data: {"choices":[{"delta":{"content":"Plato\'s"}}]}\n\n',
            'data: {"choices":[{"delta":{"content":" Theory"}}]}\n\n',
            'data: {"choices":[{"delta":{"content":" of"}}]}\n\n',
            'data: {"choices":[{"delta":{"content":" Forms"}}]}\n\n',
            'data: {"choices":[{"finish_reason":"stop","delta":{}}],"usage":{"total_tokens":42}}\n\n',
            'data: [DONE]\n\n'
        ]
        
        async def mock_aiter_lines():
            for line in stream_data:
                yield line.strip()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.aiter_lines = mock_aiter_lines
        
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        self.provider._initialized = True
        
        messages = [LLMMessage(role=MessageRole.USER, content="Test streaming")]
        
        response = await self.provider.generate_response(
            messages,
            model="anthropic/claude-3-haiku",
            stream=True
        )
        
        assert response.content == "Plato's Theory of Forms"
        assert response.provider == "openrouter"
        assert response.usage_tokens == 42
        assert response.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_generate_response_not_initialized(self):
        """Test response generation when provider not initialized."""
        messages = [LLMMessage(role=MessageRole.USER, content="Test")]
        
        with pytest.raises(LLMProviderError, match="Provider not initialized"):
            await self.provider.generate_response(messages)

    @patch('arete.services.openrouter_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_response_rate_limit_error(self, mock_client_class):
        """Test response generation when rate limit is hit."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"retry-after": "60"}
        mock_response.json.return_value = {
            "error": {
                "message": "Rate limit exceeded",
                "type": "rate_limit_error"
            }
        }
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        self.provider._initialized = True
        
        messages = [LLMMessage(role=MessageRole.USER, content="Test")]
        
        with pytest.raises(RateLimitError) as exc_info:
            await self.provider.generate_response(messages)
        
        assert exc_info.value.retry_after == 60

    @patch('arete.services.openrouter_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_response_authentication_error(self, mock_client_class):
        """Test response generation with authentication error."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": {
                "message": "Invalid API key",
                "type": "authentication_error"
            }
        }
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        self.provider._initialized = True
        
        messages = [LLMMessage(role=MessageRole.USER, content="Test")]
        
        with pytest.raises(AuthenticationError, match="OpenRouter API authentication failed"):
            await self.provider.generate_response(messages)

    @patch('arete.services.openrouter_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_response_timeout(self, mock_client_class):
        """Test response generation with timeout."""
        mock_client = Mock()
        mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Request timeout"))
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        self.provider._initialized = True
        
        messages = [LLMMessage(role=MessageRole.USER, content="Test")]
        
        with pytest.raises(LLMProviderError, match="Request timeout"):
            await self.provider.generate_response(messages)

    def test_format_messages_for_openrouter(self):
        """Test message formatting for OpenRouter API."""
        messages = [
            LLMMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
            LLMMessage(role=MessageRole.USER, content="What is philosophy?"),
            LLMMessage(role=MessageRole.ASSISTANT, content="Philosophy is the study of wisdom."),
            LLMMessage(role=MessageRole.USER, content="Can you elaborate?")
        ]
        
        formatted = self.provider._format_messages(messages)
        
        assert len(formatted) == 4
        assert formatted[0] == {"role": "system", "content": "You are a helpful assistant."}
        assert formatted[1] == {"role": "user", "content": "What is philosophy?"}
        assert formatted[2] == {"role": "assistant", "content": "Philosophy is the study of wisdom."}
        assert formatted[3] == {"role": "user", "content": "Can you elaborate?"}

    def test_extract_content_from_response_normal(self):
        """Test content extraction from normal response."""
        response_data = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Test response content"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "total_tokens": 25
            },
            "model": "anthropic/claude-3-haiku"
        }
        
        content, tokens, finish_reason = self.provider._extract_content_from_response(response_data)
        
        assert content == "Test response content"
        assert tokens == 25
        assert finish_reason == "stop"

    def test_extract_content_from_response_no_choices(self):
        """Test content extraction when response has no choices."""
        response_data = {
            "choices": [],
            "error": {"message": "No response generated"}
        }
        
        content, tokens, finish_reason = self.provider._extract_content_from_response(response_data)
        
        assert content == ""
        assert tokens is None
        assert finish_reason == "error"

    def test_get_default_model(self):
        """Test default model selection."""
        # Test with no models available
        assert self.provider._get_default_model([]) == "anthropic/claude-3-haiku"
        
        # Test with available models
        models = ["openai/gpt-4-turbo", "anthropic/claude-3-haiku", "meta-llama/llama-3-8b-instruct"]
        default = self.provider._get_default_model(models)
        assert default == "anthropic/claude-3-haiku"  # Should prefer Claude
        
        # Test without preferred models
        models = ["openai/gpt-3.5-turbo", "meta-llama/llama-3-8b-instruct"]
        default = self.provider._get_default_model(models)
        assert default == "openai/gpt-3.5-turbo"  # Should return first available

    def test_build_request_params(self):
        """Test building request parameters for OpenRouter API."""
        messages = [LLMMessage(role=MessageRole.USER, content="Test")]
        
        params = self.provider._build_request_params(
            messages=messages,
            model="anthropic/claude-3-haiku",
            max_tokens=1000,
            temperature=0.5
        )
        
        expected_params = {
            "model": "anthropic/claude-3-haiku",
            "messages": [{"role": "user", "content": "Test"}],
            "max_tokens": 1000,
            "temperature": 0.5,
            "stream": False
        }
        
        assert params == expected_params

    def test_build_request_params_with_defaults(self):
        """Test building request parameters with default values."""
        messages = [LLMMessage(role=MessageRole.USER, content="Test")]
        
        params = self.provider._build_request_params(
            messages=messages,
            model="openai/gpt-4-turbo"
        )
        
        assert params["max_tokens"] == 4000
        assert params["temperature"] == 0.7
        assert params["stream"] is False

    def test_get_health_status_not_initialized(self):
        """Test health status when not initialized."""
        status = self.provider.get_health_status()
        
        assert status["provider"] == "openrouter"
        assert status["status"] == "not_initialized"
        assert not status["initialized"]

    def test_get_health_status_initialized(self):
        """Test health status when initialized."""
        self.provider._initialized = True
        self.provider._available_models = ["anthropic/claude-3-haiku", "openai/gpt-4-turbo"]
        
        status = self.provider.get_health_status()
        
        assert status["provider"] == "openrouter"
        assert status["status"] == "healthy"
        assert status["initialized"]
        assert status["available_models"] == ["anthropic/claude-3-haiku", "openai/gpt-4-turbo"]
        assert status["api_url"] == "https://openrouter.ai/api/v1"

    def test_cleanup(self):
        """Test provider cleanup."""
        self.provider.cleanup()
        assert not self.provider._initialized
        assert self.provider._available_models == []


class TestOpenRouterProviderIntegration:
    """Integration tests for OpenRouter provider with mocked API responses."""
    
    @patch('arete.services.openrouter_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_end_to_end_philosophy_conversation(self, mock_client_class):
        """Test complete philosophy tutoring conversation flow."""
        settings = Settings(openrouter_api_key="test-key")
        provider = OpenRouterProvider(settings)
        
        mock_client = Mock()
        
        # Mock initialization
        models_response = Mock()
        models_response.status_code = 200
        models_response.json.return_value = {
            "data": [
                {"id": "anthropic/claude-3-haiku", "name": "Claude 3 Haiku"},
                {"id": "openai/gpt-4-turbo", "name": "GPT-4 Turbo"}
            ]
        }
        
        # Mock generation response
        gen_response = Mock()
        gen_response.status_code = 200
        gen_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Plato's Theory of Forms suggests that beyond our physical world exists a realm of perfect, unchanging Forms that represent the true essence of all things. For example, there is a perfect Form of Beauty that all beautiful things in our world participate in or imitate."
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {"total_tokens": 67},
            "model": "anthropic/claude-3-haiku"
        }
        
        mock_client.get = AsyncMock(return_value=models_response)
        mock_client.post = AsyncMock(return_value=gen_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Initialize provider
        provider.initialize()
        
        # Test philosophy conversation
        messages = [
            LLMMessage(role=MessageRole.SYSTEM, content="You are a philosophy tutor specializing in ancient Greek philosophy."),
            LLMMessage(role=MessageRole.USER, content="Can you explain Plato's Theory of Forms with a simple example?")
        ]
        
        response = await provider.generate_response(messages, model="anthropic/claude-3-haiku")
        
        assert isinstance(response, LLMResponse)
        assert "Theory of Forms" in response.content
        assert "perfect" in response.content
        assert response.provider == "openrouter"
        assert response.model == "anthropic/claude-3-haiku"
        assert response.usage_tokens == 67

    @patch('arete.services.openrouter_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_model_fallback_on_unavailability(self, mock_client_class):
        """Test fallback to different model when preferred one is unavailable."""
        provider = OpenRouterProvider(Settings(openrouter_api_key="test-key"))
        provider._initialized = True
        provider._available_models = ["anthropic/claude-3-haiku", "openai/gpt-4-turbo"]
        
        mock_client = Mock()
        
        # First attempt with Claude fails
        error_response = Mock()
        error_response.status_code = 503
        error_response.json.return_value = {"error": {"message": "Model temporarily unavailable"}}
        
        # Second attempt with GPT-4 succeeds  
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "choices": [{"message": {"content": "Response from GPT-4"}, "finish_reason": "stop"}],
            "usage": {"total_tokens": 15},
            "model": "openai/gpt-4-turbo"
        }
        
        mock_client.post = AsyncMock(side_effect=[error_response, success_response])
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        messages = [LLMMessage(role=MessageRole.USER, content="Test message")]
        
        # This would typically be handled by the multi-provider service
        # For now, we test that the error is properly raised
        with pytest.raises(LLMProviderError):
            await provider.generate_response(messages, model="anthropic/claude-3-haiku")


class TestOpenRouterProviderConfiguration:
    """Test OpenRouter provider configuration and settings."""
    
    def test_api_key_validation(self):
        """Test API key validation during initialization."""
        # Valid API key
        settings = Settings(openrouter_api_key="sk-test-12345")
        provider = OpenRouterProvider(settings)
        assert provider.api_key == "sk-test-12345"
        
        # Empty API key should raise error
        settings = Settings(openrouter_api_key="")
        with pytest.raises(AuthenticationError):
            OpenRouterProvider(settings)
        
        # None API key should raise error  
        settings = Settings()
        settings.openrouter_api_key = None
        with pytest.raises(AuthenticationError):
            OpenRouterProvider(settings)

    def test_headers_construction(self):
        """Test HTTP headers construction."""
        provider = OpenRouterProvider(Settings(openrouter_api_key="test-key"))
        
        headers = provider._get_headers()
        
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test-key"
        assert headers["Content-Type"] == "application/json"
        assert "User-Agent" in headers
        assert "arete" in headers["User-Agent"].lower()

    def test_cost_tracking_headers(self):
        """Test cost tracking headers for OpenRouter."""
        provider = OpenRouterProvider(Settings(openrouter_api_key="test-key"))
        
        headers = provider._get_headers(
            app_name="Arete Philosophy Tutor",
            site_url="https://example.com"
        )
        
        assert "HTTP-Referer" in headers
        assert headers["HTTP-Referer"] == "https://example.com"
        assert "X-Title" in headers
        assert headers["X-Title"] == "Arete Philosophy Tutor"

    def test_model_pricing_info(self):
        """Test model pricing information parsing."""
        model_data = {
            "id": "anthropic/claude-3-haiku",
            "pricing": {
                "prompt": "0.00025",
                "completion": "0.00125"
            }
        }
        
        provider = OpenRouterProvider(Settings(openrouter_api_key="test-key"))
        pricing = provider._extract_pricing_info(model_data)
        
        assert pricing["prompt_cost"] == 0.00025
        assert pricing["completion_cost"] == 0.00125
        assert pricing["currency"] == "USD"

    def test_request_parameters_with_openrouter_specifics(self):
        """Test OpenRouter-specific request parameters."""
        provider = OpenRouterProvider(Settings(openrouter_api_key="test-key"))
        
        messages = [LLMMessage(role=MessageRole.USER, content="Test")]
        
        params = provider._build_request_params(
            messages=messages,
            model="anthropic/claude-3-haiku",
            provider_preferences={
                "allow_fallbacks": True,
                "require_parameters": True
            }
        )
        
        # OpenRouter-specific parameters should be included
        assert "provider" in params
        assert params["provider"]["allow_fallbacks"] is True
        assert params["provider"]["require_parameters"] is True