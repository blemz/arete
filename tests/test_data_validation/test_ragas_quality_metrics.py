"""
Tests for RAGAS-based data quality metrics system.

Tests the integration of RAGAS (RAG Assessment) library for evaluating
the quality of our philosophical tutoring RAG system including:
- Faithfulness evaluation
- Answer relevance assessment
- Context precision measurement
- Context recall validation
- Citation accuracy verification
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any, Optional
from uuid import uuid4
from datetime import datetime, timezone

import pandas as pd
from pydantic import BaseModel

# Assuming RAGAS classes (will be imported once installed)
# from ragas import evaluate
# from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall

from arete.services.data_quality.ragas_quality_service import (
    RAGASQualityService,
    QualityMetrics,
    EvaluationResult,
    QualityThresholds,
    PhilosophicalEvaluationDataset
)
from arete.models.document import Document
from arete.models.chunk import Chunk
from arete.models.citation import Citation


class TestRAGASQualityService:
    """Test suite for RAGAS-based quality service."""
    
    @pytest.fixture
    def sample_philosophical_texts(self):
        """Sample philosophical texts for testing."""
        return [
            {
                "question": "What is justice according to Plato?",
                "contexts": [
                    "In the Republic, Plato defines justice as each part doing its own work and not meddling with others.",
                    "Justice in the soul, according to Plato, mirrors justice in the state - with reason ruling over spirit and appetite."
                ],
                "answer": "According to Plato in the Republic, justice is achieved when each part performs its proper function without interfering with others. In the soul, this means reason should rule over spirit and appetite, just as in the state, each class should perform its designated role.",
                "ground_truth": "Plato defines justice as each part doing its own work in both the soul and the state."
            },
            {
                "question": "What is virtue according to Aristotle?",
                "contexts": [
                    "Aristotle defines virtue as a disposition to choose the mean between extremes of excess and deficiency.",
                    "In the Nicomachean Ethics, Aristotle explains that virtue is acquired through habit and practice."
                ],
                "answer": "Aristotle defines virtue as a habitual disposition to choose the mean between extremes. For example, courage is the mean between cowardice (deficiency) and recklessness (excess).",
                "ground_truth": "According to Aristotle, virtue is the mean between extremes and is developed through habit."
            }
        ]
    
    @pytest.fixture
    def quality_service(self):
        """Create RAGASQualityService instance."""
        return RAGASQualityService()
    
    @pytest.fixture
    def sample_evaluation_result(self):
        """Sample evaluation result for testing."""
        return EvaluationResult(
            query_id=str(uuid4()),
            question="What is justice according to Plato?",
            faithfulness_score=0.85,
            answer_relevancy_score=0.92,
            context_precision_score=0.78,
            context_recall_score=0.83,
            citation_accuracy_score=0.90,
            overall_quality_score=0.856,
            evaluation_timestamp=datetime.now(timezone.utc),
            metadata={"evaluation_method": "ragas", "model_used": "gpt-3.5-turbo"}
        )

    def test_service_initialization(self, quality_service):
        """Test service initializes with proper configuration."""
        assert quality_service is not None
        assert hasattr(quality_service, 'thresholds')
        assert hasattr(quality_service, 'metrics')
        
    def test_quality_thresholds_configuration(self, quality_service):
        """Test quality thresholds are properly configured."""
        thresholds = quality_service.get_quality_thresholds()
        
        assert thresholds.faithfulness_min >= 0.7
        assert thresholds.answer_relevancy_min >= 0.7
        assert thresholds.context_precision_min >= 0.6
        assert thresholds.context_recall_min >= 0.6
        assert thresholds.citation_accuracy_min >= 0.8
        assert thresholds.overall_quality_min >= 0.7

    @pytest.mark.asyncio
    async def test_evaluate_philosophical_query(self, quality_service, sample_philosophical_texts):
        """Test evaluation of a single philosophical query."""
        test_data = sample_philosophical_texts[0]
        
        with patch('arete.services.data_quality.ragas_quality_service.evaluate') as mock_evaluate:
            # Mock RAGAS evaluation result
            mock_result = pd.DataFrame({
                'faithfulness': [0.85],
                'answer_relevancy': [0.92],
                'context_precision': [0.78],
                'context_recall': [0.83]
            })
            mock_evaluate.return_value = mock_result
            
            result = await quality_service.evaluate_single_query(
                question=test_data["question"],
                contexts=test_data["contexts"],
                answer=test_data["answer"],
                ground_truth=test_data.get("ground_truth")
            )
            
            assert isinstance(result, EvaluationResult)
            assert result.faithfulness_score == 0.85
            assert result.answer_relevancy_score == 0.92
            assert result.context_precision_score == 0.78
            assert result.context_recall_score == 0.83
            assert result.overall_quality_score > 0.8

    @pytest.mark.asyncio
    async def test_batch_evaluation(self, quality_service, sample_philosophical_texts):
        """Test batch evaluation of multiple queries."""
        with patch('arete.services.data_quality.ragas_quality_service.evaluate') as mock_evaluate:
            # Mock batch evaluation result
            mock_result = pd.DataFrame({
                'faithfulness': [0.85, 0.88],
                'answer_relevancy': [0.92, 0.89],
                'context_precision': [0.78, 0.82],
                'context_recall': [0.83, 0.79]
            })
            mock_evaluate.return_value = mock_result
            
            results = await quality_service.evaluate_batch(sample_philosophical_texts)
            
            assert len(results) == 2
            assert all(isinstance(result, EvaluationResult) for result in results)
            assert all(result.overall_quality_score > 0.8 for result in results)

    def test_citation_accuracy_evaluation(self, quality_service):
        """Test citation accuracy evaluation."""
        # Mock citations and source texts
        citations = [
            Citation(
                text="Justice is each part doing its own work",
                reference="Republic, 433a",
                confidence_score=0.9
            )
        ]
        
        source_texts = [
            "In the Republic 433a, Plato states that justice consists in each part doing its own work and not meddling with others."
        ]
        
        accuracy_score = quality_service.evaluate_citation_accuracy(citations, source_texts)
        
        assert 0.0 <= accuracy_score <= 1.0
        assert isinstance(accuracy_score, float)

    def test_quality_threshold_validation(self, quality_service, sample_evaluation_result):
        """Test validation against quality thresholds."""
        passed_metrics, failed_metrics = quality_service.validate_against_thresholds(
            sample_evaluation_result
        )
        
        # Should pass most metrics with high scores
        assert len(passed_metrics) >= 4
        assert isinstance(passed_metrics, list)
        assert isinstance(failed_metrics, list)

    def test_quality_trend_analysis(self, quality_service):
        """Test quality trend analysis over time."""
        # Mock historical results
        historical_results = [
            EvaluationResult(
                query_id=str(uuid4()),
                question=f"Test question {i}",
                faithfulness_score=0.8 + (i * 0.02),
                answer_relevancy_score=0.85 + (i * 0.01),
                context_precision_score=0.75 + (i * 0.015),
                context_recall_score=0.78 + (i * 0.012),
                citation_accuracy_score=0.88 + (i * 0.01),
                overall_quality_score=0.81 + (i * 0.015),
                evaluation_timestamp=datetime.now(timezone.utc),
                metadata={}
            ) for i in range(5)
        ]
        
        trend_analysis = quality_service.analyze_quality_trends(historical_results)
        
        assert 'faithfulness_trend' in trend_analysis
        assert 'answer_relevancy_trend' in trend_analysis
        assert 'overall_improvement' in trend_analysis
        assert isinstance(trend_analysis['overall_improvement'], bool)

    @pytest.mark.asyncio
    async def test_continuous_monitoring_setup(self, quality_service):
        """Test setup of continuous quality monitoring."""
        monitoring_config = {
            'evaluation_interval_hours': 24,
            'sample_size': 10,
            'alert_thresholds': {
                'faithfulness_drop': 0.1,
                'overall_quality_drop': 0.05
            }
        }
        
        monitor = await quality_service.setup_continuous_monitoring(monitoring_config)
        
        assert monitor is not None
        assert hasattr(monitor, 'start_monitoring')
        assert hasattr(monitor, 'stop_monitoring')

    def test_philosophical_domain_specific_metrics(self, quality_service):
        """Test philosophical domain-specific quality metrics."""
        philosophical_content = {
            "argument_coherence": "The argument follows logical structure from premises to conclusion",
            "conceptual_clarity": "Concepts are clearly defined and consistently used",
            "textual_fidelity": "Response accurately represents the original philosophical text",
            "dialogical_quality": "Engages with counterarguments and alternative perspectives"
        }
        
        domain_scores = quality_service.evaluate_philosophical_quality(philosophical_content)
        
        assert 'argument_coherence_score' in domain_scores
        assert 'conceptual_clarity_score' in domain_scores
        assert 'textual_fidelity_score' in domain_scores
        assert 'dialogical_quality_score' in domain_scores
        assert all(0.0 <= score <= 1.0 for score in domain_scores.values())

    def test_quality_report_generation(self, quality_service, sample_evaluation_result):
        """Test generation of quality assessment reports."""
        results = [sample_evaluation_result]
        
        report = quality_service.generate_quality_report(results)
        
        assert 'summary_statistics' in report
        assert 'metric_distributions' in report
        assert 'quality_insights' in report
        assert 'recommendations' in report
        
        # Check summary statistics
        stats = report['summary_statistics']
        assert 'total_evaluations' in stats
        assert 'average_overall_quality' in stats
        assert 'metric_averages' in stats

    @pytest.mark.asyncio
    async def test_integration_with_rag_pipeline(self, quality_service):
        """Test integration with existing RAG pipeline."""
        # Mock RAG pipeline components
        mock_retrieval_results = [
            {
                "chunk_id": str(uuid4()),
                "text": "Plato defines justice as harmony in the soul",
                "relevance_score": 0.85,
                "source": "Republic, Book IV"
            }
        ]
        
        mock_llm_response = "According to Plato, justice is the harmony of the soul where each part performs its proper function."
        
        # Test evaluation of RAG pipeline output
        evaluation = await quality_service.evaluate_rag_pipeline_output(
            query="What is justice according to Plato?",
            retrieved_contexts=mock_retrieval_results,
            generated_response=mock_llm_response
        )
        
        assert isinstance(evaluation, EvaluationResult)
        assert evaluation.overall_quality_score > 0.0

    def test_custom_metric_registration(self, quality_service):
        """Test registration of custom philosophical metrics."""
        
        def socratic_questioning_metric(response: str, contexts: List[str]) -> float:
            """Custom metric for evaluating Socratic questioning approach."""
            questioning_indicators = ["why", "how", "what if", "consider"]
            score = sum(1 for indicator in questioning_indicators if indicator in response.lower())
            return min(score / len(questioning_indicators), 1.0)
        
        quality_service.register_custom_metric("socratic_questioning", socratic_questioning_metric)
        
        custom_metrics = quality_service.get_available_metrics()
        assert "socratic_questioning" in custom_metrics

    def test_error_handling_invalid_input(self, quality_service):
        """Test error handling with invalid input."""
        with pytest.raises(ValueError):
            quality_service.evaluate_citation_accuracy([], [])  # Empty inputs
        
        with pytest.raises(TypeError):
            quality_service.evaluate_citation_accuracy("invalid", ["valid"])  # Wrong type

    def test_quality_metrics_serialization(self, sample_evaluation_result):
        """Test serialization of quality metrics for storage."""
        serialized = sample_evaluation_result.model_dump()
        
        assert 'faithfulness_score' in serialized
        assert 'answer_relevancy_score' in serialized
        assert 'overall_quality_score' in serialized
        
        # Test deserialization
        deserialized = EvaluationResult.model_validate(serialized)
        assert deserialized.faithfulness_score == sample_evaluation_result.faithfulness_score


class TestPhilosophicalEvaluationDataset:
    """Test suite for philosophical evaluation dataset management."""
    
    @pytest.fixture
    def dataset_manager(self):
        """Create dataset manager instance."""
        return PhilosophicalEvaluationDataset()
    
    def test_dataset_creation(self, dataset_manager):
        """Test creation of philosophical evaluation dataset."""
        questions = ["What is virtue?", "What is justice?"]
        contexts = [
            ["Virtue is excellence of character"],
            ["Justice is each part doing its work"]
        ]
        answers = ["Virtue is excellence", "Justice is harmony"]
        
        dataset = dataset_manager.create_dataset(questions, contexts, answers)
        
        assert len(dataset) == 2
        assert 'question' in dataset.columns
        assert 'contexts' in dataset.columns
        assert 'answer' in dataset.columns

    def test_dataset_validation(self, dataset_manager):
        """Test validation of dataset quality."""
        valid_dataset = pd.DataFrame({
            'question': ['What is virtue?'],
            'contexts': [['Virtue is excellence']],
            'answer': ['Virtue is excellence of character']
        })
        
        is_valid, validation_errors = dataset_manager.validate_dataset(valid_dataset)
        
        assert is_valid
        assert len(validation_errors) == 0

    def test_dataset_augmentation(self, dataset_manager):
        """Test augmentation of evaluation dataset."""
        base_dataset = pd.DataFrame({
            'question': ['What is virtue?'],
            'contexts': [['Virtue is excellence']],
            'answer': ['Virtue is excellence of character']
        })
        
        augmented_dataset = dataset_manager.augment_dataset(base_dataset, augmentation_factor=2)
        
        assert len(augmented_dataset) >= len(base_dataset)