"""
Tests for Citation Validation Service.

This test suite validates the citation validation functionality including:
- Individual citation validation against multiple rules
- Batch citation validation with parallel processing
- Textual accuracy validation against source material
- Source attribution verification
- Contextual relevance assessment
- Scholarly format validation
- Confidence score calculation and quality metrics
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from src.arete.services.citation_validation_service import (
    CitationValidationService,
    CitationValidationConfig,
    ValidationResult,
    BatchValidationResult,
    ValidationRule,
    ValidationType,
    CitationValidationError,
    ValidationRuleError
)
from src.arete.services.context_composition_service import ContextResult, CitationContext
from src.arete.models.citation import Citation, CitationType, CitationContext as CitationContextType
from src.arete.models.document import Document


class TestCitationValidationService:
    """Test suite for CitationValidationService."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return CitationValidationConfig(
            min_confidence_threshold=0.7,
            textual_similarity_threshold=0.8,
            contextual_relevance_threshold=0.6,
            enable_textual_validation=True,
            enable_source_validation=True,
            enable_contextual_validation=True,
            enable_format_validation=True
        )
    
    @pytest.fixture
    def validation_service(self, config):
        """Create citation validation service instance."""
        return CitationValidationService(config)
    
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
            source_edition="Jowett Translation",
            confidence=0.9
        )
    
    @pytest.fixture
    def source_citation(self):
        """Create source citation for validation."""
        return Citation(
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
    
    @pytest.fixture
    def context_result(self, source_citation):
        """Create context result with source citations."""
        citation_context = CitationContext(
            citation=source_citation,
            relevance_score=0.9,
            context_text="This is the context around the citation",
            chunk_id=uuid4()
        )
        
        return ContextResult(
            composed_text="Sample composed text with the philosophical quote",
            citations=[citation_context],
            total_tokens=100,
            metadata={"validation_test": True}
        )
    
    def test_service_initialization(self, config):
        """Test service initialization with configuration."""
        service = CitationValidationService(config)
        
        assert service.config == config
        assert len(service.validation_rules) > 0
        
        # Check that rules match enabled validations
        rule_types = {rule.validation_type for rule in service.validation_rules}
        assert ValidationType.TEXTUAL_ACCURACY in rule_types
        assert ValidationType.SOURCE_ATTRIBUTION in rule_types
        assert ValidationType.CONTEXTUAL_RELEVANCE in rule_types
        assert ValidationType.SCHOLARLY_FORMAT in rule_types
    
    def test_service_initialization_default_config(self):
        """Test service initialization with default configuration."""
        service = CitationValidationService()
        
        assert isinstance(service.config, CitationValidationConfig)
        assert service.config.min_confidence_threshold == 0.7
        assert len(service.validation_rules) > 0
    
    @pytest.mark.asyncio
    async def test_single_citation_validation(self, validation_service, sample_citation, context_result):
        """Test validation of a single citation."""
        result = await validation_service.validate_citation(
            sample_citation, context_result
        )
        
        assert isinstance(result, ValidationResult)
        assert result.citation_id == sample_citation.id
        assert isinstance(result.is_valid, bool)
        assert 0.0 <= result.confidence_score <= 1.0
        assert len(result.rule_results) > 0
    
    @pytest.mark.asyncio
    async def test_high_quality_citation_validation(self, validation_service, sample_citation, context_result):
        """Test validation of a high-quality citation."""
        result = await validation_service.validate_citation(
            sample_citation, context_result
        )
        
        # High-quality citation should pass validation
        assert result.is_valid == True
        assert result.confidence_score >= 0.7
        assert result.source_found == True
        assert result.source_accuracy > 0.8
    
    @pytest.mark.asyncio
    async def test_textual_accuracy_validation(self, validation_service, sample_citation, context_result):
        """Test textual accuracy validation rule."""
        result = await validation_service.validate_citation(
            sample_citation, context_result
        )
        
        # Should have textual accuracy result
        assert "textual_accuracy" in result.rule_results
        textual_result = result.rule_results["textual_accuracy"]
        
        assert "passed" in textual_result
        assert "score" in textual_result
        assert "similarity" in textual_result
        assert textual_result["similarity"] > 0.9  # Exact match
    
    @pytest.mark.asyncio
    async def test_source_attribution_validation(self, validation_service, sample_citation, context_result):
        """Test source attribution validation rule."""
        result = await validation_service.validate_citation(
            sample_citation, context_result
        )
        
        # Should have source attribution result
        assert "source_attribution" in result.rule_results
        attribution_result = result.rule_results["source_attribution"]
        
        assert "passed" in attribution_result
        assert "score" in attribution_result
        # Should pass due to complete attribution
        assert attribution_result["passed"] == True
    
    @pytest.mark.asyncio
    async def test_contextual_relevance_validation(self, validation_service, sample_citation):
        """Test contextual relevance validation rule."""
        result = await validation_service.validate_citation(sample_citation)
        
        # Should have contextual relevance result
        assert "contextual_relevance" in result.rule_results
        relevance_result = result.rule_results["contextual_relevance"]
        
        assert "passed" in relevance_result
        assert "score" in relevance_result
        assert relevance_result["score"] > 0.5  # Should have reasonable relevance
    
    @pytest.mark.asyncio
    async def test_scholarly_format_validation(self, validation_service, sample_citation):
        """Test scholarly format validation rule."""
        result = await validation_service.validate_citation(sample_citation)
        
        # Should have scholarly format result
        assert "scholarly_format" in result.rule_results
        format_result = result.rule_results["scholarly_format"]
        
        assert "passed" in format_result
        assert "score" in format_result
        # Should pass due to proper classical reference format
        assert format_result["passed"] == True
    
    @pytest.mark.asyncio
    async def test_invalid_citation_validation(self, validation_service, context_result):
        """Test validation of an invalid citation."""
        invalid_citation = Citation(
            id=uuid4(),
            text="Some random text not in sources",
            citation_type=CitationType.REFERENCE,
            context=CitationContextType.EXPLANATION,
            document_id=uuid4(),
            source_title="",  # Missing title
            source_author="",  # Missing author
            source_reference="",  # Missing reference
            confidence=0.3
        )
        
        result = await validation_service.validate_citation(
            invalid_citation, context_result
        )
        
        # Should fail validation
        assert result.is_valid == False
        assert result.confidence_score < 0.7
        assert len(result.issues) > 0
    
    @pytest.mark.asyncio
    async def test_batch_citation_validation(self, validation_service, sample_citation, context_result):
        """Test batch validation of multiple citations."""
        # Create multiple citations
        citations = []
        for i in range(3):
            citation = Citation(
                id=uuid4(),
                text=f"Test citation {i}",
                citation_type=CitationType.REFERENCE,
                context=CitationContextType.EXPLANATION,
                document_id=uuid4(),
                source_title="Test Source",
                source_author="Test Author",
                source_reference=f"Test {i}a",
                confidence=0.8
            )
            citations.append(citation)
        
        result = await validation_service.validate_citations_batch(
            citations, context_result
        )
        
        assert isinstance(result, BatchValidationResult)
        assert len(result.citation_results) == 3
        assert result.total_citations == 3
        assert result.processing_time > 0.0
        assert 0.0 <= result.average_confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_batch_validation_metrics(self, validation_service, sample_citation, context_result):
        """Test batch validation aggregate metrics."""
        # Create mix of valid and invalid citations
        valid_citation = sample_citation
        invalid_citation = Citation(
            id=uuid4(),
            text="Invalid citation",
            citation_type=CitationType.REFERENCE,
            context=CitationContextType.EXPLANATION,
            document_id=uuid4(),
            source_title="",
            source_author="",
            confidence=0.2
        )
        
        citations = [valid_citation, invalid_citation]
        
        result = await validation_service.validate_citations_batch(
            citations, context_result
        )
        
        # Check aggregate metrics
        assert result.total_citations == 2
        assert result.valid_citations <= 2
        assert 0.0 <= result.accuracy_score <= 1.0
        assert 0.0 <= result.coverage_score <= 1.0
        assert 0.0 <= result.scholarly_quality <= 1.0
    
    @pytest.mark.asyncio
    async def test_batch_validation_timeout(self, validation_service, sample_citation):
        """Test batch validation timeout handling."""
        # Configure short timeout
        validation_service.config.validation_timeout = 0.001  # Very short timeout
        
        citations = [sample_citation] * 10  # Many citations
        
        result = await validation_service.validate_citations_batch(citations)
        
        # Should handle timeout gracefully
        assert isinstance(result, BatchValidationResult)
        assert result.total_citations == 10
    
    @pytest.mark.asyncio
    async def test_confidence_score_calculation(self, validation_service, sample_citation, context_result):
        """Test confidence score calculation from rule results."""
        result = await validation_service.validate_citation(
            sample_citation, context_result
        )
        
        # Confidence should be weighted average of rule scores
        assert 0.0 <= result.confidence_score <= 1.0
        
        # High-quality citation should have high confidence
        if result.is_valid and len(result.issues) == 0:
            assert result.confidence_score >= 0.7
    
    @pytest.mark.asyncio
    async def test_source_verification(self, validation_service, sample_citation, context_result):
        """Test source verification against context."""
        result = await validation_service.validate_citation(
            sample_citation, context_result
        )
        
        # Should find matching source
        assert result.source_found == True
        assert result.source_accuracy > 0.8  # High accuracy for exact match
        assert result.attribution_accuracy > 0.8
    
    @pytest.mark.asyncio
    async def test_contextual_relevance_analysis(self, validation_service, sample_citation):
        """Test contextual relevance analysis."""
        result = await validation_service.validate_citation(sample_citation)
        
        # Should analyze contextual relevance
        assert 0.0 <= result.contextual_relevance <= 1.0
        assert 0.0 <= result.philosophical_accuracy <= 1.0
        
        # Argument context should have good relevance
        if sample_citation.context == CitationContextType.ARGUMENT:
            assert result.contextual_relevance >= 0.7
    
    @pytest.mark.asyncio
    async def test_improvement_suggestions(self, validation_service, context_result):
        """Test generation of improvement suggestions."""
        # Create citation with issues
        problematic_citation = Citation(
            id=uuid4(),
            text="Vague reference",
            citation_type=CitationType.REFERENCE,
            context=CitationContextType.EXPLANATION,
            document_id=uuid4(),
            source_title="Some Source",
            source_author="Unknown",
            source_reference="",  # Missing reference
            confidence=0.4
        )
        
        result = await validation_service.validate_citation(
            problematic_citation, context_result
        )
        
        # Should provide suggestions for improvement
        assert len(result.suggestions) > 0
        
        # Should suggest adding reference
        suggestions_text = " ".join(result.suggestions).lower()
        assert "reference" in suggestions_text or "citation" in suggestions_text
    
    @pytest.mark.asyncio
    async def test_validation_without_context(self, validation_service, sample_citation):
        """Test validation without source context."""
        result = await validation_service.validate_citation(sample_citation, None)
        
        # Should still validate but with limited accuracy
        assert isinstance(result, ValidationResult)
        assert result.source_found == False
        assert result.source_accuracy == 0.0
    
    @pytest.mark.asyncio
    async def test_parallel_validation(self, validation_service, sample_citation, context_result):
        """Test parallel validation processing."""
        # Create multiple citations for parallel processing
        citations = []
        for i in range(5):
            citation = Citation(
                id=uuid4(),
                text=f"Citation {i}",
                citation_type=CitationType.REFERENCE,
                context=CitationContextType.EXPLANATION,
                document_id=uuid4(),
                source_title="Test Source",
                source_author="Test Author",
                source_reference=f"Test {i}a",
                confidence=0.8
            )
            citations.append(citation)
        
        # Time the batch validation
        import time
        start_time = time.time()
        
        result = await validation_service.validate_citations_batch(
            citations, context_result
        )
        
        end_time = time.time()
        
        # Should complete all validations
        assert len(result.citation_results) == 5
        assert result.processing_time > 0.0
        
        # Parallel processing should be reasonably fast
        assert end_time - start_time < 5.0  # Should complete within 5 seconds
    
    @pytest.mark.asyncio
    async def test_quality_assessment(self, validation_service, context_result):
        """Test quality assessment in batch validation."""
        # Create citations with various quality levels
        high_quality = Citation(
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
        
        low_quality = Citation(
            id=uuid4(),
            text="Something vague",
            citation_type=CitationType.REFERENCE,
            context=CitationContextType.EXPLANATION,
            document_id=uuid4(),
            source_title="",
            source_author="",
            confidence=0.3
        )
        
        citations = [high_quality, low_quality]
        
        result = await validation_service.validate_citations_batch(
            citations, context_result
        )
        
        # Should assess quality issues
        if result.accuracy_score < 0.7:
            assert len(result.quality_issues) > 0
        
        # Should provide recommendations
        if not result.overall_validity:
            assert len(result.quality_recommendations) > 0


class TestCitationValidationConfig:
    """Test suite for CitationValidationConfig."""
    
    def test_default_configuration(self):
        """Test default configuration values."""
        config = CitationValidationConfig()
        
        assert config.min_confidence_threshold == 0.7
        assert config.textual_similarity_threshold == 0.8
        assert config.contextual_relevance_threshold == 0.6
        assert config.enable_textual_validation == True
        assert config.enable_source_validation == True
        assert config.enable_contextual_validation == True
        assert config.enable_format_validation == True
    
    def test_custom_configuration(self):
        """Test custom configuration values."""
        config = CitationValidationConfig(
            min_confidence_threshold=0.8,
            textual_similarity_threshold=0.9,
            enable_textual_validation=False,
            max_concurrent_validations=10
        )
        
        assert config.min_confidence_threshold == 0.8
        assert config.textual_similarity_threshold == 0.9
        assert config.enable_textual_validation == False
        assert config.max_concurrent_validations == 10


class TestValidationRule:
    """Test suite for ValidationRule dataclass."""
    
    def test_validation_rule_creation(self):
        """Test creation of ValidationRule objects."""
        rule = ValidationRule(
            name="test_rule",
            validation_type=ValidationType.TEXTUAL_ACCURACY,
            weight=0.8,
            is_required=True,
            min_similarity_threshold=0.7
        )
        
        assert rule.name == "test_rule"
        assert rule.validation_type == ValidationType.TEXTUAL_ACCURACY
        assert rule.weight == 0.8
        assert rule.is_required == True
        assert rule.min_similarity_threshold == 0.7


class TestValidationResult:
    """Test suite for ValidationResult dataclass."""
    
    def test_validation_result_creation(self):
        """Test creation of ValidationResult objects."""
        citation_id = uuid4()
        result = ValidationResult(
            citation_id=citation_id,
            is_valid=True,
            confidence_score=0.85,
            source_found=True,
            source_accuracy=0.9
        )
        
        assert result.citation_id == citation_id
        assert result.is_valid == True
        assert result.confidence_score == 0.85
        assert result.source_found == True
        assert result.source_accuracy == 0.9
        assert len(result.issues) == 0
        assert len(result.warnings) == 0
        assert len(result.suggestions) == 0


class TestBatchValidationResult:
    """Test suite for BatchValidationResult dataclass."""
    
    def test_batch_validation_result_creation(self):
        """Test creation of BatchValidationResult objects."""
        result = BatchValidationResult(
            total_citations=5,
            valid_citations=4,
            overall_validity=False,
            average_confidence=0.75,
            processing_time=1.2
        )
        
        assert result.total_citations == 5
        assert result.valid_citations == 4
        assert result.overall_validity == False
        assert result.average_confidence == 0.75
        assert result.processing_time == 1.2
        assert len(result.citation_results) == 0  # Default empty
        assert len(result.quality_issues) == 0
        assert len(result.quality_recommendations) == 0


class TestValidationErrors:
    """Test suite for validation error handling."""
    
    def test_citation_validation_error(self):
        """Test CitationValidationError exception."""
        with pytest.raises(CitationValidationError):
            raise CitationValidationError("Test validation error")
    
    def test_validation_rule_error(self):
        """Test ValidationRuleError exception."""
        with pytest.raises(ValidationRuleError):
            raise ValidationRuleError("Test rule error")
    
    @pytest.mark.asyncio
    async def test_error_handling_in_validation(self, validation_service):
        """Test error handling during validation process."""
        # Create citation that might cause validation issues
        problematic_citation = Citation(
            id=uuid4(),
            text=None,  # This might cause issues
            citation_type=CitationType.REFERENCE,
            context=CitationContextType.EXPLANATION,
            document_id=uuid4(),
            source_title="Test",
            source_author="Test",
            confidence=0.5
        )
        
        # Should not raise exception
        result = await validation_service.validate_citation(problematic_citation)
        
        # Should handle gracefully
        assert isinstance(result, ValidationResult)
        assert result.is_valid == False
        assert len(result.issues) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])