"""
Integration Tests for Response Generation Service with Citation System.

This test suite validates the integration of the citation system with response generation:
- End-to-end citation extraction and validation in response generation
- Citation tracking throughout the response pipeline
- Integration between citation services and response generation
- Citation quality metrics and validation integration
- Response generation with citation-aware prompting
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from src.arete.services.response_generation_service import (
    ResponseGenerationService,
    ResponseGenerationConfig,
    ResponseResult,
    create_response_generation_service
)
from src.arete.services.citation_extraction_service import (
    CitationExtractionService,
    CitationExtractionConfig,
    ExtractionResult
)
from src.arete.services.citation_validation_service import (
    CitationValidationService,
    CitationValidationConfig,
    BatchValidationResult,
    ValidationResult
)
from src.arete.services.citation_tracking_service import (
    CitationTrackingService,
    CitationTrackingConfig,
    TrackingEventType,
    CitationSource
)
from src.arete.services.context_composition_service import ContextResult, CitationContext
from src.arete.services.simple_llm_service import SimpleLLMService
from src.arete.services.llm_provider import LLMResponse, MessageRole
from src.arete.models.citation import Citation, CitationType, CitationContext as CitationContextType


class TestResponseGenerationWithCitations:
    """Test suite for integrated response generation with citation system."""
    
    @pytest.fixture
    def response_config(self):
        """Create response generation configuration."""
        return ResponseGenerationConfig(
            max_response_tokens=1000,
            enable_validation=True,
            citation_format="classical",
            deduplicate_citations=True,
            max_citations=10
        )
    
    @pytest.fixture
    def mock_llm_service(self):
        """Create mock LLM service."""
        service = Mock(spec=SimpleLLMService)
        
        # Mock response with citations
        mock_response = LLMResponse(
            content="""According to Plato in Republic 514a, the allegory of the cave illustrates 
            the journey from ignorance to knowledge. As he states, "The unexamined life is not worth living" 
            (Apology 38a). This connects to Aristotle's discussion in Ethics 1094a about the highest good.""",
            model="test-model",
            provider="test-provider",
            usage_tokens=150,
            metadata={}
        )
        
        service.generate_response = AsyncMock(return_value=mock_response)
        return service
    
    @pytest.fixture
    def mock_extraction_service(self):
        """Create mock citation extraction service."""
        service = Mock(spec=CitationExtractionService)
        
        # Create mock citations
        citation1 = Citation(
            id=uuid4(),
            text="Republic 514a",
            citation_type=CitationType.REFERENCE,
            context=CitationContextType.EXPLANATION,
            document_id=uuid4(),
            source_title="Republic",
            source_author="Plato",
            source_reference="Republic 514a",
            confidence=0.9
        )
        
        citation2 = Citation(
            id=uuid4(),
            text="The unexamined life is not worth living",
            citation_type=CitationType.DIRECT_QUOTE,
            context=CitationContextType.ARGUMENT,
            document_id=uuid4(),
            source_title="Apology",
            source_author="Plato",
            source_reference="Apology 38a",
            confidence=0.95
        )
        
        mock_result = ExtractionResult(
            citations=[citation1, citation2],
            total_matches_found=3,
            validated_matches=2,
            accuracy_score=0.9,
            coverage_score=0.8,
            processing_time=0.1
        )
        
        service.extract_citations_from_response = Mock(return_value=mock_result)
        return service
    
    @pytest.fixture
    def mock_validation_service(self):
        """Create mock citation validation service."""
        service = Mock(spec=CitationValidationService)
        
        # Create mock validation results
        validation_result1 = ValidationResult(
            citation_id=uuid4(),
            is_valid=True,
            confidence_score=0.9,
            source_found=True,
            source_accuracy=0.95
        )
        
        validation_result2 = ValidationResult(
            citation_id=uuid4(),
            is_valid=True,
            confidence_score=0.85,
            source_found=True,
            source_accuracy=0.9
        )
        
        mock_batch_result = BatchValidationResult(
            citation_results=[validation_result1, validation_result2],
            total_citations=2,
            valid_citations=2,
            overall_validity=True,
            average_confidence=0.875,
            accuracy_score=0.9,
            scholarly_quality=0.85
        )
        
        service.validate_citations_batch = AsyncMock(return_value=mock_batch_result)
        return service
    
    @pytest.fixture
    def mock_tracking_service(self):
        """Create mock citation tracking service."""
        service = Mock(spec=CitationTrackingService)
        service.record_citation_event = Mock()
        return service
    
    @pytest.fixture
    def sample_context_result(self):
        """Create sample context result with citations."""
        source_citation = Citation(
            id=uuid4(),
            text="The unexamined life is not worth living",
            citation_type=CitationType.DIRECT_QUOTE,
            context=CitationContextType.ARGUMENT,
            document_id=uuid4(),
            source_title="Apology",
            source_author="Plato",
            source_reference="Apology 38a",
            confidence=1.0
        )
        
        citation_context = CitationContext(
            citation=source_citation,
            relevance_score=0.9,
            context_text="Context around the citation",
            chunk_id=uuid4()
        )
        
        return ContextResult(
            composed_text="Sample philosophical text discussing Socrates and the examined life.",
            citations=[citation_context],
            total_tokens=200,
            metadata={"test": True}
        )
    
    @pytest.fixture
    def integrated_service(
        self,
        response_config,
        mock_llm_service,
        mock_extraction_service,
        mock_validation_service,
        mock_tracking_service
    ):
        """Create integrated response generation service with all citation services."""
        return ResponseGenerationService(
            llm_service=mock_llm_service,
            citation_extraction_service=mock_extraction_service,
            citation_validation_service=mock_validation_service,
            citation_tracking_service=mock_tracking_service,
            config=response_config
        )
    
    @pytest.mark.asyncio
    async def test_end_to_end_response_generation_with_citations(
        self,
        integrated_service,
        sample_context_result
    ):
        """Test complete response generation with citation integration."""
        query = "What does Socrates say about the examined life?"
        
        result = await integrated_service.generate_response(
            context_result=sample_context_result,
            query=query
        )
        
        # Verify response generation
        assert isinstance(result, ResponseResult)
        assert result.response_text is not None
        assert len(result.response_text) > 0
        assert result.query == query
        
        # Verify citation extraction was called
        integrated_service.citation_extraction_service.extract_citations_from_response.assert_called_once()
        
        # Verify citation validation was called
        integrated_service.citation_validation_service.validate_citations_batch.assert_called_once()
        
        # Verify citation tracking was called
        assert integrated_service.citation_tracking_service.record_citation_event.call_count >= 1
        
        # Verify citations are included in result
        assert len(result.citations) > 0
        assert result.citations_formatted > 0
    
    @pytest.mark.asyncio
    async def test_citation_extraction_integration(
        self,
        integrated_service,
        sample_context_result
    ):
        """Test citation extraction integration in response generation."""
        query = "Discuss Plato's philosophy"
        
        result = await integrated_service.generate_response(
            sample_context_result, query
        )
        
        # Verify extraction service was called with correct parameters
        call_args = integrated_service.citation_extraction_service.extract_citations_from_response.call_args
        assert call_args[0][1] == sample_context_result  # context_result
        assert call_args[0][2] == query  # query
        
        # Verify extracted citations are in result
        assert len(result.citations) >= 2  # From mock extraction service
        
        # Check citation types
        citation_types = {c.citation_type for c in result.citations}
        assert CitationType.REFERENCE in citation_types or CitationType.DIRECT_QUOTE in citation_types
    
    @pytest.mark.asyncio
    async def test_citation_validation_integration(
        self,
        integrated_service,
        sample_context_result
    ):
        """Test citation validation integration in response generation."""
        query = "What are Plato's main ideas?"
        
        result = await integrated_service.generate_response(
            sample_context_result, query
        )
        
        # Verify validation service was called
        validation_call = integrated_service.citation_validation_service.validate_citations_batch.call_args
        extracted_citations = validation_call[0][0]  # First argument should be citations
        context_arg = validation_call[0][1]  # Second argument should be context
        
        assert len(extracted_citations) > 0
        assert context_arg == sample_context_result
        
        # Verify only valid citations are included (based on mock config)
        assert all(isinstance(c, Citation) for c in result.citations)
    
    @pytest.mark.asyncio
    async def test_citation_tracking_integration(
        self,
        integrated_service,
        sample_context_result
    ):
        """Test citation tracking integration in response generation."""
        query = "Explain Socratic method"
        
        result = await integrated_service.generate_response(
            sample_context_result, query
        )
        
        # Verify tracking events were recorded
        tracking_calls = integrated_service.citation_tracking_service.record_citation_event.call_args_list
        
        assert len(tracking_calls) >= 1
        
        # Verify tracking call parameters
        for call_args in tracking_calls:
            citation = call_args[0][0]  # citation
            event_type = call_args[0][1]  # event_type
            
            assert isinstance(citation, Citation)
            assert event_type == TrackingEventType.EXTRACTED
            assert call_args[1]["source_type"] == CitationSource.LLM_RESPONSE
            assert call_args[1]["processor"] == "response_generation_service"
    
    @pytest.mark.asyncio
    async def test_citation_deduplication(
        self,
        integrated_service,
        sample_context_result
    ):
        """Test citation deduplication in response generation."""
        # Enable deduplication
        integrated_service.config.deduplicate_citations = True
        
        query = "Discuss philosophical concepts"
        
        result = await integrated_service.generate_response(
            sample_context_result, query
        )
        
        # Verify deduplication was applied
        citation_references = [c.source_reference for c in result.citations if c.source_reference]
        unique_references = set(citation_references)
        
        # Should not have duplicate references
        assert len(citation_references) == len(unique_references)
    
    @pytest.mark.asyncio
    async def test_citation_limit_enforcement(
        self,
        integrated_service,
        sample_context_result
    ):
        """Test citation limit enforcement in response generation."""
        # Set low citation limit
        integrated_service.config.max_citations = 1
        
        query = "Survey of ancient philosophy"
        
        result = await integrated_service.generate_response(
            sample_context_result, query
        )
        
        # Should not exceed citation limit
        assert len(result.citations) <= 1
    
    @pytest.mark.asyncio
    async def test_source_attribution_formatting(
        self,
        integrated_service,
        sample_context_result
    ):
        """Test source attribution formatting in response generation."""
        integrated_service.config.include_source_attribution = True
        integrated_service.config.citation_format = "classical"
        
        query = "What are the key philosophical insights?"
        
        result = await integrated_service.generate_response(
            sample_context_result, query
        )
        
        # Verify source attribution is formatted
        assert result.source_attribution is not None
        assert len(result.source_attribution) > 0
        assert "Sources:" in result.source_attribution
    
    @pytest.mark.asyncio
    async def test_citation_quality_metrics(
        self,
        integrated_service,
        sample_context_result
    ):
        """Test citation quality metrics in response generation."""
        query = "Analyze philosophical arguments"
        
        result = await integrated_service.generate_response(
            sample_context_result, query
        )
        
        # Should have quality metrics from validation
        # (These would come from the actual validation service in real usage)
        assert result.citations_formatted > 0
        
        # Verify metadata includes citation information
        if result.metadata:
            assert isinstance(result.metadata, dict)
    
    @pytest.mark.asyncio
    async def test_validation_failure_handling(
        self,
        integrated_service,
        sample_context_result,
        mock_validation_service
    ):
        """Test handling of citation validation failures."""
        # Mock validation failure
        failed_result = BatchValidationResult(
            citation_results=[
                ValidationResult(
                    citation_id=uuid4(),
                    is_valid=False,
                    confidence_score=0.3,
                    issues=["Low confidence", "Poor attribution"]
                )
            ],
            total_citations=1,
            valid_citations=0,
            overall_validity=False,
            average_confidence=0.3
        )
        mock_validation_service.validate_citations_batch = AsyncMock(return_value=failed_result)
        
        # Configure to not fail on validation errors
        integrated_service.config.fail_on_validation_error = False
        
        query = "Discuss problematic citations"
        
        result = await integrated_service.generate_response(
            sample_context_result, query
        )
        
        # Should still generate response despite validation failures
        assert isinstance(result, ResponseResult)
        assert result.response_text is not None
    
    @pytest.mark.asyncio
    async def test_empty_extraction_handling(
        self,
        integrated_service,
        sample_context_result,
        mock_extraction_service
    ):
        """Test handling when no citations are extracted."""
        # Mock empty extraction result
        empty_result = ExtractionResult(
            citations=[],
            total_matches_found=0,
            validated_matches=0,
            accuracy_score=0.0,
            coverage_score=0.0
        )
        mock_extraction_service.extract_citations_from_response = Mock(return_value=empty_result)
        
        query = "Discuss general concepts"
        
        result = await integrated_service.generate_response(
            sample_context_result, query
        )
        
        # Should still generate response
        assert isinstance(result, ResponseResult)
        assert result.response_text is not None
        
        # May still have context citations
        assert isinstance(result.citations, list)
    
    @pytest.mark.asyncio
    async def test_citation_context_integration(
        self,
        integrated_service,
        sample_context_result
    ):
        """Test integration with citation context from composition service."""
        query = "How do the sources relate to this question?"
        
        result = await integrated_service.generate_response(
            sample_context_result, query
        )
        
        # Should integrate context citations with extracted citations
        assert len(result.citations) > 0
        
        # Should have citations from both extraction and context
        extracted_citations = len([c for c in result.citations])
        assert extracted_citations > 0
    
    @pytest.mark.asyncio
    async def test_citation_aware_prompting(
        self,
        integrated_service,
        sample_context_result,
        mock_llm_service
    ):
        """Test that citations are properly formatted in prompts to LLM."""
        query = "Explain the philosophical position"
        
        await integrated_service.generate_response(
            sample_context_result, query
        )
        
        # Verify LLM service was called with citation-aware prompts
        call_args = mock_llm_service.generate_response.call_args
        messages = call_args[1]["messages"]  # messages parameter
        
        # Check system message includes citation guidance
        system_message = next((m for m in messages if m.role == MessageRole.SYSTEM), None)
        assert system_message is not None
        system_content = system_message.content.lower()
        assert "cite" in system_content or "source" in system_content
        
        # Check user message includes source material and citations
        user_message = next((m for m in messages if m.role == MessageRole.USER), None)
        assert user_message is not None
        user_content = user_message.content
        assert "Source Material:" in user_content or "Citations:" in user_content


class TestResponseGenerationFactory:
    """Test suite for response generation service factory with citation services."""
    
    def test_factory_with_citation_services(self):
        """Test factory function with citation services."""
        extraction_service = Mock(spec=CitationExtractionService)
        validation_service = Mock(spec=CitationValidationService)
        tracking_service = Mock(spec=CitationTrackingService)
        
        service = create_response_generation_service(
            citation_extraction_service=extraction_service,
            citation_validation_service=validation_service,
            citation_tracking_service=tracking_service
        )
        
        assert isinstance(service, ResponseGenerationService)
        assert service.citation_extraction_service == extraction_service
        assert service.citation_validation_service == validation_service
        assert service.citation_tracking_service == tracking_service
    
    def test_factory_with_default_citation_services(self):
        """Test factory function creates default citation services."""
        service = create_response_generation_service()
        
        assert isinstance(service, ResponseGenerationService)
        assert isinstance(service.citation_extraction_service, CitationExtractionService)
        assert isinstance(service.citation_validation_service, CitationValidationService)
        assert isinstance(service.citation_tracking_service, CitationTrackingService)


class TestCitationSystemConfiguration:
    """Test suite for citation system configuration in response generation."""
    
    def test_citation_format_configuration(self):
        """Test citation format configuration."""
        config = ResponseGenerationConfig(
            citation_format="modern",
            include_source_attribution=True
        )
        
        assert config.citation_format == "modern"
        assert config.include_source_attribution == True
    
    def test_citation_limits_configuration(self):
        """Test citation limits configuration."""
        config = ResponseGenerationConfig(
            max_citations=5,
            deduplicate_citations=True
        )
        
        assert config.max_citations == 5
        assert config.deduplicate_citations == True
    
    def test_validation_configuration(self):
        """Test validation configuration."""
        config = ResponseGenerationConfig(
            enable_validation=True,
            fail_on_validation_error=True,
            min_accuracy_score=0.8,
            min_citation_coverage=0.6
        )
        
        assert config.enable_validation == True
        assert config.fail_on_validation_error == True
        assert config.min_accuracy_score == 0.8
        assert config.min_citation_coverage == 0.6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])