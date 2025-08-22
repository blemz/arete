"""
Tests for Advanced Re-ranking Algorithms in Arete Graph-RAG system.

Tests the re-ranking service that improves search result quality through
cross-encoder models and advanced scoring techniques for philosophical content.

Following TDD methodology: Red-Green-Refactor cycle with focused testing approach.
"""

import pytest
from typing import List, Dict, Any, Optional
from uuid import uuid4
from unittest.mock import Mock, MagicMock, patch

from src.arete.services.reranking_service import (
    RerankingService,
    RerankingResult,
    RerankingConfig,
    RerankingMethod,
    RerankingError
)
from src.arete.services.dense_retrieval_service import SearchResult
from src.arete.models.chunk import Chunk
from src.arete.config import Settings


class TestRerankingResult:
    """Test reranking result data structure."""
    
    def test_reranking_result_creation(self):
        """Test basic reranking result object creation."""
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
            relevance_score=0.7,
            query="virtue knowledge"
        )
        
        reranked_result = RerankingResult(
            original_result=original_result,
            rerank_score=0.85,
            original_rank=5,
            new_rank=2,
            score_improvement=0.15,
            reranking_method=RerankingMethod.CROSS_ENCODER
        )
        
        assert reranked_result.original_result == original_result
        assert reranked_result.rerank_score == 0.85
        assert reranked_result.original_rank == 5
        assert reranked_result.new_rank == 2
        assert reranked_result.score_improvement == 0.15
        assert reranked_result.reranking_method == RerankingMethod.CROSS_ENCODER
    
    def test_reranking_result_final_score_calculation(self):
        """Test final score calculation combining original and rerank scores."""
        chunk = Chunk(
            text="Plato's Republic discusses justice",
            document_id=uuid4(),
            position=1,
            chunk_type="paragraph",
            start_char=0,
            end_char=32
        )
        
        original_result = SearchResult(
            chunk=chunk,
            relevance_score=0.6,
            query="justice"
        )
        
        reranked_result = RerankingResult(
            original_result=original_result,
            rerank_score=0.9,
            original_rank=10,
            new_rank=1,
            score_improvement=0.3
        )
        
        # Test different combination strategies
        assert reranked_result.get_final_score("rerank_only") == 0.9
        assert reranked_result.get_final_score("original_only") == 0.6
        
        # Weighted average (default: 0.3 original + 0.7 rerank)
        expected_weighted = 0.6 * 0.3 + 0.9 * 0.7
        assert abs(reranked_result.get_final_score("weighted") - expected_weighted) < 0.001
        
        # Custom weights
        expected_custom = 0.6 * 0.5 + 0.9 * 0.5
        assert abs(reranked_result.get_final_score("weighted", original_weight=0.5) - expected_custom) < 0.001


class TestRerankingConfig:
    """Test reranking configuration and validation."""
    
    def test_reranking_config_creation(self):
        """Test reranking configuration object creation."""
        config = RerankingConfig(
            method=RerankingMethod.CROSS_ENCODER,
            model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
            max_candidates=100,
            top_k=10,
            batch_size=16,
            original_weight=0.3,
            rerank_weight=0.7,
            score_threshold=0.1
        )
        
        assert config.method == RerankingMethod.CROSS_ENCODER
        assert config.model_name == "cross-encoder/ms-marco-MiniLM-L-6-v2"
        assert config.max_candidates == 100
        assert config.top_k == 10
        assert config.batch_size == 16
        assert config.original_weight == 0.3
        assert config.rerank_weight == 0.7
        assert config.score_threshold == 0.1
    
    def test_reranking_config_validation(self):
        """Test reranking configuration validation rules."""
        # Valid configuration should pass
        valid_config = RerankingConfig()
        assert valid_config.is_valid()
        
        # Invalid weight combination
        with pytest.raises(ValueError):
            RerankingConfig(original_weight=0.6, rerank_weight=0.6)  # Sum > 1.0
        
        # Invalid batch size
        with pytest.raises(ValueError):
            RerankingConfig(batch_size=0)
        
        # Invalid top_k
        with pytest.raises(ValueError):
            RerankingConfig(top_k=-1)
    
    def test_reranking_config_defaults(self):
        """Test default configuration values."""
        config = RerankingConfig()
        
        assert config.method == RerankingMethod.CROSS_ENCODER
        assert config.max_candidates == 50
        assert config.top_k == 20
        assert config.batch_size == 8
        assert config.original_weight == 0.3
        assert config.rerank_weight == 0.7
        assert config.score_threshold == 0.0


class TestRerankingService:
    """Test the main reranking service."""
    
    @pytest.fixture
    def mock_cross_encoder(self):
        """Mock cross-encoder model for testing."""
        model = Mock()
        model.predict.return_value = [0.8, 0.9, 0.6, 0.75, 0.85]  # Mock scores
        return model
    
    @pytest.fixture
    def reranking_service(self, mock_cross_encoder):
        """Create reranking service with mocked dependencies."""
        service = RerankingService(
            config=RerankingConfig(),
            settings=Settings()
        )
        # Replace the initialized models with mocks
        service.cross_encoder = mock_cross_encoder
        service.embedding_service = Mock()
        service.embedding_service.embed.return_value = [0.1] * 768
        return service
    
    @pytest.fixture
    def sample_search_results(self):
        """Create sample search results for testing."""
        results = []
        texts = [
            "Socrates teaches that virtue is knowledge",
            "Plato discusses justice in the Republic", 
            "Aristotle's Ethics explores moral virtue",
            "The cave allegory illustrates enlightenment",
            "Stoicism emphasizes rational acceptance"
        ]
        
        for i, text in enumerate(texts):
            chunk = Chunk(
                text=text,
                document_id=uuid4(),
                position=i,
                chunk_type="paragraph",
                start_char=0,
                end_char=len(text),
                embedding_vector=[0.1] * 768  # Mock embedding
            )
            
            result = SearchResult(
                chunk=chunk,
                relevance_score=0.5 + i * 0.1,  # Varying scores
                query="virtue philosophy"
            )
            results.append(result)
        
        return results
    
    def test_service_initialization(self):
        """Test proper service initialization."""
        config = RerankingConfig()
        service = RerankingService(config=config, settings=Settings())
        
        assert service.config == config
        assert service.is_initialized
    
    def test_cross_encoder_reranking(self, reranking_service, sample_search_results):
        """Test cross-encoder based reranking."""
        query = "What did Socrates teach about virtue?"
        
        reranked_results = reranking_service.rerank(
            query=query,
            search_results=sample_search_results,
            method=RerankingMethod.CROSS_ENCODER
        )
        
        # Should return RerankingResult objects
        assert len(reranked_results) <= len(sample_search_results)
        assert all(isinstance(result, RerankingResult) for result in reranked_results)
        
        # Should be sorted by rerank score (descending)
        rerank_scores = [result.rerank_score for result in reranked_results]
        assert rerank_scores == sorted(rerank_scores, reverse=True)
        
        # Should have updated ranks
        for i, result in enumerate(reranked_results):
            assert result.new_rank == i + 1
    
    def test_semantic_similarity_reranking(self, reranking_service, sample_search_results):
        """Test semantic similarity based reranking."""
        query = "philosophical virtue and knowledge"
        
        # Mock embedding service for semantic similarity
        reranking_service.embedding_service = Mock()
        reranking_service.embedding_service.embed.return_value = [0.1] * 768  # Mock embedding
        
        # Mock similarity calculation by patching the method
        with patch.object(reranking_service, '_calculate_cosine_similarity') as mock_similarity:
            mock_similarity.side_effect = [0.8, 0.9, 0.7, 0.6, 0.75]
            
            reranked_results = reranking_service.rerank(
                query=query,
                search_results=sample_search_results,
                method=RerankingMethod.SEMANTIC_SIMILARITY
            )
        
        assert len(reranked_results) > 0
        assert all(isinstance(result, RerankingResult) for result in reranked_results)
    
    def test_hybrid_reranking(self, reranking_service, sample_search_results):
        """Test hybrid reranking combining multiple methods."""
        query = "Socratic method and virtue ethics"
        
        # Setup mocks for both methods
        reranking_service.embedding_service = Mock()
        reranking_service.embedding_service.embed.return_value = [0.1] * 768
        
        with patch.object(reranking_service, '_calculate_cosine_similarity') as mock_similarity:
            mock_similarity.side_effect = [0.7, 0.8, 0.6, 0.9, 0.75]
            
            reranked_results = reranking_service.rerank(
                query=query,
                search_results=sample_search_results,
                method=RerankingMethod.HYBRID
            )
        
        assert len(reranked_results) > 0
        
        # Hybrid should combine scores from multiple methods
        for result in reranked_results:
            assert result.reranking_method == RerankingMethod.HYBRID
            assert result.rerank_score > 0
    
    def test_batch_processing(self, reranking_service, sample_search_results):
        """Test batch processing of large result sets."""
        # Create large result set
        large_results = sample_search_results * 10  # 50 results
        
        reranked_results = reranking_service.rerank(
            query="virtue and wisdom",
            search_results=large_results,
            method=RerankingMethod.CROSS_ENCODER
        )
        
        # Should handle batching internally
        assert len(reranked_results) <= reranking_service.config.top_k
        assert all(isinstance(result, RerankingResult) for result in reranked_results)
    
    def test_score_threshold_filtering(self, reranking_service, sample_search_results):
        """Test filtering results below score threshold."""
        # Set high threshold
        config = RerankingConfig(score_threshold=0.8)
        reranking_service.config = config
        
        reranked_results = reranking_service.rerank(
            query="philosophical ethics",
            search_results=sample_search_results,
            method=RerankingMethod.CROSS_ENCODER
        )
        
        # Should only return results above threshold
        for result in reranked_results:
            assert result.rerank_score >= config.score_threshold
    
    def test_error_handling(self, reranking_service, sample_search_results):
        """Test error handling in reranking process."""
        # Test with invalid query
        with pytest.raises(RerankingError):
            reranking_service.rerank(
                query="",  # Empty query
                search_results=sample_search_results
            )
        
        # Test with empty results
        empty_results = reranking_service.rerank(
            query="test query",
            search_results=[]
        )
        assert empty_results == []
        
        # Test with model failure
        reranking_service.cross_encoder.predict.side_effect = Exception("Model error")
        
        with pytest.raises(RerankingError):
            reranking_service.rerank(
                query="test query",
                search_results=sample_search_results,
                method=RerankingMethod.CROSS_ENCODER
            )
    
    def test_performance_metrics(self, reranking_service, sample_search_results):
        """Test performance metrics collection."""
        query = "virtue ethics philosophy"
        
        reranked_results = reranking_service.rerank(
            query=query,
            search_results=sample_search_results
        )
        
        metrics = reranking_service.get_metrics()
        
        assert metrics['total_queries'] > 0
        assert metrics['average_processing_time'] >= 0
        assert metrics['total_results_processed'] > 0
        assert 'reranking_method_usage' in metrics
    
    def test_caching_mechanism(self, reranking_service, sample_search_results):
        """Test result caching for repeated queries."""
        query = "philosophical virtue"
        
        # First call
        results1 = reranking_service.rerank(
            query=query,
            search_results=sample_search_results
        )
        
        # Second call with same query should use cache
        results2 = reranking_service.rerank(
            query=query,
            search_results=sample_search_results
        )
        
        # Results should be identical
        assert len(results1) == len(results2)
        for r1, r2 in zip(results1, results2):
            assert r1.rerank_score == r2.rerank_score


class TestRerankingIntegration:
    """Test integration with retrieval systems."""
    
    @pytest.fixture
    def mock_retrieval_repository(self):
        """Mock retrieval repository for integration testing."""
        from src.arete.repositories.retrieval import RetrievalRepository
        
        repo = Mock(spec=RetrievalRepository)
        repo.search.return_value = []
        return repo
    
    def test_reranking_integration_with_retrieval(self, mock_retrieval_repository):
        """Test reranking integration with retrieval repository."""
        # This will be implemented as part of the RetrievalRepository extension
        query_text = "How does Aristotle define virtue?"
        
        # Should integrate reranking after initial retrieval
        # Mock implementation for now
        enhanced_results = mock_retrieval_repository.search(
            query=query_text,
            method="hybrid_with_reranking"
        )
        
        # Verify the integration pattern is established
        mock_retrieval_repository.search.assert_called_once()
    
    def test_reranking_with_graph_results(self):
        """Test reranking integration with graph traversal results."""
        # Test that reranking works with graph-enhanced search results
        # This ensures compatibility with Phase 3.3 graph traversal
        pass  # Implementation will follow graph integration patterns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])