"""
Tests for Context Composition Engine.

Tests the intelligent context composition system that prepares
search results for LLM consumption with token limit management,
passage stitching, and citation integration.
"""

import pytest
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from unittest.mock import Mock, MagicMock, patch

from src.arete.services.context_composition_service import (
    ContextCompositionService,
    ContextCompositionConfig,
    CompositionStrategy,
    ContextResult,
    PassageGroup,
    CitationContext,
    ContextCompositionError
)
from src.arete.services.dense_retrieval_service import SearchResult
from src.arete.models.chunk import Chunk, ChunkType
from src.arete.models.citation import Citation, CitationType, CitationContext as CitationContextEnum


class TestContextCompositionService:
    """Test suite for ContextCompositionService."""

    @pytest.fixture
    def sample_chunks(self) -> List[Chunk]:
        """Create sample chunks for testing."""
        return [
            Chunk(
                text="In the Republic, Plato presents the allegory of the cave to illustrate the nature of knowledge.",
                document_id=uuid4(),
                position=0,
                start_char=0,
                end_char=89,
                chunk_type=ChunkType.PARAGRAPH,
                metadata={"author": "Plato", "work": "Republic", "section": "514a"}
            ),
            Chunk(
                text="The prisoners in the cave mistake shadows for reality until one is freed.",
                document_id=uuid4(),
                position=1,
                start_char=90,
                end_char=164,
                chunk_type=ChunkType.SENTENCE,
                metadata={"author": "Plato", "work": "Republic", "section": "514b"}
            ),
            Chunk(
                text="This allegory demonstrates Plato's theory of Forms and the philosopher's journey to truth.",
                document_id=uuid4(),
                position=2,
                start_char=165,
                end_char=252,
                chunk_type=ChunkType.SENTENCE,
                metadata={"author": "Plato", "work": "Republic", "section": "515a"}
            )
        ]

    @pytest.fixture
    def sample_citations(self) -> List[Citation]:
        """Create sample citations for testing."""
        return [
            Citation(
                text="In the Republic, Plato presents the allegory of the cave",
                citation_type=CitationType.DIRECT_QUOTE,
                document_id=uuid4(),
                source_title="Republic",
                source_author="Plato",
                source_reference="Republic 514a",
                confidence_score=0.95,
                chunk_id=uuid4()
            ),
            Citation(
                text="The prisoners mistake shadows for reality",
                citation_type=CitationType.PARAPHRASE,
                document_id=uuid4(),
                source_title="Republic",
                source_author="Plato",
                source_reference="Republic 514b",
                confidence_score=0.88,
                chunk_id=uuid4()
            )
        ]

    @pytest.fixture
    def sample_search_results(self, sample_chunks) -> List[SearchResult]:
        """Create sample search results for testing."""
        return [
            SearchResult(
                chunk=sample_chunks[0],
                relevance_score=0.95,
                query="cave allegory",
                enhanced_score=0.92,
                metadata={"retrieval_method": "hybrid", "domain_boost": 0.1}
            ),
            SearchResult(
                chunk=sample_chunks[1],
                relevance_score=0.87,
                query="cave allegory",
                enhanced_score=0.85,
                metadata={"retrieval_method": "dense", "semantic_similarity": 0.89}
            ),
            SearchResult(
                chunk=sample_chunks[2],
                relevance_score=0.82,
                query="cave allegory",
                enhanced_score=0.80,
                metadata={"retrieval_method": "sparse", "term_match": 0.75}
            )
        ]

    @pytest.fixture
    def composition_service(self) -> ContextCompositionService:
        """Create a ContextCompositionService instance for testing."""
        return ContextCompositionService()

    @pytest.fixture
    def composition_config(self) -> ContextCompositionConfig:
        """Create a test configuration."""
        return ContextCompositionConfig(
            max_tokens=5000,
            strategy=CompositionStrategy.INTELLIGENT_STITCHING,
            overlap_threshold=0.3,
            citation_format="classical",
            include_metadata=True,
            preserve_context=True
        )

    def test_service_initialization(self, composition_service):
        """Test service initialization with default configuration."""
        assert composition_service is not None
        assert composition_service.config.max_tokens == 5000
        assert composition_service.config.strategy == CompositionStrategy.INTELLIGENT_STITCHING

    def test_service_initialization_with_custom_config(self):
        """Test service initialization with custom configuration."""
        config = ContextCompositionConfig(
            max_tokens=3000,
            strategy=CompositionStrategy.MAP_REDUCE,
            overlap_threshold=0.5
        )
        service = ContextCompositionService(config=config)
        
        assert service.config.max_tokens == 3000
        assert service.config.strategy == CompositionStrategy.MAP_REDUCE
        assert service.config.overlap_threshold == 0.5

    def test_token_counting_basic(self, composition_service):
        """Test basic token counting functionality."""
        text = "This is a simple test sentence with multiple words."
        token_count = composition_service.count_tokens(text)
        
        # Should be approximately the word count * tokens_per_word (rough estimation)
        word_count = len(text.split())
        expected_range = (word_count, int(word_count * 2))  # Allow for tokens_per_word multiplier
        
        assert isinstance(token_count, int)
        assert token_count > 0
        assert expected_range[0] <= token_count <= expected_range[1]

    def test_token_counting_empty_text(self, composition_service):
        """Test token counting with empty text."""
        assert composition_service.count_tokens("") == 0
        assert composition_service.count_tokens("   ") == 0

    def test_compose_context_basic(self, composition_service, sample_search_results, composition_config):
        """Test basic context composition."""
        result = composition_service.compose_context(
            search_results=sample_search_results,
            query="cave allegory",
            config=composition_config
        )
        
        assert isinstance(result, ContextResult)
        assert result.composed_text is not None
        assert result.total_tokens > 0
        assert result.total_tokens <= composition_config.max_tokens
        assert len(result.passage_groups) > 0
        assert result.query == "cave allegory"

    def test_compose_context_with_citations(self, composition_service, sample_search_results, sample_citations, composition_config):
        """Test context composition with citation integration."""
        result = composition_service.compose_context(
            search_results=sample_search_results,
            query="cave allegory",
            citations=sample_citations,
            config=composition_config
        )
        
        assert isinstance(result, ContextResult)
        assert len(result.citations) > 0
        assert any("Republic 514a" in citation.formatted_citation for citation in result.citations)

    def test_compose_context_token_limit_enforcement(self, composition_service, sample_search_results):
        """Test that token limit is strictly enforced."""
        # Set a very low token limit
        config = ContextCompositionConfig(max_tokens=10)
        
        result = composition_service.compose_context(
            search_results=sample_search_results,
            query="cave allegory",
            config=config
        )
        
        assert result.total_tokens <= 10
        assert result.truncated is True

    def test_compose_context_empty_results(self, composition_service, composition_config):
        """Test context composition with empty search results."""
        result = composition_service.compose_context(
            search_results=[],
            query="empty query",
            config=composition_config
        )
        
        assert isinstance(result, ContextResult)
        assert result.composed_text == ""
        assert result.total_tokens == 0
        assert len(result.passage_groups) == 0

    def test_intelligent_stitching_strategy(self, composition_service, sample_search_results):
        """Test intelligent stitching composition strategy."""
        config = ContextCompositionConfig(
            strategy=CompositionStrategy.INTELLIGENT_STITCHING,
            overlap_threshold=0.3
        )
        
        result = composition_service.compose_context(
            search_results=sample_search_results,
            query="cave allegory",
            config=config
        )
        
        # Should create coherent passage groups
        assert len(result.passage_groups) > 0
        for group in result.passage_groups:
            assert isinstance(group, PassageGroup)
            assert len(group.chunks) > 0
            assert group.coherence_score >= 0.0

    def test_map_reduce_strategy(self, composition_service, sample_search_results):
        """Test Map-Reduce composition strategy for long contexts."""
        # Create many search results to trigger map-reduce
        extended_results = sample_search_results * 10  # Create 30 results
        
        config = ContextCompositionConfig(
            strategy=CompositionStrategy.MAP_REDUCE,
            max_tokens=2000
        )
        
        result = composition_service.compose_context(
            search_results=extended_results,
            query="cave allegory",
            config=config
        )
        
        assert result.total_tokens <= 2000
        assert result.strategy_used == CompositionStrategy.MAP_REDUCE
        assert len(result.passage_groups) > 0

    def test_overlap_detection_and_removal(self, composition_service, sample_search_results):
        """Test detection and removal of overlapping content."""
        # Add duplicate content to trigger overlap detection
        duplicate_result = SearchResult(
            chunk=sample_search_results[0].chunk,  # Same chunk as first result
            relevance_score=0.80,
            query="cave allegory",
            enhanced_score=0.78
        )
        
        results_with_overlap = sample_search_results + [duplicate_result]
        
        config = ContextCompositionConfig(overlap_threshold=0.8)
        
        result = composition_service.compose_context(
            search_results=results_with_overlap,
            query="cave allegory",
            config=config
        )
        
        # Should detect and handle overlapping content
        assert result.overlaps_detected > 0
        assert len(result.passage_groups) == len(sample_search_results)  # No duplicates

    def test_citation_formatting_classical(self, composition_service, sample_search_results, sample_citations):
        """Test classical citation formatting."""
        config = ContextCompositionConfig(citation_format="classical")
        
        result = composition_service.compose_context(
            search_results=sample_search_results,
            query="cave allegory",
            citations=sample_citations,
            config=config
        )
        
        # Should format citations in classical format
        formatted_citations = [c.formatted_citation for c in result.citations]
        assert any("Republic 514a" in citation for citation in formatted_citations)
        assert all("Republic" in citation for citation in formatted_citations if citation)

    def test_citation_formatting_modern(self, composition_service, sample_search_results, sample_citations):
        """Test modern citation formatting."""
        config = ContextCompositionConfig(citation_format="modern")
        
        result = composition_service.compose_context(
            search_results=sample_search_results,
            query="cave allegory",
            citations=sample_citations,
            config=config
        )
        
        # Should format citations in modern format
        formatted_citations = [c.formatted_citation for c in result.citations]
        assert len(formatted_citations) > 0

    def test_metadata_preservation(self, composition_service, sample_search_results):
        """Test preservation of important metadata."""
        config = ContextCompositionConfig(include_metadata=True)
        
        result = composition_service.compose_context(
            search_results=sample_search_results,
            query="cave allegory",
            config=config
        )
        
        # Should preserve important metadata
        assert result.metadata is not None
        assert "retrieval_methods" in result.metadata
        assert "composition_stats" in result.metadata

    def test_performance_metrics_collection(self, composition_service, sample_search_results, composition_config):
        """Test performance metrics collection."""
        result = composition_service.compose_context(
            search_results=sample_search_results,
            query="cave allegory",
            config=composition_config
        )
        
        assert result.composition_time >= 0  # Allow zero time for fast operations
        assert result.performance_metrics is not None
        assert "token_efficiency" in result.performance_metrics
        assert isinstance(result.performance_metrics["token_efficiency"], float)

    def test_error_handling_invalid_search_results(self, composition_service, composition_config):
        """Test error handling with invalid search results."""
        invalid_results = [None, "invalid", 123]
        
        with pytest.raises(ContextCompositionError):
            composition_service.compose_context(
                search_results=invalid_results,
                query="test query",
                config=composition_config
            )

    def test_error_handling_invalid_config(self, composition_service, sample_search_results):
        """Test error handling with invalid configuration."""
        with pytest.raises(ValueError):  # ContextCompositionConfig validation should raise ValueError
            ContextCompositionConfig(max_tokens=-100)

    def test_caching_functionality(self, composition_service, sample_search_results, composition_config):
        """Test caching of composition results."""
        # First composition
        result1 = composition_service.compose_context(
            search_results=sample_search_results,
            query="cave allegory",
            config=composition_config
        )
        
        # Second composition with same inputs (should hit cache)
        result2 = composition_service.compose_context(
            search_results=sample_search_results,
            query="cave allegory",
            config=composition_config
        )
        
        # Results should be identical due to caching
        assert result1.composed_text == result2.composed_text
        assert result1.total_tokens == result2.total_tokens

    def test_batch_processing_capability(self, composition_service):
        """Test batch processing of multiple queries."""
        queries = ["cave allegory", "forms theory", "philosopher king"]
        
        # Mock multiple search result sets
        batch_results = []
        for query in queries:
            mock_results = [Mock(spec=SearchResult) for _ in range(3)]
            for i, mock_result in enumerate(mock_results):
                mock_result.chunk = Mock(spec=Chunk)
                mock_result.chunk.text = f"Test text for {query} result {i}"
                mock_result.relevance_score = 0.8 - (i * 0.1)
                mock_result.query = query
            batch_results.append(mock_results)
        
        config = ContextCompositionConfig(max_tokens=1000)
        
        # Process batch
        results = composition_service.compose_context_batch(
            search_results_list=batch_results,
            queries=queries,
            config=config
        )
        
        assert len(results) == len(queries)
        for result in results:
            assert isinstance(result, ContextResult)
            assert result.total_tokens <= 1000


class TestPassageGroup:
    """Test suite for PassageGroup model."""

    def test_passage_group_creation(self):
        """Test PassageGroup creation with basic data."""
        chunks = []
        for i in range(2):
            chunk = Mock(spec=Chunk)
            chunk.text = f"Test chunk {i} with some content for token counting."
            chunks.append(chunk)
        
        group = PassageGroup(
            chunks=chunks,
            coherence_score=0.85,
            topic="Plato's Cave",
            start_position=0,
            end_position=100
        )
        
        assert len(group.chunks) == 2
        assert group.coherence_score == 0.85
        assert group.topic == "Plato's Cave"
        assert group.token_count > 0

    def test_passage_group_text_composition(self):
        """Test text composition from chunks."""
        mock_chunks = []
        for i in range(3):
            chunk = Mock(spec=Chunk)
            chunk.text = f"Sentence {i+1} about philosophy."
            mock_chunks.append(chunk)
        
        group = PassageGroup(
            chunks=mock_chunks,
            coherence_score=0.8,
            topic="Philosophy"
        )
        
        composed_text = group.get_composed_text()
        assert "Sentence 1" in composed_text
        assert "Sentence 2" in composed_text
        assert "Sentence 3" in composed_text


class TestCitationContext:
    """Test suite for CitationContext model."""

    def test_citation_context_creation(self):
        """Test CitationContext creation."""
        citation = Mock(spec=Citation)
        citation.source_reference = "Republic 514a"
        citation.citation_type = CitationType.DIRECT_QUOTE
        
        context = CitationContext(
            citation=citation,
            formatted_citation="Plato, Republic 514a",
            context_relevance=0.92,
            position_in_text=45
        )
        
        assert context.citation == citation
        assert context.formatted_citation == "Plato, Republic 514a"
        assert context.context_relevance == 0.92
        assert context.position_in_text == 45


class TestContextCompositionConfig:
    """Test suite for ContextCompositionConfig."""

    def test_config_default_values(self):
        """Test default configuration values."""
        config = ContextCompositionConfig()
        
        assert config.max_tokens == 5000
        assert config.strategy == CompositionStrategy.INTELLIGENT_STITCHING
        assert config.overlap_threshold == 0.3
        assert config.citation_format == "classical"
        assert config.include_metadata is True
        assert config.preserve_context is True

    def test_config_validation(self):
        """Test configuration validation."""
        # Valid config
        config = ContextCompositionConfig(
            max_tokens=1000,
            overlap_threshold=0.5
        )
        assert config.max_tokens == 1000
        
        # Invalid config should raise error
        with pytest.raises(ValueError):
            ContextCompositionConfig(max_tokens=-100)
        
        with pytest.raises(ValueError):
            ContextCompositionConfig(overlap_threshold=1.5)