"""
Test suite for SimpleLLMService - user-controlled provider selection.

Tests the simple LLM service that allows direct provider selection
via environment variables and method parameters.
"""

import pytest
import os
from unittest.mock import Mock, AsyncMock, patch

from arete.services.simple_llm_service import (
    SimpleLLMService,
    get_llm_service,
    quick_generate
)
from arete.services.llm_provider import (
    LLMMessage,
    LLMResponse,
    MessageRole,
    LLMProviderError,
    ProviderUnavailableError,
    AuthenticationError
)
from arete.config import Settings


class TestSimpleLLMService:
    """Test SimpleLLMService functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        # Clear environment variable for clean tests
        os.environ.pop("SELECTED_LLM_PROVIDER", None)
        
        self.settings = Settings(
            default_llm_provider="ollama",
            selected_llm_provider="",
            ollama_api_key="",
            anthropic_api_key="test-key"
        )
        
        self.service = SimpleLLMService(self.settings)
    
    def teardown_method(self):
        """Clean up after tests."""
        os.environ.pop("SELECTED_LLM_PROVIDER", None)
    
    def test_service_initialization(self):
        """Test service initialization."""
        assert self.service.settings == self.settings
        assert self.service.factory is not None
        assert len(self.service._providers) == 0
        assert self.service.available_provider_types == [
            "ollama", "openrouter", "gemini", "anthropic", "openai"
        ]
    
    def test_get_active_provider_name_default(self):
        """Test getting active provider name from default."""
        # No env var, no selection -> default
        provider = self.service.get_active_provider_name()
        assert provider == "ollama"
    
    def test_get_active_provider_name_selected(self):
        """Test getting active provider name from settings selection."""
        self.settings.selected_llm_provider = "anthropic"
        provider = self.service.get_active_provider_name()
        assert provider == "anthropic"
    
    def test_get_active_provider_name_environment(self):
        """Test getting active provider name from environment variable."""
        os.environ["SELECTED_LLM_PROVIDER"] = "openai"
        provider = self.service.get_active_provider_name()
        assert provider == "openai"
    
    def test_get_active_provider_name_environment_priority(self):
        """Test that environment variable takes priority."""
        self.settings.selected_llm_provider = "anthropic"
        os.environ["SELECTED_LLM_PROVIDER"] = "gemini"
        
        provider = self.service.get_active_provider_name()
        assert provider == "gemini"  # Environment takes priority
    
    def test_get_active_provider_name_invalid_env(self):
        """Test handling of invalid environment variable."""
        os.environ["SELECTED_LLM_PROVIDER"] = "invalid-provider"
        
        # Should fall back to settings
        provider = self.service.get_active_provider_name()
        assert provider == "ollama"  # Default from settings
    
    def test_set_provider_valid(self):
        """Test setting valid provider."""
        self.service.set_provider("anthropic")
        
        # Should update environment variable
        assert os.environ["SELECTED_LLM_PROVIDER"] == "anthropic"
        
        # Should be reflected in active provider
        assert self.service.get_active_provider_name() == "anthropic"
    
    def test_set_provider_invalid(self):
        """Test setting invalid provider."""
        with pytest.raises(LLMProviderError, match="Invalid provider"):
            self.service.set_provider("invalid-provider")
    
    def test_set_provider_case_insensitive(self):
        """Test setting provider is case insensitive."""
        self.service.set_provider("ANTHROPIC")
        assert os.environ["SELECTED_LLM_PROVIDER"] == "anthropic"
        
        self.service.set_provider("  OpenAI  ")
        assert os.environ["SELECTED_LLM_PROVIDER"] == "openai"
    
    @patch('arete.services.simple_llm_service.LLMProviderFactory')
    def test_get_provider_creates_and_caches(self, mock_factory_class):
        """Test provider creation and caching."""
        mock_factory = Mock()
        mock_provider = Mock()
        mock_provider.initialize = Mock()
        mock_factory.create_provider.return_value = mock_provider
        mock_factory_class.return_value = mock_factory
        
        service = SimpleLLMService(self.settings)
        service.factory = mock_factory
        
        # First call should create provider
        provider = service.get_provider("ollama")
        
        mock_factory.create_provider.assert_called_once_with("ollama")
        mock_provider.initialize.assert_called_once()
        assert provider == mock_provider
        
        # Second call should use cached provider
        mock_factory.create_provider.reset_mock()
        mock_provider.initialize.reset_mock()
        
        provider2 = service.get_provider("ollama")
        
        mock_factory.create_provider.assert_not_called()
        mock_provider.initialize.assert_not_called()
        assert provider2 == mock_provider
    
    @patch('arete.services.simple_llm_service.LLMProviderFactory')
    def test_get_provider_initialization_error(self, mock_factory_class):
        """Test provider initialization error handling."""
        mock_factory = Mock()
        mock_provider = Mock()
        mock_provider.initialize.side_effect = AuthenticationError("Invalid API key", "test")
        mock_factory.create_provider.return_value = mock_provider
        mock_factory_class.return_value = mock_factory
        
        service = SimpleLLMService(self.settings)
        service.factory = mock_factory
        
        with pytest.raises(AuthenticationError, match="Authentication failed for test"):
            service.get_provider("test")
    
    @patch('arete.services.simple_llm_service.LLMProviderFactory')
    @pytest.mark.asyncio
    async def test_generate_response_success(self, mock_factory_class):
        """Test successful response generation."""
        mock_factory = Mock()
        mock_provider = Mock()
        mock_provider.initialize = Mock()
        mock_provider.is_available = True
        mock_response = LLMResponse(
            content="Test response",
            provider="ollama",
            model="test-model",
            usage_tokens=50,
            metadata={}
        )
        mock_provider.generate_response = AsyncMock(return_value=mock_response)
        mock_factory.create_provider.return_value = mock_provider
        mock_factory_class.return_value = mock_factory
        
        service = SimpleLLMService(self.settings)
        service.factory = mock_factory
        
        messages = [LLMMessage(role=MessageRole.USER, content="Hello")]
        
        response = await service.generate_response(messages)
        
        assert response.content == "Test response"
        assert response.metadata["service"] == "SimpleLLMService"
        assert response.metadata["active_provider"] == "ollama"
        
        mock_provider.generate_response.assert_called_once()
        call_args = mock_provider.generate_response.call_args
        assert call_args[1]["messages"] == messages
        assert call_args[1]["max_tokens"] == self.settings.llm_max_tokens
        assert call_args[1]["temperature"] == self.settings.llm_temperature
    
    @patch('arete.services.simple_llm_service.LLMProviderFactory')
    @pytest.mark.asyncio
    async def test_generate_response_specific_provider(self, mock_factory_class):
        """Test response generation with specific provider."""
        mock_factory = Mock()
        mock_provider = Mock()
        mock_provider.initialize = Mock()
        mock_provider.is_available = True
        mock_response = LLMResponse(
            content="Anthropic response",
            provider="anthropic",
            model="claude-3",
            usage_tokens=75
        )
        mock_provider.generate_response = AsyncMock(return_value=mock_response)
        mock_factory.create_provider.return_value = mock_provider
        mock_factory_class.return_value = mock_factory
        
        service = SimpleLLMService(self.settings)
        service.factory = mock_factory
        
        messages = [LLMMessage(role=MessageRole.USER, content="Hello")]
        
        response = await service.generate_response(
            messages, 
            provider="anthropic",
            model="claude-3-opus",
            temperature=0.5
        )
        
        assert response.content == "Anthropic response"
        assert response.metadata["provider_selected_by"] == "user"
        
        mock_factory.create_provider.assert_called_once_with("anthropic")
        call_args = mock_provider.generate_response.call_args
        assert call_args[1]["model"] == "claude-3-opus"
        assert call_args[1]["temperature"] == 0.5
    
    @patch('arete.services.simple_llm_service.LLMProviderFactory')
    @pytest.mark.asyncio
    async def test_generate_response_provider_unavailable(self, mock_factory_class):
        """Test response generation with unavailable provider."""
        mock_factory = Mock()
        mock_provider = Mock()
        mock_provider.initialize = Mock()
        mock_provider.is_available = False
        mock_factory.create_provider.return_value = mock_provider
        mock_factory_class.return_value = mock_factory
        
        service = SimpleLLMService(self.settings)
        service.factory = mock_factory
        
        messages = [LLMMessage(role=MessageRole.USER, content="Hello")]
        
        with pytest.raises(ProviderUnavailableError, match="is not available"):
            await service.generate_response(messages)
    
    def test_list_available_providers(self):
        """Test listing available providers."""
        providers = self.service.list_available_providers()
        assert providers == ["ollama", "openrouter", "gemini", "anthropic", "openai"]
    
    def test_get_provider_info(self):
        """Test getting provider information."""
        os.environ["SELECTED_LLM_PROVIDER"] = "anthropic"
        
        info = self.service.get_provider_info()
        
        assert info["active_provider"] == "anthropic"
        assert info["available_providers"] == [
            "ollama", "openrouter", "gemini", "anthropic", "openai"
        ]
        assert "ollama" in info["configured_providers"]  # No API key needed
        assert "anthropic" in info["configured_providers"]  # Has test-key
        assert info["source"]["env_variable"] == "anthropic"
        assert info["source"]["settings_default"] == "ollama"
    
    @patch('arete.services.simple_llm_service.LLMProviderFactory')
    def test_get_provider_health(self, mock_factory_class):
        """Test getting provider health status."""
        mock_factory = Mock()
        mock_provider = Mock()
        mock_provider.initialize = Mock()
        mock_provider.get_health_status.return_value = {
            "provider": "ollama",
            "status": "healthy"
        }
        mock_factory.create_provider.return_value = mock_provider
        mock_factory_class.return_value = mock_factory
        
        service = SimpleLLMService(self.settings)
        service.factory = mock_factory
        
        health = service.get_provider_health("ollama")
        
        assert health["provider"] == "ollama"
        assert health["status"] == "healthy"
    
    @patch('arete.services.simple_llm_service.LLMProviderFactory')
    def test_get_provider_health_error(self, mock_factory_class):
        """Test provider health check error handling."""
        mock_factory = Mock()
        mock_factory.create_provider.side_effect = Exception("Provider creation failed")
        mock_factory_class.return_value = mock_factory
        
        service = SimpleLLMService(self.settings)
        service.factory = mock_factory
        
        health = service.get_provider_health("invalid")
        
        assert health["provider"] == "invalid"
        assert health["status"] == "error"
        assert "Provider creation failed" in health["error"]
        assert health["available"] is False
    
    def test_cleanup(self):
        """Test service cleanup."""
        # Add mock providers
        mock_provider_1 = Mock()
        mock_provider_1.cleanup = Mock()
        mock_provider_2 = Mock()  # No cleanup method
        
        self.service._providers = {
            "provider1": mock_provider_1,
            "provider2": mock_provider_2
        }
        self.service._initialized_providers = {
            "provider1": True,
            "provider2": True
        }
        
        self.service.cleanup()
        
        # Should call cleanup on provider1
        mock_provider_1.cleanup.assert_called_once()
        
        # Should clear caches
        assert len(self.service._providers) == 0
        assert len(self.service._initialized_providers) == 0


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_get_llm_service(self):
        """Test getting LLM service instance."""
        service = get_llm_service()
        assert isinstance(service, SimpleLLMService)
    
    @patch('arete.services.simple_llm_service.SimpleLLMService')
    @pytest.mark.asyncio
    async def test_quick_generate(self, mock_service_class):
        """Test quick generate utility function."""
        mock_service = Mock()
        mock_response = LLMResponse(content="Quick response", provider="test")
        mock_service.generate_response = AsyncMock(return_value=mock_response)
        mock_service_class.return_value = mock_service
        
        result = await quick_generate("Hello", provider="anthropic", temperature=0.8)
        
        assert result == "Quick response"
        
        # Verify service was called correctly
        mock_service.generate_response.assert_called_once()
        call_args = mock_service.generate_response.call_args
        assert len(call_args[1]["messages"]) == 1
        assert call_args[1]["messages"][0].content == "Hello"
        assert call_args[1]["provider"] == "anthropic"
        assert call_args[1]["temperature"] == 0.8


class TestEnvironmentIntegration:
    """Test environment variable integration."""
    
    def setup_method(self):
        """Setup for environment tests."""
        # Clear all environment variables
        env_vars = [
            "SELECTED_LLM_PROVIDER",
            "ANTHROPIC_API_KEY", 
            "OPENAI_API_KEY",
            "GEMINI_API_KEY",
            "OPENROUTER_API_KEY"
        ]
        for var in env_vars:
            os.environ.pop(var, None)
    
    def teardown_method(self):
        """Clean up environment variables."""
        self.setup_method()  # Same cleanup
    
    def test_environment_provider_selection(self):
        """Test provider selection via environment variable."""
        os.environ["SELECTED_LLM_PROVIDER"] = "anthropic"
        
        service = SimpleLLMService()
        assert service.get_active_provider_name() == "anthropic"
    
    def test_environment_api_key_detection(self):
        """Test API key detection from environment."""
        os.environ["ANTHROPIC_API_KEY"] = "sk-test-123"
        os.environ["OPENAI_API_KEY"] = "sk-openai-456"
        
        service = SimpleLLMService()
        info = service.get_provider_info()
        
        configured = info["configured_providers"]
        assert "ollama" in configured  # Always available (local)
        assert "anthropic" in configured  # Has API key
        assert "openai" in configured  # Has API key
        assert "gemini" not in configured  # No API key
        assert "openrouter" not in configured  # No API key
    
    def test_mixed_configuration_priority(self):
        """Test priority when both env and settings are configured."""
        # Set environment
        os.environ["SELECTED_LLM_PROVIDER"] = "openai"
        
        # Create service with different settings
        settings = Settings(
            default_llm_provider="ollama",
            selected_llm_provider="anthropic"
        )
        
        service = SimpleLLMService(settings)
        
        # Environment should win
        assert service.get_active_provider_name() == "openai"
        
        # Clear environment - should fall back to settings selection
        del os.environ["SELECTED_LLM_PROVIDER"]
        assert service.get_active_provider_name() == "anthropic"