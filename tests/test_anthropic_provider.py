"""
Test suite for Anthropic Claude LLM provider integration.

Tests the Anthropic provider implementation including API key management,
model selection, message formatting, and error handling for Claude models.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any
import json
import httpx

from arete.services.anthropic_provider import AnthropicProvider
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


class TestAnthropicProvider:
    """Test Anthropic provider functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.settings = Settings(
            anthropic_api_key="sk-ant-test-12345",
            llm_max_tokens=4000,
            llm_temperature=0.7,
            llm_timeout=30
        )
        self.provider = AnthropicProvider(self.settings)

    def test_provider_initialization(self):
        """Test provider initialization with settings."""
        assert self.provider.name == "anthropic"
        assert self.provider.settings == self.settings
        assert self.provider.api_key == "sk-ant-test-12345"
        assert self.provider.base_url == "https://api.anthropic.com/v1"
        assert not self.provider._initialized

    def test_provider_initialization_no_api_key(self):
        """Test provider initialization without API key."""
        settings = Settings(anthropic_api_key="")
        
        with pytest.raises(AuthenticationError, match="Anthropic API key not provided"):
            AnthropicProvider(settings)

    def test_provider_properties(self):
        """Test provider property access."""
        assert self.provider.timeout == 30
        assert self.provider.max_tokens == 4000
        assert self.provider.temperature == 0.7

    def test_initialize_success(self):
        """Test successful provider initialization."""
        # Anthropic doesn't require async initialization for models
        self.provider.initialize()
        assert self.provider._initialized

    def test_is_available_property_not_initialized(self):
        """Test is_available property when not initialized."""
        assert not self.provider.is_available

    def test_is_available_property_initialized(self):
        """Test is_available property when initialized."""
        self.provider._initialized = True
        assert self.provider.is_available

    def test_supported_models_property(self):
        """Test supported_models property."""
        models = self.provider.supported_models
        assert isinstance(models, list)
        assert len(models) > 0
        assert "claude-3-haiku-20240307" in models
        assert "claude-3-sonnet-20240229" in models
        assert "claude-3-opus-20240229" in models

    @patch('arete.services.anthropic_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_response_success(self, mock_client_class):
        """Test successful response generation."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "msg_01AbCdEfGhIjKlMnOpQrSt",
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "Plato's Theory of Forms is a fundamental philosophical doctrine that proposes the existence of a realm of perfect, eternal, and immutable Forms or Ideas. These Forms serve as the true reality behind the imperfect copies we perceive in the physical world. For example, when we see beautiful objects, they are merely imperfect reflections of the perfect Form of Beauty."
                }
            ],
            "model": "claude-3-haiku-20240307",
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {
                "input_tokens": 45,
                "output_tokens": 67
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
        
        response = await self.provider.generate_response(messages, model="claude-3-haiku-20240307")
        
        assert isinstance(response, LLMResponse)
        assert "Theory of Forms" in response.content
        assert response.provider == "anthropic"
        assert response.model == "claude-3-haiku-20240307"
        assert response.usage_tokens == 112  # input + output tokens
        assert response.finish_reason == "stop"

    @patch('arete.services.anthropic_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_response_with_streaming(self, mock_client_class):
        """Test response generation with streaming."""
        mock_client = Mock()
        
        # Mock streaming responses
        stream_data = [
            'event: message_start\ndata: {"type": "message_start", "message": {"id": "msg_123", "type": "message", "role": "assistant", "content": [], "model": "claude-3-haiku-20240307", "stop_reason": null, "stop_sequence": null, "usage": {"input_tokens": 25, "output_tokens": 1}}}\n\n',
            'event: content_block_start\ndata: {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}}\n\n',
            'event: content_block_delta\ndata: {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "Plato\'s"}}\n\n',
            'event: content_block_delta\ndata: {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": " Theory"}}\n\n',
            'event: content_block_delta\ndata: {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": " of Forms"}}\n\n',
            'event: content_block_stop\ndata: {"type": "content_block_stop", "index": 0}\n\n',
            'event: message_delta\ndata: {"type": "message_delta", "delta": {"stop_reason": "end_turn", "stop_sequence": null}, "usage": {"output_tokens": 15}}\n\n',
            'event: message_stop\ndata: {"type": "message_stop"}\n\n'
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
            model="claude-3-haiku-20240307",
            stream=True
        )
        
        assert response.content == "Plato's Theory of Forms"
        assert response.provider == "anthropic"
        assert response.usage_tokens == 40  # input + output tokens
        assert response.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_generate_response_not_initialized(self):
        """Test response generation when provider not initialized."""
        messages = [LLMMessage(role=MessageRole.USER, content="Test")]
        
        with pytest.raises(LLMProviderError, match="Provider not initialized"):
            await self.provider.generate_response(messages)

    @patch('arete.services.anthropic_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_response_rate_limit_error(self, mock_client_class):
        """Test response generation when rate limit is hit."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"retry-after": "60"}
        mock_response.json.return_value = {
            "type": "error",
            "error": {
                "type": "rate_limit_error",
                "message": "Number of requests per minute has been exceeded"
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

    @patch('arete.services.anthropic_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_response_authentication_error(self, mock_client_class):
        """Test response generation with authentication error."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "type": "error",
            "error": {
                "type": "authentication_error",
                "message": "Invalid API key"
            }
        }
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        self.provider._initialized = True
        
        messages = [LLMMessage(role=MessageRole.USER, content="Test")]
        
        with pytest.raises(AuthenticationError, match="Anthropic API authentication failed"):
            await self.provider.generate_response(messages)

    def test_format_messages_for_anthropic(self):
        """Test message formatting for Anthropic API."""
        messages = [
            LLMMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
            LLMMessage(role=MessageRole.USER, content="What is philosophy?"),
            LLMMessage(role=MessageRole.ASSISTANT, content="Philosophy is the study of wisdom."),
            LLMMessage(role=MessageRole.USER, content="Can you elaborate?")
        ]
        
        formatted = self.provider._format_messages(messages)
        
        # Should have system message separate from conversation
        assert "system" in formatted
        assert formatted["system"] == "You are a helpful assistant."
        
        # Should have conversation messages
        assert "messages" in formatted
        assert len(formatted["messages"]) == 3
        
        assert formatted["messages"][0]["role"] == "user"
        assert formatted["messages"][0]["content"] == "What is philosophy?"
        assert formatted["messages"][1]["role"] == "assistant"
        assert formatted["messages"][1]["content"] == "Philosophy is the study of wisdom."
        assert formatted["messages"][2]["role"] == "user"
        assert formatted["messages"][2]["content"] == "Can you elaborate?"

    def test_extract_content_from_response_normal(self):
        """Test content extraction from normal response."""
        response_data = {
            "content": [
                {"type": "text", "text": "Test response content"}
            ],
            "usage": {
                "input_tokens": 10,
                "output_tokens": 15
            },
            "stop_reason": "end_turn"
        }
        
        content, tokens, finish_reason = self.provider._extract_content_from_response(response_data)
        
        assert content == "Test response content"
        assert tokens == 25  # input + output
        assert finish_reason == "stop"

    def test_extract_content_from_response_multiple_text_blocks(self):
        """Test content extraction with multiple text blocks."""
        response_data = {
            "content": [
                {"type": "text", "text": "First part "},
                {"type": "text", "text": "second part "},
                {"type": "text", "text": "third part."}
            ],
            "usage": {
                "input_tokens": 10,
                "output_tokens": 20
            },
            "stop_reason": "end_turn"
        }
        
        content, tokens, finish_reason = self.provider._extract_content_from_response(response_data)
        
        assert content == "First part second part third part."
        assert tokens == 30
        assert finish_reason == "stop"

    def test_get_default_model(self):
        """Test default model selection."""
        models = ["claude-3-opus-20240229", "claude-3-haiku-20240307", "claude-3-sonnet-20240229"]
        default = self.provider._get_default_model(models)
        assert default == "claude-3-sonnet-20240229"  # Should prefer Sonnet for balance

    def test_build_request_params(self):
        """Test building request parameters for Anthropic API."""
        messages = [
            LLMMessage(role=MessageRole.SYSTEM, content="You are helpful."),
            LLMMessage(role=MessageRole.USER, content="Test")
        ]
        
        params = self.provider._build_request_params(
            messages=messages,
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            temperature=0.5
        )
        
        assert params["model"] == "claude-3-haiku-20240307"
        assert params["max_tokens"] == 1000
        assert params["temperature"] == 0.5
        assert params["system"] == "You are helpful."
        assert len(params["messages"]) == 1
        assert params["messages"][0]["content"] == "Test"

    def test_get_headers(self):
        """Test HTTP headers construction."""
        headers = self.provider._get_headers()
        
        assert "x-api-key" in headers
        assert headers["x-api-key"] == "sk-ant-test-12345"
        assert headers["content-type"] == "application/json"
        assert headers["anthropic-version"] == "2023-06-01"

    def test_get_health_status_not_initialized(self):
        """Test health status when not initialized."""
        status = self.provider.get_health_status()
        
        assert status["provider"] == "anthropic"
        assert status["status"] == "not_initialized"
        assert not status["initialized"]

    def test_get_health_status_initialized(self):
        """Test health status when initialized."""
        self.provider._initialized = True
        
        status = self.provider.get_health_status()
        
        assert status["provider"] == "anthropic"
        assert status["status"] == "healthy"
        assert status["initialized"]
        assert len(status["available_models"]) > 0
        assert status["api_url"] == "https://api.anthropic.com/v1"

    def test_cleanup(self):
        """Test provider cleanup."""
        self.provider._initialized = True
        self.provider.cleanup()
        assert not self.provider._initialized


class TestAnthropicProviderIntegration:
    """Integration tests for Anthropic provider with mocked API responses."""
    
    @patch('arete.services.anthropic_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_end_to_end_philosophy_conversation(self, mock_client_class):
        """Test complete philosophy tutoring conversation flow."""
        settings = Settings(anthropic_api_key="sk-ant-test")
        provider = AnthropicProvider(settings)
        provider.initialize()
        
        mock_client = Mock()
        
        # Mock generation response
        gen_response = Mock()
        gen_response.status_code = 200
        gen_response.json.return_value = {
            "id": "msg_123",
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "Plato's Theory of Forms is one of the most influential ideas in Western philosophy. It suggests that our physical world is merely a shadow or reflection of a perfect realm of Forms. These Forms are eternal, unchanging, and represent the true essence of concepts like Beauty, Justice, and Goodness. When we see beautiful things in our world, they participate in or imitate the perfect Form of Beauty."
                }
            ],
            "model": "claude-3-sonnet-20240229",
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": 52,
                "output_tokens": 78
            }
        }
        
        mock_client.post = AsyncMock(return_value=gen_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Test philosophy conversation
        messages = [
            LLMMessage(role=MessageRole.SYSTEM, content="You are a philosophy tutor specializing in ancient Greek philosophy. Provide clear, educational explanations."),
            LLMMessage(role=MessageRole.USER, content="Can you explain Plato's Theory of Forms with examples?")
        ]
        
        response = await provider.generate_response(messages, model="claude-3-sonnet-20240229")
        
        assert isinstance(response, LLMResponse)
        assert "Theory of Forms" in response.content
        assert "perfect" in response.content
        assert "Beauty" in response.content
        assert response.provider == "anthropic"
        assert response.model == "claude-3-sonnet-20240229"
        assert response.usage_tokens == 130


class TestAnthropicProviderConfiguration:
    """Test Anthropic provider configuration and settings."""
    
    def test_api_key_validation(self):
        """Test API key validation during initialization."""
        # Valid API key
        settings = Settings(anthropic_api_key="sk-ant-api03-test")
        provider = AnthropicProvider(settings)
        assert provider.api_key == "sk-ant-api03-test"
        
        # Empty API key should raise error
        settings = Settings(anthropic_api_key="")
        with pytest.raises(AuthenticationError):
            AnthropicProvider(settings)

    def test_model_selection_preferences(self):
        """Test model selection preferences."""
        provider = AnthropicProvider(Settings(anthropic_api_key="test-key"))
        
        # Test with full model list
        all_models = [
            "claude-3-haiku-20240307",
            "claude-3-sonnet-20240229", 
            "claude-3-opus-20240229"
        ]
        default = provider._get_default_model(all_models)
        assert default == "claude-3-sonnet-20240229"  # Balanced choice
        
        # Test with only one model
        single_model = ["claude-3-haiku-20240307"]
        default = provider._get_default_model(single_model)
        assert default == "claude-3-haiku-20240307"

    def test_stop_reason_mapping(self):
        """Test stop reason mapping from Anthropic to standard."""
        provider = AnthropicProvider(Settings(anthropic_api_key="test-key"))
        
        assert provider._map_stop_reason("end_turn") == "stop"
        assert provider._map_stop_reason("max_tokens") == "length"
        assert provider._map_stop_reason("stop_sequence") == "stop"
        assert provider._map_stop_reason("unknown") == "unknown"