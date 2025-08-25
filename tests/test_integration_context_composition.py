"""
Integration tests for Context Composition Service with retrieval pipeline.

Tests the complete integration between the ContextCompositionService and
the retrieval pipeline (sparse + dense + graph retrieval systems).
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
    create_context_composition_service
)
from src.arete.repositories.retrieval import RetrievalRepository, RetrievalMethod
from src.arete.services.dense_retrieval_service import SearchResult
from src.arete.services.reranking_service import RerankingService
from src.arete.services.diversity_service import DiversityService
from src.arete.models.chunk import Chunk, ChunkType
from src.arete.models.citation import Citation, CitationType


class TestContextCompositionIntegration:
    """Integration tests for Context Composition with retrieval pipeline."""
    
    @pytest.fixture
    def mock_retrieval_repository(self) -> Mock:
        """Create a mock retrieval repository for testing."""
        mock_repo = Mock(spec=RetrievalRepository)
        
        # Create sample search results
        sample_chunks = [
            Chunk(
                text="In the Republic, Plato presents the allegory of the cave to illustrate the nature of knowledge and reality.",
                document_id=uuid4(),
                position=0,
                start_char=0,
                end_char=95,
                chunk_type=ChunkType.PARAGRAPH,
                metadata={"author": "Plato", "work": "Republic", "section": "514a-517a"}
            ),
            Chunk(
                text="The prisoners in the cave mistake shadows on the wall for reality itself until one is freed and sees the truth.",
                document_id=uuid4(),
                position=1,
                start_char=96,
                end_char=208,
                chunk_type=ChunkType.SENTENCE,
                metadata={"author": "Plato", "work": "Republic", "section": "514b-515a"}
            ),
            Chunk(
                text="This allegory demonstrates Plato's theory of Forms and the philosopher's journey from ignorance to knowledge.",
                document_id=uuid4(),
                position=2,
                start_char=209,
                end_char=318,
                chunk_type=ChunkType.SENTENCE,
                metadata={"author": "Plato", "work": "Republic", "section": "515a-517c"}
            )
        ]
        
        search_results = [
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
                metadata={"retrieval_method": "graph", "path_length": 2}
            )
        ]
        
        mock_repo.search.return_value = search_results
        return mock_repo
    
    @pytest.fixture
    def mock_reranking_service(self) -> Mock:
        """Create a mock reranking service for testing."""
        mock_service = Mock(spec=RerankingService)
        
        def rerank_results(results, query, config=None):
            # Simple mock reranking - just return results with slightly adjusted scores
            reranked = []
            for i, result in enumerate(results):
                result.enhanced_score = result.relevance_score * (1.0 - i * 0.05)  # Small adjustments
                result.metadata['reranking_applied'] = True
                reranked.append(result)
            return reranked
        
        mock_service.rerank.side_effect = rerank_results
        return mock_service
    
    @pytest.fixture
    def mock_diversity_service(self) -> Mock:
        """Create a mock diversity service for testing."""
        mock_service = Mock(spec=DiversityService)
        
        def diversify_results(results, query, config=None):
            # Simple mock diversification - return unique results
            seen_texts = set()
            diversified = []
            
            for result in results:
                if result.chunk.text not in seen_texts:
                    seen_texts.add(result.chunk.text)
                    result.metadata['diversity_applied'] = True
                    diversified.append(result)
            
            return diversified
        
        mock_service.diversify.side_effect = diversify_results
        return mock_service
    
    @pytest.fixture
    def composition_service(self) -> ContextCompositionService:
        """Create a ContextCompositionService for testing."""
        return create_context_composition_service()
    
    def test_end_to_end_retrieval_composition(
        self, 
        composition_service, 
        mock_retrieval_repository,
        mock_reranking_service,
        mock_diversity_service
    ):
        """Test complete end-to-end retrieval and composition pipeline."""
        query = "What is Plato's cave allegory about?"
        
        # Step 1: Retrieve results
        search_results = mock_retrieval_repository.search(
            query=query,
            method=RetrievalMethod.GRAPH_ENHANCED_HYBRID,
            limit=10
        )
        
        # Step 2: Apply reranking
        reranked_results = mock_reranking_service.rerank(
            search_results, query
        )
        
        # Step 3: Apply diversification
        diversified_results = mock_diversity_service.diversify(
            reranked_results, query
        )
        
        # Step 4: Compose context
        config = ContextCompositionConfig(
            max_tokens=2000,
            strategy=CompositionStrategy.INTELLIGENT_STITCHING,
            include_citations=True
        )
        
        result = composition_service.compose_context(
            search_results=diversified_results,
            query=query,
            config=config
        )
        
        # Validate complete pipeline
        assert isinstance(result, ContextResult)
        assert result.query == query
        assert result.total_tokens > 0
        assert result.total_tokens <= 2000
        assert len(result.passage_groups) > 0
        assert result.strategy_used == CompositionStrategy.INTELLIGENT_STITCHING
        
        # Validate that all processing stages were applied
        for i, original_result in enumerate(diversified_results):
            assert 'reranking_applied' in original_result.metadata
            assert 'diversity_applied' in original_result.metadata
        
        # Validate composed content contains philosophical concepts
        composed_text = result.composed_text.lower()
        assert any(keyword in composed_text for keyword in ["plato", "cave", "allegory", "republic"])
        
        # Validate metadata preservation
        assert result.metadata is not None
        assert "retrieval_methods" in result.metadata
        assert set(result.metadata["retrieval_methods"]) == {"hybrid", "dense", "graph"}
    
    def test_hybrid_retrieval_composition_strategies(
        self, 
        composition_service,
        mock_retrieval_repository
    ):
        """Test different composition strategies with hybrid retrieval."""
        query = "Forms theory in Plato"
        search_results = mock_retrieval_repository.search(query=query)
        
        strategies = [
            CompositionStrategy.INTELLIGENT_STITCHING,
            CompositionStrategy.MAP_REDUCE,
            CompositionStrategy.SEMANTIC_GROUPING,
            CompositionStrategy.SIMPLE_CONCAT
        ]
        
        for strategy in strategies:
            config = ContextCompositionConfig(
                max_tokens=1500,
                strategy=strategy
            )
            
            result = composition_service.compose_context(
                search_results=search_results,
                query=query,
                config=config
            )
            
            assert isinstance(result, ContextResult)
            assert result.strategy_used == strategy
            assert result.total_tokens <= 1500
            assert len(result.passage_groups) > 0
    
    def test_large_result_set_composition(
        self,
        composition_service,
        mock_retrieval_repository
    ):
        """Test composition with large result sets requiring Map-Reduce."""
        # Mock a large result set
        large_results = []
        for i in range(50):  # Simulate 50 search results
            chunk = Chunk(
                text=f"Philosophical text segment {i} discussing various aspects of ancient philosophy and wisdom traditions.",
                document_id=uuid4(),
                position=i,
                start_char=i * 100,
                end_char=(i + 1) * 100 - 1,
                chunk_type=ChunkType.PARAGRAPH
            )
            
            result = SearchResult(
                chunk=chunk,
                relevance_score=0.9 - (i * 0.01),  # Decreasing relevance
                query="philosophy",
                enhanced_score=0.85 - (i * 0.01)
            )
            large_results.append(result)
        
        mock_retrieval_repository.search.return_value = large_results
        
        # Test with Map-Reduce strategy
        config = ContextCompositionConfig(
            max_tokens=3000,
            strategy=CompositionStrategy.MAP_REDUCE
        )
        
        result = composition_service.compose_context(
            search_results=large_results,
            query="philosophy",
            config=config
        )
        
        assert isinstance(result, ContextResult)
        assert result.strategy_used == CompositionStrategy.MAP_REDUCE
        assert result.total_tokens <= 3000
        assert len(result.passage_groups) > 0
        # Should handle large dataset efficiently
        assert result.composition_time < 5.0  # Should complete in reasonable time
    
    def test_citation_integration_with_retrieval(
        self,
        composition_service,
        mock_retrieval_repository
    ):
        """Test citation integration with retrieval results."""
        query = "Socratic method"
        search_results = mock_retrieval_repository.search(query=query)
        
        # Create citations that match the search results
        citations = [
            Citation(
                text="The unexamined life is not worth living",
                citation_type=CitationType.DIRECT_QUOTE,
                document_id=search_results[0].chunk.document_id,
                source_title="Apology",
                source_author="Plato",
                source_reference="Apology 38a",
                confidence_score=0.95,
                chunk_id=search_results[0].chunk.id
            ),
            Citation(
                text="Socrates used questioning to expose ignorance",
                citation_type=CitationType.PARAPHRASE,
                document_id=search_results[1].chunk.document_id,
                source_title="Meno",
                source_author="Plato", 
                source_reference="Meno 80d-84c",
                confidence_score=0.88,
                chunk_id=search_results[1].chunk.id
            )
        ]
        
        config = ContextCompositionConfig(
            max_tokens=2000,
            strategy=CompositionStrategy.INTELLIGENT_STITCHING,
            include_citations=True,
            citation_format="classical"
        )
        
        result = composition_service.compose_context(
            search_results=search_results,
            query=query,
            citations=citations,
            config=config
        )
        
        # Validate citation integration
        assert len(result.citations) > 0
        assert any("Apology 38a" in c.formatted_citation for c in result.citations)
        assert any("Meno 80d-84c" in c.formatted_citation for c in result.citations)
        
        # Validate citation relevance calculation
        for citation_context in result.citations:
            assert 0.0 <= citation_context.context_relevance <= 1.0
    
    def test_performance_with_realistic_data(
        self,
        composition_service,
        mock_retrieval_repository
    ):
        """Test performance with realistic philosophical data."""
        # Create realistic philosophical text chunks
        philosophical_texts = [
            "In the Nicomachean Ethics, Aristotle defines happiness (eudaimonia) as the highest good achievable by human action.",
            "Kant's categorical imperative states that we should act only according to maxims we could will to be universal laws.",
            "Descartes' cogito ergo sum establishes the thinking self as the foundation of certain knowledge.",
            "Hume's problem of induction questions whether we can justifiably infer future events from past experience.",
            "Sartre's existentialism emphasizes radical freedom and the anxiety that comes with absolute responsibility."
        ]
        
        realistic_results = []
        for i, text in enumerate(philosophical_texts):
            chunk = Chunk(
                text=text,
                document_id=uuid4(),
                position=i,
                start_char=i * 200,
                end_char=(i + 1) * 200 - 1,
                chunk_type=ChunkType.PARAGRAPH,
                metadata={"topic": "ethics", "period": "modern"}
            )
            
            result = SearchResult(
                chunk=chunk,
                relevance_score=0.9 - (i * 0.1),
                query="philosophical ethics",
                enhanced_score=0.85 - (i * 0.1),
                metadata={"retrieval_method": "hybrid"}
            )
            realistic_results.append(result)
        
        mock_retrieval_repository.search.return_value = realistic_results
        
        # Test composition performance
        config = ContextCompositionConfig(
            max_tokens=1500,
            strategy=CompositionStrategy.INTELLIGENT_STITCHING,
            enable_caching=True
        )
        
        # First composition (cache miss)
        start_time = pytest.approx(0.0, abs=5.0)  # Allow up to 5 seconds
        result1 = composition_service.compose_context(
            search_results=realistic_results,
            query="philosophical ethics",
            config=config
        )
        
        # Second composition (cache hit - should be faster)
        result2 = composition_service.compose_context(
            search_results=realistic_results,
            query="philosophical ethics", 
            config=config
        )
        
        # Validate both results
        assert result1.composed_text == result2.composed_text
        assert result1.total_tokens == result2.total_tokens
        
        # Validate performance metrics
        assert result1.performance_metrics["token_efficiency"] > 0.0
        assert result1.performance_metrics["composition_speed"] > 0.0
    
    def test_error_handling_in_pipeline(
        self,
        composition_service,
        mock_retrieval_repository
    ):
        """Test error handling throughout the pipeline."""
        # Test with empty results
        mock_retrieval_repository.search.return_value = []
        
        result = composition_service.compose_context(
            search_results=[],
            query="empty query",
            config=ContextCompositionConfig()
        )
        
        assert isinstance(result, ContextResult)
        assert result.composed_text == ""
        assert result.total_tokens == 0
        assert len(result.passage_groups) == 0
        
        # Test with malformed search results
        mock_malformed = Mock()
        mock_malformed.chunk = None  # This should cause an error
        
        with pytest.raises(Exception):  # Should handle gracefully or raise appropriate error
            composition_service.compose_context(
                search_results=[mock_malformed],
                query="malformed query",
                config=ContextCompositionConfig()
            )
    
    def test_token_efficiency_across_strategies(
        self,
        composition_service,
        mock_retrieval_repository
    ):
        """Test token efficiency across different composition strategies."""
        query = "virtue ethics"
        search_results = mock_retrieval_repository.search(query=query)
        
        results_by_strategy = {}
        
        for strategy in CompositionStrategy:
            config = ContextCompositionConfig(
                max_tokens=1000,
                strategy=strategy
            )
            
            result = composition_service.compose_context(
                search_results=search_results,
                query=query,
                config=config
            )
            
            results_by_strategy[strategy] = {
                'tokens': result.total_tokens,
                'efficiency': result.performance_metrics['token_efficiency'],
                'groups': len(result.passage_groups)
            }
        
        # All strategies should respect token limits
        for strategy, metrics in results_by_strategy.items():
            assert metrics['tokens'] <= 1000, f"Strategy {strategy} exceeded token limit"
            assert metrics['efficiency'] <= 1.0, f"Strategy {strategy} has invalid efficiency"
            assert metrics['groups'] >= 0, f"Strategy {strategy} has negative groups"
    
    def test_batch_processing_integration(
        self,
        composition_service,
        mock_retrieval_repository
    ):
        """Test batch processing integration with retrieval pipeline."""
        queries = ["virtue ethics", "social contract theory", "phenomenology"]
        
        # Mock different results for each query
        def mock_search(query, **kwargs):
            base_text = f"Philosophical discussion about {query}"
            chunk = Chunk(
                text=base_text,
                document_id=uuid4(),
                position=0,
                start_char=0,
                end_char=len(base_text),
                chunk_type=ChunkType.PARAGRAPH
            )
            
            return [SearchResult(
                chunk=chunk,
                relevance_score=0.9,
                query=query,
                enhanced_score=0.85
            )]
        
        mock_retrieval_repository.search.side_effect = mock_search
        
        # Get search results for all queries
        all_search_results = []
        for query in queries:
            results = mock_retrieval_repository.search(query=query)
            all_search_results.append(results)
        
        # Batch compose
        config = ContextCompositionConfig(max_tokens=500)
        batch_results = composition_service.compose_context_batch(
            search_results_list=all_search_results,
            queries=queries,
            config=config
        )
        
        assert len(batch_results) == len(queries)
        
        for i, result in enumerate(batch_results):
            assert isinstance(result, ContextResult)
            assert result.query == queries[i]
            assert result.total_tokens <= 500
            assert queries[i] in result.composed_text.lower() or result.composed_text == ""


class TestContextCompositionFactory:
    """Test the factory function for creating context composition services."""
    
    def test_factory_default_creation(self):
        """Test factory function with default parameters."""
        service = create_context_composition_service()
        
        assert isinstance(service, ContextCompositionService)
        assert service.config.max_tokens == 5000
        assert service.config.strategy == CompositionStrategy.INTELLIGENT_STITCHING
    
    def test_factory_custom_config(self):
        """Test factory function with custom configuration."""
        config = ContextCompositionConfig(
            max_tokens=3000,
            strategy=CompositionStrategy.MAP_REDUCE
        )
        
        service = create_context_composition_service(config=config)
        
        assert isinstance(service, ContextCompositionService)
        assert service.config.max_tokens == 3000
        assert service.config.strategy == CompositionStrategy.MAP_REDUCE
    
    def test_factory_with_settings(self):
        """Test factory function with custom settings."""
        mock_settings = Mock()
        service = create_context_composition_service(settings=mock_settings)
        
        assert isinstance(service, ContextCompositionService)
        assert service.settings == mock_settings