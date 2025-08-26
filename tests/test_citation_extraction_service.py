"""
Tests for Citation Extraction Service.

This test suite validates the citation extraction functionality including:
- Pattern matching for classical philosophical references
- Direct quote detection and extraction
- Author-work pattern recognition
- Citation validation against source context
- Extraction result metrics and quality assessment
"""

import pytest
from unittest.mock import Mock, patch
from uuid import uuid4
from datetime import datetime, timezone

from src.arete.services.citation_extraction_service import (
    CitationExtractionService,
    CitationExtractionConfig,
    ExtractionResult,
    CitationMatch,
    CitationExtractionError
)
from src.arete.services.context_composition_service import ContextResult, CitationContext
from src.arete.models.citation import Citation, CitationType, CitationContext as CitationContextType
from src.arete.models.document import Document


class TestCitationExtractionService:
    """Test suite for CitationExtractionService."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return CitationExtractionConfig(
            min_confidence_threshold=0.6,
            similarity_threshold=0.7,
            max_citations_to_extract=10
        )
    
    @pytest.fixture
    def extraction_service(self, config):
        """Create citation extraction service instance."""
        return CitationExtractionService(config)
    
    @pytest.fixture
    def sample_citation(self):
        """Create sample citation for testing."""
        return Citation(
            id=uuid4(),
            text="The unexamined life is not worth living",
            citation_type=CitationType.DIRECT_QUOTE,
            context=CitationContextType.ARGUMENT,
            document_id=uuid4(),
            source_title="Apology",
            source_author="Plato",
            source_reference="Apology 38a",
            confidence=0.9
        )
    
    @pytest.fixture
    def context_result(self, sample_citation):
        """Create context result with sample citations."""
        citation_context = CitationContext(
            citation=sample_citation,
            relevance_score=0.9,
            context_text="This is the context around the citation",
            chunk_id=uuid4()
        )
        
        return ContextResult(
            composed_text="Sample composed text with philosophical content",
            citations=[citation_context],
            total_tokens=100,
            metadata={"test": True}
        )
    
    def test_service_initialization(self, config):
        """Test service initialization with configuration."""
        service = CitationExtractionService(config)
        
        assert service.config == config
        assert len(service._classical_patterns) > 0
        assert len(service._quote_patterns) > 0
        assert len(service._author_work_patterns) > 0
    
    def test_service_initialization_default_config(self):
        """Test service initialization with default configuration."""
        service = CitationExtractionService()
        
        assert isinstance(service.config, CitationExtractionConfig)
        assert service.config.min_confidence_threshold == 0.6
    
    def test_classical_reference_extraction(self, extraction_service, context_result):
        """Test extraction of classical philosophical references."""
        response_text = """
        As Plato argues in Republic 514a, the allegory of the cave illustrates the journey 
        from ignorance to knowledge. This connects to what Aristotle discusses in Ethics 1094a 
        about the highest good.
        """
        
        result = extraction_service.extract_citations_from_response(
            response_text, context_result, "What is Plato's cave allegory?"
        )
        
        # Should find classical references
        assert isinstance(result, ExtractionResult)
        assert result.total_matches_found > 0
        
        # Check for Republic and Ethics references
        references = [c.source_reference for c in result.citations if c.source_reference]
        assert any("Republic 514a" in ref for ref in references)
        assert any("Ethics 1094a" in ref for ref in references)
    
    def test_direct_quote_extraction(self, extraction_service, context_result):
        """Test extraction of direct quotes."""
        response_text = '''
        Socrates famously stated "The unexamined life is not worth living" in his defense.
        He also said "I know that I know nothing" which shows his humility.
        '''
        
        result = extraction_service.extract_citations_from_response(
            response_text, context_result, "What did Socrates say?"
        )
        
        # Should find quotes
        assert result.total_matches_found > 0
        
        # Check for direct quotes
        quote_citations = [c for c in result.citations if c.citation_type == CitationType.DIRECT_QUOTE]
        assert len(quote_citations) > 0
        
        # Verify quote text
        quote_texts = [c.text for c in quote_citations]
        assert any("unexamined life" in text.lower() for text in quote_texts)
    
    def test_author_work_pattern_extraction(self, extraction_service, context_result):
        """Test extraction of author-work patterns."""
        response_text = """
        Plato argues in Republic that justice is harmony in the soul.
        Aristotle writes in Ethics about virtue and the good life.
        """
        
        result = extraction_service.extract_citations_from_response(
            response_text, context_result, "What do philosophers say about virtue?"
        )
        
        # Should find author-work patterns
        assert result.total_matches_found > 0
        
        # Check for author-work citations
        author_citations = [c for c in result.citations if "Plato" in c.source_author or "Aristotle" in c.source_author]
        assert len(author_citations) > 0
    
    def test_overlapping_match_removal(self, extraction_service, context_result):
        """Test removal of overlapping citation matches."""
        response_text = """
        As Plato, Republic 514a demonstrates, the cave allegory is profound.
        """
        
        result = extraction_service.extract_citations_from_response(
            response_text, context_result, "Explain the cave allegory"
        )
        
        # Should not have overlapping citations for the same text span
        citations = result.citations
        if len(citations) > 1:
            # Check that no citations overlap in their character positions
            for i, citation1 in enumerate(citations):
                for citation2 in citations[i+1:]:
                    if citation1.start_char and citation1.end_char and citation2.start_char and citation2.end_char:
                        # No overlap
                        assert not (citation1.start_char < citation2.end_char and 
                                  citation1.end_char > citation2.start_char)
    
    def test_confidence_filtering(self, extraction_service, context_result):
        """Test filtering citations by confidence threshold."""
        response_text = "Plato mentions something in Republic."
        
        # Set high confidence threshold
        extraction_service.config.min_confidence_threshold = 0.9
        
        result = extraction_service.extract_citations_from_response(
            response_text, context_result, "What does Plato say?"
        )
        
        # All extracted citations should meet confidence threshold
        for citation in result.citations:
            assert citation.confidence >= 0.9
    
    def test_citation_limit(self, extraction_service, context_result):
        """Test maximum citation extraction limit."""
        # Create response with many potential citations
        response_text = """
        Republic 514a, Ethics 1094a, Meditations 2.1, Politics 1252a, 
        Poetics 1447a, Timaeus 27a, Phaedo 64a, Apology 38a, Symposium 210a, 
        Phaedrus 245a, Meno 80a, Theaetetus 150a
        """
        
        # Set low limit
        extraction_service.config.max_citations_to_extract = 5
        
        result = extraction_service.extract_citations_from_response(
            response_text, context_result, "List philosophical references"
        )
        
        # Should not exceed limit
        assert len(result.citations) <= 5
    
    def test_validation_against_context(self, extraction_service, context_result):
        """Test citation validation against source context."""
        response_text = '''
        As stated in the source: "The unexamined life is not worth living"
        '''
        
        result = extraction_service.extract_citations_from_response(
            response_text, context_result, "What did the source say?"
        )
        
        # Should validate against context citation
        assert result.validated_matches > 0
        assert result.accuracy_score > 0.5
    
    def test_coverage_score_calculation(self, extraction_service, context_result):
        """Test calculation of coverage score."""
        response_text = """
        The source discusses Plato's Apology and the famous statement about examination.
        """
        
        result = extraction_service.extract_citations_from_response(
            response_text, context_result, "Summarize the source"
        )
        
        # Should calculate coverage based on source material usage
        assert 0.0 <= result.coverage_score <= 1.0
    
    def test_accuracy_score_calculation(self, extraction_service, context_result):
        """Test calculation of accuracy score."""
        response_text = '''
        "The unexamined life is not worth living" - this exact quote appears in sources.
        '''
        
        result = extraction_service.extract_citations_from_response(
            response_text, context_result, "Quote the source"
        )
        
        # Should have high accuracy for exact matches
        assert result.accuracy_score > 0.7
    
    def test_quality_issue_detection(self, extraction_service, context_result):
        """Test detection of quality issues in citations."""
        response_text = "Some vague reference to philosophy without specific citations."
        
        result = extraction_service.extract_citations_from_response(
            response_text, context_result, "Discuss philosophy"
        )
        
        # Should detect low coverage as an issue
        if result.coverage_score < 0.5:
            assert len(result.issues) > 0
            assert any("coverage" in issue.lower() for issue in result.issues)
    
    def test_warning_generation(self, extraction_service, context_result):
        """Test generation of citation warnings."""
        response_text = '''
        "Quote 1" "Quote 2" "Quote 3" "Quote 4" - all direct quotes
        '''
        
        result = extraction_service.extract_citations_from_response(
            response_text, context_result, "Just quote everything"
        )
        
        # Should warn about excessive quoting
        quote_count = sum(1 for c in result.citations if c.citation_type == CitationType.DIRECT_QUOTE)
        if quote_count > len(result.citations) * 0.7:
            assert len(result.warnings) > 0
            assert any("quote" in warning.lower() for warning in result.warnings)
    
    def test_empty_response_handling(self, extraction_service, context_result):
        """Test handling of empty response text."""
        result = extraction_service.extract_citations_from_response(
            "", context_result, "Empty query"
        )
        
        assert isinstance(result, ExtractionResult)
        assert result.total_matches_found == 0
        assert len(result.citations) == 0
    
    def test_no_context_handling(self, extraction_service):
        """Test handling when no context is provided."""
        context_result = ContextResult(
            composed_text="",
            citations=[],
            total_tokens=0
        )
        
        response_text = "Republic 514a discusses the cave allegory."
        
        result = extraction_service.extract_citations_from_response(
            response_text, context_result, "Discuss cave allegory"
        )
        
        # Should still extract patterns but with lower validation
        assert isinstance(result, ExtractionResult)
    
    def test_processing_time_tracking(self, extraction_service, context_result):
        """Test that processing time is tracked."""
        response_text = "Republic 514a is a famous passage in Plato's work."
        
        result = extraction_service.extract_citations_from_response(
            response_text, context_result, "Discuss Republic"
        )
        
        # Should track processing time
        assert result.processing_time > 0.0
    
    def test_citation_relationship_tracking(self, extraction_service, context_result):
        """Test tracking of citation relationships."""
        response_text = """
        Republic 514a introduces the cave allegory, which connects to what 
        Aristotle later discusses in Ethics 1094a about knowledge and virtue.
        """
        
        result = extraction_service.extract_citations_from_response(
            response_text, context_result, "How do Republic and Ethics relate?"
        )
        
        # Should extract multiple related citations
        assert len(result.citations) >= 2
        
        # Citations should have relationship potential
        plato_citations = [c for c in result.citations if "Republic" in (c.source_reference or "")]
        aristotle_citations = [c for c in result.citations if "Ethics" in (c.source_reference or "")]
        
        assert len(plato_citations) > 0 or len(aristotle_citations) > 0


class TestCitationExtractionConfig:
    """Test suite for CitationExtractionConfig."""
    
    def test_default_configuration(self):
        """Test default configuration values."""
        config = CitationExtractionConfig()
        
        assert config.enable_classical_patterns == True
        assert config.enable_direct_quote_detection == True
        assert config.enable_author_work_patterns == True
        assert config.min_confidence_threshold == 0.6
        assert config.similarity_threshold == 0.8
        assert config.max_citations_to_extract == 20
    
    def test_custom_configuration(self):
        """Test custom configuration values."""
        config = CitationExtractionConfig(
            min_confidence_threshold=0.8,
            similarity_threshold=0.9,
            max_citations_to_extract=5,
            enable_classical_patterns=False
        )
        
        assert config.min_confidence_threshold == 0.8
        assert config.similarity_threshold == 0.9
        assert config.max_citations_to_extract == 5
        assert config.enable_classical_patterns == False


class TestCitationMatch:
    """Test suite for CitationMatch dataclass."""
    
    def test_citation_match_creation(self):
        """Test creation of CitationMatch objects."""
        match = CitationMatch(
            text="Republic 514a",
            start_pos=10,
            end_pos=22,
            confidence=0.9,
            pattern_type="classical_ref"
        )
        
        assert match.text == "Republic 514a"
        assert match.start_pos == 10
        assert match.end_pos == 22
        assert match.confidence == 0.9
        assert match.pattern_type == "classical_ref"
        assert match.is_validated == False
    
    def test_citation_match_validation_state(self):
        """Test validation state tracking in CitationMatch."""
        match = CitationMatch(
            text="Test quote",
            start_pos=0,
            end_pos=10
        )
        
        # Initially not validated
        assert match.is_validated == False
        assert match.validation_score == 0.0
        assert match.source_citation is None
        
        # After validation
        match.is_validated = True
        match.validation_score = 0.8
        
        assert match.is_validated == True
        assert match.validation_score == 0.8


class TestExtractionResult:
    """Test suite for ExtractionResult dataclass."""
    
    def test_extraction_result_creation(self):
        """Test creation of ExtractionResult objects."""
        result = ExtractionResult(
            total_matches_found=5,
            validated_matches=3,
            processing_time=0.1,
            accuracy_score=0.8,
            coverage_score=0.6
        )
        
        assert result.total_matches_found == 5
        assert result.validated_matches == 3
        assert result.processing_time == 0.1
        assert result.accuracy_score == 0.8
        assert result.coverage_score == 0.6
        assert len(result.citations) == 0  # Default empty list
        assert len(result.issues) == 0
        assert len(result.warnings) == 0
    
    def test_extraction_result_with_citations(self):
        """Test ExtractionResult with actual citations."""
        citation = Citation(
            id=uuid4(),
            text="Test citation",
            citation_type=CitationType.REFERENCE,
            context=CitationContextType.EXPLANATION,
            document_id=uuid4(),
            source_title="Test Source",
            source_author="Test Author",
            confidence=0.8
        )
        
        result = ExtractionResult(
            citations=[citation],
            total_matches_found=1,
            validated_matches=1
        )
        
        assert len(result.citations) == 1
        assert result.citations[0] == citation
        assert result.total_matches_found == 1
        assert result.validated_matches == 1


class TestCitationExtractionErrors:
    """Test suite for citation extraction error handling."""
    
    def test_citation_extraction_error(self):
        """Test CitationExtractionError exception."""
        with pytest.raises(CitationExtractionError):
            raise CitationExtractionError("Test error message")
    
    def test_service_error_handling(self, extraction_service):
        """Test service error handling with invalid input."""
        context_result = ContextResult(
            composed_text="",
            citations=[],
            total_tokens=0
        )
        
        # Should not raise exception even with problematic input
        result = extraction_service.extract_citations_from_response(
            None, context_result, ""  # None as response_text
        )
        
        # Should handle gracefully and return valid result
        assert isinstance(result, ExtractionResult)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])