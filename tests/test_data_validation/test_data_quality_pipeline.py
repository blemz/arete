"""
Tests for comprehensive data quality pipeline orchestration.

Tests the integration and coordination of all data quality validation activities
including RAGAS evaluation, duplicate detection, citation validation, and
quality monitoring into a unified pipeline.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any
from datetime import datetime, timezone
from uuid import uuid4

from arete.services.data_quality.data_quality_pipeline import (
    DataQualityPipeline,
    QualityAssessmentReport,
    QualityValidationRules,
    QualityPipelineConfig,
    QualityAssessmentLevel,
    ValidationStatus
)
from arete.services.data_quality.ragas_quality_service import (
    EvaluationResult,
    QualityMetrics
)
from arete.services.data_quality.duplicate_detection_service import (
    DuplicateResult,
    DeduplicationResult,
    KeepStrategy
)
from arete.services.data_quality.quality_monitor import (
    QualityAlert,
    AlertSeverity,
    MonitoringStats
)
from arete.models.document import Document
from arete.models.chunk import Chunk, ChunkType
from arete.models.citation import Citation, CitationType


class TestDataQualityPipeline:
    """Test suite for comprehensive data quality pipeline."""
    
    @pytest.fixture
    def pipeline_config(self):
        """Create pipeline configuration for testing."""
        return QualityPipelineConfig(
            assessment_level=QualityAssessmentLevel.STANDARD,
            enable_ragas_evaluation=True,
            enable_duplicate_detection=True,
            enable_citation_validation=True,
            batch_size=10,
            save_results=False  # Don't save during tests
        )
    
    @pytest.fixture
    def quality_pipeline(self, pipeline_config):
        """Create data quality pipeline instance."""
        return DataQualityPipeline(pipeline_config)
    
    @pytest.fixture
    def sample_documents(self):
        """Sample documents for testing."""
        return [
            Document(
                title="The Republic",
                author="Plato",
                content="Justice is the advantage of the stronger...",
                metadata={"source": "perseus", "quality": "high"}
            ),
            Document(
                title="Nicomachean Ethics",
                author="Aristotle", 
                content="Every art and every inquiry aims at some good...",
                metadata={"source": "perseus", "quality": "high"}
            ),
            Document(
                title="Republic Duplicate",
                author="Plato",
                content="Justice is the advantage of the stronger...",  # Same content
                metadata={"source": "gutenberg", "quality": "medium"}
            )
        ]
    
    @pytest.fixture
    def sample_chunks(self):
        """Sample chunks for testing."""
        return [
            Chunk(
                text="Virtue is excellence of character developed through habit.",
                chunk_type=ChunkType.PARAGRAPH,
                document_id=uuid4(),
                start_position=0,
                end_position=57,
                sequence_number=0
            ),
            Chunk(
                text="Excellence of character (virtue) is developed through habituation.",
                chunk_type=ChunkType.PARAGRAPH,
                document_id=uuid4(),
                start_position=58,
                end_position=124,
                sequence_number=1
            )
        ]
    
    @pytest.fixture
    def sample_citations(self):
        """Sample citations for testing."""
        return [
            Citation(
                text="Justice is each part doing its own work",
                target_passage="Republic 433a",
                citation_type=CitationType.DIRECT_QUOTE,
                confidence=0.9
            ),
            Citation(
                text="Invalid citation without reference",
                target_passage="",  # Invalid
                citation_type=CitationType.DIRECT_QUOTE,
                confidence=0.3  # Low confidence
            )
        ]
    
    @pytest.fixture
    def mock_ragas_result(self):
        """Mock RAGAS evaluation result."""
        return EvaluationResult(
            query_id="test_query_001",
            question="What is justice according to Plato?",
            faithfulness_score=0.85,
            answer_relevancy_score=0.92,
            context_precision_score=0.78,
            context_recall_score=0.83,
            citation_accuracy_score=0.87,
            overall_quality_score=0.84,
            argument_coherence_score=0.88,
            conceptual_clarity_score=0.75,
            textual_fidelity_score=0.90,
            dialogical_quality_score=0.85,
            evaluation_duration_ms=2500.0
        )

    def test_pipeline_initialization(self, quality_pipeline):
        """Test pipeline initializes correctly."""
        assert quality_pipeline is not None
        assert quality_pipeline.config is not None
        assert quality_pipeline.config.assessment_level == QualityAssessmentLevel.STANDARD
        
    def test_pipeline_config_validation(self):
        """Test pipeline configuration validation."""
        # Valid configuration
        config = QualityPipelineConfig(
            assessment_level=QualityAssessmentLevel.COMPREHENSIVE,
            batch_size=25,
            max_workers=2
        )
        assert config.assessment_level == QualityAssessmentLevel.COMPREHENSIVE
        assert config.batch_size == 25
        
        # Invalid batch size should raise validation error
        with pytest.raises(ValueError):
            QualityPipelineConfig(batch_size=0)
    
    def test_data_categorization(self, quality_pipeline, sample_documents, sample_chunks, sample_citations):
        """Test data categorization by type."""
        mixed_data = sample_documents + sample_chunks + sample_citations
        
        categorized = quality_pipeline._categorize_data(mixed_data)
        
        assert len(categorized["documents"]) == 3
        assert len(categorized["chunks"]) == 2
        assert len(categorized["citations"]) == 2
        assert len(categorized["other"]) == 0
    
    def test_data_categorization_with_dict(self, quality_pipeline, sample_documents, sample_chunks):
        """Test data categorization when data is already a dictionary."""
        data_dict = {
            "documents": sample_documents,
            "chunks": sample_chunks
        }
        
        categorized = quality_pipeline._categorize_data(data_dict)
        
        assert categorized == data_dict
    
    @pytest.mark.asyncio
    async def test_basic_quality_assessment(self, quality_pipeline, sample_documents, mock_ragas_result):
        """Test basic quality assessment workflow."""
        with patch.object(quality_pipeline.ragas_service, 'evaluate_query') as mock_ragas:
            mock_ragas.return_value = mock_ragas_result
            
            with patch.object(quality_pipeline.duplicate_service, 'find_exact_duplicates') as mock_duplicates:
                mock_duplicates.return_value = []
                
                report = await quality_pipeline.assess_data_quality(
                    data=sample_documents,
                    query="What is justice?",
                    contexts=["Justice is a virtue"]
                )
        
        assert report is not None
        assert report.assessment_level == QualityAssessmentLevel.STANDARD
        assert report.items_processed == 3
        assert report.ragas_results == mock_ragas_result
        assert report.ragas_status == ValidationStatus.PASSED
        assert report.processing_time is not None
        assert report.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_comprehensive_assessment_with_duplicates(
        self, 
        quality_pipeline, 
        sample_documents, 
        mock_ragas_result
    ):
        """Test comprehensive assessment including duplicate detection."""
        # Mock duplicate detection
        mock_duplicate = DuplicateResult(
            similarity_score=1.0,
            detection_method="exact_match",
            items=[sample_documents[0], sample_documents[2]]  # Same content
        )
        
        mock_dedup_result = DeduplicationResult(
            kept_items=[sample_documents[0], sample_documents[1]],
            removed_items=[sample_documents[2]],
            original_count=3,
            final_count=2,
            removal_rate=0.33,
            keep_strategy=KeepStrategy.HIGHEST_QUALITY,
            processing_time_ms=10.0,
            duplicate_groups_processed=1
        )
        
        with patch.object(quality_pipeline.ragas_service, 'evaluate_query') as mock_ragas:
            mock_ragas.return_value = mock_ragas_result
            
            with patch.object(quality_pipeline.duplicate_service, 'find_exact_duplicates') as mock_find_dups:
                mock_find_dups.return_value = [mock_duplicate]
                
                with patch.object(quality_pipeline.duplicate_service, 'deduplicate_items') as mock_dedup:
                    mock_dedup.return_value = mock_dedup_result
                    
                    report = await quality_pipeline.assess_data_quality(
                        data=sample_documents,
                        query="What is justice?",
                        contexts=["Justice is a virtue"]
                    )
        
        assert len(report.duplicate_results) == 1
        assert report.deduplication_summary == mock_dedup_result
        assert report.duplicate_status == ValidationStatus.PASSED
        assert report.overall_quality_score is not None
        assert report.quality_grade is not None
    
    @pytest.mark.asyncio
    async def test_citation_validation(self, quality_pipeline, sample_citations):
        """Test citation validation component."""
        # Disable other components for focused testing
        quality_pipeline.config.enable_ragas_evaluation = False
        quality_pipeline.config.enable_duplicate_detection = False
        
        report = await quality_pipeline.assess_data_quality(data=sample_citations)
        
        assert report.citation_accuracy is not None
        assert report.citation_accuracy == 0.5  # 1 valid out of 2 citations
        assert len(report.citation_issues) == 2  # Two issues found
        assert report.citation_status == ValidationStatus.FAILED  # Below threshold
    
    def test_classical_reference_validation(self, quality_pipeline):
        """Test validation of classical text references."""
        valid_references = [
            "Republic 514a",
            "Ethics 1094a", 
            "Rep. 433a",
            "Eth. 1177b",
            "Politics 1253a"
        ]
        
        invalid_references = [
            "",
            "Invalid Reference",
            "123",
            "Book without number"
        ]
        
        for ref in valid_references:
            assert quality_pipeline._is_valid_classical_reference(ref), f"Should be valid: {ref}"
        
        for ref in invalid_references:
            assert not quality_pipeline._is_valid_classical_reference(ref), f"Should be invalid: {ref}"
    
    def test_text_field_mapping(self, quality_pipeline):
        """Test text field mapping for different data types."""
        assert quality_pipeline._get_text_field_for_type("documents") == "content"
        assert quality_pipeline._get_text_field_for_type("chunks") == "text"
        assert quality_pipeline._get_text_field_for_type("citations") == "text"
        assert quality_pipeline._get_text_field_for_type("other") is None
        assert quality_pipeline._get_text_field_for_type("unknown") is None
    
    @pytest.mark.asyncio
    async def test_assessment_with_no_data(self, quality_pipeline):
        """Test assessment behavior with no data."""
        report = await quality_pipeline.assess_data_quality(data=[])
        
        assert report.items_processed == 0
        assert report.ragas_status == ValidationStatus.SKIPPED
        assert report.duplicate_status == ValidationStatus.SKIPPED
        assert report.citation_status == ValidationStatus.SKIPPED
    
    @pytest.mark.asyncio
    async def test_assessment_error_handling(self, quality_pipeline, sample_documents):
        """Test error handling during assessment."""
        # Mock RAGAS service to raise exception
        with patch.object(quality_pipeline.ragas_service, 'evaluate_query') as mock_ragas:
            mock_ragas.side_effect = Exception("RAGAS service unavailable")
            
            report = await quality_pipeline.assess_data_quality(
                data=sample_documents,
                query="What is justice?"
            )
        
        assert report.ragas_status == ValidationStatus.FAILED
        assert any("RAGAS evaluation failed" in alert.message for alert in report.quality_alerts)
    
    @pytest.mark.asyncio 
    async def test_quality_monitoring_integration(self, quality_pipeline):
        """Test integration with quality monitoring."""
        # Enable quality monitoring
        quality_pipeline.config.enable_quality_monitoring = True
        quality_pipeline.config.assessment_level = QualityAssessmentLevel.COMPREHENSIVE
        
        mock_stats = MonitoringStats(
            total_evaluations=100,
            average_quality_score=0.82,
            evaluations_last_24h=15,
            active_alerts=[]
        )
        
        with patch.object(quality_pipeline.quality_monitor, 'get_monitoring_stats') as mock_monitor:
            mock_monitor.return_value = mock_stats
            
            report = await quality_pipeline.assess_data_quality(data=[])
        
        assert "monitoring_stats" in report.validation_summary
        assert report.validation_summary["monitoring_stats"]["total_evaluations"] == 100
    
    def test_recommendation_generation(self, quality_pipeline):
        """Test quality improvement recommendation generation."""
        # Create report with various quality issues
        report = QualityAssessmentReport(
            assessment_id="test_001",
            assessment_level=QualityAssessmentLevel.STANDARD
        )
        
        # Add RAGAS results with low scores
        report.ragas_results = EvaluationResult(
            query_id="test_query_002",
            question="Test query",
            faithfulness_score=0.6,  # Low
            answer_relevancy_score=0.7,  # Low
            context_precision_score=0.6,  # Low  
            context_recall_score=0.5,  # Low
            overall_quality_score=0.65,
            argument_coherence_score=0.8,
            conceptual_clarity_score=0.9,
            textual_fidelity_score=0.85
        )
        
        # Add duplicate results
        report.duplicate_results = [
            DuplicateResult(
                similarity_score=1.0,
                detection_method="exact_match",
                items=["item1", "item2"]
            )
        ]
        
        # Add citation accuracy
        report.citation_accuracy = 0.7  # Low
        
        # Generate recommendations
        quality_pipeline._generate_recommendations(report)
        
        assert len(report.recommendations) > 0
        
        # Check for specific recommendations
        recommendation_text = " ".join(report.recommendations)
        assert "faithfulness" in recommendation_text
        assert "relevancy" in recommendation_text
        assert "precision" in recommendation_text
        assert "recall" in recommendation_text
        assert "duplicate" in recommendation_text
        assert "citation" in recommendation_text


class TestQualityValidationRules:
    """Test suite for quality validation rules."""
    
    @pytest.fixture
    def validation_rules(self):
        """Create validation rules for testing."""
        return QualityValidationRules(
            min_faithfulness=0.8,
            min_answer_relevancy=0.75,
            min_context_precision=0.7,
            max_duplicate_rate=0.1,
            min_citation_accuracy=0.85
        )
    
    def test_rules_initialization(self, validation_rules):
        """Test validation rules initialization."""
        assert validation_rules.min_faithfulness == 0.8
        assert validation_rules.min_answer_relevancy == 0.75
        assert validation_rules.max_duplicate_rate == 0.1
    
    def test_ragas_validation_passed(self, validation_rules):
        """Test RAGAS validation when thresholds are met."""
        results = EvaluationResult(
            query_id="test_query_004",
            question="Test query",
            faithfulness_score=0.85,  # Above threshold
            answer_relevancy_score=0.80,  # Above threshold
            context_precision_score=0.75,  # Above threshold
            context_recall_score=0.75,  # Above threshold
            overall_quality_score=0.81,
            argument_coherence_score=0.8,
            conceptual_clarity_score=0.9,
            textual_fidelity_score=0.85
        )
        
        status, issues = validation_rules.validate_ragas_results(results)
        
        assert status == ValidationStatus.PASSED
        assert len(issues) == 0
    
    def test_ragas_validation_failed(self, validation_rules):
        """Test RAGAS validation when thresholds are not met."""
        results = EvaluationResult(
            query_id="test_query_005",
            question="Test query",
            faithfulness_score=0.6,  # Below threshold
            answer_relevancy_score=0.7,  # Below threshold
            context_precision_score=0.6,  # Below threshold (warning)
            context_recall_score=0.5,  # Below threshold (warning)
            overall_quality_score=0.64,
            argument_coherence_score=0.8,
            conceptual_clarity_score=0.9,
            textual_fidelity_score=0.85
        )
        
        status, issues = validation_rules.validate_ragas_results(results)
        
        assert status == ValidationStatus.FAILED
        assert len(issues) == 4  # All metrics below thresholds
        assert any("Faithfulness" in issue for issue in issues)
        assert any("Answer relevancy" in issue for issue in issues)
    
    def test_duplicate_validation_passed(self, validation_rules):
        """Test duplicate validation when within thresholds."""
        # No duplicates
        duplicates = []
        total_items = 100
        
        status, issues = validation_rules.validate_duplicate_results(duplicates, total_items)
        
        assert status == ValidationStatus.PASSED
        assert len(issues) == 0
    
    def test_duplicate_validation_warning(self, validation_rules):
        """Test duplicate validation when exceeding thresholds."""
        # Create duplicates that exceed threshold
        duplicates = [
            DuplicateResult(similarity_score=1.0, detection_method="exact", items=["a", "b", "c"]),  # 2 duplicates
            DuplicateResult(similarity_score=1.0, detection_method="exact", items=["d", "e", "f", "g"])  # 3 duplicates  
        ]
        total_items = 20  # 5 duplicates out of 20 = 25% rate (above 10% threshold)
        
        status, issues = validation_rules.validate_duplicate_results(duplicates, total_items)
        
        assert status == ValidationStatus.WARNING
        assert len(issues) == 1
        assert "Duplicate rate" in issues[0]
    
    def test_citation_validation_passed(self, validation_rules):
        """Test citation validation when thresholds are met."""
        status, issues = validation_rules.validate_citation_accuracy(0.9, 2)  # Good accuracy, few errors
        
        assert status == ValidationStatus.PASSED
        assert len(issues) == 0
    
    def test_citation_validation_failed(self, validation_rules):
        """Test citation validation when thresholds are not met."""
        status, issues = validation_rules.validate_citation_accuracy(0.7, 10)  # Low accuracy, many errors
        
        assert status == ValidationStatus.FAILED
        assert len(issues) == 2
        assert any("accuracy" in issue for issue in issues)
        assert any("errors" in issue for issue in issues)


class TestQualityAssessmentReport:
    """Test suite for quality assessment report."""
    
    @pytest.fixture
    def sample_report(self):
        """Create sample quality assessment report."""
        return QualityAssessmentReport(
            assessment_id="test_report_001",
            assessment_level=QualityAssessmentLevel.STANDARD
        )
    
    def test_report_initialization(self, sample_report):
        """Test report initializes with required fields."""
        assert sample_report.assessment_id == "test_report_001"
        assert sample_report.assessment_level == QualityAssessmentLevel.STANDARD
        assert sample_report.timestamp is not None
        assert isinstance(sample_report.duplicate_results, list)
        assert isinstance(sample_report.citation_issues, list)
        assert isinstance(sample_report.quality_alerts, list)
        assert isinstance(sample_report.recommendations, list)
    
    def test_overall_score_calculation(self, sample_report):
        """Test overall quality score calculation."""
        # Add component scores
        sample_report.ragas_results = EvaluationResult(
            query_id="test_query_003",
            question="Test",
            faithfulness_score=0.8,
            answer_relevancy_score=0.9,
            context_precision_score=0.7,
            context_recall_score=0.8,
            overall_quality_score=0.82,
            argument_coherence_score=0.8,
            conceptual_clarity_score=0.9,
            textual_fidelity_score=0.85
        )
        sample_report.citation_accuracy = 0.9
        
        # Mock deduplication result
        sample_report.deduplication_summary = DeduplicationResult(
            kept_items=["item1", "item2", "item3"],
            removed_items=["item4"],  # 25% duplicate rate
            original_count=4,
            final_count=3,
            removal_rate=0.25,
            keep_strategy=KeepStrategy.KEEP_FIRST,
            processing_time_ms=5.0,
            duplicate_groups_processed=1
        )
        
        overall_score = sample_report.calculate_overall_score()
        
        assert 0.0 <= overall_score <= 1.0
        assert sample_report.overall_quality_score == overall_score
        # Score should be weighted average of components
        # RAGAS (50%) + Citation (30%) + Duplicate penalty (20%)
        expected = (0.82 * 0.5) + (0.9 * 0.3) + (0.75 * 0.2)  # 0.75 for 25% duplicate rate
        assert abs(overall_score - expected) < 0.01
    
    def test_quality_grade_assignment(self, sample_report):
        """Test quality grade assignment based on score."""
        # Test different score ranges
        test_cases = [
            (0.95, "A"),
            (0.85, "B"), 
            (0.75, "C"),
            (0.65, "D"),
            (0.45, "F")
        ]
        
        for score, expected_grade in test_cases:
            sample_report.overall_quality_score = score
            grade = sample_report.assign_quality_grade()
            assert grade == expected_grade
            assert sample_report.quality_grade == expected_grade
    
    def test_recommendation_management(self, sample_report):
        """Test recommendation addition and deduplication."""
        # Add recommendations
        sample_report.add_recommendation("Improve faithfulness scores")
        sample_report.add_recommendation("Address duplicate content")
        sample_report.add_recommendation("Improve faithfulness scores")  # Duplicate
        
        assert len(sample_report.recommendations) == 2  # No duplicates
        assert "Improve faithfulness scores" in sample_report.recommendations
        assert "Address duplicate content" in sample_report.recommendations
    
    def test_summary_dict_generation(self, sample_report):
        """Test summary dictionary generation for reporting."""
        sample_report.overall_quality_score = 0.82
        sample_report.quality_grade = "B"
        sample_report.items_processed = 50
        sample_report.processing_time = 15.5
        
        summary = sample_report.get_summary_dict()
        
        assert summary["assessment_id"] == "test_report_001"
        assert summary["overall_score"] == 0.82
        assert summary["quality_grade"] == "B"
        assert summary["items_processed"] == 50
        assert summary["processing_time"] == 15.5
        assert "validation_status" in summary
        assert "alerts_count" in summary
        assert "recommendations_count" in summary
    
    def test_report_serialization(self, sample_report):
        """Test report serialization and deserialization."""
        # Add some data to the report
        sample_report.overall_quality_score = 0.85
        sample_report.quality_grade = "B"
        sample_report.citation_accuracy = 0.9
        
        # Test serialization
        serialized = sample_report.model_dump()
        assert isinstance(serialized, dict)
        assert serialized["assessment_id"] == "test_report_001"
        assert serialized["overall_quality_score"] == 0.85
        
        # Test deserialization
        deserialized = QualityAssessmentReport.model_validate(serialized)
        assert deserialized.assessment_id == sample_report.assessment_id
        assert deserialized.overall_quality_score == sample_report.overall_quality_score
        assert deserialized.quality_grade == sample_report.quality_grade