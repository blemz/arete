"""
Comprehensive tests for cross-provider prompt performance comparison system.

Tests cover prompt performance metrics collection, provider comparison analytics,
quality assessment, and optimization recommendations for philosophical tutoring.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any
import asyncio
from datetime import datetime

from arete.services.prompt_performance_comparison import (
    PromptPerformanceComparison,
    PerformanceMetrics,
    ProviderComparison,
    PromptTest,
    ComparisonResult,
    OptimizationRecommendation,
    MetricType
)
from arete.services.prompt_template import (
    PromptType,
    PromptContext,
    PhilosophicalContext,
    Citation
)


class TestPerformanceMetrics:
    """Test PerformanceMetrics data class."""
    
    def test_metrics_creation(self):
        """Test basic performance metrics creation."""
        metrics = PerformanceMetrics(
            provider="anthropic",
            response_time=1.234,
            token_count=156,
            accuracy_score=0.89,
            citation_quality=0.92,
            educational_value=0.87,
            coherence_score=0.94
        )
        
        assert metrics.provider == "anthropic"
        assert metrics.response_time == 1.234
        assert metrics.token_count == 156
        assert metrics.accuracy_score == 0.89
        assert metrics.citation_quality == 0.92
        assert metrics.educational_value == 0.87
        assert metrics.coherence_score == 0.94
    
    def test_metrics_overall_score_calculation(self):
        """Test overall score calculation."""
        metrics = PerformanceMetrics(
            provider="ollama",
            response_time=0.5,
            token_count=200,
            accuracy_score=0.85,
            citation_quality=0.88,
            educational_value=0.90,
            coherence_score=0.87
        )
        
        # Should calculate weighted average
        expected_score = (0.85 * 0.3 + 0.88 * 0.25 + 0.90 * 0.25 + 0.87 * 0.2)
        assert abs(metrics.get_overall_score() - expected_score) < 0.001


class TestPromptTest:
    """Test PromptTest data class."""
    
    def test_prompt_test_creation(self):
        """Test prompt test case creation."""
        test_case = PromptTest(
            query="What is Plato's theory of Forms?",
            expected_concepts=["Forms", "ideal", "reality", "knowledge"],
            philosophical_context=PhilosophicalContext.ANCIENT,
            student_level="undergraduate",
            learning_objective="Understand Platonic epistemology"
        )
        
        assert test_case.query == "What is Plato's theory of Forms?"
        assert len(test_case.expected_concepts) == 4
        assert test_case.philosophical_context == PhilosophicalContext.ANCIENT
        assert test_case.student_level == "undergraduate"
    
    def test_prompt_test_with_citations(self):
        """Test prompt test with source citations."""
        citation = Citation(
            text="The Forms are perfect, eternal patterns.",
            source="plato_republic",
            reference="Republic 596a"
        )
        
        test_case = PromptTest(
            query="Explain the relationship between Forms and physical objects.",
            expected_concepts=["participation", "imitation", "copies"],
            citations=[citation]
        )
        
        assert len(test_case.citations) == 1
        assert test_case.citations[0].reference == "Republic 596a"


class TestPromptPerformanceComparison:
    """Test PromptPerformanceComparison service."""
    
    @pytest.fixture
    def mock_prompt_service(self):
        """Mock prompt service for testing."""
        service = Mock()
        service.generate_tutoring_response = AsyncMock()
        return service
    
    @pytest.fixture
    def performance_comparison(self, mock_prompt_service):
        """Create performance comparison instance."""
        return PromptPerformanceComparison(prompt_service=mock_prompt_service)
    
    @pytest.fixture
    def sample_test_cases(self):
        """Sample test cases for comparison."""
        return [
            PromptTest(
                query="What is virtue according to Aristotle?",
                expected_concepts=["eudaimonia", "golden mean", "habit"],
                philosophical_context=PhilosophicalContext.ANCIENT,
                student_level="undergraduate"
            ),
            PromptTest(
                query="How does Descartes establish certainty?",
                expected_concepts=["cogito", "methodical doubt", "clear ideas"],
                philosophical_context=PhilosophicalContext.MODERN,
                student_level="graduate"
            )
        ]
    
    def test_initialization(self, performance_comparison):
        """Test service initialization."""
        assert performance_comparison.prompt_service is not None
        assert performance_comparison.comparison_cache == {}
        assert performance_comparison.test_results == []
    
    @pytest.mark.asyncio
    async def test_run_provider_comparison_basic(self, performance_comparison, sample_test_cases, mock_prompt_service):
        """Test basic provider comparison functionality."""
        # Mock response
        mock_response = Mock()
        mock_response.content = "Virtue according to Aristotle is eudaimonia, achieved through the golden mean and habit."
        mock_response.llm_response.response_time = 1.2
        mock_response.llm_response.metadata = {"token_count": 150}
        mock_response.citations_provided = []
        
        mock_prompt_service.generate_tutoring_response.return_value = mock_response
        
        # Run comparison
        result = await performance_comparison.run_provider_comparison(
            test_cases=sample_test_cases[:1],
            providers=["anthropic", "ollama"],
            include_metrics=[MetricType.RESPONSE_TIME, MetricType.ACCURACY]
        )
        
        assert isinstance(result, ComparisonResult)
        assert len(result.provider_comparisons) == 2
        assert "anthropic" in [pc.provider for pc in result.provider_comparisons]
        assert "ollama" in [pc.provider for pc in result.provider_comparisons]
    
    @pytest.mark.asyncio
    async def test_evaluate_response_accuracy(self, performance_comparison):
        """Test response accuracy evaluation."""
        response_content = "Virtue according to Aristotle is eudaimonia, the highest good achieved through the golden mean."
        expected_concepts = ["eudaimonia", "golden mean", "virtue", "highest good"]
        
        accuracy = await performance_comparison._evaluate_accuracy(response_content, expected_concepts)
        
        # Should find most expected concepts
        assert accuracy >= 0.7  # At least 70% accuracy
    
    def test_evaluate_citation_quality(self, performance_comparison):
        """Test citation quality evaluation."""
        citations = [
            Citation(text="Text 1", source="source1", reference="Ethics 1094a"),
            Citation(text="Text 2", source="source2", reference="Republic 514a")
        ]
        
        quality = performance_comparison._evaluate_citation_quality(citations)
        
        # Should have good quality with proper references
        assert quality >= 0.8
    
    def test_evaluate_educational_value(self, performance_comparison):
        """Test educational value assessment."""
        response = (
            "Aristotle's concept of virtue (arete) is central to his ethics. "
            "He distinguishes between intellectual virtues and moral virtues. "
            "Moral virtues are acquired through habit and practice. "
            "The goal is eudaimonia - human flourishing or the good life."
        )
        
        value = performance_comparison._evaluate_educational_value(response, "undergraduate")
        
        # Should be appropriate for undergraduate level
        assert value >= 0.7
    
    def test_calculate_coherence_score(self, performance_comparison):
        """Test coherence score calculation."""
        coherent_response = (
            "Virtue ethics focuses on character rather than actions. "
            "Aristotle argues that virtues are habits developed through practice. "
            "This leads to eudaimonia, which is the ultimate goal of human life."
        )
        
        incoherent_response = (
            "Virtue is good. Plato wrote dialogues. "
            "Mathematics is important. The cave allegory shows reality."
        )
        
        coherent_score = performance_comparison._calculate_coherence_score(coherent_response)
        incoherent_score = performance_comparison._calculate_coherence_score(incoherent_response)
        
        assert coherent_score > incoherent_score
        assert coherent_score >= 0.7  # Should score well with intelligent algorithm
        assert incoherent_score <= 0.5  # Strict expectation - algorithm should distinguish clearly
    
    def test_generate_optimization_recommendations(self, performance_comparison):
        """Test optimization recommendation generation."""
        # Mock comparison result with lower scores to trigger recommendations
        anthropic_comparison = ProviderComparison(
            provider="anthropic",
            average_metrics=PerformanceMetrics(
                provider="anthropic",
                response_time=1.5,
                token_count=200,
                accuracy_score=0.92,
                citation_quality=0.70,  # Lower to trigger citation recommendation
                educational_value=0.70,  # Lower to trigger educational recommendation
                coherence_score=0.89
            ),
            test_count=5,
            score_variance=0.05  # Low variance
        )
        
        ollama_comparison = ProviderComparison(
            provider="ollama",
            average_metrics=PerformanceMetrics(
                provider="ollama",
                response_time=0.8,
                token_count=150,
                accuracy_score=0.85,
                citation_quality=0.65,  # Lower citation quality
                educational_value=0.65,  # Lower educational value
                coherence_score=0.84
            ),
            test_count=5,
            score_variance=0.20  # High variance to trigger consistency recommendation
        )
        
        comparison_result = ComparisonResult(
            provider_comparisons=[anthropic_comparison, ollama_comparison],
            test_cases_used=[],
            total_tests=10,
            best_provider="anthropic",
            recommendations=[]
        )
        
        recommendations = performance_comparison._generate_optimization_recommendations(comparison_result)
        
        assert len(recommendations) >= 2  # Should have citation and educational recommendations
        recommendation_types = [rec.recommendation_type for rec in recommendations]
        assert "prompt_tuning" in recommendation_types
    
    @pytest.mark.asyncio
    async def test_batch_comparison_processing(self, performance_comparison, sample_test_cases, mock_prompt_service):
        """Test batch processing of comparisons."""
        # Mock responses for different providers
        responses = {
            "anthropic": Mock(
                content="Detailed philosophical response...",
                llm_response=Mock(response_time=1.2, metadata={"token_count": 180}),
                citations_provided=[]
            ),
            "ollama": Mock(
                content="Concise philosophical answer...",
                llm_response=Mock(response_time=0.6, metadata={"token_count": 120}),
                citations_provided=[]
            )
        }
        
        async def mock_generate(request):
            return responses.get(request.provider, responses["anthropic"])
        
        mock_prompt_service.generate_tutoring_response.side_effect = mock_generate
        
        # Run batch comparison
        result = await performance_comparison.run_provider_comparison(
            test_cases=sample_test_cases,
            providers=["anthropic", "ollama"],
            include_metrics=[MetricType.RESPONSE_TIME, MetricType.ACCURACY],
            batch_size=2
        )
        
        assert len(result.provider_comparisons) == 2
        assert result.total_tests == 4  # 2 test cases × 2 providers
        assert result.best_provider is not None
    
    def test_comparison_result_caching(self, performance_comparison, sample_test_cases):
        """Test caching of comparison results."""
        cache_key = performance_comparison._generate_cache_key(
            test_cases=sample_test_cases[:1],
            providers=["anthropic"],
            include_metrics=[MetricType.ACCURACY]
        )
        
        # Cache should be initially empty
        assert cache_key not in performance_comparison.comparison_cache
        
        # Add to cache
        mock_result = ComparisonResult(
            provider_comparisons=[],
            test_cases_used=sample_test_cases[:1],
            total_tests=1,
            best_provider="anthropic",
            recommendations=[]
        )
        
        performance_comparison.comparison_cache[cache_key] = mock_result
        
        # Should be cached now
        assert cache_key in performance_comparison.comparison_cache
    
    def test_get_historical_comparisons(self, performance_comparison):
        """Test retrieving historical comparison data."""
        # Add some test results
        performance_comparison.test_results = [
            Mock(timestamp=datetime.now(), provider="anthropic", overall_score=0.89),
            Mock(timestamp=datetime.now(), provider="ollama", overall_score=0.84)
        ]
        
        history = performance_comparison.get_historical_comparisons(days_back=7)
        
        assert len(history) == 2
        assert any(result.provider == "anthropic" for result in history)


class TestComparisonResult:
    """Test ComparisonResult data class."""
    
    def test_comparison_result_creation(self):
        """Test comparison result creation."""
        comparisons = [
            ProviderComparison(
                provider="anthropic",
                average_metrics=PerformanceMetrics(
                    provider="anthropic",
                    response_time=1.2,
                    token_count=180,
                    accuracy_score=0.90,
                    citation_quality=0.85,
                    educational_value=0.88,
                    coherence_score=0.87
                ),
                test_count=3,
                score_variance=0.05
            )
        ]
        
        result = ComparisonResult(
            provider_comparisons=comparisons,
            test_cases_used=[],
            total_tests=3,
            best_provider="anthropic",
            recommendations=[]
        )
        
        assert len(result.provider_comparisons) == 1
        assert result.best_provider == "anthropic"
        assert result.total_tests == 3
    
    def test_get_provider_ranking(self):
        """Test provider ranking functionality."""
        comparisons = [
            ProviderComparison(
                provider="anthropic",
                average_metrics=PerformanceMetrics(
                    provider="anthropic",
                    response_time=1.2,
                    token_count=180,
                    accuracy_score=0.90,
                    citation_quality=0.85,
                    educational_value=0.88,
                    coherence_score=0.87
                ),
                test_count=3,
                score_variance=0.05
            ),
            ProviderComparison(
                provider="ollama", 
                average_metrics=PerformanceMetrics(
                    provider="ollama",
                    response_time=0.8,
                    token_count=150,
                    accuracy_score=0.85,
                    citation_quality=0.80,
                    educational_value=0.84,
                    coherence_score=0.82
                ),
                test_count=3,
                score_variance=0.08
            )
        ]
        
        result = ComparisonResult(
            provider_comparisons=comparisons,
            test_cases_used=[],
            total_tests=6,
            best_provider="anthropic",
            recommendations=[]
        )
        
        ranking = result.get_provider_ranking()
        
        assert len(ranking) == 2
        assert ranking[0].provider == "anthropic"  # Should be first (best)
        assert ranking[1].provider == "ollama"


class TestOptimizationRecommendation:
    """Test OptimizationRecommendation data class."""
    
    def test_recommendation_creation(self):
        """Test recommendation creation."""
        rec = OptimizationRecommendation(
            recommendation_type="provider_selection",
            priority="high",
            description="Use Anthropic Claude for accuracy-critical queries",
            expected_improvement=0.15,
            implementation_effort="low"
        )
        
        assert rec.recommendation_type == "provider_selection"
        assert rec.priority == "high"
        assert rec.expected_improvement == 0.15
        assert rec.implementation_effort == "low"