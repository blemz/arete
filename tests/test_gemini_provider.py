"""
Test suite for Google Gemini LLM provider integration.

Tests the Gemini provider implementation including API key management,
model selection, safety settings, and error handling for Google's Gemini models.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any
import json
import httpx

from arete.services.gemini_provider import GeminiProvider
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


class TestGeminiProvider:
    """Test Gemini provider functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.settings = Settings(
            gemini_api_key="test-api-key-12345",
            llm_max_tokens=4000,
            llm_temperature=0.7,
            llm_timeout=30
        )
        self.provider = GeminiProvider(self.settings)

    def test_provider_initialization(self):
        """Test provider initialization with settings."""
        assert self.provider.name == "gemini"
        assert self.provider.settings == self.settings
        assert self.provider.api_key == "test-api-key-12345"
        assert self.provider.base_url == "https://generativelanguage.googleapis.com/v1beta"
        assert not self.provider._initialized

    def test_provider_initialization_no_api_key(self):
        """Test provider initialization without API key."""
        settings = Settings(gemini_api_key="")
        
        with pytest.raises(AuthenticationError, match="Gemini API key not provided"):
            GeminiProvider(settings)

    def test_provider_properties(self):
        """Test provider property access."""
        assert self.provider.timeout == 30
        assert self.provider.max_tokens == 4000
        assert self.provider.temperature == 0.7

    @patch('arete.services.gemini_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_initialize_success(self, mock_client_class):
        """Test successful provider initialization."""
        mock_client = Mock()
        
        # Mock models response
        models_response = Mock()
        models_response.status_code = 200
        models_response.json.return_value = {
            "models": [
                {
                    "name": "models/gemini-1.5-pro",
                    "displayName": "Gemini 1.5 Pro",
                    "description": "Advanced reasoning and complex tasks",
                    "inputTokenLimit": 2097152,
                    "outputTokenLimit": 8192
                },
                {
                    "name": "models/gemini-1.5-flash",
                    "displayName": "Gemini 1.5 Flash",
                    "description": "Fast and versatile performance",
                    "inputTokenLimit": 1048576,
                    "outputTokenLimit": 8192
                }
            ]
        }
        
        mock_client.get = AsyncMock(return_value=models_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        self.provider.initialize()
        assert self.provider._initialized

    @patch('arete.services.gemini_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_initialize_api_error(self, mock_client_class):
        """Test initialization when API returns error."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.json.return_value = {
            "error": {
                "code": 403,
                "message": "API key not valid",
                "status": "PERMISSION_DENIED"
            }
        }
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with pytest.raises(AuthenticationError, match="Gemini API authentication failed"):
            self.provider.initialize()

    @patch('arete.services.gemini_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_initialize_network_error(self, mock_client_class):
        """Test initialization when network error occurs."""
        mock_client = Mock()
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with pytest.raises(ProviderUnavailableError, match="Gemini API unavailable"):
            self.provider.initialize()

    def test_is_available_property_not_initialized(self):
        """Test is_available property when not initialized."""
        assert not self.provider.is_available

    def test_is_available_property_initialized(self):
        """Test is_available property when initialized."""
        self.provider._initialized = True
        assert self.provider.is_available

    @patch('arete.services.gemini_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_get_available_models_success(self, mock_client_class):
        """Test getting available models from Gemini API."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {
                    "name": "models/gemini-1.5-pro",
                    "displayName": "Gemini 1.5 Pro",
                    "inputTokenLimit": 2097152
                },
                {
                    "name": "models/gemini-1.5-flash",
                    "displayName": "Gemini 1.5 Flash",
                    "inputTokenLimit": 1048576
                },
                {
                    "name": "models/gemini-pro",
                    "displayName": "Gemini Pro",
                    "inputTokenLimit": 32768
                }
            ]
        }
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        models = await self.provider._get_available_models()
        
        assert len(models) == 3
        assert "gemini-1.5-pro" in models
        assert "gemini-1.5-flash" in models
        assert "gemini-pro" in models

    def test_supported_models_property_not_initialized(self):
        """Test supported_models property when not initialized."""
        models = self.provider.supported_models
        assert isinstance(models, list)
        assert len(models) >= 0

    def test_supported_models_property_initialized(self):
        """Test supported_models property when initialized."""
        self.provider._initialized = True
        self.provider._available_models = ["gemini-1.5-pro", "gemini-1.5-flash"]
        
        models = self.provider.supported_models
        assert models == ["gemini-1.5-pro", "gemini-1.5-flash"]

    @patch('arete.services.gemini_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_response_success(self, mock_client_class):
        """Test successful response generation."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": "Plato's Theory of Forms is a central doctrine in his philosophy that proposes the existence of a realm of perfect, eternal, and immutable Forms or Ideas that serve as the templates for all things in our physical world. For instance, there is a perfect Form of Beauty that all beautiful objects in our world participate in or imitate."
                            }
                        ],
                        "role": "model"
                    },
                    "finishReason": "STOP",
                    "safetyRatings": [
                        {
                            "category": "HARM_CATEGORY_HATE_SPEECH",
                            "probability": "NEGLIGIBLE"
                        }
                    ]
                }
            ],
            "usageMetadata": {
                "promptTokenCount": 45,
                "candidatesTokenCount": 67,
                "totalTokenCount": 112
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
        
        response = await self.provider.generate_response(messages, model="gemini-1.5-pro")
        
        assert isinstance(response, LLMResponse)
        assert "Theory of Forms" in response.content
        assert response.provider == "gemini"
        assert response.model == "gemini-1.5-pro"
        assert response.usage_tokens == 112
        assert response.finish_reason == "stop"

    @patch('arete.services.gemini_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_response_with_streaming(self, mock_client_class):
        """Test response generation with streaming."""
        mock_client = Mock()
        
        # Mock streaming responses
        stream_data = [
            '{"candidates":[{"content":{"parts":[{"text":"Plato\'s"}],"role":"model"}}]}\n',
            '{"candidates":[{"content":{"parts":[{"text":" Theory"}],"role":"model"}}]}\n',
            '{"candidates":[{"content":{"parts":[{"text":" of"}],"role":"model"}}]}\n',
            '{"candidates":[{"content":{"parts":[{"text":" Forms"}],"role":"model"}}]}\n',
            '{"candidates":[{"content":{"parts":[{"text":""}],"role":"model"},"finishReason":"STOP"}],"usageMetadata":{"totalTokenCount":42}}\n'
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
            model="gemini-1.5-pro",
            stream=True
        )
        
        assert response.content == "Plato's Theory of Forms"
        assert response.provider == "gemini"
        assert response.usage_tokens == 42
        assert response.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_generate_response_not_initialized(self):
        """Test response generation when provider not initialized."""
        messages = [LLMMessage(role=MessageRole.USER, content="Test")]
        
        with pytest.raises(LLMProviderError, match="Provider not initialized"):
            await self.provider.generate_response(messages)

    @patch('arete.services.gemini_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_response_safety_blocked(self, mock_client_class):
        """Test response generation when content is safety blocked."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [],
                        "role": "model"
                    },
                    "finishReason": "SAFETY",
                    "safetyRatings": [
                        {
                            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                            "probability": "HIGH"
                        }
                    ]
                }
            ]
        }
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        self.provider._initialized = True
        
        messages = [LLMMessage(role=MessageRole.USER, content="Test")]
        
        with pytest.raises(LLMProviderError, match="Content blocked by safety filters"):
            await self.provider.generate_response(messages)

    @patch('arete.services.gemini_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_response_rate_limit_error(self, mock_client_class):
        """Test response generation when rate limit is hit."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {
            "error": {
                "code": 429,
                "message": "Quota exceeded",
                "status": "RESOURCE_EXHAUSTED"
            }
        }
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        self.provider._initialized = True
        
        messages = [LLMMessage(role=MessageRole.USER, content="Test")]
        
        with pytest.raises(RateLimitError):
            await self.provider.generate_response(messages)

    @patch('arete.services.gemini_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_response_authentication_error(self, mock_client_class):
        """Test response generation with authentication error."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.json.return_value = {
            "error": {
                "code": 403,
                "message": "API key not valid",
                "status": "PERMISSION_DENIED"
            }
        }
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        self.provider._initialized = True
        
        messages = [LLMMessage(role=MessageRole.USER, content="Test")]
        
        with pytest.raises(AuthenticationError, match="Gemini API authentication failed"):
            await self.provider.generate_response(messages)

    def test_format_messages_for_gemini(self):
        """Test message formatting for Gemini API."""
        messages = [
            LLMMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
            LLMMessage(role=MessageRole.USER, content="What is philosophy?"),
            LLMMessage(role=MessageRole.ASSISTANT, content="Philosophy is the study of wisdom."),
            LLMMessage(role=MessageRole.USER, content="Can you elaborate?")
        ]
        
        formatted = self.provider._format_messages(messages)
        
        # Gemini combines system message with first user message
        assert len(formatted) == 3
        assert formatted[0]["role"] == "user"
        assert "You are a helpful assistant." in formatted[0]["parts"][0]["text"]
        assert "What is philosophy?" in formatted[0]["parts"][0]["text"]
        assert formatted[1]["role"] == "model"
        assert formatted[1]["parts"][0]["text"] == "Philosophy is the study of wisdom."
        assert formatted[2]["role"] == "user"
        assert formatted[2]["parts"][0]["text"] == "Can you elaborate?"

    def test_extract_content_from_response_normal(self):
        """Test content extraction from normal response."""
        response_data = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "Test response content"}
                        ],
                        "role": "model"
                    },
                    "finishReason": "STOP"
                }
            ],
            "usageMetadata": {
                "totalTokenCount": 25
            }
        }
        
        content, tokens, finish_reason = self.provider._extract_content_from_response(response_data)
        
        assert content == "Test response content"
        assert tokens == 25
        assert finish_reason == "stop"

    def test_extract_content_from_response_no_candidates(self):
        """Test content extraction when response has no candidates."""
        response_data = {
            "candidates": [],
            "usageMetadata": {"totalTokenCount": 0}
        }
        
        content, tokens, finish_reason = self.provider._extract_content_from_response(response_data)
        
        assert content == ""
        assert tokens == 0
        assert finish_reason == "error"

    def test_get_default_model(self):
        """Test default model selection."""
        # Test with no models available
        assert self.provider._get_default_model([]) == "gemini-1.5-pro"
        
        # Test with available models
        models = ["gemini-pro", "gemini-1.5-pro", "gemini-1.5-flash"]
        default = self.provider._get_default_model(models)
        assert default == "gemini-1.5-pro"  # Should prefer 1.5-pro
        
        # Test without preferred models
        models = ["gemini-pro", "gemini-1.0-pro"]
        default = self.provider._get_default_model(models)
        assert default == "gemini-pro"  # Should return first available

    def test_build_request_params(self):
        """Test building request parameters for Gemini API."""
        messages = [LLMMessage(role=MessageRole.USER, content="Test")]
        
        params = self.provider._build_request_params(
            messages=messages,
            model="gemini-1.5-pro",
            max_tokens=1000,
            temperature=0.5
        )
        
        assert "contents" in params
        assert "generationConfig" in params
        assert params["generationConfig"]["maxOutputTokens"] == 1000
        assert params["generationConfig"]["temperature"] == 0.5
        assert "safetySettings" in params

    def test_safety_settings_configuration(self):
        """Test safety settings configuration."""
        safety_settings = self.provider._get_safety_settings()
        
        # Should have settings for all major harm categories
        expected_categories = [
            "HARM_CATEGORY_HATE_SPEECH",
            "HARM_CATEGORY_DANGEROUS_CONTENT", 
            "HARM_CATEGORY_HARASSMENT",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT"
        ]
        
        categories = [setting["category"] for setting in safety_settings]
        for category in expected_categories:
            assert category in categories

    def test_get_health_status_not_initialized(self):
        """Test health status when not initialized."""
        status = self.provider.get_health_status()
        
        assert status["provider"] == "gemini"
        assert status["status"] == "not_initialized"
        assert not status["initialized"]

    def test_get_health_status_initialized(self):
        """Test health status when initialized."""
        self.provider._initialized = True
        self.provider._available_models = ["gemini-1.5-pro", "gemini-1.5-flash"]
        
        status = self.provider.get_health_status()
        
        assert status["provider"] == "gemini"
        assert status["status"] == "healthy"
        assert status["initialized"]
        assert status["available_models"] == ["gemini-1.5-pro", "gemini-1.5-flash"]
        assert status["api_url"] == "https://generativelanguage.googleapis.com/v1beta"

    def test_cleanup(self):
        """Test provider cleanup."""
        self.provider.cleanup()
        assert not self.provider._initialized
        assert self.provider._available_models == []


class TestGeminiProviderIntegration:
    """Integration tests for Gemini provider with mocked API responses."""
    
    @patch('arete.services.gemini_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_end_to_end_philosophy_conversation(self, mock_client_class):
        """Test complete philosophy tutoring conversation flow."""
        settings = Settings(gemini_api_key="test-key")
        provider = GeminiProvider(settings)
        
        mock_client = Mock()
        
        # Mock initialization
        models_response = Mock()
        models_response.status_code = 200
        models_response.json.return_value = {
            "models": [
                {"name": "models/gemini-1.5-pro", "displayName": "Gemini 1.5 Pro"},
                {"name": "models/gemini-1.5-flash", "displayName": "Gemini 1.5 Flash"}
            ]
        }
        
        # Mock generation response
        gen_response = Mock()
        gen_response.status_code = 200
        gen_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": "Plato's Theory of Forms is a foundational concept in Western philosophy. It proposes that beyond our physical world of imperfect objects exists a realm of perfect, eternal Forms or Ideas. For example, when we see beautiful things in our world, they are merely imperfect copies of the perfect Form of Beauty."
                            }
                        ],
                        "role": "model"
                    },
                    "finishReason": "STOP"
                }
            ],
            "usageMetadata": {"totalTokenCount": 89}
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
        
        response = await provider.generate_response(messages, model="gemini-1.5-pro")
        
        assert isinstance(response, LLMResponse)
        assert "Theory of Forms" in response.content
        assert "perfect" in response.content
        assert response.provider == "gemini"
        assert response.model == "gemini-1.5-pro"
        assert response.usage_tokens == 89

    @patch('arete.services.gemini_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_safety_filter_handling(self, mock_client_class):
        """Test handling of safety-filtered responses."""
        provider = GeminiProvider(Settings(gemini_api_key="test-key"))
        provider._initialized = True
        
        mock_client = Mock()
        
        # Mock safety-blocked response
        blocked_response = Mock()
        blocked_response.status_code = 200
        blocked_response.json.return_value = {
            "candidates": [
                {
                    "content": {"parts": [], "role": "model"},
                    "finishReason": "SAFETY",
                    "safetyRatings": [
                        {
                            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                            "probability": "HIGH"
                        }
                    ]
                }
            ]
        }
        
        mock_client.post = AsyncMock(return_value=blocked_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        messages = [LLMMessage(role=MessageRole.USER, content="Test message")]
        
        with pytest.raises(LLMProviderError, match="Content blocked by safety filters"):
            await provider.generate_response(messages)


class TestGeminiProviderConfiguration:
    """Test Gemini provider configuration and settings."""
    
    def test_api_key_validation(self):
        """Test API key validation during initialization."""
        # Valid API key
        settings = Settings(gemini_api_key="AIzaSy-test-12345")
        provider = GeminiProvider(settings)
        assert provider.api_key == "AIzaSy-test-12345"
        
        # Empty API key should raise error
        settings = Settings(gemini_api_key="")
        with pytest.raises(AuthenticationError):
            GeminiProvider(settings)

    def test_model_name_normalization(self):
        """Test model name normalization for Gemini API."""
        provider = GeminiProvider(Settings(gemini_api_key="test-key"))
        
        # Should remove 'models/' prefix if present
        assert provider._normalize_model_name("models/gemini-1.5-pro") == "gemini-1.5-pro"
        assert provider._normalize_model_name("gemini-1.5-pro") == "gemini-1.5-pro"

    def test_url_construction(self):
        """Test API URL construction."""
        provider = GeminiProvider(Settings(gemini_api_key="test-key"))
        
        # Models list URL
        models_url = provider._get_models_url()
        assert models_url == f"{provider.base_url}/models?key={provider.api_key}"
        
        # Generation URL
        gen_url = provider._get_generation_url("gemini-1.5-pro")
        assert gen_url == f"{provider.base_url}/models/gemini-1.5-pro:generateContent?key={provider.api_key}"
        
        # Streaming URL
        stream_url = provider._get_generation_url("gemini-1.5-pro", stream=True)
        assert stream_url == f"{provider.base_url}/models/gemini-1.5-pro:streamGenerateContent?key={provider.api_key}"

    def test_request_parameters_with_system_instruction(self):
        """Test system instruction handling in requests."""
        provider = GeminiProvider(Settings(gemini_api_key="test-key"))
        
        messages = [
            LLMMessage(role=MessageRole.SYSTEM, content="You are a philosophy tutor."),
            LLMMessage(role=MessageRole.USER, content="What is ethics?")
        ]
        
        params = provider._build_request_params(messages, "gemini-1.5-pro")
        
        # System instruction should be separate from contents
        assert "systemInstruction" in params
        assert params["systemInstruction"]["parts"][0]["text"] == "You are a philosophy tutor."
        
        # Contents should only have user message
        assert len(params["contents"]) == 1
        assert params["contents"][0]["role"] == "user"
        assert params["contents"][0]["parts"][0]["text"] == "What is ethics?"