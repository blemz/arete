"""
Tests for Entity repository implementation.

Following focused testing methodology proven in database client implementations.
Tests cover entity repository contract, dual persistence, graph operations, and entity-specific methods.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime
from typing import List, Optional, Dict, Any

from arete.repositories.base import (
    BaseRepository,
    GraphRepository,
    SearchableRepository,
    EntityNotFoundError,
    DuplicateEntityError,
    ValidationError,
    RepositoryError
)
from arete.repositories.entity import EntityRepository
from arete.models.entity import Entity, EntityType, MentionData, RelationshipData
from arete.database.client import Neo4jClient
from arete.database.weaviate_client import WeaviateClient


class TestEntityRepositoryInterface:
    """Test EntityRepository interface contracts."""

    def test_entity_repository_extends_graph_repository(self):
        """Test that EntityRepository extends GraphRepository."""
        assert issubclass(EntityRepository, GraphRepository)

    def test_entity_repository_extends_searchable_repository(self):
        """Test that EntityRepository extends SearchableRepository."""
        assert issubclass(EntityRepository, SearchableRepository)

    def test_entity_repository_extends_base_repository(self):
        """Test that EntityRepository extends BaseRepository."""
        assert issubclass(EntityRepository, BaseRepository)

    def test_entity_repository_has_entity_specific_methods(self):
        """Test that EntityRepository has entity-specific methods."""
        entity_methods = {
            'get_by_name', 'get_by_type', 'search_entities',
            'get_related', 'get_neighbors'
        }
        
        actual_methods = {
            name for name in dir(EntityRepository)
            if not name.startswith('_') and callable(getattr(EntityRepository, name))
        }
        
        assert entity_methods.issubset(actual_methods)


class TestEntityRepositoryInitialization:
    """Test EntityRepository initialization and dependency injection."""

    def test_entity_repository_requires_neo4j_client(self):
        """Test that EntityRepository requires Neo4j client."""
        mock_neo4j = MagicMock(spec=Neo4jClient)
        mock_weaviate = MagicMock(spec=WeaviateClient)
        
        repo = EntityRepository(
            neo4j_client=mock_neo4j,
            weaviate_client=mock_weaviate
        )
        
        assert repo._neo4j_client == mock_neo4j
        assert repo._weaviate_client == mock_weaviate

    def test_entity_repository_requires_weaviate_client(self):
        """Test that EntityRepository requires Weaviate client."""
        mock_neo4j = MagicMock(spec=Neo4jClient)
        mock_weaviate = MagicMock(spec=WeaviateClient)
        
        repo = EntityRepository(
            neo4j_client=mock_neo4j,
            weaviate_client=mock_weaviate
        )
        
        assert repo._weaviate_client == mock_weaviate

    def test_entity_repository_cannot_initialize_without_clients(self):
        """Test that EntityRepository requires both clients."""
        with pytest.raises(TypeError):
            EntityRepository()


class TestEntityRepositoryBasicOperations:
    """Test basic CRUD operations for EntityRepository."""

    @pytest.fixture
    def mock_neo4j_client(self):
        """Provide mock Neo4j client."""
        return MagicMock(spec=Neo4jClient)

    @pytest.fixture
    def mock_weaviate_client(self):
        """Provide mock Weaviate client."""
        return MagicMock(spec=WeaviateClient)

    @pytest.fixture
    def entity_repository(self, mock_neo4j_client, mock_weaviate_client):
        """Provide EntityRepository instance with mocked clients."""
        return EntityRepository(
            neo4j_client=mock_neo4j_client,
            weaviate_client=mock_weaviate_client
        )

    @pytest.fixture
    def sample_entity(self):
        """Provide sample entity for testing."""
        return Entity(
            id=uuid4(),
            name="Socrates",
            entity_type=EntityType.PERSON,
            source_document_id=uuid4(),
            description="Classical Greek philosopher",
            canonical_form="Socrates of Athens",
            aliases=["Sokrates"],
            confidence=0.95
        )

    @pytest.fixture
    def sample_mention(self, sample_entity):
        """Provide sample mention data."""
        return MentionData(
            text="Socrates",
            context="Socrates was a classical Greek philosopher",
            start_position=0,
            end_position=8,
            confidence=0.9,
            document_id=sample_entity.source_document_id
        )

    @pytest.fixture
    def sample_relationship(self):
        """Provide sample relationship data."""
        return RelationshipData(
            target_entity_id=uuid4(),
            relationship_type="TEACHER_OF",
            confidence=0.8,
            source="Plato's Dialogues",
            bidirectional=False
        )

    @pytest.mark.asyncio
    async def test_create_entity_stores_in_both_databases(
        self, 
        entity_repository, 
        mock_neo4j_client, 
        mock_weaviate_client,
        sample_entity
    ):
        """Test create stores entity in both Neo4j and Weaviate."""
        # Mock successful storage in both databases
        mock_neo4j_client.create_node = AsyncMock(return_value=sample_entity.model_dump())
        mock_weaviate_client.save_entity = AsyncMock()
        
        result = await entity_repository.create(sample_entity)
        
        # Verify Neo4j call
        mock_neo4j_client.create_node.assert_called_once()
        neo4j_call_args = mock_neo4j_client.create_node.call_args[1]
        assert neo4j_call_args['label'] == 'Entity'
        assert neo4j_call_args['properties']['name'] == sample_entity.name
        assert neo4j_call_args['properties']['entity_type'] == str(sample_entity.entity_type)
        
        # Verify Weaviate call
        mock_weaviate_client.save_entity.assert_called_once()
        weaviate_call_args = mock_weaviate_client.save_entity.call_args
        assert weaviate_call_args[0][0] == sample_entity
        
        assert result == sample_entity

    @pytest.mark.asyncio
    async def test_create_entity_handles_duplicate_error(
        self,
        entity_repository,
        mock_neo4j_client,
        mock_weaviate_client,
        sample_entity
    ):
        """Test create handles duplicate entity errors."""
        mock_neo4j_client.create_node = AsyncMock(
            side_effect=Exception("Constraint violation")
        )
        
        with pytest.raises(DuplicateEntityError):
            await entity_repository.create(sample_entity)

    @pytest.mark.asyncio
    async def test_get_by_id_retrieves_from_neo4j(
        self,
        entity_repository,
        mock_neo4j_client,
        sample_entity
    ):
        """Test get_by_id retrieves entity from Neo4j."""
        entity_id = str(sample_entity.id)
        mock_neo4j_client.get_node_by_id = AsyncMock(
            return_value=sample_entity.model_dump()
        )
        
        result = await entity_repository.get_by_id(entity_id)
        
        mock_neo4j_client.get_node_by_id.assert_called_once_with(
            entity_id, 'Entity'
        )
        assert result.id == sample_entity.id
        assert result.name == sample_entity.name
        assert result.entity_type == sample_entity.entity_type

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(
        self,
        entity_repository,
        mock_neo4j_client
    ):
        """Test get_by_id returns None for non-existent entity."""
        entity_id = str(uuid4())
        mock_neo4j_client.get_node_by_id = AsyncMock(return_value=None)
        
        result = await entity_repository.get_by_id(entity_id)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_update_entity_updates_both_databases(
        self,
        entity_repository,
        mock_neo4j_client,
        mock_weaviate_client,
        sample_entity
    ):
        """Test update modifies entity in both databases."""
        updated_entity = sample_entity.model_copy()
        updated_entity.description = "Updated description"
        
        mock_neo4j_client.update_node = AsyncMock(
            return_value=updated_entity.model_dump()
        )
        mock_weaviate_client.save_entity = AsyncMock()
        
        result = await entity_repository.update(updated_entity)
        
        # Verify Neo4j update
        mock_neo4j_client.update_node.assert_called_once()
        
        # Verify Weaviate update
        mock_weaviate_client.save_entity.assert_called_once()
        
        assert result.description == "Updated description"

    @pytest.mark.asyncio
    async def test_update_raises_not_found_for_missing_entity(
        self,
        entity_repository,
        mock_neo4j_client,
        sample_entity
    ):
        """Test update raises EntityNotFoundError for missing entity."""
        mock_neo4j_client.update_node = AsyncMock(
            side_effect=Exception("Node not found")
        )
        
        with pytest.raises(EntityNotFoundError):
            await entity_repository.update(sample_entity)

    @pytest.mark.asyncio
    async def test_delete_removes_from_both_databases(
        self,
        entity_repository,
        mock_neo4j_client,
        mock_weaviate_client
    ):
        """Test delete removes entity from both databases."""
        entity_id = str(uuid4())
        
        mock_neo4j_client.delete_node = AsyncMock(return_value=True)
        mock_weaviate_client.delete_entity = AsyncMock()
        
        result = await entity_repository.delete(entity_id)
        
        mock_neo4j_client.delete_node.assert_called_once_with(
            entity_id, 'Entity'
        )
        mock_weaviate_client.delete_entity.assert_called_once_with(
            'Entity', entity_id
        )
        
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_returns_false_for_missing_entity(
        self,
        entity_repository,
        mock_neo4j_client,
        mock_weaviate_client
    ):
        """Test delete returns False for non-existent entity."""
        entity_id = str(uuid4())
        
        mock_neo4j_client.delete_node = AsyncMock(return_value=False)
        mock_weaviate_client.delete_entity = AsyncMock()
        
        result = await entity_repository.delete(entity_id)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_list_all_entities_with_filters(
        self,
        entity_repository,
        mock_neo4j_client,
        sample_entity
    ):
        """Test list_all with entity type filters."""
        mock_neo4j_client.query = AsyncMock(
            return_value=[{"e": sample_entity.model_dump()}]
        )
        
        results = await entity_repository.list_all(
            limit=10,
            offset=0,
            filters={"entity_type": "person"}
        )
        
        # Verify query was called with filters
        mock_neo4j_client.query.assert_called_once()
        query_call = mock_neo4j_client.query.call_args[0][0]
        assert "MATCH (e:Entity)" in query_call
        assert "WHERE" in query_call
        assert "entity_type" in query_call
        
        assert len(results) == 1
        assert results[0].name == sample_entity.name

    @pytest.mark.asyncio
    async def test_count_entities_with_filters(
        self,
        entity_repository,
        mock_neo4j_client
    ):
        """Test count with entity type filters."""
        mock_neo4j_client.query = AsyncMock(
            return_value=[{"count": 5}]
        )
        
        result = await entity_repository.count(
            filters={"entity_type": "person"}
        )
        
        # Verify count query
        mock_neo4j_client.query.assert_called_once()
        query_call = mock_neo4j_client.query.call_args[0][0]
        assert "count(e)" in query_call
        assert "WHERE" in query_call
        
        assert result == 5

    @pytest.mark.asyncio
    async def test_exists_entity_by_id(
        self,
        entity_repository,
        mock_neo4j_client
    ):
        """Test exists checks entity presence."""
        entity_id = str(uuid4())
        mock_neo4j_client.query = AsyncMock(
            return_value=[{"exists": True}]
        )
        
        result = await entity_repository.exists(entity_id)
        
        # Verify existence query
        mock_neo4j_client.query.assert_called_once()
        query_call = mock_neo4j_client.query.call_args[0][0]
        assert "count(e) > 0" in query_call
        assert "e.id = $entity_id" in query_call
        
        assert result is True


class TestEntityRepositorySearchOperations:
    """Test search operations for EntityRepository."""

    @pytest.fixture
    def mock_neo4j_client(self):
        """Provide mock Neo4j client."""
        return MagicMock(spec=Neo4jClient)

    @pytest.fixture
    def mock_weaviate_client(self):
        """Provide mock Weaviate client."""
        return MagicMock(spec=WeaviateClient)

    @pytest.fixture
    def entity_repository(self, mock_neo4j_client, mock_weaviate_client):
        """Provide EntityRepository instance."""
        return EntityRepository(
            neo4j_client=mock_neo4j_client,
            weaviate_client=mock_weaviate_client
        )

    @pytest.fixture
    def sample_entities(self):
        """Provide sample entities for search testing."""
        return [
            Entity(
                id=uuid4(),
                name="Socrates",
                entity_type=EntityType.PERSON,
                source_document_id=uuid4(),
                description="Classical Greek philosopher"
            ),
            Entity(
                id=uuid4(),
                name="Justice",
                entity_type=EntityType.CONCEPT,
                source_document_id=uuid4(),
                description="Virtue and moral principle"
            ),
            Entity(
                id=uuid4(),
                name="Athens",
                entity_type=EntityType.PLACE,
                source_document_id=uuid4(),
                description="City-state in ancient Greece"
            )
        ]

    @pytest.mark.asyncio
    async def test_search_by_text_uses_weaviate(
        self,
        entity_repository,
        mock_weaviate_client,
        sample_entities
    ):
        """Test search_by_text uses Weaviate for semantic search."""
        mock_weaviate_client.search_near_text = AsyncMock(
            return_value=[entity.model_dump() for entity in sample_entities[:2]]
        )
        
        results = await entity_repository.search_by_text(
            "Greek philosopher",
            limit=5,
            similarity_threshold=0.8
        )
        
        mock_weaviate_client.search_near_text.assert_called_once_with(
            collection='Entity',
            query='Greek philosopher',
            limit=5,
            certainty=0.8
        )
        
        assert len(results) == 2
        assert results[0].name == "Socrates"

    @pytest.mark.asyncio
    async def test_search_by_embedding_uses_weaviate(
        self,
        entity_repository,
        mock_weaviate_client,
        sample_entities
    ):
        """Test search_by_embedding uses Weaviate vector search."""
        test_embedding = [0.1, 0.2, 0.3] * 128  # Mock 384-dim embedding
        mock_weaviate_client.search_near_vector = AsyncMock(
            return_value=[sample_entities[0].model_dump()]
        )
        
        results = await entity_repository.search_by_embedding(
            test_embedding,
            limit=3,
            similarity_threshold=0.9
        )
        
        mock_weaviate_client.search_near_vector.assert_called_once_with(
            collection='Entity',
            vector=test_embedding,
            limit=3,
            certainty=0.9
        )
        
        assert len(results) == 1
        assert results[0].name == "Socrates"

    @pytest.mark.asyncio
    async def test_get_by_name_queries_neo4j(
        self,
        entity_repository,
        mock_neo4j_client,
        sample_entities
    ):
        """Test get_by_name queries Neo4j for name matches."""
        mock_neo4j_client.query = AsyncMock(
            return_value=[{"e": sample_entities[0].model_dump()}]
        )
        
        results = await entity_repository.get_by_name("Socrates")
        
        # Verify Cypher query was called
        mock_neo4j_client.query.assert_called_once()
        query_call = mock_neo4j_client.query.call_args[0][0]
        assert "MATCH (e:Entity)" in query_call
        assert "e.name" in query_call or "e.aliases" in query_call
        
        assert len(results) == 1
        assert results[0].name == "Socrates"

    @pytest.mark.asyncio
    async def test_get_by_type_queries_neo4j(
        self,
        entity_repository,
        mock_neo4j_client,
        sample_entities
    ):
        """Test get_by_type queries Neo4j for entity type matches."""
        person_entities = [sample_entities[0]]
        mock_neo4j_client.query = AsyncMock(
            return_value=[{"e": entity.model_dump()} for entity in person_entities]
        )
        
        results = await entity_repository.get_by_type(EntityType.PERSON)
        
        # Verify Cypher query
        mock_neo4j_client.query.assert_called_once()
        query_call = mock_neo4j_client.query.call_args[0][0]
        assert "MATCH (e:Entity)" in query_call
        assert "e.entity_type" in query_call
        
        # Verify parameters
        params = mock_neo4j_client.query.call_args[1]
        assert params["entity_type"] == "person"
        
        assert len(results) == 1
        assert results[0].entity_type == EntityType.PERSON

    @pytest.mark.asyncio
    async def test_search_entities_combines_text_and_attributes(
        self,
        entity_repository,
        mock_neo4j_client,
        mock_weaviate_client,
        sample_entities
    ):
        """Test search_entities uses hybrid approach."""
        # Mock Neo4j name/description search
        mock_neo4j_client.query = AsyncMock(
            return_value=[{"e": sample_entities[0].model_dump()}]
        )
        
        # Mock Weaviate semantic search  
        mock_weaviate_client.search_near_text = AsyncMock(
            return_value=[sample_entities[1].model_dump()]
        )
        
        results = await entity_repository.search_entities("philosopher")
        
        # Both databases should be queried
        mock_neo4j_client.query.assert_called_once()
        mock_weaviate_client.search_near_text.assert_called_once()
        
        # Results should be merged
        assert len(results) >= 1


class TestEntityRepositoryGraphOperations:
    """Test graph-specific operations for EntityRepository."""

    @pytest.fixture
    def mock_neo4j_client(self):
        """Provide mock Neo4j client for graph operations."""
        return MagicMock(spec=Neo4jClient)

    @pytest.fixture
    def mock_weaviate_client(self):
        """Provide mock Weaviate client."""
        return MagicMock(spec=WeaviateClient)

    @pytest.fixture
    def entity_repository(self, mock_neo4j_client, mock_weaviate_client):
        """Provide EntityRepository instance for graph testing."""
        return EntityRepository(
            neo4j_client=mock_neo4j_client,
            weaviate_client=mock_weaviate_client
        )

    @pytest.fixture
    def sample_entities(self):
        """Provide related entities for graph testing."""
        return [
            Entity(
                id=uuid4(),
                name="Socrates",
                entity_type=EntityType.PERSON,
                source_document_id=uuid4()
            ),
            Entity(
                id=uuid4(),
                name="Plato",
                entity_type=EntityType.PERSON,
                source_document_id=uuid4()
            ),
            Entity(
                id=uuid4(),
                name="Aristotle",
                entity_type=EntityType.PERSON,
                source_document_id=uuid4()
            )
        ]

    @pytest.mark.asyncio
    async def test_get_related_entities_with_relationship_type(
        self,
        entity_repository,
        mock_neo4j_client,
        sample_entities
    ):
        """Test get_related retrieves entities with specific relationship type."""
        entity_id = str(sample_entities[0].id)
        related_entities = sample_entities[1:2]  # Plato
        
        mock_neo4j_client.query = AsyncMock(
            return_value=[{"related": entity.model_dump()} for entity in related_entities]
        )
        
        results = await entity_repository.get_related(
            entity_id=entity_id,
            relationship_type="TEACHER_OF",
            direction="OUTGOING",
            limit=10
        )
        
        # Verify graph traversal query
        mock_neo4j_client.query.assert_called_once()
        query_call = mock_neo4j_client.query.call_args[0][0]
        assert "MATCH (e:Entity)" in query_call
        assert "-[r:" in query_call  # Relationship pattern
        assert "->" in query_call or "<-" in query_call  # Direction
        
        # Verify parameters
        params = mock_neo4j_client.query.call_args[1]
        assert params["entity_id"] == entity_id
        assert params["relationship_type"] == "TEACHER_OF"
        assert params["limit"] == 10
        
        assert len(results) == 1
        assert results[0].name == "Plato"

    @pytest.mark.asyncio
    async def test_get_related_entities_all_relationships(
        self,
        entity_repository,
        mock_neo4j_client,
        sample_entities
    ):
        """Test get_related retrieves all related entities regardless of type."""
        entity_id = str(sample_entities[0].id)
        related_entities = sample_entities[1:]  # Plato and Aristotle
        
        mock_neo4j_client.query = AsyncMock(
            return_value=[{"related": entity.model_dump()} for entity in related_entities]
        )
        
        results = await entity_repository.get_related(
            entity_id=entity_id,
            relationship_type=None,  # All relationship types
            direction="BOTH",
            limit=5
        )
        
        # Verify query handles all relationship types
        mock_neo4j_client.query.assert_called_once()
        query_call = mock_neo4j_client.query.call_args[0][0]
        assert "MATCH (e:Entity)" in query_call
        assert "-[r]-" in query_call  # Bidirectional without type filter
        
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_neighbors_within_depth(
        self,
        entity_repository,
        mock_neo4j_client,
        sample_entities
    ):
        """Test get_neighbors retrieves entities within specified depth."""
        entity_id = str(sample_entities[0].id)
        neighbor_entities = sample_entities[1:]  # Plato and Aristotle
        
        mock_neo4j_client.query = AsyncMock(
            return_value=[{"neighbor": entity.model_dump()} for entity in neighbor_entities]
        )
        
        results = await entity_repository.get_neighbors(
            entity_id=entity_id,
            depth=2,
            limit=10
        )
        
        # Verify neighbor traversal query
        mock_neo4j_client.query.assert_called_once()
        query_call = mock_neo4j_client.query.call_args[0][0]
        assert "MATCH (e:Entity)" in query_call
        assert "*1..2" in query_call or "depth" in query_call.lower()  # Depth constraint
        
        # Verify parameters
        params = mock_neo4j_client.query.call_args[1]
        assert params["entity_id"] == entity_id
        assert params["depth"] == 2
        assert params["limit"] == 10
        
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_neighbors_default_depth_one(
        self,
        entity_repository,
        mock_neo4j_client,
        sample_entities
    ):
        """Test get_neighbors defaults to depth 1."""
        entity_id = str(sample_entities[0].id)
        direct_neighbors = [sample_entities[1]]  # Only Plato
        
        mock_neo4j_client.query = AsyncMock(
            return_value=[{"neighbor": entity.model_dump()} for entity in direct_neighbors]
        )
        
        results = await entity_repository.get_neighbors(entity_id)
        
        # Verify default depth parameter
        params = mock_neo4j_client.query.call_args[1]
        assert params["depth"] == 1
        
        assert len(results) == 1


class TestEntityRepositoryRelationshipManagement:
    """Test relationship-specific operations for EntityRepository."""

    @pytest.fixture
    def mock_neo4j_client(self):
        """Provide mock Neo4j client for relationship operations."""
        return MagicMock(spec=Neo4jClient)

    @pytest.fixture
    def mock_weaviate_client(self):
        """Provide mock Weaviate client."""
        return MagicMock(spec=WeaviateClient)

    @pytest.fixture
    def entity_repository(self, mock_neo4j_client, mock_weaviate_client):
        """Provide EntityRepository instance for relationship testing."""
        return EntityRepository(
            neo4j_client=mock_neo4j_client,
            weaviate_client=mock_weaviate_client
        )

    @pytest.fixture
    def teacher_student_entities(self):
        """Provide teacher-student entity relationship."""
        socrates_id = uuid4()
        plato_id = uuid4()
        
        socrates = Entity(
            id=socrates_id,
            name="Socrates",
            entity_type=EntityType.PERSON,
            source_document_id=uuid4()
        )
        
        plato = Entity(
            id=plato_id,
            name="Plato",
            entity_type=EntityType.PERSON,
            source_document_id=uuid4()
        )
        
        # Add relationship to Socrates
        relationship = RelationshipData(
            target_entity_id=plato_id,
            relationship_type="TEACHER_OF",
            confidence=0.9,
            source="Historical records"
        )
        socrates.add_relationship(relationship)
        
        return socrates, plato

    @pytest.mark.asyncio
    async def test_create_entity_with_relationships(
        self,
        entity_repository,
        mock_neo4j_client,
        mock_weaviate_client,
        teacher_student_entities
    ):
        """Test creating entity with relationships creates both entity and relationship nodes."""
        socrates, plato = teacher_student_entities
        
        # Mock entity creation
        mock_neo4j_client.create_node = AsyncMock(return_value=socrates.model_dump())
        mock_weaviate_client.save_entity = AsyncMock()
        
        # Mock relationship creation (should be called separately)
        mock_neo4j_client.query = AsyncMock()
        
        result = await entity_repository.create(socrates)
        
        # Verify entity was created
        mock_neo4j_client.create_node.assert_called_once_with(
            label='Entity',
            properties=socrates.model_dump(exclude={'relationships', 'mentions'})
        )
        
        # Verify relationships are handled separately (not embedded in entity)
        entity_data = mock_neo4j_client.create_node.call_args[1]['properties']
        assert 'relationships' not in entity_data
        
        assert result.name == "Socrates"
        assert len(result.relationships) == 1

    @pytest.mark.asyncio
    async def test_get_related_handles_complex_relationship_types(
        self,
        entity_repository,
        mock_neo4j_client
    ):
        """Test get_related handles various philosophical relationship types."""
        entity_id = str(uuid4())
        
        # Mock results with different relationship types
        mock_results = [
            {"related": {"id": str(uuid4()), "name": "Student", "entity_type": "person"}},
            {"related": {"id": str(uuid4()), "name": "Concept", "entity_type": "concept"}},
        ]
        mock_neo4j_client.query = AsyncMock(return_value=mock_results)
        
        # Test philosophical relationship types
        relationship_types = [
            "TEACHER_OF", "STUDENT_OF", "INFLUENCED_BY", "OPPOSED_TO",
            "DEVELOPED_CONCEPT", "DISCUSSED_IN", "LOCATED_IN"
        ]
        
        for rel_type in relationship_types:
            await entity_repository.get_related(
                entity_id=entity_id,
                relationship_type=rel_type,
                direction="OUTGOING"
            )
            
            # Verify relationship type is passed correctly
            query_params = mock_neo4j_client.query.call_args[1]
            assert query_params["relationship_type"] == rel_type

    @pytest.mark.asyncio
    async def test_philosophical_entity_graph_traversal(
        self,
        entity_repository,
        mock_neo4j_client
    ):
        """Test graph traversal for philosophical knowledge representation."""
        socrates_id = str(uuid4())
        
        # Mock complex philosophical relationship network
        mock_results = [
            {
                "neighbor": {
                    "id": str(uuid4()),
                    "name": "Plato",
                    "entity_type": "person",
                    "source_document_id": str(uuid4())
                }
            },
            {
                "neighbor": {
                    "id": str(uuid4()),
                    "name": "Knowledge",
                    "entity_type": "concept", 
                    "source_document_id": str(uuid4())
                }
            },
            {
                "neighbor": {
                    "id": str(uuid4()),
                    "name": "Agora",
                    "entity_type": "place",
                    "source_document_id": str(uuid4())
                }
            }
        ]
        mock_neo4j_client.query = AsyncMock(return_value=mock_results)
        
        results = await entity_repository.get_neighbors(
            entity_id=socrates_id,
            depth=2,
            limit=20
        )
        
        # Verify diverse entity types in philosophical network
        entity_types = {result.entity_type for result in results}
        assert EntityType.PERSON in entity_types
        assert EntityType.CONCEPT in entity_types
        assert EntityType.PLACE in entity_types
        
        assert len(results) == 3


class TestEntityRepositoryErrorHandling:
    """Test error handling in EntityRepository."""

    @pytest.fixture
    def mock_neo4j_client(self):
        """Provide mock Neo4j client for error testing."""
        return MagicMock(spec=Neo4jClient)

    @pytest.fixture
    def mock_weaviate_client(self):
        """Provide mock Weaviate client for error testing."""
        return MagicMock(spec=WeaviateClient)

    @pytest.fixture
    def entity_repository(self, mock_neo4j_client, mock_weaviate_client):
        """Provide EntityRepository for error testing."""
        return EntityRepository(
            neo4j_client=mock_neo4j_client,
            weaviate_client=mock_weaviate_client
        )

    @pytest.fixture
    def sample_entity(self):
        """Provide sample entity for error testing."""
        return Entity(
            id=uuid4(),
            name="Test Entity",
            entity_type=EntityType.CONCEPT,
            source_document_id=uuid4()
        )

    @pytest.mark.asyncio
    async def test_create_handles_neo4j_failures(
        self,
        entity_repository,
        mock_neo4j_client,
        mock_weaviate_client,
        sample_entity
    ):
        """Test create handles Neo4j database failures gracefully."""
        mock_neo4j_client.create_node = AsyncMock(
            side_effect=Exception("Database connection failed")
        )
        
        with pytest.raises(RepositoryError) as exc_info:
            await entity_repository.create(sample_entity)
        
        assert "Database connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_handles_weaviate_failures(
        self,
        entity_repository,
        mock_neo4j_client,
        mock_weaviate_client,
        sample_entity
    ):
        """Test create handles Weaviate failures gracefully."""
        # Neo4j succeeds
        mock_neo4j_client.create_node = AsyncMock(
            return_value=sample_entity.model_dump()
        )
        
        # Weaviate fails
        mock_weaviate_client.save_entity = AsyncMock(
            side_effect=Exception("Vector store unavailable")
        )
        
        with pytest.raises(RepositoryError) as exc_info:
            await entity_repository.create(sample_entity)
        
        assert "Vector store unavailable" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_handles_weaviate_unavailable(
        self,
        entity_repository,
        mock_weaviate_client
    ):
        """Test search gracefully handles Weaviate being unavailable."""
        mock_weaviate_client.search_near_text = AsyncMock(
            side_effect=Exception("Weaviate service unavailable")
        )
        
        with pytest.raises(RepositoryError):
            await entity_repository.search_by_text("test query")

    @pytest.mark.asyncio
    async def test_graph_operations_handle_neo4j_failures(
        self,
        entity_repository,
        mock_neo4j_client
    ):
        """Test graph operations handle Neo4j failures gracefully."""
        entity_id = str(uuid4())
        mock_neo4j_client.query = AsyncMock(
            side_effect=Exception("Graph query failed")
        )
        
        with pytest.raises(RepositoryError):
            await entity_repository.get_related(entity_id)
        
        with pytest.raises(RepositoryError):
            await entity_repository.get_neighbors(entity_id)

    @pytest.mark.asyncio
    async def test_invalid_entity_type_validation(
        self,
        entity_repository,
        mock_neo4j_client
    ):
        """Test validation of invalid entity types."""
        # This test ensures entity type validation happens at the model level
        with pytest.raises(ValueError):
            Entity(
                name="Invalid Entity",
                entity_type="invalid_type",  # Should fail validation
                source_document_id=uuid4()
            )

    @pytest.mark.asyncio
    async def test_relationship_consistency_validation(
        self,
        entity_repository,
        sample_entity
    ):
        """Test relationship data consistency validation."""
        # Test invalid relationship data
        with pytest.raises(ValueError):
            RelationshipData(
                target_entity_id=uuid4(),
                relationship_type="",  # Should fail validation
                confidence=0.5
            )
        
        # Test confidence out of range
        with pytest.raises(ValueError):
            RelationshipData(
                target_entity_id=uuid4(),
                relationship_type="TEACHER_OF",
                confidence=1.5  # Should fail validation
            )


class TestEntityRepositoryPhilosophicalIntegration:
    """Test philosophical-specific features and integration scenarios."""

    @pytest.fixture
    def mock_neo4j_client(self):
        """Provide mock Neo4j client for philosophical testing."""
        return MagicMock(spec=Neo4jClient)

    @pytest.fixture
    def mock_weaviate_client(self):
        """Provide mock Weaviate client for philosophical testing."""
        return MagicMock(spec=WeaviateClient)

    @pytest.fixture
    def entity_repository(self, mock_neo4j_client, mock_weaviate_client):
        """Provide EntityRepository for philosophical testing."""
        return EntityRepository(
            neo4j_client=mock_neo4j_client,
            weaviate_client=mock_weaviate_client
        )

    @pytest.fixture
    def philosophical_entities(self):
        """Provide comprehensive philosophical entity set."""
        doc_id = uuid4()
        
        return [
            # Philosophers
            Entity(
                id=uuid4(),
                name="Socrates",
                entity_type=EntityType.PERSON,
                source_document_id=doc_id,
                canonical_form="Socrates of Athens",
                aliases=["Sokrates"],
                description="Classical Greek philosopher known for the Socratic method"
            ),
            # Concepts
            Entity(
                id=uuid4(),
                name="Justice",
                entity_type=EntityType.CONCEPT,
                source_document_id=doc_id,
                description="The virtue of giving each their due"
            ),
            # Places
            Entity(
                id=uuid4(),
                name="Academy",
                entity_type=EntityType.PLACE,
                source_document_id=doc_id,
                description="Plato's philosophical school in Athens"
            ),
            # Works
            Entity(
                id=uuid4(),
                name="Republic",
                entity_type=EntityType.WORK,
                source_document_id=doc_id,
                canonical_form="The Republic",
                description="Plato's dialogue on justice and the ideal state"
            )
        ]

    @pytest.mark.asyncio
    async def test_entity_type_distribution_query(
        self,
        entity_repository,
        mock_neo4j_client,
        philosophical_entities
    ):
        """Test querying entities by type for philosophical analysis."""
        for entity_type in EntityType:
            filtered_entities = [
                e for e in philosophical_entities 
                if e.entity_type == entity_type
            ]
            
            mock_neo4j_client.query = AsyncMock(
                return_value=[{"e": e.model_dump()} for e in filtered_entities]
            )
            
            results = await entity_repository.get_by_type(entity_type)
            
            # Verify correct entity type filtering
            for result in results:
                assert result.entity_type == entity_type

    @pytest.mark.asyncio
    async def test_canonical_form_and_alias_search(
        self,
        entity_repository,
        mock_neo4j_client,
        philosophical_entities
    ):
        """Test searching by canonical forms and aliases."""
        socrates = philosophical_entities[0]
        mock_neo4j_client.query = AsyncMock(
            return_value=[{"e": socrates.model_dump()}]
        )
        
        # Test search by canonical form
        results = await entity_repository.get_by_name("Socrates of Athens")
        
        # Verify query includes canonical form and aliases
        query_call = mock_neo4j_client.query.call_args[0][0]
        assert "canonical_form" in query_call or "aliases" in query_call
        
        assert len(results) == 1
        assert results[0].canonical_form == "Socrates of Athens"

    @pytest.mark.asyncio
    async def test_vectorizable_text_generation(
        self,
        entity_repository,
        mock_weaviate_client,
        philosophical_entities
    ):
        """Test vectorizable text generation for philosophical entities."""
        socrates = philosophical_entities[0]
        
        # Mock Weaviate call
        mock_weaviate_client.save_entity = AsyncMock()
        
        # Test that vectorizable text includes all relevant fields
        vectorizable_text = socrates.get_vectorizable_text()
        
        assert "Socrates" in vectorizable_text
        assert "Classical Greek philosopher" in vectorizable_text
        assert "Sokrates" in vectorizable_text
        assert "Socrates of Athens" in vectorizable_text

    @pytest.mark.asyncio
    async def test_confidence_weighted_search_results(
        self,
        entity_repository,
        mock_neo4j_client,
        philosophical_entities
    ):
        """Test that high-confidence entities are prioritized."""
        # Set different confidence levels
        philosophical_entities[0].confidence = 0.95  # Socrates - high confidence
        philosophical_entities[1].confidence = 0.60  # Justice - medium confidence
        
        mock_neo4j_client.query = AsyncMock(
            return_value=[{"e": e.model_dump()} for e in philosophical_entities[:2]]
        )
        
        results = await entity_repository.list_all()
        
        # Verify query includes confidence-based ordering
        query_call = mock_neo4j_client.query.call_args[0][0]
        assert "confidence" in query_call.lower() or "created_at" in query_call

    @pytest.mark.asyncio
    async def test_mention_integration_with_entities(
        self,
        entity_repository,
        philosophical_entities
    ):
        """Test that mention data enhances entity confidence and context."""
        socrates = philosophical_entities[0]
        
        # Add mentions to entity
        mention1 = MentionData(
            text="Socrates",
            context="Socrates was a great philosopher",
            start_position=0,
            end_position=8,
            confidence=0.9,
            document_id=socrates.source_document_id
        )
        
        mention2 = MentionData(
            text="Sokrates",
            context="In Greek, Sokrates means...",
            start_position=10,
            end_position=18,
            confidence=0.85,
            document_id=socrates.source_document_id
        )
        
        socrates.add_mention(mention1)
        socrates.add_mention(mention2)
        
        # Verify mention integration
        assert socrates.mention_count == 2
        assert socrates.average_mention_confidence == 0.875
        
        # Verify mentions don't create duplicates
        socrates.add_mention(mention1)  # Same mention
        assert socrates.mention_count == 2  # Should not increase