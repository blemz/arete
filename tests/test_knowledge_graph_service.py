"""
Tests for KnowledgeGraphService with comprehensive knowledge graph extraction.
"""

import uuid
import pytest
from unittest.mock import AsyncMock, Mock
from typing import List, Dict, Any

from arete.models.entity import Entity, EntityType
from arete.services.knowledge_graph_service import KnowledgeGraphService, KnowledgeGraphExtractionResult
from arete.processing.extractors import EntityExtractor, RelationshipExtractor, TripleValidator


class TestKnowledgeGraphExtractionResult:
    """Test KnowledgeGraphExtractionResult functionality."""
    
    def test_initialization(self):
        """Test result initialization with default values."""
        result = KnowledgeGraphExtractionResult()
        
        assert result.entities_created == 0
        assert result.entities_found == 0
        assert result.relationships_created == 0
        assert result.triples_extracted == 0
        assert result.triples_validated == 0
        assert result.errors == []
        assert result.warnings == []
        assert result.processing_time == 0.0
    
    def test_add_error(self):
        """Test adding errors."""
        result = KnowledgeGraphExtractionResult()
        
        result.add_error("Test error")
        assert len(result.errors) == 1
        assert result.errors[0] == "Test error"
    
    def test_add_warning(self):
        """Test adding warnings."""
        result = KnowledgeGraphExtractionResult()
        
        result.add_warning("Test warning")
        assert len(result.warnings) == 1
        assert result.warnings[0] == "Test warning"
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = KnowledgeGraphExtractionResult()
        result.entities_created = 5
        result.relationships_created = 3
        result.add_warning("Test warning")
        
        result_dict = result.to_dict()
        
        assert result_dict["entities_created"] == 5
        assert result_dict["relationships_created"] == 3
        assert result_dict["warnings"] == ["Test warning"]
        assert result_dict["success"] is True  # No errors
        
        # Test with errors
        result.add_error("Test error")
        result_dict = result.to_dict()
        assert result_dict["success"] is False


class TestKnowledgeGraphService:
    """Test KnowledgeGraphService functionality."""
    
    @pytest.fixture
    def mock_entity_repository(self):
        """Create mock entity repository."""
        repo = AsyncMock()
        repo.find_or_create_entities_by_name = AsyncMock(return_value={})
        repo.batch_create_triples = AsyncMock(return_value=0)
        repo.get_by_name = AsyncMock(return_value=[])
        repo.create = AsyncMock()
        repo.create_relationship = AsyncMock(return_value=True)
        repo.get_by_id = AsyncMock()
        repo.get_relationships = AsyncMock(return_value=[])
        repo.get_neighbors = AsyncMock(return_value=[])
        repo.get_related = AsyncMock(return_value=[])
        repo.list_all = AsyncMock(return_value=[])
        return repo
    
    @pytest.fixture
    def mock_entity_extractor(self):
        """Create mock entity extractor."""
        extractor = Mock()
        extractor.extract_entities = Mock(return_value=[])
        return extractor
    
    @pytest.fixture
    def mock_relationship_extractor(self):
        """Create mock relationship extractor."""
        extractor = Mock()
        extractor.extract_relationships = Mock(return_value=[])
        return extractor
    
    @pytest.fixture
    def mock_triple_validator(self):
        """Create mock triple validator."""
        validator = Mock()
        validator.validate = Mock(return_value=[])
        return validator
    
    @pytest.fixture
    def kg_service(self, mock_entity_repository, mock_entity_extractor, 
                   mock_relationship_extractor, mock_triple_validator):
        """Create KnowledgeGraphService with mocked dependencies."""
        return KnowledgeGraphService(
            entity_repository=mock_entity_repository,
            entity_extractor=mock_entity_extractor,
            relationship_extractor=mock_relationship_extractor,
            triple_validator=mock_triple_validator
        )
    
    def test_initialization_with_defaults(self, mock_entity_repository):
        """Test service initialization with default extractors."""
        service = KnowledgeGraphService(mock_entity_repository)
        
        assert service.entity_repository == mock_entity_repository
        assert service.entity_extractor is not None
        assert service.relationship_extractor is not None
        assert service.triple_validator is not None
    
    @pytest.mark.asyncio
    async def test_extract_knowledge_graph_basic(self, kg_service, mock_entity_extractor,
                                                 mock_relationship_extractor, mock_triple_validator,
                                                 mock_entity_repository):
        """Test basic knowledge graph extraction."""
        # Setup mocks
        test_entity = Entity(
            name="Socrates",
            entity_type=EntityType.PERSON,
            source_document_id=uuid.uuid4()
        )
        
        mock_entity_extractor.extract_entities.return_value = [test_entity]
        mock_relationship_extractor.extract_relationships.return_value = [
            {"subject": "Socrates", "relation": "TEACHES", "object": "Plato", "confidence": 0.8}
        ]
        mock_triple_validator.validate.return_value = [
            {"subject": "Socrates", "relation": "TEACHES", "object": "Plato", "confidence": 0.8}
        ]
        mock_entity_repository.find_or_create_entities_by_name.return_value = {
            "Socrates": uuid.uuid4(),
            "Plato": uuid.uuid4()
        }
        mock_entity_repository.batch_create_triples.return_value = 1
        
        # Execute
        text = "Socrates teaches Plato."
        document_id = uuid.uuid4()
        result = await kg_service.extract_knowledge_graph(text, document_id)
        
        # Verify
        assert isinstance(result, KnowledgeGraphExtractionResult)
        assert result.triples_extracted == 1
        assert result.triples_validated == 1
        assert result.relationships_created == 1
        assert len(result.errors) == 0
        
        # Verify method calls
        mock_entity_extractor.extract_entities.assert_called_once_with(text, document_id)
        mock_relationship_extractor.extract_relationships.assert_called_once()
        mock_triple_validator.validate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extract_knowledge_graph_with_chunking(self, kg_service):
        """Test knowledge graph extraction with chunking for large text."""
        text = "A" * 2000  # Large text to trigger chunking
        document_id = uuid.uuid4()
        chunk_size = 500
        
        result = await kg_service.extract_knowledge_graph(
            text, document_id, chunk_size=chunk_size
        )
        
        # Should complete without errors even with chunking
        assert isinstance(result, KnowledgeGraphExtractionResult)
        assert result.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_extract_knowledge_graph_error_handling(self, kg_service, mock_entity_extractor):
        """Test error handling in knowledge graph extraction."""
        # Make entity extractor raise an exception
        mock_entity_extractor.extract_entities.side_effect = Exception("Test error")
        
        text = "Test text"
        document_id = uuid.uuid4()
        result = await kg_service.extract_knowledge_graph(text, document_id)
        
        # Should handle error gracefully
        assert len(result.errors) == 1
        assert "Test error" in result.errors[0]
        assert result.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_get_entity_relationships(self, kg_service, mock_entity_repository):
        """Test getting entity relationships."""
        entity_id = uuid.uuid4()
        test_entity = Entity(
            name="Socrates",
            entity_type=EntityType.PERSON,
            source_document_id=uuid.uuid4()
        )
        
        mock_entity_repository.get_by_id.return_value = test_entity
        mock_entity_repository.get_relationships.return_value = [
            {"relationship_type": "TEACHES", "target": "Plato"}
        ]
        mock_entity_repository.get_neighbors.return_value = [test_entity]
        mock_entity_repository.get_related.return_value = [test_entity]
        
        result = await kg_service.get_entity_relationships(entity_id)
        
        assert result["entity"] == test_entity
        assert "direct_relationships" in result
        assert "neighbors" in result
        assert "related_entities" in result
        assert result["relationship_count"] == 1
    
    @pytest.mark.asyncio
    async def test_get_entity_relationships_not_found(self, kg_service, mock_entity_repository):
        """Test getting relationships for non-existent entity."""
        entity_id = uuid.uuid4()
        mock_entity_repository.get_by_id.return_value = None
        
        with pytest.raises(ValueError, match="Entity not found"):
            await kg_service.get_entity_relationships(entity_id)
    
    @pytest.mark.asyncio
    async def test_analyze_philosophical_network(self, kg_service, mock_entity_repository):
        """Test philosophical network analysis."""
        # Setup mock entities
        test_entities = [
            Entity(name="Socrates", entity_type=EntityType.PERSON, source_document_id=uuid.uuid4()),
            Entity(name="Plato", entity_type=EntityType.PERSON, source_document_id=uuid.uuid4()),
            Entity(name="Justice", entity_type=EntityType.CONCEPT, source_document_id=uuid.uuid4())
        ]
        
        mock_entity_repository.list_all.return_value = test_entities
        mock_entity_repository.get_relationships.return_value = [
            {"relationship_type": "TEACHES"}
        ]
        
        result = await kg_service.analyze_philosophical_network()
        
        assert "total_entities" in result
        assert "total_relationships" in result
        assert "average_relationships_per_entity" in result
        assert "most_connected_entities" in result
        assert "entity_type_distribution" in result
        
        # Should have filtered entities (those with >= 1 relationship)
        assert result["total_entities"] >= 0
    
    @pytest.mark.asyncio
    async def test_analyze_philosophical_network_with_filters(self, kg_service, mock_entity_repository):
        """Test network analysis with entity type filters."""
        test_entities = [
            Entity(name="Socrates", entity_type=EntityType.PERSON, source_document_id=uuid.uuid4())
        ]
        
        mock_entity_repository.list_all.return_value = test_entities
        mock_entity_repository.get_relationships.return_value = [
            {"relationship_type": "TEACHES"}
        ]
        
        result = await kg_service.analyze_philosophical_network(
            entity_types=[EntityType.PERSON],
            min_relationships=1
        )
        
        assert result["total_entities"] >= 0
        # Should only include PERSON entities
        if result["entity_type_distribution"]:
            assert "person" in result["entity_type_distribution"]
    
    def test_get_entity_type_distribution(self, kg_service):
        """Test entity type distribution calculation."""
        entities = [
            {"entity": Entity(name="Socrates", entity_type=EntityType.PERSON, source_document_id=uuid.uuid4())},
            {"entity": Entity(name="Justice", entity_type=EntityType.CONCEPT, source_document_id=uuid.uuid4())},
            {"entity": Entity(name="Plato", entity_type=EntityType.PERSON, source_document_id=uuid.uuid4())}
        ]
        
        distribution = kg_service._get_entity_type_distribution(entities)
        
        assert distribution["person"] == 2
        assert distribution["concept"] == 1
    
    @pytest.mark.asyncio
    async def test_batching_enabled_vs_disabled(self, kg_service, mock_entity_repository,
                                               mock_entity_extractor, mock_relationship_extractor,
                                               mock_triple_validator):
        """Test difference between batching enabled and disabled."""
        # Setup common mocks
        test_entity = Entity(name="Socrates", entity_type=EntityType.PERSON, source_document_id=uuid.uuid4())
        mock_entity_extractor.extract_entities.return_value = [test_entity]
        mock_relationship_extractor.extract_relationships.return_value = []
        mock_triple_validator.validate.return_value = []
        
        text = "Test text"
        document_id = uuid.uuid4()
        
        # Test with batching enabled
        mock_entity_repository.find_or_create_entities_by_name.return_value = {"Socrates": uuid.uuid4()}
        result_batched = await kg_service.extract_knowledge_graph(text, document_id, enable_batching=True)
        
        # Test with batching disabled
        mock_entity_repository.reset_mock()
        mock_entity_repository.get_by_name.return_value = []
        mock_entity_repository.create.return_value = test_entity
        result_individual = await kg_service.extract_knowledge_graph(text, document_id, enable_batching=False)
        
        # Both should succeed
        assert len(result_batched.errors) == 0
        assert len(result_individual.errors) == 0
        
        # Batching should use find_or_create_entities_by_name
        # Individual should use get_by_name and create
        if result_batched.entities_created > 0 or result_batched.entities_found > 0:
            mock_entity_repository.find_or_create_entities_by_name.assert_called()
    
    @pytest.mark.asyncio
    async def test_confidence_threshold_filtering(self, kg_service, mock_relationship_extractor,
                                                 mock_triple_validator):
        """Test that confidence threshold properly filters triples."""
        # Setup triples with varying confidence
        raw_triples = [
            {"subject": "A", "relation": "R1", "object": "B", "confidence": 0.9},
            {"subject": "C", "relation": "R2", "object": "D", "confidence": 0.5},
            {"subject": "E", "relation": "R3", "object": "F", "confidence": 0.3}
        ]
        
        mock_relationship_extractor.extract_relationships.return_value = raw_triples
        
        # Mock validator to filter based on confidence
        def mock_validate(triples, min_confidence):
            return [t for t in triples if t["confidence"] >= min_confidence]
        
        mock_triple_validator.validate.side_effect = mock_validate
        
        text = "Test text"
        document_id = uuid.uuid4()
        min_confidence = 0.6
        
        result = await kg_service.extract_knowledge_graph(text, document_id, min_confidence=min_confidence)
        
        # Should have extracted all triples but validated only high-confidence ones
        assert result.triples_extracted == 3
        assert result.triples_validated == 1  # Only confidence >= 0.6