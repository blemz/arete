"""
Comprehensive tests for prompt service system.

Tests cover prompt template factory, tutoring service, and integration
with LLM providers for philosophical tutoring scenarios.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

from arete.services.prompt_service import (
    PromptTemplateFactory,
    PromptService,
    TutoringRequest,
    TutoringResponse,
    get_prompt_service,
    quick_tutoring_response
)
from arete.services.prompt_template import (
    BasePromptTemplate,
    PhilosophicalTutoringTemplate,
    ExplanationTemplate,
    PromptType,
    PromptContext,
    PromptResult,
    PhilosophicalContext,
    Citation
)
from arete.services.llm_provider import LLMMessage, MessageRole, LLMResponse
from arete.config import Settings


class MockTemplate(BasePromptTemplate):
    """Mock template for testing."""
    
    def __init__(self, provider: str):
        """Initialize mock template with fake prompt type."""
        fake_type = Mock()
        fake_type.value = "custom"
        super().__init__(provider, fake_type)
    
    def generate(self, context: PromptContext) -> PromptResult:
        return PromptResult(
            system_prompt=f"Mock system for {self.provider}",
            user_prompt=f"Mock user: {context.query}",
            prompt_type=self.prompt_type,
            provider=self.provider,
            citations_included=context.citations,
            token_estimate=100,
            metadata={"mock": True}
        )


class TestPromptTemplateFactory:
    """Test prompt template factory."""
    
    @pytest.fixture
    def factory(self):
        """Create factory for testing."""
        return PromptTemplateFactory()
    
    def test_factory_initialization(self, factory):
        """Test factory initialization."""
        assert factory._template_cache == {}
        assert PromptType.TUTORING in factory._template_registry
        assert PromptType.EXPLANATION in factory._template_registry
    
    def test_get_tutoring_template(self, factory):
        """Test getting tutoring template."""
        template = factory.get_template("anthropic", PromptType.TUTORING)
        
        assert isinstance(template, PhilosophicalTutoringTemplate)
        assert template.provider == "anthropic"
        assert template.prompt_type == PromptType.TUTORING
    
    def test_get_explanation_template(self, factory):
        """Test getting explanation template."""
        template = factory.get_template("ollama", PromptType.EXPLANATION)
        
        assert isinstance(template, ExplanationTemplate)
        assert template.provider == "ollama"
        assert template.prompt_type == PromptType.EXPLANATION
    
    def test_template_caching(self, factory):
        """Test template caching behavior."""
        # First call should create template
        template1 = factory.get_template("anthropic", PromptType.TUTORING)
        
        # Second call should return cached template
        template2 = factory.get_template("anthropic", PromptType.TUTORING)
        
        assert template1 is template2
        assert len(factory._template_cache) == 1
    
    def test_different_providers_different_templates(self, factory):
        """Test that different providers get different template instances."""
        anthropic_template = factory.get_template("anthropic", PromptType.TUTORING)
        ollama_template = factory.get_template("ollama", PromptType.TUTORING)
        
        assert anthropic_template is not ollama_template
        assert anthropic_template.provider == "anthropic"
        assert ollama_template.provider == "ollama"
        assert len(factory._template_cache) == 2
    
    def test_unsupported_prompt_type(self, factory):
        """Test error handling for unsupported prompt types."""
        with pytest.raises(ValueError, match="Unsupported prompt type"):
            # Create a fake enum value
            fake_type = Mock()
            fake_type.value = "fake_type"
            factory.get_template("anthropic", fake_type)
    
    def test_register_custom_template(self, factory):
        """Test registering custom template types."""
        # Create a custom prompt type
        custom_type = Mock()
        custom_type.value = "custom"
        
        # Register custom template
        factory.register_template(custom_type, MockTemplate)
        
        # Should be able to get custom template
        template = factory.get_template("anthropic", custom_type)
        assert isinstance(template, MockTemplate)
    
    def test_list_supported_types(self, factory):
        """Test listing supported prompt types."""
        types = factory.list_supported_types()
        
        assert PromptType.TUTORING in types
        assert PromptType.EXPLANATION in types
        assert len(types) >= 2
    
    def test_clear_cache(self, factory):
        """Test cache clearing."""
        # Create some templates to populate cache
        factory.get_template("anthropic", PromptType.TUTORING)
        factory.get_template("ollama", PromptType.EXPLANATION)
        
        assert len(factory._template_cache) == 2
        
        # Clear cache
        factory.clear_cache()
        
        assert len(factory._template_cache) == 0


class TestTutoringRequest:
    """Test TutoringRequest data class."""
    
    def test_request_creation_minimal(self):
        """Test minimal request creation."""
        request = TutoringRequest(query="What is virtue?")
        
        assert request.query == "What is virtue?"
        assert request.student_level == "undergraduate"
        assert request.philosophical_context is None
        assert request.learning_objective is None
        assert request.retrieved_passages == []
        assert request.citations == []
        assert request.previous_context is None
        assert request.provider is None
        assert request.prompt_type == PromptType.TUTORING
        assert request.metadata == {}
    
    def test_request_creation_full(self):
        """Test full request creation."""
        citations = [Citation(text="Test citation", source="test")]
        passages = ["Test passage"]
        
        request = TutoringRequest(
            query="Explain Forms",
            student_level="graduate",
            philosophical_context=PhilosophicalContext.ANCIENT,
            learning_objective="Understand Plato's metaphysics",
            retrieved_passages=passages,
            citations=citations,
            previous_context="Previous discussion",
            provider="anthropic",
            prompt_type=PromptType.EXPLANATION,
            metadata={"topic": "metaphysics"}
        )
        
        assert request.query == "Explain Forms"
        assert request.student_level == "graduate"
        assert request.philosophical_context == PhilosophicalContext.ANCIENT
        assert request.learning_objective == "Understand Plato's metaphysics"
        assert request.retrieved_passages == passages
        assert request.citations == citations
        assert request.previous_context == "Previous discussion"
        assert request.provider == "anthropic"
        assert request.prompt_type == PromptType.EXPLANATION
        assert request.metadata["topic"] == "metaphysics"


class TestTutoringResponse:
    """Test TutoringResponse data class."""
    
    def test_response_creation(self):
        """Test response creation."""
        citations = [Citation(text="Test citation", source="test")]
        prompt_result = PromptResult(
            system_prompt="System",
            user_prompt="User",
            prompt_type=PromptType.TUTORING,
            provider="anthropic",
            citations_included=citations,
            token_estimate=100
        )
        llm_response = LLMResponse(
            content="Response content",
            provider="anthropic"
        )
        
        response = TutoringResponse(
            content="Response content",
            prompt_used=prompt_result,
            llm_response=llm_response,
            citations_provided=citations,
            metadata={"test": "data"}
        )
        
        assert response.content == "Response content"
        assert response.prompt_used == prompt_result
        assert response.llm_response == llm_response
        assert len(response.citations_provided) == 1
        assert response.metadata["test"] == "data"


class TestPromptService:
    """Test prompt service functionality."""
    
    @pytest.fixture
    def mock_llm_service(self):
        """Create mock LLM service."""
        mock_service = Mock()
        mock_service.get_active_provider_name.return_value = "anthropic"
        mock_service.generate_response = AsyncMock(return_value=LLMResponse(
            content="Generated response content",
            provider="anthropic",
            usage_tokens=150,
            metadata={"model": "claude-3"}
        ))
        return mock_service
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        return Mock(spec=Settings)
    
    @pytest.fixture
    def prompt_service(self, mock_settings, mock_llm_service):
        """Create prompt service with mocked dependencies."""
        return PromptService(mock_settings, mock_llm_service)
    
    def test_service_initialization(self, mock_settings, mock_llm_service):
        """Test service initialization."""
        service = PromptService(mock_settings, mock_llm_service)
        
        assert service.settings == mock_settings
        assert service.llm_service == mock_llm_service
        assert isinstance(service.template_factory, PromptTemplateFactory)
    
    def test_initialization_with_defaults(self):
        """Test service initialization with default dependencies."""
        with patch('arete.services.prompt_service.get_settings') as mock_get_settings, \
             patch('arete.services.prompt_service.SimpleLLMService') as mock_llm_class:
            
            mock_settings = Mock()
            mock_get_settings.return_value = mock_settings
            mock_llm_service = Mock()
            mock_llm_class.return_value = mock_llm_service
            
            service = PromptService()
            
            mock_get_settings.assert_called_once()
            mock_llm_class.assert_called_once_with(mock_settings)
    
    @pytest.mark.asyncio
    async def test_generate_prompt(self, prompt_service):
        """Test prompt generation."""
        context = PromptContext(
            query="What is virtue?",
            student_level="undergraduate"
        )
        
        result = await prompt_service.generate_prompt(
            context, 
            PromptType.TUTORING,
            "anthropic"
        )
        
        assert isinstance(result, PromptResult)
        assert result.provider == "anthropic"
        assert result.prompt_type == PromptType.TUTORING
        assert result.system_prompt != ""
        assert result.user_prompt != ""
        assert "What is virtue?" in result.user_prompt
    
    @pytest.mark.asyncio
    async def test_generate_prompt_uses_active_provider(self, prompt_service, mock_llm_service):
        """Test that prompt generation uses active provider when none specified."""
        context = PromptContext(query="Test query")
        
        await prompt_service.generate_prompt(context)
        
        mock_llm_service.get_active_provider_name.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_tutoring_response(self, prompt_service, mock_llm_service):
        """Test tutoring response generation."""
        citations = [Citation(text="Virtue is knowledge", source="socrates")]
        request = TutoringRequest(
            query="What is virtue according to Socrates?",
            citations=citations,
            student_level="graduate"
        )
        
        response = await prompt_service.generate_tutoring_response(request)
        
        assert isinstance(response, TutoringResponse)
        assert response.content == "Generated response content"
        assert len(response.citations_provided) == 1
        assert response.metadata["request_metadata"] == request.metadata
        
        # Check that LLM service was called correctly
        mock_llm_service.generate_response.assert_called_once()
        call_args = mock_llm_service.generate_response.call_args
        messages = call_args[1]['messages']
        assert len(messages) == 2
        assert messages[0].role == MessageRole.SYSTEM
        assert messages[1].role == MessageRole.USER
        assert "What is virtue according to Socrates?" in messages[1].content
    
    @pytest.mark.asyncio
    async def test_generate_tutoring_response_empty_query(self, prompt_service):
        """Test error handling for empty query."""
        request = TutoringRequest(query="")
        
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await prompt_service.generate_tutoring_response(request)
    
    @pytest.mark.asyncio
    async def test_generate_tutoring_response_with_provider(self, prompt_service, mock_llm_service):
        """Test tutoring response with specific provider."""
        request = TutoringRequest(
            query="Test query",
            provider="ollama"
        )
        
        await prompt_service.generate_tutoring_response(request)
        
        # Should use specified provider, not call get_active_provider_name
        mock_llm_service.get_active_provider_name.assert_not_called()
        
        # Check provider was passed to LLM service
        call_args = mock_llm_service.generate_response.call_args
        assert call_args[1]['provider'] == "ollama"
    
    def test_create_citation_from_passage(self, prompt_service):
        """Test citation creation utility."""
        citation = prompt_service.create_citation_from_passage(
            text="Knowledge is virtue",
            source="socrates_meno",
            author="Socrates",
            work="Meno",
            reference="Meno 87c",
            confidence=0.9
        )
        
        assert isinstance(citation, Citation)
        assert citation.text == "Knowledge is virtue"
        assert citation.source == "socrates_meno"
        assert citation.author == "Socrates"
        assert citation.work == "Meno"
        assert citation.reference == "Meno 87c"
        assert citation.confidence == 0.9
    
    def test_get_supported_prompt_types(self, prompt_service):
        """Test getting supported prompt types."""
        types = prompt_service.get_supported_prompt_types()
        
        assert PromptType.TUTORING in types
        assert PromptType.EXPLANATION in types
    
    def test_get_provider_info(self, prompt_service, mock_llm_service):
        """Test getting provider information."""
        mock_llm_service.get_provider_info.return_value = {
            "active_provider": "anthropic",
            "available_providers": ["anthropic", "ollama"]
        }
        
        info = prompt_service.get_provider_info()
        
        assert "llm_providers" in info
        assert "supported_prompt_types" in info
        assert "active_provider" in info
        assert "template_cache_size" in info
        assert info["active_provider"] == "anthropic"
    
    def test_clear_template_cache(self, prompt_service):
        """Test clearing template cache."""
        # Populate cache first
        prompt_service.template_factory.get_template("anthropic", PromptType.TUTORING)
        assert len(prompt_service.template_factory._template_cache) > 0
        
        # Clear cache
        prompt_service.clear_template_cache()
        assert len(prompt_service.template_factory._template_cache) == 0


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    @patch('arete.services.prompt_service.PromptService')
    def test_get_prompt_service(self, mock_service_class):
        """Test get_prompt_service convenience function."""
        mock_settings = Mock()
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        result = get_prompt_service(mock_settings)
        
        mock_service_class.assert_called_once_with(mock_settings)
        assert result == mock_service
    
    @pytest.mark.asyncio
    @patch('arete.services.prompt_service.get_prompt_service')
    async def test_quick_tutoring_response(self, mock_get_service):
        """Test quick_tutoring_response convenience function."""
        mock_service = Mock()
        mock_response = TutoringResponse(
            content="Quick response",
            prompt_used=Mock(),
            llm_response=Mock(),
            citations_provided=[]
        )
        mock_service.generate_tutoring_response = AsyncMock(return_value=mock_response)
        mock_get_service.return_value = mock_service
        
        citations = [Citation(text="Test", source="test")]
        passages = ["Test passage"]
        
        result = await quick_tutoring_response(
            query="Test query",
            retrieved_passages=passages,
            citations=citations,
            student_level="graduate",
            provider="anthropic"
        )
        
        assert result == "Quick response"
        
        # Verify service was called correctly
        mock_service.generate_tutoring_response.assert_called_once()
        call_args = mock_service.generate_tutoring_response.call_args[0][0]
        assert isinstance(call_args, TutoringRequest)
        assert call_args.query == "Test query"
        assert call_args.retrieved_passages == passages
        assert call_args.citations == citations
        assert call_args.student_level == "graduate"
        assert call_args.provider == "anthropic"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])