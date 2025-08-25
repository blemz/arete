"""
Test suite for Ollama LLM provider integration.

Tests the Ollama provider implementation including model management,
local server communication, and error handling for offline scenarios.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any
import json
import httpx

from arete.services.ollama_provider import OllamaProvider
from arete.services.llm_provider import (
    LLMMessage,
    LLMResponse,
    MessageRole,
    LLMProviderError,
    ProviderUnavailableError,
    RateLimitError
)
from arete.config import Settings


class TestOllamaProvider:
    """Test Ollama provider functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.settings = Settings(
            ollama_base_url="http://localhost:11434",
            llm_max_tokens=4000,
            llm_temperature=0.7,
            llm_timeout=30
        )
        self.provider = OllamaProvider(self.settings)

    def test_provider_initialization(self):
        """Test provider initialization with settings."""
        assert self.provider.name == "ollama"
        assert self.provider.settings == self.settings
        assert self.provider.base_url == "http://localhost:11434"
        assert not self.provider._initialized

    def test_provider_properties(self):
        """Test provider property access."""
        assert self.provider.timeout == 30
        assert self.provider.max_tokens == 4000
        assert self.provider.temperature == 0.7

    @patch('arete.services.ollama_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_initialize_success(self, mock_client_class):
        """Test successful provider initialization."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        self.provider.initialize()
        assert self.provider._initialized

    @patch('arete.services.ollama_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_initialize_server_unavailable(self, mock_client_class):
        """Test initialization when Ollama server is unavailable."""
        mock_client = Mock()
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with pytest.raises(ProviderUnavailableError, match="Ollama server unavailable"):
            self.provider.initialize()

    @patch('arete.services.ollama_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_check_availability_online(self, mock_client_class):
        """Test availability check when server is online."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        is_available = await self.provider._check_availability()
        assert is_available

    @patch('arete.services.ollama_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_check_availability_offline(self, mock_client_class):
        """Test availability check when server is offline."""
        mock_client = Mock()
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        is_available = await self.provider._check_availability()
        assert not is_available

    def test_is_available_property_not_initialized(self):
        """Test is_available property when not initialized."""
        # Should be False when not initialized
        assert not self.provider.is_available

    @patch('arete.services.ollama_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_get_available_models_success(self, mock_client_class):
        """Test getting available models from Ollama server."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama2:latest"},
                {"name": "codellama:python"},
                {"name": "phi:latest"}
            ]
        }
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        models = await self.provider._get_available_models()
        
        assert len(models) == 3
        assert "llama2:latest" in models
        assert "codellama:python" in models
        assert "phi:latest" in models

    @patch('arete.services.ollama_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_get_available_models_server_error(self, mock_client_class):
        """Test getting models when server returns error."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 500
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        models = await self.provider._get_available_models()
        assert models == []

    def test_supported_models_property_not_initialized(self):
        """Test supported_models property when not initialized."""
        models = self.provider.supported_models
        assert isinstance(models, list)
        # Should return empty list or default models when not initialized
        assert len(models) >= 0

    @patch('arete.services.ollama_provider.OllamaProvider._get_available_models')
    def test_supported_models_property_initialized(self, mock_get_models):
        """Test supported_models property when initialized."""
        mock_get_models.return_value = ["llama2:latest", "phi:latest"]
        self.provider._initialized = True
        self.provider._available_models = ["llama2:latest", "phi:latest"]
        
        models = self.provider.supported_models
        assert models == ["llama2:latest", "phi:latest"]

    @patch('arete.services.ollama_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_response_success(self, mock_client_class):
        """Test successful response generation."""
        # Setup mock client and response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "This is a response about Plato's philosophy."
            },
            "done": True,
            "total_duration": 1000000000,  # 1 second in nanoseconds
            "eval_count": 25,
            "model": "llama2:latest"
        }
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Initialize provider
        self.provider._initialized = True
        
        # Create test messages
        messages = [
            LLMMessage(role=MessageRole.SYSTEM, content="You are a philosophy tutor."),
            LLMMessage(role=MessageRole.USER, content="Explain Plato's theory of Forms.")
        ]
        
        response = await self.provider.generate_response(messages, model="llama2:latest")
        
        # Verify response
        assert isinstance(response, LLMResponse)
        assert response.content == "This is a response about Plato's philosophy."
        assert response.provider == "ollama"
        assert response.model == "llama2:latest"
        assert response.usage_tokens == 25
        assert response.finish_reason == "stop"

    @patch('arete.services.ollama_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_response_streaming(self, mock_client_class):
        """Test response generation with streaming."""
        # Setup mock client for streaming response
        mock_client = Mock()
        
        # Mock streaming responses
        stream_responses = [
            {"message": {"content": "This"}, "done": False},
            {"message": {"content": " is"}, "done": False},
            {"message": {"content": " a"}, "done": False},
            {"message": {"content": " response"}, "done": False},
            {"done": True, "total_duration": 1000000000, "eval_count": 20, "model": "llama2:latest"}
        ]
        
        async def mock_stream():
            for response_data in stream_responses:
                mock_response = Mock()
                mock_response.json.return_value = response_data
                yield mock_response
        
        mock_client.stream = Mock(return_value=mock_stream())
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        self.provider._initialized = True
        
        messages = [LLMMessage(role=MessageRole.USER, content="Test streaming")]
        
        response = await self.provider.generate_response(
            messages, 
            model="llama2:latest",
            stream=True
        )
        
        assert response.content == "This is a response"
        assert response.provider == "ollama"
        assert response.model == "llama2:latest"

    @pytest.mark.asyncio
    async def test_generate_response_not_initialized(self):
        """Test response generation when provider not initialized."""
        messages = [LLMMessage(role=MessageRole.USER, content="Test")]
        
        with pytest.raises(LLMProviderError, match="Provider not initialized"):
            await self.provider.generate_response(messages)

    @patch('arete.services.ollama_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_response_server_error(self, mock_client_class):
        """Test response generation when server returns error."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        self.provider._initialized = True
        
        messages = [LLMMessage(role=MessageRole.USER, content="Test")]
        
        with pytest.raises(LLMProviderError, match="Ollama API error"):
            await self.provider.generate_response(messages)

    @patch('arete.services.ollama_provider.httpx.AsyncClient')
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

    @patch('arete.services.ollama_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_response_connection_error(self, mock_client_class):
        """Test response generation with connection error."""
        mock_client = Mock()
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        self.provider._initialized = True
        
        messages = [LLMMessage(role=MessageRole.USER, content="Test")]
        
        with pytest.raises(ProviderUnavailableError, match="Ollama server unavailable"):
            await self.provider.generate_response(messages)

    def test_format_messages_for_ollama(self):
        """Test message formatting for Ollama API."""
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

    def test_format_messages_empty_list(self):
        """Test formatting empty message list."""
        formatted = self.provider._format_messages([])
        assert formatted == []

    def test_extract_content_from_response_normal(self):
        """Test content extraction from normal response."""
        response_data = {
            "message": {
                "role": "assistant",
                "content": "Test response content"
            },
            "done": True,
            "total_duration": 1000000000,
            "eval_count": 15,
            "model": "llama2:latest"
        }
        
        content, tokens, finish_reason = self.provider._extract_content_from_response(response_data)
        
        assert content == "Test response content"
        assert tokens == 15
        assert finish_reason == "stop"

    def test_extract_content_from_response_no_message(self):
        """Test content extraction when response has no message."""
        response_data = {
            "done": True,
            "error": "No message generated"
        }
        
        content, tokens, finish_reason = self.provider._extract_content_from_response(response_data)
        
        assert content == ""
        assert tokens is None
        assert finish_reason == "error"

    def test_extract_content_from_response_incomplete(self):
        """Test content extraction from incomplete response."""
        response_data = {
            "message": {
                "role": "assistant",
                "content": "Partial response"
            },
            "done": False
        }
        
        content, tokens, finish_reason = self.provider._extract_content_from_response(response_data)
        
        assert content == "Partial response"
        assert tokens is None
        assert finish_reason is None

    @patch('arete.services.ollama_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_pull_model_success(self, mock_client_class):
        """Test successful model pulling."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        success = await self.provider.pull_model("llama2:latest")
        assert success

    @patch('arete.services.ollama_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_pull_model_failure(self, mock_client_class):
        """Test model pulling failure."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 404
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        success = await self.provider.pull_model("nonexistent:model")
        assert not success

    @patch('arete.services.ollama_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_delete_model_success(self, mock_client_class):
        """Test successful model deletion."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.delete = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        success = await self.provider.delete_model("llama2:latest")
        assert success

    def test_get_health_status_not_initialized(self):
        """Test health status when not initialized."""
        status = self.provider.get_health_status()
        
        assert status["provider"] == "ollama"
        assert status["status"] == "not_initialized"
        assert not status["initialized"]

    @patch('arete.services.ollama_provider.OllamaProvider._check_availability')
    def test_get_health_status_initialized(self, mock_check_availability):
        """Test health status when initialized."""
        mock_check_availability.return_value = True
        self.provider._initialized = True
        self.provider._available_models = ["llama2:latest", "phi:latest"]
        
        status = self.provider.get_health_status()
        
        assert status["provider"] == "ollama"
        assert status["status"] == "healthy"
        assert status["initialized"]
        assert status["available_models"] == ["llama2:latest", "phi:latest"]
        assert status["server_url"] == "http://localhost:11434"

    def test_cleanup(self):
        """Test provider cleanup."""
        # Should not raise any errors
        self.provider.cleanup()
        assert not self.provider._initialized


class TestOllamaProviderIntegration:
    """Integration tests for Ollama provider with mocked server responses."""
    
    @patch('arete.services.ollama_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_end_to_end_conversation_flow(self, mock_client_class):
        """Test complete conversation flow with model management."""
        # Setup provider
        settings = Settings(ollama_base_url="http://localhost:11434")
        provider = OllamaProvider(settings)
        
        # Mock client setup
        mock_client = Mock()
        
        # Mock initialization check
        init_response = Mock()
        init_response.status_code = 200
        init_response.json.return_value = {"status": "success"}
        
        # Mock models list
        models_response = Mock()
        models_response.status_code = 200
        models_response.json.return_value = {
            "models": [{"name": "llama2:latest"}, {"name": "phi:latest"}]
        }
        
        # Mock generation response
        gen_response = Mock()
        gen_response.status_code = 200
        gen_response.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "Plato's Theory of Forms suggests that beyond our physical world..."
            },
            "done": True,
            "total_duration": 2000000000,
            "eval_count": 45,
            "model": "llama2:latest"
        }
        
        # Configure mock client
        mock_client.get = AsyncMock(side_effect=[init_response, models_response])
        mock_client.post = AsyncMock(return_value=gen_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Initialize provider
        provider.initialize()
        
        # Test conversation
        messages = [
            LLMMessage(role=MessageRole.SYSTEM, content="You are a philosophy tutor specializing in ancient Greek philosophy."),
            LLMMessage(role=MessageRole.USER, content="Can you explain Plato's Theory of Forms?")
        ]
        
        response = await provider.generate_response(messages, model="llama2:latest")
        
        # Verify response
        assert isinstance(response, LLMResponse)
        assert "Plato's Theory of Forms" in response.content
        assert response.provider == "ollama"
        assert response.model == "llama2:latest"
        assert response.usage_tokens == 45
        
        # Verify model availability
        models = provider.supported_models
        assert "llama2:latest" in models
        assert "phi:latest" in models

    @patch('arete.services.ollama_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_model_management_workflow(self, mock_client_class):
        """Test model pulling and management workflow."""
        provider = OllamaProvider(Settings())
        
        mock_client = Mock()
        
        # Mock successful model pull
        pull_response = Mock()
        pull_response.status_code = 200
        
        # Mock updated models list after pull
        models_response = Mock()
        models_response.status_code = 200
        models_response.json.return_value = {
            "models": [{"name": "llama2:latest"}, {"name": "new-model:latest"}]
        }
        
        mock_client.post = AsyncMock(return_value=pull_response)
        mock_client.get = AsyncMock(return_value=models_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Pull new model
        success = await provider.pull_model("new-model:latest")
        assert success
        
        # Verify model is now available
        models = await provider._get_available_models()
        assert "new-model:latest" in models

    @patch('arete.services.ollama_provider.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_error_recovery_scenarios(self, mock_client_class):
        """Test various error recovery scenarios."""
        provider = OllamaProvider(Settings())
        provider._initialized = True
        
        mock_client = Mock()
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        messages = [LLMMessage(role=MessageRole.USER, content="Test message")]
        
        # Test server error recovery
        mock_client.post = AsyncMock(side_effect=[
            Mock(status_code=500, text="Server error"),  # First attempt fails
            Mock(status_code=200, json=lambda: {  # Second attempt succeeds
                "message": {"role": "assistant", "content": "Recovery successful"},
                "done": True, "eval_count": 10, "model": "llama2:latest"
            })
        ])
        
        # Note: Current implementation doesn't have built-in retry logic
        # This test documents the expected behavior for future enhancement
        with pytest.raises(LLMProviderError):
            await provider.generate_response(messages)


class TestOllamaProviderConfiguration:
    """Test Ollama provider configuration and settings."""
    
    def test_custom_base_url_configuration(self):
        """Test provider with custom base URL."""
        settings = Settings(ollama_base_url="http://custom-ollama:11434")
        provider = OllamaProvider(settings)
        
        assert provider.base_url == "http://custom-ollama:11434"

    def test_custom_timeout_configuration(self):
        """Test provider with custom timeout."""
        settings = Settings(llm_timeout=60)
        provider = OllamaProvider(settings)
        
        assert provider.timeout == 60

    def test_default_model_selection(self):
        """Test default model selection behavior."""
        provider = OllamaProvider(Settings())
        
        # Test with no models available
        assert provider._get_default_model([]) == "llama2:latest"
        
        # Test with available models
        models = ["phi:latest", "codellama:python", "llama2:latest"]
        default = provider._get_default_model(models)
        assert default in models

    def test_request_parameters_building(self):
        """Test building request parameters for Ollama API."""
        provider = OllamaProvider(Settings())
        
        messages = [LLMMessage(role=MessageRole.USER, content="Test")]
        
        params = provider._build_request_params(
            messages=messages,
            model="llama2:latest",
            max_tokens=1000,
            temperature=0.5
        )
        
        expected_params = {
            "model": "llama2:latest",
            "messages": [{"role": "user", "content": "Test"}],
            "stream": False,
            "options": {
                "num_predict": 1000,
                "temperature": 0.5
            }
        }
        
        assert params == expected_params

    def test_request_parameters_with_defaults(self):
        """Test building request parameters with default values."""
        settings = Settings(llm_max_tokens=2000, llm_temperature=0.8)
        provider = OllamaProvider(settings)
        
        messages = [LLMMessage(role=MessageRole.USER, content="Test")]
        
        params = provider._build_request_params(
            messages=messages,
            model="phi:latest"
        )
        
        assert params["options"]["num_predict"] == 2000
        assert params["options"]["temperature"] == 0.8