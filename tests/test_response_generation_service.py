"""
Test suite for Response Generation Service.

Tests the complete response generation pipeline including:
- LLM integration and response generation  
- Citation formatting and source attribution
- Educational accuracy validation
- Integration with RAG pipeline components
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any, Optional
import asyncio
from uuid import uuid4

# Import the service classes we'll be testing
from arete.services.response_generation_service import (
    ResponseGenerationService,
    ResponseGenerationConfig,
    ResponseResult,
    ResponseValidation,
    ValidationError,
    CitationError,
    ResponseGenerationError
)
from arete.services.context_composition_service import ContextResult, PassageGroup, CitationContext, CompositionStrategy
from arete.services.llm_provider import LLMMessage, LLMResponse, MessageRole
from arete.models.chunk import Chunk
from arete.models.citation import Citation, CitationType


class TestResponseGenerationService:
    """Test cases for ResponseGenerationService core functionality."""
    
    @pytest.fixture
    def mock_llm_service(self):
        """Mock LLM service for testing."""
        service = Mock()
        service.generate_response = AsyncMock()
        return service
    
    @pytest.fixture
    def mock_validation_service(self):
        """Mock validation service for testing."""
        service = Mock()
        service.validate_response = Mock()
        return service
    
    @pytest.fixture
    def sample_context_result(self):
        """Sample context result for testing."""
        chunk = Chunk(
            text="In the Republic, Plato describes the Cave allegory...",
            document_id=uuid4(),
            position=0,
            start_char=0,
            end_char=100,
            chunk_type="paragraph"
        )
        
        citation = Citation(
            text="The prisoners are chained...",
            document_id=uuid4(),
            source_title="Republic",
            source_author="Plato",
            source_reference="Republic 514a",
            citation_type=CitationType.DIRECT_QUOTE,
            confidence=0.9
        )
        
        passage_group = PassageGroup(
            chunks=[chunk],
            coherence_score=0.8,
            topic="Cave Allegory"
        )
        
        citation_context = CitationContext(
            citation=citation,
            formatted_citation="Republic 514a",
            context_relevance=0.9
        )
        
        return ContextResult(
            composed_text="In the Republic, Plato describes the Cave allegory...",
            total_tokens=150,
            query="Explain Plato's Cave allegory",
            passage_groups=[passage_group],
            citations=[citation_context],
            strategy_used=CompositionStrategy.INTELLIGENT_STITCHING,
            truncated=False,
            overlaps_detected=0
        )
    
    @pytest.fixture
    def sample_llm_response(self):
        """Sample LLM response for testing."""
        return LLMResponse(
            content="Plato's Cave allegory, found in Republic Book VII, illustrates...",
            model="test-model",
            provider="test-provider",
            usage_tokens=200,
            metadata={"temperature": 0.7}
        )
    
    def test_service_initialization(self, mock_llm_service, mock_validation_service):
        """Test service initialization with dependencies."""
        config = ResponseGenerationConfig(
            max_response_tokens=1000,
            temperature=0.7,
            enable_validation=True
        )
        
        service = ResponseGenerationService(
            llm_service=mock_llm_service,
            validation_service=mock_validation_service,
            config=config
        )
        
        assert service.llm_service == mock_llm_service
        assert service.validation_service == mock_validation_service
        assert service.config == config
    
    @pytest.mark.asyncio
    async def test_generate_response_success(
        self, 
        mock_llm_service, 
        mock_validation_service,
        sample_context_result,
        sample_llm_response
    ):
        """Test successful response generation."""
        # Setup mocks
        mock_llm_service.generate_response.return_value = sample_llm_response
        mock_validation_service.validate_response.return_value = ResponseValidation(
            is_valid=True,
            accuracy_score=0.9,
            citation_coverage=0.8,
            issues=[]
        )
        
        service = ResponseGenerationService(
            llm_service=mock_llm_service,
            validation_service=mock_validation_service
        )
        
        # Generate response
        result = await service.generate_response(
            context_result=sample_context_result,
            query="Explain Plato's Cave allegory"
        )
        
        # Verify result
        assert isinstance(result, ResponseResult)
        assert result.response_text == sample_llm_response.content
        assert result.query == "Explain Plato's Cave allegory"
        assert result.validation.is_valid
        assert len(result.citations) > 0
        
        # Verify LLM service was called correctly
        mock_llm_service.generate_response.assert_called_once()
        call_args = mock_llm_service.generate_response.call_args
        messages = call_args.kwargs['messages']
        assert len(messages) == 2  # system + user message
        assert messages[0].role == MessageRole.SYSTEM
        assert messages[1].role == MessageRole.USER
    
    @pytest.mark.asyncio
    async def test_generate_response_with_validation_failure(
        self,
        mock_llm_service,
        mock_validation_service, 
        sample_context_result,
        sample_llm_response
    ):
        """Test response generation with validation failure."""
        # Setup mocks
        mock_llm_service.generate_response.return_value = sample_llm_response
        mock_validation_service.validate_response.return_value = ResponseValidation(
            is_valid=False,
            accuracy_score=0.4,
            citation_coverage=0.2,
            issues=["Missing citations", "Inaccurate claims"]
        )
        
        config = ResponseGenerationConfig(
            enable_validation=True,
            fail_on_validation_error=True
        )
        
        service = ResponseGenerationService(
            llm_service=mock_llm_service,
            validation_service=mock_validation_service,
            config=config
        )
        
        # Expect validation error
        with pytest.raises(ValidationError) as exc_info:
            await service.generate_response(
                context_result=sample_context_result,
                query="Explain Plato's Cave allegory"
            )
        
        assert "Response validation failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_generate_response_batch(
        self,
        mock_llm_service,
        mock_validation_service,
        sample_context_result,
        sample_llm_response
    ):
        """Test batch response generation."""
        # Setup mocks for multiple responses
        mock_llm_service.generate_response.side_effect = [
            sample_llm_response,
            LLMResponse(
                content="Second response about ethics...",
                model="test-model", 
                provider="test-provider",
                usage_tokens=180
            )
        ]
        
        mock_validation_service.validate_response.return_value = ResponseValidation(
            is_valid=True,
            accuracy_score=0.9,
            citation_coverage=0.8,
            issues=[]
        )
        
        service = ResponseGenerationService(
            llm_service=mock_llm_service,
            validation_service=mock_validation_service
        )
        
        # Generate batch responses
        context_results = [sample_context_result, sample_context_result]
        queries = ["Query 1", "Query 2"]
        
        results = await service.generate_response_batch(
            context_results=context_results,
            queries=queries
        )
        
        # Verify results
        assert len(results) == 2
        assert all(isinstance(r, ResponseResult) for r in results)
        assert results[0].response_text == sample_llm_response.content
        assert results[1].response_text == "Second response about ethics..."
        
        # Verify service calls
        assert mock_llm_service.generate_response.call_count == 2
        assert mock_validation_service.validate_response.call_count == 2


class TestResponseGenerationConfig:
    """Test cases for ResponseGenerationConfig."""
    
    def test_config_defaults(self):
        """Test configuration default values."""
        config = ResponseGenerationConfig()
        
        assert config.max_response_tokens == 2000
        assert config.temperature == 0.7
        assert config.enable_validation is True
        assert config.fail_on_validation_error is False
        assert config.citation_format == "classical"
        assert config.include_source_attribution is True
        assert config.max_citations == 10
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Valid config
        config = ResponseGenerationConfig(
            max_response_tokens=1500,
            temperature=0.8,
            max_citations=5
        )
        assert config.max_response_tokens == 1500
        
        # Invalid temperature
        with pytest.raises(ValueError):
            ResponseGenerationConfig(temperature=1.5)
        
        # Invalid max_citations
        with pytest.raises(ValueError):
            ResponseGenerationConfig(max_citations=-1)


class TestResponseResult:
    """Test cases for ResponseResult data class."""
    
    def test_response_result_creation(self):
        """Test ResponseResult creation and properties."""
        citation = Citation(
            text="Sample quote",
            document_id=uuid4(),
            source_title="Republic",
            source_author="Plato",
            source_reference="Republic 514a",
            citation_type="direct_quote"
        )
        
        validation = ResponseValidation(
            is_valid=True,
            accuracy_score=0.9,
            citation_coverage=0.8,
            issues=[]
        )
        
        result = ResponseResult(
            response_text="Generated response text",
            query="Test query",
            citations=[citation],
            validation=validation,
            llm_response_metadata={"model": "test-model"},
            generation_time=0.5,
            metadata={"test": "value"}
        )
        
        assert result.response_text == "Generated response text"
        assert result.query == "Test query"
        assert len(result.citations) == 1
        assert result.validation.is_valid
        assert result.generation_time == 0.5
        assert result.metadata["test"] == "value"


class TestResponseValidation:
    """Test cases for ResponseValidation and validation logic."""
    
    def test_validation_creation(self):
        """Test ResponseValidation creation."""
        validation = ResponseValidation(
            is_valid=True,
            accuracy_score=0.85,
            citation_coverage=0.9,
            issues=["Minor formatting issue"]
        )
        
        assert validation.is_valid is True
        assert validation.accuracy_score == 0.85
        assert validation.citation_coverage == 0.9
        assert len(validation.issues) == 1
    
    def test_validation_scoring(self):
        """Test validation scoring thresholds."""
        # High quality validation
        high_quality = ResponseValidation(
            is_valid=True,
            accuracy_score=0.9,
            citation_coverage=0.85,
            issues=[]
        )
        assert high_quality.is_high_quality()
        
        # Low quality validation  
        low_quality = ResponseValidation(
            is_valid=True,
            accuracy_score=0.6,
            citation_coverage=0.4,
            issues=["Multiple issues"]
        )
        assert not low_quality.is_high_quality()


class TestCitationIntegration:
    """Test cases for citation formatting and integration."""
    
    @pytest.fixture
    def citations_with_references(self):
        """Sample citations with different reference formats."""
        return [
            Citation(
                text="The prisoners are chained from childhood",
                document_id=uuid4(),
                source_title="Republic",
                source_author="Plato",
                source_reference="Republic 514a",
                citation_type=CitationType.DIRECT_QUOTE,
                confidence=0.95
            ),
            Citation(
                text="Discussion of justice in the soul",
                document_id=uuid4(),
                source_title="Republic", 
                source_author="Plato",
                source_reference="Republic 441c-444a", 
                citation_type=CitationType.PARAPHRASE,
                confidence=0.8
            ),
            Citation(
                text="The philosopher king concept",
                document_id=uuid4(),
                source_title="Republic",
                source_author="Plato", 
                source_reference="Republic 473d",
                citation_type=CitationType.REFERENCE,
                confidence=0.9
            )
        ]
    
    def test_citation_formatting_classical(self, citations_with_references):
        """Test classical citation formatting."""
        service = ResponseGenerationService()
        
        formatted = service._format_citations(
            citations_with_references,
            format_style="classical"
        )
        
        assert "Republic 514a" in formatted
        assert "Republic 441c-444a" in formatted
        assert "Republic 473d" in formatted
    
    def test_citation_formatting_modern(self, citations_with_references):
        """Test modern citation formatting."""
        service = ResponseGenerationService()
        
        formatted = service._format_citations(
            citations_with_references,
            format_style="modern"
        )
        
        # Modern format should include parenthetical citations
        assert "(Republic 514a)" in formatted or "[1]" in formatted
    
    def test_citation_deduplication(self, citations_with_references):
        """Test citation deduplication logic."""
        service = ResponseGenerationService()
        
        # Add duplicate citation
        duplicate_citation = Citation(
            text="The prisoners are chained from childhood", 
            document_id=uuid4(),
            source_title="Republic",
            source_author="Plato",
            source_reference="Republic 514a",
            citation_type=CitationType.DIRECT_QUOTE,
            confidence=0.95
        )
        citations_with_duplicate = citations_with_references + [duplicate_citation]
        
        deduplicated = service._deduplicate_citations(citations_with_duplicate)
        
        # Should remove duplicate while preserving order
        assert len(deduplicated) == 3
        assert all(c.source_reference != "Republic 514a" or 
                  deduplicated.index(c) == 0 
                  for c in deduplicated 
                  if c.source_reference == "Republic 514a")


class TestErrorHandling:
    """Test cases for error handling and edge cases."""
    
    @pytest.fixture
    def mock_validation_service(self):
        """Mock validation service for testing."""
        service = Mock()
        service.validate_response = Mock()
        return service
    
    @pytest.fixture
    def sample_context_result(self):
        """Sample context result for testing."""
        chunk = Chunk(
            text="In the Republic, Plato describes the Cave allegory...",
            document_id=uuid4(),
            position=0,
            start_char=0,
            end_char=100,
            chunk_type="paragraph"
        )
        
        citation = Citation(
            text="The prisoners are chained...",
            document_id=uuid4(),
            source_title="Republic",
            source_author="Plato",
            source_reference="Republic 514a",
            citation_type=CitationType.DIRECT_QUOTE,
            confidence=0.9
        )
        
        passage_group = PassageGroup(
            chunks=[chunk],
            coherence_score=0.8,
            topic="Cave Allegory"
        )
        
        citation_context = CitationContext(
            citation=citation,
            formatted_citation="Republic 514a",
            context_relevance=0.9
        )
        
        return ContextResult(
            composed_text="In the Republic, Plato describes the Cave allegory...",
            total_tokens=150,
            query="Explain Plato's Cave allegory",
            passage_groups=[passage_group],
            citations=[citation_context],
            strategy_used=CompositionStrategy.INTELLIGENT_STITCHING,
            truncated=False,
            overlaps_detected=0
        )
    
    @pytest.mark.asyncio
    async def test_llm_service_error_handling(self, mock_validation_service, sample_context_result):
        """Test handling of LLM service errors."""
        mock_llm_service = Mock()
        mock_llm_service.generate_response = AsyncMock(
            side_effect=Exception("LLM service unavailable")
        )
        
        service = ResponseGenerationService(
            llm_service=mock_llm_service,
            validation_service=mock_validation_service
        )
        
        with pytest.raises(ResponseGenerationError) as exc_info:
            await service.generate_response(
                context_result=sample_context_result,
                query="Test query"
            )
        
        assert "Response generation failed" in str(exc_info.value)
    
    @pytest.fixture
    def mock_llm_service(self):
        """Mock LLM service for testing."""
        service = Mock()
        service.generate_response = AsyncMock()
        return service
    
    def test_empty_context_handling(self, mock_llm_service, mock_validation_service):
        """Test handling of empty context results."""
        service = ResponseGenerationService(
            llm_service=mock_llm_service,
            validation_service=mock_validation_service
        )
        
        empty_context = ContextResult(
            composed_text="",
            total_tokens=0,
            query="Test query",
            passage_groups=[],
            citations=[],
            strategy_used=CompositionStrategy.SIMPLE_CONCAT,
            truncated=False,
            overlaps_detected=0
        )
        
        # Should handle empty context gracefully
        messages = service._build_messages(empty_context, "Test query")
        assert len(messages) >= 1  # At minimum should have user message
    
    def test_citation_error_handling(self):
        """Test citation error handling."""
        error = CitationError(
            "Citation formatting failed",
            citation_id="test-citation-123"
        )
        
        assert "Citation formatting failed" in str(error)
        assert error.citation_id == "test-citation-123"


class TestPerformanceOptimization:
    """Test cases for performance optimization features."""
    
    @pytest.fixture
    def mock_llm_service(self):
        """Mock LLM service for testing."""
        service = Mock()
        service.generate_response = AsyncMock()
        return service
    
    @pytest.fixture
    def mock_validation_service(self):
        """Mock validation service for testing."""
        service = Mock()
        service.validate_response = Mock()
        return service
    
    @pytest.fixture
    def sample_context_result(self):
        """Sample context result for testing."""
        chunk = Chunk(
            text="In the Republic, Plato describes the Cave allegory...",
            document_id=uuid4(),
            position=0,
            start_char=0,
            end_char=100,
            chunk_type="paragraph"
        )
        
        citation = Citation(
            text="The prisoners are chained...",
            document_id=uuid4(),
            source_title="Republic",
            source_author="Plato",
            source_reference="Republic 514a",
            citation_type=CitationType.DIRECT_QUOTE,
            confidence=0.9
        )
        
        passage_group = PassageGroup(
            chunks=[chunk],
            coherence_score=0.8,
            topic="Cave Allegory"
        )
        
        citation_context = CitationContext(
            citation=citation,
            formatted_citation="Republic 514a",
            context_relevance=0.9
        )
        
        return ContextResult(
            composed_text="In the Republic, Plato describes the Cave allegory...",
            total_tokens=150,
            query="Explain Plato's Cave allegory",
            passage_groups=[passage_group],
            citations=[citation_context],
            strategy_used=CompositionStrategy.INTELLIGENT_STITCHING,
            truncated=False,
            overlaps_detected=0
        )
    
    @pytest.fixture
    def sample_llm_response(self):
        """Sample LLM response for testing."""
        return LLMResponse(
            content="Plato's Cave allegory, found in Republic Book VII, illustrates...",
            model="test-model",
            provider="test-provider",
            usage_tokens=200,
            metadata={"temperature": 0.7}
        )
    
    @pytest.mark.asyncio
    async def test_response_caching(
        self,
        mock_llm_service,
        mock_validation_service,
        sample_context_result,
        sample_llm_response
    ):
        """Test response caching functionality."""
        mock_llm_service.generate_response.return_value = sample_llm_response
        mock_validation_service.validate_response.return_value = ResponseValidation(
            is_valid=True,
            accuracy_score=0.9,
            citation_coverage=0.8,
            issues=[]
        )
        
        config = ResponseGenerationConfig(enable_caching=True)
        service = ResponseGenerationService(
            llm_service=mock_llm_service,
            validation_service=mock_validation_service,
            config=config
        )
        
        # First request
        result1 = await service.generate_response(
            context_result=sample_context_result,
            query="Test query"
        )
        
        # Second identical request should use cache
        result2 = await service.generate_response(
            context_result=sample_context_result,
            query="Test query"
        )
        
        # Verify caching worked
        assert result1.response_text == result2.response_text
        # LLM service should only be called once due to caching
        mock_llm_service.generate_response.assert_called_once()
    
    def test_token_limit_management(self, mock_llm_service, mock_validation_service):
        """Test token limit management in prompt construction."""
        config = ResponseGenerationConfig(max_context_tokens=500)
        service = ResponseGenerationService(
            llm_service=mock_llm_service,
            validation_service=mock_validation_service,
            config=config
        )
        
        # Create large context that exceeds token limit
        large_context = ContextResult(
            composed_text="Very long text " * 200,  # Simulate large context
            total_tokens=1000,  # Exceeds limit
            query="Test query",
            passage_groups=[],
            citations=[],
            strategy_used=CompositionStrategy.SIMPLE_CONCAT,
            truncated=False,
            overlaps_detected=0
        )
        
        messages = service._build_messages(large_context, "Test query")
        
        # Should truncate context to fit within token limits
        user_message_content = next(
            (m.content for m in messages if m.role == MessageRole.USER), 
            ""
        )
        
        # Verify content was truncated (rough approximation)
        assert len(user_message_content) < len("Very long text " * 200)


# Integration test class
class TestResponseGenerationIntegration:
    """Integration tests for the complete response generation pipeline."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_response_generation(self):
        """Test complete end-to-end response generation pipeline."""
        # This would test integration with actual services
        # Skipped in unit tests, but important for integration testing
        pytest.skip("Integration test - requires actual service dependencies")
    
    @pytest.mark.asyncio  
    async def test_rag_pipeline_integration(self):
        """Test integration with RAG pipeline components."""
        # Test integration with retrieval, re-ranking, diversification
        pytest.skip("Integration test - requires full RAG pipeline")


# Performance and load testing
class TestResponseGenerationPerformance:
    """Performance tests for response generation."""
    
    @pytest.mark.asyncio
    async def test_concurrent_response_generation(self):
        """Test concurrent response generation performance."""
        pytest.skip("Performance test - run separately")
    
    def test_memory_usage_large_contexts(self):
        """Test memory usage with large context inputs."""
        pytest.skip("Performance test - run separately")