"""
Tests for dense retrieval system.

This module tests the semantic similarity search capabilities for the RAG system,
building on the EmbeddingRepository foundation to provide comprehensive retrieval
with ranking, scoring, and result optimization.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4, UUID
from typing import List, Tuple, Dict, Any

from src.arete.services.dense_retrieval_service import (
    DenseRetrievalService,
    DenseRetrievalError,
    QueryProcessingError,
    RankingError,
    SearchResult,
    RetrievalMetrics
)
from src.arete.models.chunk import Chunk, ChunkType
from src.arete.models.document import Document
from src.arete.repositories.embedding import EmbeddingRepository
from src.arete.config import Settings


class TestDenseRetrievalService:
    """Test suite for DenseRetrievalService."""

    @pytest.fixture
    def mock_embedding_repository(self):
        """Create a mock embedding repository."""
        mock_repo = Mock(spec=EmbeddingRepository)
        mock_repo.search_by_text.return_value = []
        mock_repo.search_by_vector.return_value = []
        mock_repo.embedding_service.generate_embedding.return_value = [0.1] * 768
        return mock_repo

    @pytest.fixture
    def sample_chunks(self):
        """Create sample chunks for testing."""
        doc_id = uuid4()
        chunks = []
        
        for i in range(5):
            chunk = Chunk(
                text=f"This is sample philosophical text {i} about virtue and ethics.",
                chunk_type=ChunkType.PARAGRAPH,
                document_id=doc_id,
                position=i,
                start_char=i * 100,
                end_char=(i + 1) * 100 - 1,
                word_count=10,
                embedding_vector=[0.1 + i * 0.1] * 768
            )
            chunks.append(chunk)
        
        return chunks

    @pytest.fixture
    def retrieval_service(self, mock_embedding_repository):
        """Create DenseRetrievalService instance."""
        settings = Settings()
        return DenseRetrievalService(
            embedding_repository=mock_embedding_repository,
            settings=settings
        )

    def test_service_initialization(self, mock_embedding_repository):
        """Test proper service initialization."""
        settings = Settings()
        service = DenseRetrievalService(
            embedding_repository=mock_embedding_repository,
            settings=settings
        )
        
        assert service.embedding_repository == mock_embedding_repository
        assert service.settings == settings
        assert isinstance(service.metrics, RetrievalMetrics)
        assert service.metrics.queries_processed == 0

    def test_service_initialization_with_defaults(self):
        """Test service initialization with default parameters."""
        with patch('src.arete.services.dense_retrieval_service.create_embedding_repository') as mock_create:
            mock_repo = Mock(spec=EmbeddingRepository)
            mock_create.return_value = mock_repo
            
            service = DenseRetrievalService()
            
            assert service.embedding_repository == mock_repo
            assert service.settings is not None
            mock_create.assert_called_once()

    def test_query_preprocessing_basic(self, retrieval_service):
        """Test basic query preprocessing and normalization."""
        # Test basic text cleaning
        query = "  What is virtue according to Aristotle?  "
        processed = retrieval_service._preprocess_query(query)
        
        assert processed == "What is virtue according to Aristotle?"
        assert processed.strip() == processed
        
        # Test empty query handling
        empty_processed = retrieval_service._preprocess_query("   ")
        assert empty_processed == ""

    def test_query_preprocessing_philosophical_terms(self, retrieval_service):
        """Test preprocessing of philosophical terminology."""
        # Test philosophical term normalization
        query = "What is Eudaimonia and how does it relate to the Good Life?"
        processed = retrieval_service._preprocess_query(query)
        
        # Should preserve philosophical terms
        assert "Eudaimonia" in processed
        assert "Good Life" in processed
        
        # Test Greek term handling
        greek_query = "Explain ἀρετή (arete) in Aristotelian ethics"
        processed_greek = retrieval_service._preprocess_query(greek_query)
        
        assert "ἀρετή" in processed_greek
        assert "arete" in processed_greek

    def test_semantic_search_by_text(self, retrieval_service, sample_chunks):
        """Test semantic search using text queries."""
        query = "virtue ethics"
        expected_results = [
            (sample_chunks[0], 0.95),
            (sample_chunks[1], 0.87),
            (sample_chunks[2], 0.82)
        ]
        
        retrieval_service.embedding_repository.search_by_text.return_value = expected_results
        
        results = retrieval_service.search_by_text(
            query=query,
            limit=3,
            min_relevance=0.8
        )
        
        assert len(results) == 3
        assert all(isinstance(result, SearchResult) for result in results)
        
        # Check first result
        assert results[0].chunk == sample_chunks[0]
        assert results[0].relevance_score == 0.95
        assert results[0].query == query
        
        # Verify repository call
        retrieval_service.embedding_repository.search_by_text.assert_called_once_with(
            query_text=query,
            limit=3,
            min_certainty=0.8,
            document_ids=None,
            chunk_types=None
        )

    def test_semantic_search_with_filters(self, retrieval_service, sample_chunks):
        """Test semantic search with document and chunk type filters."""
        query = "Aristotelian ethics"
        doc_ids = [sample_chunks[0].document_id]
        chunk_types = ["paragraph", "section"]
        
        retrieval_service.embedding_repository.search_by_text.return_value = [
            (sample_chunks[0], 0.92)
        ]
        
        results = retrieval_service.search_by_text(
            query=query,
            limit=5,
            min_relevance=0.7,
            document_ids=doc_ids,
            chunk_types=chunk_types
        )
        
        assert len(results) == 1
        
        retrieval_service.embedding_repository.search_by_text.assert_called_once_with(
            query_text=query,
            limit=5,
            min_certainty=0.7,
            document_ids=doc_ids,
            chunk_types=chunk_types
        )

    def test_search_result_ranking(self, retrieval_service, sample_chunks):
        """Test result ranking and scoring algorithms."""
        # Create results with different scores
        repository_results = [
            (sample_chunks[0], 0.95),
            (sample_chunks[1], 0.82),
            (sample_chunks[2], 0.87),
            (sample_chunks[3], 0.79),
            (sample_chunks[4], 0.91)
        ]
        
        retrieval_service.embedding_repository.search_by_text.return_value = repository_results
        
        results = retrieval_service.search_by_text(
            query="philosophical concepts",
            limit=10,
            min_relevance=0.75
        )
        
        # Results should be sorted by relevance score (descending)
        assert len(results) == 5
        scores = [result.relevance_score for result in results]
        assert scores == sorted(scores, reverse=True)
        
        # Check specific ordering
        assert results[0].relevance_score == 0.95  # sample_chunks[0]
        assert results[1].relevance_score == 0.91  # sample_chunks[4]
        assert results[2].relevance_score == 0.87  # sample_chunks[2]
        assert results[3].relevance_score == 0.82  # sample_chunks[1]
        assert results[4].relevance_score == 0.79  # sample_chunks[3]

    def test_search_result_filtering_by_threshold(self, retrieval_service, sample_chunks):
        """Test filtering results by minimum relevance threshold."""
        repository_results = [
            (sample_chunks[0], 0.95),
            (sample_chunks[1], 0.82),
            (sample_chunks[2], 0.72),  # Below threshold
            (sample_chunks[3], 0.68),  # Below threshold
        ]
        
        retrieval_service.embedding_repository.search_by_text.return_value = repository_results
        
        results = retrieval_service.search_by_text(
            query="ethics",
            limit=10,
            min_relevance=0.75
        )
        
        # Only results above threshold should be returned
        assert len(results) == 2
        assert all(result.relevance_score >= 0.75 for result in results)

    def test_relevance_score_enhancement(self, retrieval_service, sample_chunks):
        """Test relevance score enhancement algorithms."""
        repository_results = [
            (sample_chunks[0], 0.85),
            (sample_chunks[1], 0.80),
        ]
        
        retrieval_service.embedding_repository.search_by_text.return_value = repository_results
        
        # Mock the enhancement calculation
        with patch.object(retrieval_service, '_enhance_relevance_score') as mock_enhance:
            mock_enhance.side_effect = lambda chunk, base_score, query: base_score * 1.1
            
            results = retrieval_service.search_by_text(
                query="virtue",
                enhance_scores=True
            )
            
            # Scores should be enhanced
            assert results[0].relevance_score == pytest.approx(0.935, rel=1e-3)  # 0.85 * 1.1
            assert results[1].relevance_score == pytest.approx(0.88, rel=1e-3)   # 0.80 * 1.1
            
            assert mock_enhance.call_count == 2

    def test_search_with_context_window(self, retrieval_service, sample_chunks):
        """Test search with context window expansion."""
        # Set up chunks with sequential positions
        for i, chunk in enumerate(sample_chunks):
            chunk.position = i
            chunk.start_char = i * 100
            chunk.end_char = (i + 1) * 100 - 1
        
        repository_results = [(sample_chunks[2], 0.88)]  # Middle chunk
        retrieval_service.embedding_repository.search_by_text.return_value = repository_results
        
        results = retrieval_service.search_by_text(
            query="philosophical analysis",
            expand_context=True,
            context_window=1
        )
        
        # Should include the main result
        assert len(results) >= 1
        assert results[0].chunk == sample_chunks[2]

    def test_batch_search_multiple_queries(self, retrieval_service, sample_chunks):
        """Test batch processing of multiple search queries."""
        queries = [
            "What is virtue?",
            "Explain Aristotelian ethics",
            "Define eudaimonia"
        ]
        
        # Mock different results for each query
        def mock_search_side_effect(query_text, **kwargs):
            if "virtue" in query_text:
                return [(sample_chunks[0], 0.92)]
            elif "Aristotelian" in query_text:
                return [(sample_chunks[1], 0.89)]
            elif "eudaimonia" in query_text:
                return [(sample_chunks[2], 0.95)]
            return []
        
        retrieval_service.embedding_repository.search_by_text.side_effect = mock_search_side_effect
        
        batch_results = retrieval_service.batch_search(queries, limit=5)
        
        assert len(batch_results) == 3
        assert len(batch_results[queries[0]]) == 1
        assert len(batch_results[queries[1]]) == 1
        assert len(batch_results[queries[2]]) == 1
        
        # Check specific results
        assert batch_results[queries[0]][0].relevance_score == 0.92
        assert batch_results[queries[2]][0].relevance_score == 0.95

    def test_search_metrics_tracking(self, retrieval_service, sample_chunks):
        """Test metrics tracking for search operations."""
        initial_queries = retrieval_service.metrics.queries_processed
        initial_results = retrieval_service.metrics.total_results_returned
        
        retrieval_service.embedding_repository.search_by_text.return_value = [
            (sample_chunks[0], 0.95),
            (sample_chunks[1], 0.88)
        ]
        
        # Perform searches
        retrieval_service.search_by_text("test query 1")
        retrieval_service.search_by_text("test query 2")
        
        # Check metrics
        assert retrieval_service.metrics.queries_processed == initial_queries + 2
        assert retrieval_service.metrics.total_results_returned == initial_results + 4
        assert retrieval_service.metrics.average_relevance_score > 0

    def test_error_handling_repository_failure(self, retrieval_service):
        """Test error handling when repository search fails."""
        retrieval_service.embedding_repository.search_by_text.side_effect = Exception("Repository error")
        
        with pytest.raises(DenseRetrievalError) as exc_info:
            retrieval_service.search_by_text("test query")
        
        assert "Dense retrieval failed" in str(exc_info.value)
        assert "Repository error" in str(exc_info.value)

    def test_error_handling_empty_query(self, retrieval_service):
        """Test error handling for empty or invalid queries."""
        with pytest.raises(QueryProcessingError) as exc_info:
            retrieval_service.search_by_text("")
        
        assert "Query cannot be empty" in str(exc_info.value)
        
        with pytest.raises(QueryProcessingError) as exc_info:
            retrieval_service.search_by_text("   ")
        
        assert "Query cannot be empty" in str(exc_info.value)

    def test_error_handling_invalid_parameters(self, retrieval_service):
        """Test error handling for invalid search parameters."""
        with pytest.raises(ValueError) as exc_info:
            retrieval_service.search_by_text("test", limit=-1)
        
        assert "Limit must be positive" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            retrieval_service.search_by_text("test", min_relevance=-0.1)
        
        assert "min_relevance must be between 0 and 1" in str(exc_info.value)

    def test_search_result_model_creation(self):
        """Test SearchResult model creation and validation."""
        chunk = Chunk(
            text="Sample text",
            chunk_type=ChunkType.PARAGRAPH,
            document_id=uuid4(),
            position=1,
            start_char=0,
            end_char=50,
            word_count=2
        )
        
        result = SearchResult(
            chunk=chunk,
            relevance_score=0.85,
            query="test query",
            enhanced_score=0.92,
            ranking_position=1,
            metadata={"source": "test"}
        )
        
        assert result.chunk == chunk
        assert result.relevance_score == 0.85
        assert result.query == "test query"
        assert result.enhanced_score == 0.92
        assert result.ranking_position == 1
        assert result.metadata["source"] == "test"

    def test_retrieval_metrics_model(self):
        """Test RetrievalMetrics model and calculations."""
        metrics = RetrievalMetrics()
        
        # Initial state
        assert metrics.queries_processed == 0
        assert metrics.total_results_returned == 0
        assert metrics.average_relevance_score == 0.0
        assert metrics.average_response_time == 0.0
        
        # Update metrics
        metrics.update_query_metrics(
            results_count=3,
            avg_relevance=0.87,
            response_time=0.123
        )
        
        assert metrics.queries_processed == 1
        assert metrics.total_results_returned == 3
        assert metrics.average_relevance_score == 0.87
        assert metrics.average_response_time == 0.123
        
        # Update with second query
        metrics.update_query_metrics(
            results_count=2,
            avg_relevance=0.93,
            response_time=0.098
        )
        
        assert metrics.queries_processed == 2
        assert metrics.total_results_returned == 5
        # Average relevance should be weighted by results count
        expected_avg_relevance = (0.87 * 3 + 0.93 * 2) / 5
        assert metrics.average_relevance_score == pytest.approx(expected_avg_relevance, rel=1e-3)

    def test_search_with_custom_scoring(self, retrieval_service, sample_chunks):
        """Test search with custom scoring functions."""
        repository_results = [
            (sample_chunks[0], 0.85),
            (sample_chunks[1], 0.80),
        ]
        
        retrieval_service.embedding_repository.search_by_text.return_value = repository_results
        
        def custom_scorer(chunk: Chunk, base_score: float, query: str) -> float:
            # Boost scores for chunks containing "virtue"
            if "virtue" in chunk.text.lower():
                return base_score * 1.2
            return base_score
        
        results = retrieval_service.search_by_text(
            query="ethical concepts",
            custom_scorer=custom_scorer
        )
        
        # Check that custom scoring was applied
        assert len(results) == 2
        # Assuming sample_chunks contain "virtue" - scores should be boosted
        for result in results:
            if "virtue" in result.chunk.text.lower():
                assert result.enhanced_score > result.relevance_score


class TestSearchResultDataStructures:
    """Test the data structures used in search results."""

    def test_search_result_serialization(self):
        """Test SearchResult serialization for caching/storage."""
        chunk = Chunk(
            text="Philosophical text",
            chunk_type=ChunkType.PARAGRAPH,
            document_id=uuid4(),
            position=1,
            start_char=0,
            end_char=50,
            word_count=2
        )
        
        result = SearchResult(
            chunk=chunk,
            relevance_score=0.88,
            query="philosophy"
        )
        
        # Test dict conversion
        result_dict = result.model_dump()
        assert "chunk" in result_dict
        assert "relevance_score" in result_dict
        assert "query" in result_dict
        
        # Test round-trip serialization
        reconstructed = SearchResult.model_validate(result_dict)
        assert reconstructed.relevance_score == result.relevance_score
        assert reconstructed.query == result.query

    def test_metrics_aggregation(self):
        """Test metrics aggregation across multiple queries."""
        metrics = RetrievalMetrics()
        
        # Simulate multiple search operations
        search_data = [
            (5, 0.92, 0.125),  # results_count, avg_relevance, response_time
            (3, 0.88, 0.098),
            (7, 0.95, 0.156),
            (2, 0.83, 0.087)
        ]
        
        for results_count, avg_relevance, response_time in search_data:
            metrics.update_query_metrics(results_count, avg_relevance, response_time)
        
        assert metrics.queries_processed == 4
        assert metrics.total_results_returned == 17
        
        # Calculate expected weighted average relevance
        total_relevance_sum = (5 * 0.92) + (3 * 0.88) + (7 * 0.95) + (2 * 0.83)
        expected_avg_relevance = total_relevance_sum / 17
        assert metrics.average_relevance_score == pytest.approx(expected_avg_relevance, rel=1e-3)
        
        # Calculate expected average response time
        expected_avg_time = (0.125 + 0.098 + 0.156 + 0.087) / 4
        assert metrics.average_response_time == pytest.approx(expected_avg_time, rel=1e-3)


if __name__ == "__main__":
    pytest.main([__file__])