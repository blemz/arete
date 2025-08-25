"""
Tests for Result Diversity Optimization in Arete Graph-RAG system.

Tests the diversification service that optimizes search result variety to avoid
redundant or overly similar results, improving user experience with diverse perspectives.

Following TDD methodology: Red-Green-Refactor cycle with focused testing approach.
"""

import pytest
from typing import List, Dict, Any, Optional
from uuid import uuid4
from unittest.mock import Mock, MagicMock, patch

from src.arete.services.diversity_service import (
    DiversityService,
    DiversityResult,
    DiversityConfig,
    DiversityMethod,
    DiversityError,
    ClusterInfo
)
from src.arete.services.dense_retrieval_service import SearchResult
from src.arete.models.chunk import Chunk
from src.arete.config import Settings


class TestDiversityResult:
    """Test diversity result data structure."""
    
    def test_diversity_result_creation(self):
        """Test basic diversity result object creation."""
        chunk = Chunk(
            text="Socrates teaches that virtue is knowledge",
            document_id=uuid4(),
            position=1,
            chunk_type="paragraph",
            start_char=0,
            end_char=42
        )
        
        original_result = SearchResult(
            chunk=chunk,
            relevance_score=0.8,
            query="virtue knowledge"
        )
        
        diversity_result = DiversityResult(
            original_result=original_result,
            diversity_score=0.75,
            cluster_id=1,
            cluster_center_distance=0.3,
            uniqueness_score=0.85,
            topical_diversity=0.7,
            semantic_novelty=0.8
        )
        
        assert diversity_result.original_result == original_result
        assert diversity_result.diversity_score == 0.75
        assert diversity_result.cluster_id == 1
        assert diversity_result.cluster_center_distance == 0.3
        assert diversity_result.uniqueness_score == 0.85
        assert diversity_result.topical_diversity == 0.7
        assert diversity_result.semantic_novelty == 0.8
    
    def test_diversity_result_final_score_calculation(self):
        """Test final score calculation balancing relevance and diversity."""
        chunk = Chunk(
            text="Plato discusses justice in the Republic",
            document_id=uuid4(),
            position=1,
            chunk_type="paragraph",
            start_char=0,
            end_char=35
        )
        
        original_result = SearchResult(
            chunk=chunk,
            relevance_score=0.9,
            query="justice"
        )
        
        diversity_result = DiversityResult(
            original_result=original_result,
            diversity_score=0.6,
            cluster_id=0,
            cluster_center_distance=0.4,
            uniqueness_score=0.7,
            topical_diversity=0.5,
            semantic_novelty=0.6
        )
        
        # Test different balance strategies
        assert diversity_result.get_final_score("relevance_only") == 0.9
        assert diversity_result.get_final_score("diversity_only") == 0.6
        
        # Balanced approach (default: 0.7 relevance + 0.3 diversity)
        expected_balanced = 0.9 * 0.7 + 0.6 * 0.3
        assert abs(diversity_result.get_final_score("balanced") - expected_balanced) < 0.001
        
        # Custom weights
        expected_custom = 0.9 * 0.5 + 0.6 * 0.5
        assert abs(diversity_result.get_final_score("balanced", relevance_weight=0.5) - expected_custom) < 0.001


class TestClusterInfo:
    """Test cluster information representation."""
    
    def test_cluster_info_creation(self):
        """Test creating cluster information objects."""
        cluster = ClusterInfo(
            cluster_id=0,
            center_embedding=[0.1] * 768,
            size=5,
            coherence=0.85,
            topic_keywords=["virtue", "knowledge", "ethics"],
            representative_text="Socrates teaches virtue"
        )
        
        assert cluster.cluster_id == 0
        assert len(cluster.center_embedding) == 768
        assert cluster.size == 5
        assert cluster.coherence == 0.85
        assert "virtue" in cluster.topic_keywords
        assert cluster.representative_text == "Socrates teaches virtue"
    
    def test_cluster_similarity_calculation(self):
        """Test similarity calculation between clusters."""
        cluster1 = ClusterInfo(
            cluster_id=0,
            center_embedding=[0.8, 0.6, 0.0],
            size=3,
            coherence=0.9,
            topic_keywords=["virtue", "ethics"],
            representative_text="Virtue ethics"
        )
        
        cluster2 = ClusterInfo(
            cluster_id=1,
            center_embedding=[0.6, 0.8, 0.0],
            size=4,
            coherence=0.8,
            topic_keywords=["justice", "politics"],
            representative_text="Political justice"
        )
        
        similarity = cluster1.calculate_similarity(cluster2)
        assert 0.0 <= similarity <= 1.0
        assert similarity > 0  # Should have some similarity


class TestDiversityConfig:
    """Test diversity configuration and validation."""
    
    def test_diversity_config_creation(self):
        """Test diversity configuration object creation."""
        config = DiversityConfig(
            method=DiversityMethod.MMR,
            lambda_param=0.7,
            max_results=20,
            similarity_threshold=0.8,
            cluster_method="kmeans",
            num_clusters=5,
            min_cluster_size=2,
            diversity_weight=0.3
        )
        
        assert config.method == DiversityMethod.MMR
        assert config.lambda_param == 0.7
        assert config.max_results == 20
        assert config.similarity_threshold == 0.8
        assert config.cluster_method == "kmeans"
        assert config.num_clusters == 5
        assert config.min_cluster_size == 2
        assert config.diversity_weight == 0.3
    
    def test_diversity_config_validation(self):
        """Test diversity configuration validation rules."""
        # Valid configuration should pass
        valid_config = DiversityConfig()
        assert valid_config.is_valid()
        
        # Invalid lambda parameter
        with pytest.raises(ValueError):
            DiversityConfig(lambda_param=1.5)  # Should be 0-1
        
        # Invalid similarity threshold
        with pytest.raises(ValueError):
            DiversityConfig(similarity_threshold=-0.1)  # Should be 0-1
        
        # Invalid cluster count
        with pytest.raises(ValueError):
            DiversityConfig(num_clusters=0)  # Should be positive
    
    def test_diversity_config_defaults(self):
        """Test default configuration values."""
        config = DiversityConfig()
        
        assert config.method == DiversityMethod.MMR
        assert config.lambda_param == 0.7
        assert config.max_results == 50
        assert config.similarity_threshold == 0.85
        assert config.cluster_method == "kmeans"
        assert config.num_clusters == 5
        assert config.min_cluster_size == 2
        assert config.diversity_weight == 0.3


class TestDiversityService:
    """Test the main diversity optimization service."""
    
    @pytest.fixture
    def diversity_service(self):
        """Create diversity service with default configuration."""
        return DiversityService(
            config=DiversityConfig(),
            settings=Settings()
        )
    
    @pytest.fixture
    def sample_search_results(self):
        """Create sample search results with varying content."""
        results = []
        
        # Similar results about virtue (should be clustered)
        virtue_texts = [
            "Socrates teaches that virtue is knowledge",
            "Virtue is knowledge according to Socrates",
            "Knowledge equals virtue in Socratic philosophy",
        ]
        
        # Different topic about justice
        justice_texts = [
            "Plato discusses justice in the Republic",
            "Justice is the harmony of the soul for Plato",
        ]
        
        # Another topic about happiness
        happiness_texts = [
            "Aristotle defines happiness as flourishing",
            "Eudaimonia is the highest good in Aristotelian ethics",
        ]
        
        all_texts = virtue_texts + justice_texts + happiness_texts
        
        for i, text in enumerate(all_texts):
            chunk = Chunk(
                text=text,
                document_id=uuid4(),
                position=i,
                chunk_type="paragraph",
                start_char=0,
                end_char=len(text),
                embedding_vector=[0.1 + i * 0.05] * 768  # Varied embeddings
            )
            
            result = SearchResult(
                chunk=chunk,
                relevance_score=0.9 - i * 0.05,  # Decreasing relevance
                query="philosophical concepts"
            )
            results.append(result)
        
        return results
    
    def test_service_initialization(self):
        """Test proper service initialization."""
        config = DiversityConfig()
        service = DiversityService(config=config, settings=Settings())
        
        assert service.config == config
        assert service.is_initialized
    
    def test_mmr_diversification(self, diversity_service, sample_search_results):
        """Test Maximum Marginal Relevance (MMR) diversification."""
        diversified_results = diversity_service.diversify(
            search_results=sample_search_results,
            method=DiversityMethod.MMR
        )
        
        # Should return DiversityResult objects
        assert len(diversified_results) > 0
        assert all(isinstance(result, DiversityResult) for result in diversified_results)
        
        # Should maintain high relevance while increasing diversity
        assert all(result.original_result.relevance_score >= 0.5 for result in diversified_results)
        assert any(result.diversity_score > 0.5 for result in diversified_results)
        
        # Should select fewer results than input (diversification effect)
        assert len(diversified_results) <= len(sample_search_results)
    
    def test_clustering_diversification(self, diversity_service, sample_search_results):
        """Test clustering-based diversification."""
        diversified_results = diversity_service.diversify(
            search_results=sample_search_results,
            method=DiversityMethod.CLUSTERING
        )
        
        assert len(diversified_results) > 0
        assert all(isinstance(result, DiversityResult) for result in diversified_results)
        
        # Should have cluster assignments
        cluster_ids = {result.cluster_id for result in diversified_results}
        assert len(cluster_ids) >= 2  # Should form multiple clusters
        
        # Each cluster should have representative results
        for cluster_id in cluster_ids:
            cluster_results = [r for r in diversified_results if r.cluster_id == cluster_id]
            assert len(cluster_results) >= 1
    
    def test_semantic_diversification(self, diversity_service, sample_search_results):
        """Test semantic distance-based diversification."""
        diversified_results = diversity_service.diversify(
            search_results=sample_search_results,
            method=DiversityMethod.SEMANTIC_DISTANCE
        )
        
        assert len(diversified_results) > 0
        
        # Results should have high semantic novelty
        assert any(result.semantic_novelty > 0.6 for result in diversified_results)
        
        # Should avoid semantically similar results
        for i, result1 in enumerate(diversified_results):
            for result2 in diversified_results[i+1:]:
                # Calculate semantic similarity between results
                similarity = diversity_service._calculate_cosine_similarity(
                    result1.original_result.chunk.embedding_vector,
                    result2.original_result.chunk.embedding_vector
                )
                assert similarity < diversity_service.config.similarity_threshold
    
    def test_hybrid_diversification(self, diversity_service, sample_search_results):
        """Test hybrid diversification combining multiple methods."""
        diversified_results = diversity_service.diversify(
            search_results=sample_search_results,
            method=DiversityMethod.HYBRID
        )
        
        assert len(diversified_results) > 0
        
        # Hybrid should combine benefits of different methods
        assert any(result.topical_diversity >= 0.5 for result in diversified_results)
        # Check that semantic novelty is being calculated (not None)
        assert all(result.semantic_novelty is not None for result in diversified_results)
        
        # Should have balanced final scores
        final_scores = [result.get_final_score("balanced") for result in diversified_results]
        assert all(score > 0.4 for score in final_scores)  # Maintain quality
    
    def test_topical_diversity_calculation(self, diversity_service, sample_search_results):
        """Test topical diversity scoring."""
        # Group results by topic
        topics = diversity_service._extract_topics(sample_search_results)
        
        assert len(topics) >= 2  # Should detect multiple topics
        
        # Calculate topical diversity for each result
        for result in sample_search_results:
            diversity_score = diversity_service._calculate_topical_diversity(result, sample_search_results)
            assert 0.0 <= diversity_score <= 1.0
    
    def test_similarity_threshold_filtering(self, diversity_service, sample_search_results):
        """Test filtering based on similarity threshold."""
        # Set strict similarity threshold
        config = DiversityConfig(similarity_threshold=0.7)
        diversity_service.config = config
        
        diversified_results = diversity_service.diversify(
            search_results=sample_search_results,
            method=DiversityMethod.MMR
        )
        
        # Should filter out highly similar results
        assert len(diversified_results) < len(sample_search_results)
        
        # Remaining results should be sufficiently different
        for i, result1 in enumerate(diversified_results):
            for result2 in diversified_results[i+1:]:
                similarity = diversity_service._calculate_cosine_similarity(
                    result1.original_result.chunk.embedding_vector,
                    result2.original_result.chunk.embedding_vector
                )
                assert similarity <= config.similarity_threshold
    
    def test_philosophical_domain_optimization(self, diversity_service, sample_search_results):
        """Test philosophical domain-specific diversity optimization."""
        # Results should consider philosophical concepts and authors
        diversified_results = diversity_service.diversify(
            search_results=sample_search_results,
            method=DiversityMethod.HYBRID
        )
        
        # Should detect and separate different philosophical concepts
        concepts = set()
        for result in diversified_results:
            text = result.original_result.chunk.text.lower()
            if "virtue" in text:
                concepts.add("virtue")
            if "justice" in text:
                concepts.add("justice")
            if "happiness" in text or "eudaimonia" in text:
                concepts.add("happiness")
        
        assert len(concepts) >= 2  # Should preserve conceptual diversity
    
    def test_error_handling(self, diversity_service):
        """Test error handling in diversification process."""
        # Test with empty results
        empty_results = diversity_service.diversify(search_results=[])
        assert empty_results == []
        
        # Test with single result
        chunk = Chunk(
            text="Single result",
            document_id=uuid4(),
            position=1,
            chunk_type="paragraph",
            start_char=0,
            end_char=13,
            embedding_vector=[0.1] * 768
        )
        single_search_result = [SearchResult(chunk=chunk, relevance_score=0.9, query="test")]
        
        single_diversified = diversity_service.diversify(search_results=single_search_result)
        assert len(single_diversified) == 1
        
        # Test with invalid method - need to pass a string that can't be converted to DiversityMethod
        with pytest.raises((DiversityError, AttributeError)):
            # This should fail when trying to access method.value on invalid method
            diversity_service.diversify(
                search_results=single_search_result,
                method="invalid_method"
            )
    
    def test_performance_metrics(self, diversity_service, sample_search_results):
        """Test performance metrics collection."""
        diversified_results = diversity_service.diversify(
            search_results=sample_search_results
        )
        
        metrics = diversity_service.get_metrics()
        
        assert metrics['total_diversification_requests'] > 0
        assert metrics['average_processing_time'] >= 0
        assert metrics['average_diversity_score'] >= 0
        assert metrics['clustering_efficiency'] >= 0
        assert 'method_usage' in metrics
    
    def test_caching_mechanism(self, diversity_service, sample_search_results):
        """Test result caching for repeated diversification."""
        # First diversification
        results1 = diversity_service.diversify(
            search_results=sample_search_results,
            method=DiversityMethod.MMR
        )
        
        # Second diversification with same parameters should use cache
        results2 = diversity_service.diversify(
            search_results=sample_search_results,
            method=DiversityMethod.MMR
        )
        
        # Results should be identical (from cache)
        assert len(results1) == len(results2)
        for r1, r2 in zip(results1, results2):
            assert r1.diversity_score == r2.diversity_score
            assert r1.cluster_id == r2.cluster_id


class TestDiversityIntegration:
    """Test integration with retrieval systems."""
    
    @pytest.fixture
    def mock_reranking_service(self):
        """Mock reranking service for integration testing."""
        from src.arete.services.reranking_service import RerankingService
        
        service = Mock(spec=RerankingService)
        service.rerank.return_value = []
        return service
    
    def test_diversity_with_reranking_integration(self, mock_reranking_service):
        """Test diversity optimization integration with re-ranking."""
        # This will be implemented as part of the complete pipeline
        query_text = "How does virtue relate to knowledge?"
        
        # Should integrate diversity after re-ranking
        # Mock implementation for now
        enhanced_results = mock_reranking_service.rerank(
            query=query_text,
            search_results=[]
        )
        
        # Verify the integration pattern is established
        mock_reranking_service.rerank.assert_called_once()
    
    def test_diversity_with_retrieval_repository(self):
        """Test diversity integration with retrieval repository."""
        # Test that diversity works with repository-based search results
        # This ensures compatibility with existing retrieval systems
        pass  # Implementation will follow repository integration patterns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])