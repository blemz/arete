"""
Test Graph Traversal Integration with RetrievalRepository.

Tests the integration of GraphTraversalService with the existing
retrieval repository to provide graph-enhanced search capabilities.
"""

import pytest
from typing import List
from uuid import uuid4
from unittest.mock import Mock, MagicMock

from src.arete.repositories.retrieval import (
    RetrievalRepository, 
    RetrievalMethod,
    create_retrieval_repository
)
from src.arete.services.graph_traversal_service import (
    GraphTraversalService,
    GraphResult,
    EntityMention
)
from src.arete.models.entity import Entity, EntityType
from src.arete.config import Settings


class TestGraphIntegration:
    """Test graph traversal integration with RetrievalRepository."""
    
    @pytest.fixture
    def mock_graph_service(self):
        """Mock graph traversal service for testing."""
        service = Mock(spec=GraphTraversalService)
        
        # Mock entity detection
        service.detect_entities.return_value = [
            EntityMention(
                text="Socrates",
                entity_type=EntityType.PERSON,
                confidence=0.95,
                start_position=0,
                end_position=8
            )
        ]
        
        # Mock graph results
        entity = Entity(
            name="Socrates",
            entity_type=EntityType.PERSON,
            source_document_id=uuid4()
        )
        
        service.execute_traversal.return_value = [
            GraphResult(
                entity=entity,
                relationships=[],
                path_length=1,
                relevance_score=0.9,
                confidence=0.85
            )
        ]
        
        # Mock integration method
        service.integrate_with_search_results.return_value = []
        
        return service
    
    @pytest.fixture
    def mock_dense_service(self):
        """Mock dense retrieval service."""
        service = Mock()
        service.search.return_value = []
        service.get_metrics.return_value.get_summary.return_value = {}
        service.reset_metrics.return_value = None
        return service
    
    @pytest.fixture
    def mock_sparse_service(self):
        """Mock sparse retrieval service."""
        service = Mock()
        service.search.return_value = []
        service.get_algorithm_name.return_value = "BM25"
        service.get_index_statistics.return_value = {}
        service.get_metrics.return_value.get_summary.return_value = {}
        service.get_metrics.return_value.reset.return_value = None
        return service
    
    def test_repository_initialization_with_graph_service(
        self, 
        mock_dense_service, 
        mock_sparse_service, 
        mock_graph_service
    ):
        """Test repository initialization includes graph service."""
        repo = RetrievalRepository(
            dense_service=mock_dense_service,
            sparse_service=mock_sparse_service,
            graph_service=mock_graph_service,
            settings=Settings()
        )
        
        assert repo.graph_service == mock_graph_service
        assert hasattr(repo, 'dense_service')
        assert hasattr(repo, 'sparse_service')
    
    def test_graph_search_method_available(
        self, 
        mock_dense_service, 
        mock_sparse_service, 
        mock_graph_service
    ):
        """Test that GRAPH retrieval method is available."""
        repo = RetrievalRepository(
            dense_service=mock_dense_service,
            sparse_service=mock_sparse_service,
            graph_service=mock_graph_service,
            settings=Settings()
        )
        
        # Test that GRAPH method exists in enum
        assert RetrievalMethod.GRAPH in RetrievalMethod
        assert RetrievalMethod.GRAPH_ENHANCED_HYBRID in RetrievalMethod
        
        # Test that search method accepts GRAPH method
        results = repo.search(query="What did Socrates say?", method=RetrievalMethod.GRAPH)
        
        # Should call graph service methods
        mock_graph_service.detect_entities.assert_called_once()
        mock_graph_service.generate_cypher_query.assert_called_once()
        mock_graph_service.execute_traversal.assert_called_once()
    
    def test_graph_enhanced_hybrid_search(
        self, 
        mock_dense_service, 
        mock_sparse_service, 
        mock_graph_service
    ):
        """Test graph-enhanced hybrid search."""
        repo = RetrievalRepository(
            dense_service=mock_dense_service,
            sparse_service=mock_sparse_service,
            graph_service=mock_graph_service,
            settings=Settings()
        )
        
        # Mock hybrid search results
        repo._hybrid_search = Mock(return_value=[])
        
        results = repo.search(
            query="How does Plato define justice?", 
            method=RetrievalMethod.GRAPH_ENHANCED_HYBRID
        )
        
        # Should call both hybrid search and graph integration
        repo._hybrid_search.assert_called_once()
        mock_graph_service.integrate_with_search_results.assert_called_once()
    
    def test_factory_function_with_graph_service(
        self, 
        mock_graph_service, 
        mock_dense_service, 
        mock_sparse_service
    ):
        """Test factory function includes graph service parameter."""
        repo = create_retrieval_repository(
            dense_service=mock_dense_service,
            sparse_service=mock_sparse_service,
            graph_service=mock_graph_service,
            settings=Settings()
        )
        
        assert repo.graph_service == mock_graph_service
    
    def test_error_handling_in_graph_search(
        self, 
        mock_dense_service, 
        mock_sparse_service, 
        mock_graph_service
    ):
        """Test error handling in graph search methods."""
        # Make graph service raise an exception
        mock_graph_service.detect_entities.side_effect = Exception("Graph service error")
        
        repo = RetrievalRepository(
            dense_service=mock_dense_service,
            sparse_service=mock_sparse_service,
            graph_service=mock_graph_service,
            settings=Settings()
        )
        
        # Graph search should handle errors gracefully
        results = repo.search(query="Test query", method=RetrievalMethod.GRAPH)
        
        # Should return empty results instead of raising exception
        assert results == []
    
    def test_graph_enhanced_hybrid_fallback(
        self, 
        mock_dense_service, 
        mock_sparse_service, 
        mock_graph_service
    ):
        """Test fallback behavior in graph-enhanced hybrid search."""
        # Make graph service integration fail
        mock_graph_service.integrate_with_search_results.side_effect = Exception("Integration error")
        
        repo = RetrievalRepository(
            dense_service=mock_dense_service,
            sparse_service=mock_sparse_service,
            graph_service=mock_graph_service,
            settings=Settings()
        )
        
        # Mock hybrid search for fallback
        repo._hybrid_search = Mock(return_value=[])
        
        results = repo.search(
            query="Test query", 
            method=RetrievalMethod.GRAPH_ENHANCED_HYBRID
        )
        
        # Should fall back to regular hybrid search
        assert repo._hybrid_search.call_count >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])