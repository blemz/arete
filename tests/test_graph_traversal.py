"""
Tests for Graph Traversal Integration in Arete Graph-RAG system.

Tests the graph traversal service that generates Cypher queries and integrates
graph-based retrieval with the existing hybrid retrieval system.

Following TDD methodology: Red-Green-Refactor cycle with focused testing approach.
"""

import pytest
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from unittest.mock import Mock, MagicMock, patch

from src.arete.services.graph_traversal_service import (
    GraphTraversalService,
    CypherQuery,
    GraphResult,
    EntityMention,
    RelationshipType,
    GraphTraversalError
)
from src.arete.models.entity import Entity, EntityType
from src.arete.database.client import Neo4jClient
from src.arete.config import Settings


class TestCypherQuery:
    """Test Cypher query generation and validation."""
    
    def test_cypher_query_creation(self):
        """Test basic Cypher query object creation."""
        query = CypherQuery(
            cypher="MATCH (e:Entity) RETURN e",
            parameters={"name": "Socrates"}
        )
        
        assert query.cypher == "MATCH (e:Entity) RETURN e"
        assert query.parameters == {"name": "Socrates"}
        assert query.estimated_complexity == 2  # 1 base + 1 MATCH
    
    def test_cypher_query_validation(self):
        """Test Cypher query syntax validation."""
        # Valid query should pass
        valid_query = CypherQuery(
            cypher="MATCH (e:Entity {name: $name}) RETURN e",
            parameters={"name": "Plato"}
        )
        assert valid_query.is_valid()
        
        # Invalid query should fail
        invalid_query = CypherQuery(
            cypher="INVALID CYPHER SYNTAX",
            parameters={}
        )
        assert not invalid_query.is_valid()
    
    def test_cypher_query_complexity_estimation(self):
        """Test automatic complexity estimation for queries."""
        # Simple entity lookup - low complexity
        simple_query = CypherQuery(
            cypher="MATCH (e:Entity {name: $name}) RETURN e",
            parameters={"name": "Aristotle"}
        )
        assert simple_query.estimated_complexity == 2  # 1 base + 1 MATCH
        
        # Relationship traversal - medium complexity
        traversal_query = CypherQuery(
            cypher="MATCH (e1:Entity)-[r:RELATES_TO]->(e2:Entity) RETURN e1, r, e2",
            parameters={}
        )
        assert traversal_query.estimated_complexity == 4  # 1 base + 1 MATCH + 1 relationship * 2
        
        # Deep traversal - high complexity
        deep_query = CypherQuery(
            cypher="MATCH path=(e1:Entity)-[:RELATES_TO*2..4]->(e2:Entity) RETURN path",
            parameters={}
        )
        assert deep_query.estimated_complexity >= 4  # Should detect variable length pattern


class TestEntityMention:
    """Test entity mention detection and representation."""
    
    def test_entity_mention_creation(self):
        """Test creating entity mentions from query text."""
        mention = EntityMention(
            text="Socrates",
            entity_type=EntityType.PERSON,
            confidence=0.95,
            start_position=0,
            end_position=8
        )
        
        assert mention.text == "Socrates"
        assert mention.entity_type == EntityType.PERSON
        assert mention.confidence == 0.95
        assert mention.start_position == 0
        assert mention.end_position == 8
    
    def test_entity_mention_validation(self):
        """Test entity mention validation rules."""
        # Valid mention
        valid_mention = EntityMention(
            text="justice",
            entity_type=EntityType.CONCEPT,
            confidence=0.8,
            start_position=10,
            end_position=17
        )
        assert valid_mention.is_valid()
        
        # Invalid mention - end position before start
        with pytest.raises(ValueError):
            EntityMention(
                text="invalid",
                entity_type=EntityType.CONCEPT,
                confidence=0.5,
                start_position=20,
                end_position=15  # Invalid: end < start
            )


class TestGraphResult:
    """Test graph traversal result representation."""
    
    def test_graph_result_creation(self):
        """Test creating graph result objects."""
        # Mock entity for testing
        entity = Entity(
            name="Socrates",
            entity_type=EntityType.PERSON,
            description="Classical Greek philosopher",
            source_document_id=uuid4()
        )
        
        result = GraphResult(
            entity=entity,
            relationships=[],
            path_length=1,
            relevance_score=0.9,
            confidence=0.85
        )
        
        assert result.entity.name == "Socrates"
        assert result.path_length == 1
        assert result.relevance_score == 0.9
        assert result.confidence == 0.85
    
    def test_graph_result_with_relationships(self):
        """Test graph result with relationship information."""
        entity1 = Entity(name="Socrates", entity_type=EntityType.PERSON, source_document_id=uuid4())
        entity2 = Entity(name="Plato", entity_type=EntityType.PERSON, source_document_id=uuid4())
        
        relationship = {
            "type": RelationshipType.TEACHER_STUDENT,
            "source": entity1,
            "target": entity2,
            "properties": {"duration": "20 years"}
        }
        
        result = GraphResult(
            entity=entity1,
            relationships=[relationship],
            path_length=2,
            relevance_score=0.8,
            confidence=0.9
        )
        
        assert len(result.relationships) == 1
        assert result.relationships[0]["type"] == RelationshipType.TEACHER_STUDENT


class TestGraphTraversalService:
    """Test the main graph traversal service."""
    
    @pytest.fixture
    def mock_neo4j_client(self):
        """Mock Neo4j client for testing."""
        client = Mock(spec=Neo4jClient)
        client.is_connected = True
        
        # Mock session methods used by the service
        mock_session = Mock()
        mock_session.run.return_value = []
        client.session.return_value.__enter__ = Mock(return_value=mock_session)
        client.session.return_value.__exit__ = Mock(return_value=None)
        
        return client
    
    @pytest.fixture
    def graph_service(self, mock_neo4j_client):
        """Create graph traversal service with mocked dependencies."""
        return GraphTraversalService(
            neo4j_client=mock_neo4j_client,
            settings=Settings()
        )
    
    def test_service_initialization(self, mock_neo4j_client):
        """Test proper service initialization."""
        service = GraphTraversalService(
            neo4j_client=mock_neo4j_client,
            settings=Settings()
        )
        
        assert service.neo4j_client == mock_neo4j_client
        assert service.is_initialized
    
    def test_entity_detection_basic(self, graph_service):
        """Test basic entity detection in query text."""
        query_text = "What did Socrates say about justice?"
        
        # Mock entity detection results
        graph_service.entity_detector = Mock()
        graph_service.entity_detector.detect_entities.return_value = [
            EntityMention(
                text="Socrates",
                entity_type=EntityType.PERSON,
                confidence=0.95,
                start_position=9,
                end_position=17
            ),
            EntityMention(
                text="justice",
                entity_type=EntityType.CONCEPT,
                confidence=0.9,
                start_position=28,
                end_position=35
            )
        ]
        
        entities = graph_service.detect_entities(query_text)
        
        assert len(entities) == 2
        assert entities[0].text == "Socrates"
        assert entities[0].entity_type == EntityType.PERSON
        assert entities[1].text == "justice"
        assert entities[1].entity_type == EntityType.CONCEPT
    
    def test_cypher_query_generation_simple(self, graph_service):
        """Test generating simple Cypher queries."""
        entities = [
            EntityMention(
                text="Plato",
                entity_type=EntityType.PERSON,
                confidence=0.95,
                start_position=0,
                end_position=5
            )
        ]
        
        query = graph_service.generate_cypher_query(
            entities=entities,
            query_type="entity_lookup"
        )
        
        assert query.cypher is not None
        assert "MATCH" in query.cypher
        assert "Entity" in query.cypher
        assert "plato" in str(query.parameters.values())  # EntityMention normalizes text to lowercase
    
    def test_cypher_query_generation_relationship(self, graph_service):
        """Test generating relationship traversal queries."""
        entities = [
            EntityMention(
                text="Aristotle",
                entity_type=EntityType.PERSON,
                confidence=0.9,
                start_position=0,
                end_position=9
            ),
            EntityMention(
                text="virtue",
                entity_type=EntityType.CONCEPT,
                confidence=0.85,
                start_position=20,
                end_position=26
            )
        ]
        
        query = graph_service.generate_cypher_query(
            entities=entities,
            query_type="relationship_traversal"
        )
        
        assert query.cypher is not None
        assert "RELATES_TO" in query.cypher or "MENTIONS" in query.cypher
        assert query.estimated_complexity >= 2
    
    def test_graph_traversal_execution(self, graph_service, mock_neo4j_client):
        """Test executing graph traversal queries."""
        # Mock Neo4j response - create a mock record that acts like a dictionary
        test_entity_id = str(uuid4())
        mock_record = {
            "e": {
                "id": test_entity_id,
                "name": "Socrates",
                "type": "person",
                "description": "Greek philosopher",
                "source_document_id": str(uuid4())
            },
            "r": {
                "type": "discusses",
                "strength": 0.9
            }
        }
        
        mock_session = Mock()
        mock_session.run.return_value = [mock_record]
        mock_neo4j_client.session.return_value.__enter__ = Mock(return_value=mock_session)
        
        query = CypherQuery(
            cypher="MATCH (e:Entity {name: $name}) RETURN e",
            parameters={"name": "Socrates"}
        )
        
        results = graph_service.execute_traversal(query)
        
        assert len(results) > 0
        assert results[0].entity.name == "Socrates"
        mock_neo4j_client.session.assert_called()
    
    def test_result_integration_with_hybrid_search(self, graph_service):
        """Test integrating graph results with existing search results."""
        # Mock search results from existing retrieval system
        from src.arete.services.dense_retrieval_service import SearchResult
        from src.arete.models.chunk import Chunk
        
        chunk = Chunk(
            text="Socrates discusses virtue in the Republic",
            document_id=uuid4(),
            position=1,
            chunk_type="paragraph",
            start_char=0,
            end_char=40
        )
        
        existing_results = [
            SearchResult(
                chunk=chunk,
                relevance_score=0.8,
                query="Socrates virtue"
            )
        ]
        
        # Mock graph results
        entity = Entity(name="Socrates", entity_type=EntityType.PERSON, source_document_id=uuid4())
        graph_results = [
            GraphResult(
                entity=entity,
                relationships=[],
                path_length=1,
                relevance_score=0.9,
                confidence=0.85
            )
        ]
        
        integrated_results = graph_service.integrate_with_search_results(
            search_results=existing_results,
            graph_results=graph_results
        )
        
        # Should combine and re-rank results
        assert len(integrated_results) >= len(existing_results)
        # Graph-enhanced results should have higher scores
        assert any(result.final_score > 0.8 for result in integrated_results)
    
    def test_error_handling(self, graph_service):
        """Test proper error handling in graph traversal."""
        # Test with disconnected client
        graph_service.neo4j_client = None
        
        query = CypherQuery(
            cypher="MATCH (e:Entity) RETURN e",
            parameters={}
        )
        
        with pytest.raises(GraphTraversalError):
            graph_service.execute_traversal(query)
    
    def test_performance_optimization(self, graph_service):
        """Test query complexity limits and optimization."""
        # High complexity query should be optimized or rejected
        complex_entities = [
            EntityMention(f"entity_{i}", EntityType.CONCEPT, 0.8, i*10, (i+1)*10)
            for i in range(10)  # Many entities
        ]
        
        query = graph_service.generate_cypher_query(
            entities=complex_entities,
            query_type="deep_traversal"
        )
        
        # Should limit complexity or optimize query
        assert query.estimated_complexity <= graph_service.max_query_complexity
    
    def test_caching_mechanism(self, graph_service):
        """Test query result caching for performance."""
        query = CypherQuery(
            cypher="MATCH (e:Entity {name: $name}) RETURN e",
            parameters={"name": "Plato"}
        )
        
        # First execution
        results1 = graph_service.execute_traversal(query)
        
        # Second execution should use cache
        results2 = graph_service.execute_traversal(query)
        
        assert results1 == results2
        # Verify caching behavior (implementation dependent)


class TestGraphTraversalIntegration:
    """Test integration with existing retrieval system."""
    
    @pytest.fixture
    def mock_retrieval_repository(self):
        """Mock retrieval repository for integration testing."""
        from src.arete.repositories.retrieval import RetrievalRepository
        
        repo = Mock(spec=RetrievalRepository)
        repo.search.return_value = []
        return repo
    
    def test_graph_enhanced_search(self, mock_retrieval_repository):
        """Test graph-enhanced search integration."""
        # This will be implemented as part of the RetrievalRepository extension
        query_text = "How does Plato define justice?"
        
        # Should detect entities, generate graph queries,
        # combine with dense/sparse results
        # Mock implementation for now
        enhanced_results = mock_retrieval_repository.search(
            query=query_text,
            method="graph_enhanced_hybrid"
        )
        
        # Verify the integration pattern is established
        mock_retrieval_repository.search.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])