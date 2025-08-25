"""
Test suite for OpenAI LLM provider integration.

Tests the OpenAI provider implementation including API key management,
model selection, function calling, and error handling for GPT models.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any
import json
import httpx

from arete.services.openai_provider import OpenAIProvider
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


class TestOpenAIProvider:
    """Test OpenAI provider functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.settings = Settings(
            openai_api_key="sk-test-12345",
            llm_max_tokens=4000,
            llm_temperature=0.7,
            llm_timeout=30
        )
        self.provider = OpenAIProvider(self.settings)

    def test_provider_initialization(self):
        """Test provider initialization with settings."""
        assert self.provider.name == "openai"
        assert self.provider.settings == self.settings
        assert self.provider.api_key == "sk-test-12345"
        assert self.provider.base_url == "https://api.openai.com/v1"
        assert not self.provider._initialized

    def test_provider_initialization_no_api_key(self):
        """Test provider initialization without API key."""
        settings = Settings(openai_api_key="")
        
        with pytest.raises(AuthenticationError, match="OpenAI API key not provided"):
            OpenAIProvider(settings)

    def test_provider_properties(self):
        """Test provider property access."""
        assert self.provider.timeout == 30
        assert self.provider.max_tokens == 4000
        assert self.provider.temperature == 0.7

    @patch('arete.services.openai_provider.httpx.AsyncClient')
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
                    "id": "gpt-4-turbo",
                    "object": "model",
                    "created": 1700000000,
                    "owned_by": "system"
                },
                {
                    "id": "gpt-4",
                    "object": "model", 
                    "created": 1670000000,
                    "owned_by": "openai"
                },
                {
                    "id": "gpt-3.5-turbo",
                    "object": "model",
                    "created": 1660000000,
                    "owned_by": "openai"
                }
            ]
        }
        
        mock_client.get = AsyncMock(return_value=models_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        self.provider.initialize()
        assert self.provider._initialized

    @patch('arete.services.openai_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_initialize_api_error(self, mock_client_class):
        """Test initialization when API returns error."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": {
                "message": "Incorrect API key provided",
                "type": "invalid_request_error",
                "code": "invalid_api_key"
            }
        }
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with pytest.raises(AuthenticationError, match="OpenAI API authentication failed"):
            self.provider.initialize()

    def test_is_available_property_not_initialized(self):
        """Test is_available property when not initialized."""
        assert not self.provider.is_available

    def test_is_available_property_initialized(self):
        """Test is_available property when initialized."""
        self.provider._initialized = True
        assert self.provider.is_available

    @patch('arete.services.openai_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_get_available_models_success(self, mock_client_class):
        """Test getting available models from OpenAI API."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "gpt-4-turbo", "object": "model"},
                {"id": "gpt-4", "object": "model"},
                {"id": "gpt-3.5-turbo", "object": "model"},
                {"id": "text-embedding-ada-002", "object": "model"}  # Should be filtered out
            ]
        }
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        models = await self.provider._get_available_models()
        
        assert len(models) == 3  # Embedding model should be filtered out
        assert "gpt-4-turbo" in models
        assert "gpt-4" in models
        assert "gpt-3.5-turbo" in models
        assert "text-embedding-ada-002" not in models

    def test_supported_models_property_not_initialized(self):
        """Test supported_models property when not initialized."""
        models = self.provider.supported_models
        assert isinstance(models, list)
        assert len(models) >= 0

    def test_supported_models_property_initialized(self):
        """Test supported_models property when initialized."""
        self.provider._initialized = True
        self.provider._available_models = ["gpt-4-turbo", "gpt-3.5-turbo"]
        
        models = self.provider.supported_models
        assert models == ["gpt-4-turbo", "gpt-3.5-turbo"]

    @patch('arete.services.openai_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_response_success(self, mock_client_class):
        """Test successful response generation."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1700000000,
            "model": "gpt-4-turbo",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Plato's Theory of Forms is a fundamental philosophical doctrine that proposes the existence of a realm of perfect, eternal, and immutable Forms or Ideas. These Forms represent the true reality behind the imperfect copies we observe in the physical world. For example, when we see beautiful objects in our world, they are merely imperfect participations in the perfect Form of Beauty."
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 45,
                "completion_tokens": 67,
                "total_tokens": 112
            }
        }
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        self.provider._initialized = True
        
        messages = [
            LLMMessage(role=MessageRole.SYSTEM, content="You are a philosophy tutor."),
            LLMMessage(role=MessageRole.USER, content="Explain Plato's Theory of Forms.")
        ]
        
        response = await self.provider.generate_response(messages, model="gpt-4-turbo")
        
        assert isinstance(response, LLMResponse)
        assert "Theory of Forms" in response.content
        assert response.provider == "openai"
        assert response.model == "gpt-4-turbo"
        assert response.usage_tokens == 112
        assert response.finish_reason == "stop"

    @patch('arete.services.openai_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_response_with_streaming(self, mock_client_class):
        """Test response generation with streaming."""
        mock_client = Mock()
        
        # Mock streaming responses
        stream_data = [
            'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1700000000,"model":"gpt-4-turbo","choices":[{"index":0,"delta":{"content":"Plato\'s"},"finish_reason":null}]}\n\n',
            'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1700000000,"model":"gpt-4-turbo","choices":[{"index":0,"delta":{"content":" Theory"},"finish_reason":null}]}\n\n',
            'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1700000000,"model":"gpt-4-turbo","choices":[{"index":0,"delta":{"content":" of Forms"},"finish_reason":null}]}\n\n',
            'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1700000000,"model":"gpt-4-turbo","choices":[{"index":0,"delta":{},"finish_reason":"stop"}],"usage":{"total_tokens":42}}\n\n',
            'data: [DONE]\n\n'
        ]
        
        async def mock_aiter_lines():
            for line in stream_data:
                for sub_line in line.split('\n'):
                    if sub_line.strip():
                        yield sub_line
        
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
            model="gpt-4-turbo",
            stream=True
        )
        
        assert response.content == "Plato's Theory of Forms"
        assert response.provider == "openai"
        assert response.usage_tokens == 42
        assert response.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_generate_response_not_initialized(self):
        """Test response generation when provider not initialized."""
        messages = [LLMMessage(role=MessageRole.USER, content="Test")]
        
        with pytest.raises(LLMProviderError, match="Provider not initialized"):
            await self.provider.generate_response(messages)

    @patch('arete.services.openai_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_response_rate_limit_error(self, mock_client_class):
        """Test response generation when rate limit is hit."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"retry-after": "60"}
        mock_response.json.return_value = {
            "error": {
                "message": "Rate limit reached for requests",
                "type": "rate_limit_error",
                "code": "rate_limit_exceeded"
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

    @patch('arete.services.openai_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_response_authentication_error(self, mock_client_class):
        """Test response generation with authentication error."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": {
                "message": "Incorrect API key provided",
                "type": "invalid_request_error",
                "code": "invalid_api_key"
            }
        }
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        self.provider._initialized = True
        
        messages = [LLMMessage(role=MessageRole.USER, content="Test")]
        
        with pytest.raises(AuthenticationError, match="OpenAI API authentication failed"):
            await self.provider.generate_response(messages)

    def test_format_messages_for_openai(self):
        """Test message formatting for OpenAI API."""
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
            }
        }
        
        content, tokens, finish_reason = self.provider._extract_content_from_response(response_data)
        
        assert content == "Test response content"
        assert tokens == 25
        assert finish_reason == "stop"

    def test_extract_content_from_response_no_choices(self):
        """Test content extraction when response has no choices."""
        response_data = {
            "choices": [],
            "usage": {"total_tokens": 0}
        }
        
        content, tokens, finish_reason = self.provider._extract_content_from_response(response_data)
        
        assert content == ""
        assert tokens == 0
        assert finish_reason == "error"

    def test_get_default_model(self):
        """Test default model selection."""
        # Test with no models available
        assert self.provider._get_default_model([]) == "gpt-4-turbo"
        
        # Test with available models
        models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
        default = self.provider._get_default_model(models)
        assert default == "gpt-4-turbo"  # Should prefer latest GPT-4
        
        # Test without preferred models
        models = ["gpt-3.5-turbo", "gpt-3.5-turbo-16k"]
        default = self.provider._get_default_model(models)
        assert default == "gpt-3.5-turbo"  # Should return first available

    def test_build_request_params(self):
        """Test building request parameters for OpenAI API."""
        messages = [LLMMessage(role=MessageRole.USER, content="Test")]
        
        params = self.provider._build_request_params(
            messages=messages,
            model="gpt-4-turbo",
            max_tokens=1000,
            temperature=0.5
        )
        
        assert params["model"] == "gpt-4-turbo"
        assert params["max_tokens"] == 1000
        assert params["temperature"] == 0.5
        assert params["messages"] == [{"role": "user", "content": "Test"}]

    def test_get_headers(self):
        """Test HTTP headers construction."""
        headers = self.provider._get_headers()
        
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer sk-test-12345"
        assert headers["Content-Type"] == "application/json"

    def test_model_filtering(self):
        """Test filtering of non-chat models."""
        all_models = [
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "text-embedding-ada-002",  # Should be filtered out
            "whisper-1",               # Should be filtered out
            "dall-e-3"                # Should be filtered out
        ]
        
        filtered = self.provider._filter_chat_models(all_models)
        
        assert len(filtered) == 3
        assert "gpt-4-turbo" in filtered
        assert "gpt-4" in filtered
        assert "gpt-3.5-turbo" in filtered
        assert "text-embedding-ada-002" not in filtered
        assert "whisper-1" not in filtered
        assert "dall-e-3" not in filtered

    def test_get_health_status_not_initialized(self):
        """Test health status when not initialized."""
        status = self.provider.get_health_status()
        
        assert status["provider"] == "openai"
        assert status["status"] == "not_initialized"
        assert not status["initialized"]

    def test_get_health_status_initialized(self):
        """Test health status when initialized."""
        self.provider._initialized = True
        self.provider._available_models = ["gpt-4-turbo", "gpt-3.5-turbo"]
        
        status = self.provider.get_health_status()
        
        assert status["provider"] == "openai"
        assert status["status"] == "healthy"
        assert status["initialized"]
        assert status["available_models"] == ["gpt-4-turbo", "gpt-3.5-turbo"]
        assert status["api_url"] == "https://api.openai.com/v1"

    def test_cleanup(self):
        """Test provider cleanup."""
        self.provider.cleanup()
        assert not self.provider._initialized
        assert self.provider._available_models == []


class TestOpenAIProviderIntegration:
    """Integration tests for OpenAI provider with mocked API responses."""
    
    @patch('arete.services.openai_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_end_to_end_philosophy_conversation(self, mock_client_class):
        """Test complete philosophy tutoring conversation flow."""
        settings = Settings(openai_api_key="sk-test")
        provider = OpenAIProvider(settings)
        
        mock_client = Mock()
        
        # Mock initialization
        models_response = Mock()
        models_response.status_code = 200
        models_response.json.return_value = {
            "data": [
                {"id": "gpt-4-turbo", "object": "model"},
                {"id": "gpt-3.5-turbo", "object": "model"}
            ]
        }
        
        # Mock generation response
        gen_response = Mock()
        gen_response.status_code = 200
        gen_response.json.return_value = {
            "id": "chatcmpl-123",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Plato's Theory of Forms is a cornerstone of Western philosophy. It proposes that beyond our material world exists a perfect realm of Forms - eternal, unchanging templates for everything we see. For instance, all beautiful things in our world are imperfect copies of the perfect Form of Beauty. This theory explains how we can have knowledge of perfect concepts like Justice or Goodness, even though we only encounter imperfect examples in reality."
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {"total_tokens": 95},
            "model": "gpt-4-turbo"
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
        
        response = await provider.generate_response(messages, model="gpt-4-turbo")
        
        assert isinstance(response, LLMResponse)
        assert "Theory of Forms" in response.content
        assert "perfect" in response.content
        assert response.provider == "openai"
        assert response.model == "gpt-4-turbo"
        assert response.usage_tokens == 95


class TestOpenAIProviderConfiguration:
    """Test OpenAI provider configuration and settings."""
    
    def test_api_key_validation(self):
        """Test API key validation during initialization."""
        # Valid API key
        settings = Settings(openai_api_key="sk-test-12345")
        provider = OpenAIProvider(settings)
        assert provider.api_key == "sk-test-12345"
        
        # Empty API key should raise error
        settings = Settings(openai_api_key="")
        with pytest.raises(AuthenticationError):
            OpenAIProvider(settings)

    def test_custom_base_url(self):
        """Test custom base URL configuration."""
        settings = Settings(openai_api_key="sk-test", openai_base_url="https://custom-openai.example.com/v1")
        provider = OpenAIProvider(settings)
        assert provider.base_url == "https://custom-openai.example.com/v1"

    def test_organization_header(self):
        """Test organization header inclusion."""
        settings = Settings(openai_api_key="sk-test", openai_organization="org-12345")
        provider = OpenAIProvider(settings)
        
        headers = provider._get_headers()
        assert "OpenAI-Organization" in headers
        assert headers["OpenAI-Organization"] == "org-12345"

    def test_request_parameters_with_advanced_options(self):
        """Test advanced request parameters."""
        provider = OpenAIProvider(Settings(openai_api_key="sk-test"))
        
        messages = [LLMMessage(role=MessageRole.USER, content="Test")]
        
        params = provider._build_request_params(
            messages=messages,
            model="gpt-4-turbo",
            top_p=0.9,
            frequency_penalty=0.1,
            presence_penalty=0.2,
            stop=["END"]
        )
        
        assert params["top_p"] == 0.9
        assert params["frequency_penalty"] == 0.1
        assert params["presence_penalty"] == 0.2
        assert params["stop"] == ["END"]