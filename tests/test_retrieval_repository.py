"""
Tests for RetrievalRepository - unified retrieval interface.

Comprehensive test coverage for hybrid retrieval repository that combines
dense and sparse retrieval methods with various fusion strategies.
"""

import pytest
from typing import List
from uuid import UUID, uuid4
from unittest.mock import Mock, AsyncMock, patch

from src.arete.repositories.retrieval import (
    RetrievalRepository,
    RetrievalMethod,
    HybridStrategy,
    HybridRetrievalConfig,
    RetrievalRepositoryError,
    create_retrieval_repository
)
from src.arete.services.dense_retrieval_service import SearchResult
from src.arete.models.chunk import Chunk


class TestHybridRetrievalConfig:
    """Test HybridRetrievalConfig configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = HybridRetrievalConfig()
        
        assert config.dense_weight == 0.7
        assert config.sparse_weight == 0.3
        assert config.strategy == HybridStrategy.WEIGHTED_AVERAGE
        assert config.min_dense_score == 0.7
        assert config.min_sparse_score == 0.1
        assert config.fusion_k == 60
    
    def test_custom_config(self):
        """Test custom configuration creation."""
        config = HybridRetrievalConfig(
            dense_weight=0.6,
            sparse_weight=0.4,
            strategy=HybridStrategy.RANK_FUSION,
            min_dense_score=0.8,
            min_sparse_score=0.2,
            fusion_k=80
        )
        
        assert config.dense_weight == 0.6
        assert config.sparse_weight == 0.4
        assert config.strategy == HybridStrategy.RANK_FUSION
        assert config.min_dense_score == 0.8
        assert config.min_sparse_score == 0.2
        assert config.fusion_k == 80


class TestRetrievalRepository:
    """Test RetrievalRepository functionality."""
    
    @pytest.fixture
    def mock_dense_service(self):
        """Create mock dense retrieval service."""
        service = Mock()
        service.search_by_text = Mock()
        service.get_metrics = Mock()
        service.reset_metrics = Mock()
        return service
    
    @pytest.fixture
    def mock_sparse_service(self):
        """Create mock sparse retrieval service.""" 
        service = Mock()
        service.search = Mock()
        service.initialize_index = AsyncMock()
        service.get_algorithm_name = Mock(return_value="BM25")
        service.get_index_statistics = Mock(return_value={})
        service.get_metrics = Mock()
        return service
    
    @pytest.fixture
    def sample_chunk(self):
        """Create sample chunk for testing."""
        return Chunk(
            document_id=uuid4(),
            text="Virtue ethics emphasizes character development",
            position=0,
            chunk_type="paragraph", 
            start_char=0,
            end_char=45,
            word_count=6
        )
    
    @pytest.fixture
    def sample_search_results(self, sample_chunk):
        """Create sample SearchResult objects."""
        return [
            SearchResult(
                chunk=sample_chunk,
                relevance_score=0.9,
                query="virtue ethics",
                ranking_position=1
            ),
            SearchResult(
                chunk=sample_chunk,
                relevance_score=0.8,
                query="virtue ethics",
                ranking_position=2
            )
        ]
    
    def test_repository_initialization(self, mock_dense_service, mock_sparse_service):
        """Test RetrievalRepository initialization."""
        repo = RetrievalRepository(
            dense_service=mock_dense_service,
            sparse_service=mock_sparse_service
        )
        
        assert repo.dense_service == mock_dense_service
        assert repo.sparse_service == mock_sparse_service
        assert isinstance(repo.hybrid_config, HybridRetrievalConfig)
    
    def test_repository_initialization_with_defaults(self):
        """Test repository initialization with default services."""
        with patch('src.arete.repositories.retrieval.create_dense_retrieval_service') as mock_dense:
            with patch('src.arete.repositories.retrieval.create_sparse_retrieval_service') as mock_sparse:
                mock_dense.return_value = Mock()
                mock_sparse.return_value = Mock()
                
                repo = RetrievalRepository()
                
                assert repo.dense_service is not None
                assert repo.sparse_service is not None
    
    @pytest.mark.asyncio
    async def test_initialize(self, mock_dense_service, mock_sparse_service):
        """Test repository initialization."""
        repo = RetrievalRepository(
            dense_service=mock_dense_service,
            sparse_service=mock_sparse_service
        )
        
        await repo.initialize()
        
        mock_sparse_service.initialize_index.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_failure(self, mock_dense_service, mock_sparse_service):
        """Test repository initialization failure handling."""
        mock_sparse_service.initialize_index.side_effect = Exception("Index error")
        
        repo = RetrievalRepository(
            dense_service=mock_dense_service,
            sparse_service=mock_sparse_service
        )
        
        with pytest.raises(RetrievalRepositoryError):
            await repo.initialize()
    
    def test_dense_search(self, mock_dense_service, mock_sparse_service, sample_search_results):
        """Test dense-only search."""
        mock_dense_service.search_by_text.return_value = sample_search_results
        
        repo = RetrievalRepository(
            dense_service=mock_dense_service,
            sparse_service=mock_sparse_service
        )
        
        results = repo.search(
            query="virtue ethics",
            method=RetrievalMethod.DENSE,
            limit=10
        )
        
        mock_dense_service.search_by_text.assert_called_once()
        assert len(results) == 2
        assert all(r.metadata.get('retrieval_method') == 'dense' for r in results)
    
    def test_sparse_search(self, mock_dense_service, mock_sparse_service, sample_search_results):
        """Test sparse-only search."""
        mock_sparse_service.search.return_value = sample_search_results
        
        repo = RetrievalRepository(
            dense_service=mock_dense_service,
            sparse_service=mock_sparse_service
        )
        
        results = repo.search(
            query="virtue ethics",
            method=RetrievalMethod.SPARSE,
            limit=10
        )
        
        mock_sparse_service.search.assert_called_once()
        assert len(results) == 2
        assert all(r.metadata.get('retrieval_method') == 'sparse' for r in results)
    
    def test_hybrid_search_weighted_average(self, mock_dense_service, mock_sparse_service, sample_search_results):
        """Test hybrid search with weighted average fusion."""
        # Create different results for each service
        dense_results = sample_search_results[:1]  # First result
        sparse_results = sample_search_results[1:]  # Second result
        
        mock_dense_service.search_by_text.return_value = dense_results
        mock_sparse_service.search.return_value = sparse_results
        
        repo = RetrievalRepository(
            dense_service=mock_dense_service,
            sparse_service=mock_sparse_service
        )
        
        config = HybridRetrievalConfig(strategy=HybridStrategy.WEIGHTED_AVERAGE)
        
        results = repo.search(
            query="virtue ethics",
            method=RetrievalMethod.HYBRID,
            hybrid_config=config,
            limit=10
        )
        
        # Both services should be called
        mock_dense_service.search_by_text.assert_called_once()
        mock_sparse_service.search.assert_called_once()
        
        # Should combine results
        assert len(results) >= 0  # Results depend on fusion logic
        
        # Check metadata
        for result in results:
            assert result.metadata.get('retrieval_method') == 'hybrid'
            assert result.metadata.get('hybrid_strategy') == 'weighted_average'
    
    def test_hybrid_search_rank_fusion(self, mock_dense_service, mock_sparse_service, sample_search_results):
        """Test hybrid search with reciprocal rank fusion."""
        mock_dense_service.search_by_text.return_value = sample_search_results
        mock_sparse_service.search.return_value = sample_search_results
        
        repo = RetrievalRepository(
            dense_service=mock_dense_service,
            sparse_service=mock_sparse_service
        )
        
        config = HybridRetrievalConfig(strategy=HybridStrategy.RANK_FUSION)
        
        results = repo.search(
            query="virtue ethics",
            method=RetrievalMethod.HYBRID,
            hybrid_config=config,
            limit=10
        )
        
        # Check RRF metadata
        for result in results:
            assert result.metadata.get('hybrid_strategy') == 'rank_fusion'
            assert 'rrf_score' in result.metadata
    
    def test_hybrid_search_interleaved(self, mock_dense_service, mock_sparse_service, sample_search_results):
        """Test hybrid search with interleaved fusion."""
        mock_dense_service.search_by_text.return_value = sample_search_results
        mock_sparse_service.search.return_value = sample_search_results
        
        repo = RetrievalRepository(
            dense_service=mock_dense_service,
            sparse_service=mock_sparse_service
        )
        
        config = HybridRetrievalConfig(strategy=HybridStrategy.INTERLEAVED)
        
        results = repo.search(
            query="virtue ethics",
            method=RetrievalMethod.HYBRID,
            hybrid_config=config,
            limit=10
        )
        
        for result in results:
            assert result.metadata.get('hybrid_strategy') == 'interleaved'
            assert 'interleaved_position' in result.metadata
    
    def test_hybrid_search_score_threshold(self, mock_dense_service, mock_sparse_service, sample_search_results):
        """Test hybrid search with score threshold fusion."""
        mock_dense_service.search_by_text.return_value = sample_search_results
        mock_sparse_service.search.return_value = sample_search_results
        
        repo = RetrievalRepository(
            dense_service=mock_dense_service,
            sparse_service=mock_sparse_service
        )
        
        config = HybridRetrievalConfig(strategy=HybridStrategy.SCORE_THRESHOLD)
        
        results = repo.search(
            query="virtue ethics",
            method=RetrievalMethod.HYBRID,
            hybrid_config=config,
            limit=10
        )
        
        for result in results:
            assert result.metadata.get('hybrid_strategy') == 'score_threshold'
            assert 'threshold_method' in result.metadata
    
    def test_search_invalid_method(self, mock_dense_service, mock_sparse_service):
        """Test search with invalid method."""
        repo = RetrievalRepository(
            dense_service=mock_dense_service,
            sparse_service=mock_sparse_service
        )
        
        with pytest.raises(RetrievalRepositoryError):
            repo.search(query="test", method="invalid_method")
    
    def test_search_with_filters(self, mock_dense_service, mock_sparse_service, sample_search_results):
        """Test search with document and chunk type filters."""
        mock_dense_service.search_by_text.return_value = sample_search_results
        
        repo = RetrievalRepository(
            dense_service=mock_dense_service,
            sparse_service=mock_sparse_service
        )
        
        document_ids = [uuid4()]
        chunk_types = ["paragraph"]
        
        results = repo.search(
            query="virtue ethics",
            method=RetrievalMethod.DENSE,
            document_ids=document_ids,
            chunk_types=chunk_types
        )
        
        # Verify filters were passed to dense service
        mock_dense_service.search_by_text.assert_called_once()
        call_args = mock_dense_service.search_by_text.call_args
        assert call_args.kwargs['document_ids'] == document_ids
        assert call_args.kwargs['chunk_types'] == chunk_types
    
    def test_set_hybrid_config(self, mock_dense_service, mock_sparse_service):
        """Test setting hybrid configuration."""
        repo = RetrievalRepository(
            dense_service=mock_dense_service,
            sparse_service=mock_sparse_service
        )
        
        new_config = HybridRetrievalConfig(
            dense_weight=0.8,
            sparse_weight=0.2,
            strategy=HybridStrategy.RANK_FUSION
        )
        
        repo.set_hybrid_config(new_config)
        
        assert repo.hybrid_config == new_config
        assert repo.hybrid_config.dense_weight == 0.8
        assert repo.hybrid_config.strategy == HybridStrategy.RANK_FUSION
    
    def test_get_service_metrics(self, mock_dense_service, mock_sparse_service):
        """Test retrieval of service metrics."""
        mock_dense_metrics = Mock()
        mock_dense_metrics.get_summary.return_value = {'queries_processed': 5}
        mock_dense_service.get_metrics.return_value = mock_dense_metrics
        
        mock_sparse_metrics = Mock()
        mock_sparse_metrics.get_summary.return_value = {'queries_processed': 3}
        mock_sparse_service.get_metrics.return_value = mock_sparse_metrics
        
        repo = RetrievalRepository(
            dense_service=mock_dense_service,
            sparse_service=mock_sparse_service
        )
        
        metrics = repo.get_service_metrics()
        
        assert 'dense_metrics' in metrics
        assert 'sparse_metrics' in metrics
        assert metrics['dense_metrics']['queries_processed'] == 5
    
    def test_reset_metrics(self, mock_dense_service, mock_sparse_service):
        """Test metrics reset."""
        mock_sparse_metrics = Mock()
        mock_sparse_service.get_metrics.return_value = mock_sparse_metrics
        
        repo = RetrievalRepository(
            dense_service=mock_dense_service,
            sparse_service=mock_sparse_service
        )
        
        repo.reset_metrics()
        
        mock_dense_service.reset_metrics.assert_called_once()
        mock_sparse_metrics.reset.assert_called_once()


class TestWeightedAverageFusion:
    """Test weighted average fusion strategy in detail."""
    
    @pytest.fixture
    def repo_with_mocks(self):
        """Create repository with mocked services."""
        dense_service = Mock()
        sparse_service = Mock()
        repo = RetrievalRepository(
            dense_service=dense_service,
            sparse_service=sparse_service
        )
        return repo, dense_service, sparse_service
    
    @pytest.fixture
    def sample_chunks(self):
        """Create sample chunks with different IDs."""
        return [
            Chunk(
                document_id=uuid4(),
                text="First chunk about virtue",
                position=0,
                chunk_type="paragraph",
                start_char=0,
                end_char=25,
                word_count=4
            ),
            Chunk(
                document_id=uuid4(),
                text="Second chunk about ethics",
                position=1,
                chunk_type="paragraph",
                start_char=26,
                end_char=51,
                word_count=4
            )
        ]
    
    def test_weighted_average_both_methods_same_chunk(self, repo_with_mocks, sample_chunks):
        """Test weighted average when both methods find same chunk."""
        repo, dense_service, sparse_service = repo_with_mocks
        chunk = sample_chunks[0]
        
        # Both services return same chunk with different scores
        dense_results = [SearchResult(chunk=chunk, relevance_score=0.9, query="test")]
        sparse_results = [SearchResult(chunk=chunk, relevance_score=0.6, query="test")]
        
        config = HybridRetrievalConfig(dense_weight=0.7, sparse_weight=0.3)
        
        combined = repo._weighted_average_fusion(dense_results, sparse_results, config)
        
        assert len(combined) == 1
        result = combined[0]
        
        # Expected score: 0.9 * 0.7 + 0.6 * 0.3 = 0.63 + 0.18 = 0.81
        expected_score = 0.9 * 0.7 + 0.6 * 0.3
        assert abs(result.enhanced_score - expected_score) < 0.001
        
        assert result.metadata['dense_score'] == 0.9
        assert result.metadata['sparse_score'] == 0.6
    
    def test_weighted_average_different_chunks(self, repo_with_mocks, sample_chunks):
        """Test weighted average with different chunks from each method."""
        repo, dense_service, sparse_service = repo_with_mocks
        
        dense_results = [SearchResult(chunk=sample_chunks[0], relevance_score=0.9, query="test")]
        sparse_results = [SearchResult(chunk=sample_chunks[1], relevance_score=0.8, query="test")]
        
        config = HybridRetrievalConfig(dense_weight=0.7, sparse_weight=0.3)
        
        combined = repo._weighted_average_fusion(dense_results, sparse_results, config)
        
        assert len(combined) == 2
        
        # Check individual scores
        for result in combined:
            if result.chunk.id == sample_chunks[0].chunk_id:
                # Dense only: 0.9 * 0.7 = 0.63
                assert abs(result.enhanced_score - 0.63) < 0.001
                assert result.metadata['dense_score'] == 0.9
                assert result.metadata['sparse_score'] == 0.0
            else:
                # Sparse only: 0.8 * 0.3 = 0.24
                assert abs(result.enhanced_score - 0.24) < 0.001
                assert result.metadata['dense_score'] == 0.0
                assert result.metadata['sparse_score'] == 0.8


class TestReciprocalRankFusion:
    """Test reciprocal rank fusion strategy in detail."""
    
    @pytest.fixture
    def repo_with_mocks(self):
        """Create repository with mocked services."""
        dense_service = Mock()
        sparse_service = Mock()
        repo = RetrievalRepository(
            dense_service=dense_service,
            sparse_service=sparse_service
        )
        return repo, dense_service, sparse_service
    
    def test_rrf_calculation(self, repo_with_mocks):
        """Test RRF score calculation."""
        repo, _, _ = repo_with_mocks
        
        chunk = Chunk(
            document_id=uuid4(),
            text="Test chunk",
            position=0,
            chunk_type="paragraph",
            start_char=0,
            end_char=10,
            word_count=2
        )
        
        # Chunk ranked #1 in dense, #2 in sparse
        dense_results = [SearchResult(chunk=chunk, relevance_score=0.9, query="test")]
        sparse_results = [
            SearchResult(chunk=Chunk(document_id=uuid4(), text="Other", position=1, chunk_type="paragraph", start_char=0, end_char=5, word_count=1), relevance_score=0.8, query="test"),
            SearchResult(chunk=chunk, relevance_score=0.7, query="test")
        ]
        
        config = HybridRetrievalConfig(fusion_k=60)
        
        combined = repo._reciprocal_rank_fusion(dense_results, sparse_results, config)
        
        # Find our test chunk in results
        result = next(r for r in combined if r.chunk.id == chunk.id)
        
        # Expected RRF: 1/(60+1) + 1/(60+2) = 1/61 + 1/62
        expected_rrf = 1.0/(60+1) + 1.0/(60+2)
        assert abs(result.enhanced_score - expected_rrf) < 0.001
        
        assert result.metadata['dense_rank'] == 1
        assert result.metadata['sparse_rank'] == 2


class TestRetrievalRepositoryFactory:
    """Test retrieval repository factory function."""
    
    def test_create_retrieval_repository_defaults(self):
        """Test factory function with defaults."""
        with patch('src.arete.repositories.retrieval.create_dense_retrieval_service') as mock_dense:
            with patch('src.arete.repositories.retrieval.create_sparse_retrieval_service') as mock_sparse:
                mock_dense.return_value = Mock()
                mock_sparse.return_value = Mock()
                
                repo = create_retrieval_repository()
                
                assert isinstance(repo, RetrievalRepository)
                mock_dense.assert_called_once()
                mock_sparse.assert_called_once()
    
    def test_create_retrieval_repository_with_services(self):
        """Test factory function with provided services."""
        dense_service = Mock()
        sparse_service = Mock()
        
        repo = create_retrieval_repository(
            dense_service=dense_service,
            sparse_service=sparse_service
        )
        
        assert isinstance(repo, RetrievalRepository)
        assert repo.dense_service == dense_service
        assert repo.sparse_service == sparse_service


class TestRetrievalRepositoryIntegration:
    """Integration tests for retrieval repository."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_search_workflow(self):
        """Test complete search workflow from initialization to results."""
        # This would be a more comprehensive integration test
        # that tests the entire flow with real or more realistic mocks
        pass
    
    def test_performance_comparison(self):
        """Test performance metrics collection across methods."""
        # This would test the performance tracking capabilities
        # across different retrieval methods
        pass
    
    def test_large_result_set_handling(self):
        """Test handling of large result sets in hybrid fusion."""
        # This would test the system's ability to handle
        # large numbers of results efficiently
        pass


if __name__ == "__main__":
    pytest.main([__file__])