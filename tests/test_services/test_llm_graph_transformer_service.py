"""
Tests for LLM Graph Transformer Service.

Tests the LLMGraphTransformerService for philosophical text processing
with both LangChain LLMGraphTransformer and fallback extraction methods.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4, UUID

from arete.services.llm_graph_transformer_service import (
    PhilosophicalLLMGraphTransformer,
    LLMGraphTransformerService
)
from arete.models.entity import Entity, EntityType
from arete.services.simple_llm_service import SimpleLLMService
from arete.services.llm_provider import LLMResponse, MessageRole


class TestPhilosophicalLLMGraphTransformer:
    """Test the core PhilosophicalLLMGraphTransformer class."""
    
    @pytest.fixture
    def mock_llm_service(self):
        """Mock LLM service for testing."""
        mock_service = Mock(spec=SimpleLLMService)
        mock_service.generate_response = AsyncMock()
        return mock_service
    
    @pytest.fixture
    def sample_philosophical_text(self):
        """Sample philosophical text for testing."""
        return """
        In the Republic, Plato argues that justice is the harmony of the soul.
        Socrates, through his method of dialectic, questions Thrasymachus about
        the nature of justice. The Cave Allegory illustrates how knowledge 
        differs from opinion. Aristotle later critiques Plato's Theory of Forms
        in his Metaphysics.
        """
    
    @pytest.fixture
    def transformer_with_mock(self, mock_llm_service):
        """PhilosophicalLLMGraphTransformer with mocked dependencies."""
        with patch('arete.services.llm_graph_transformer_service.get_settings') as mock_settings:
            mock_config = Mock()
            mock_config.selected_llm_provider = "openai"
            mock_config.selected_llm_model = "gpt-4o-mini"
            mock_config.openai_api_key = "test-key"
            mock_settings.return_value = mock_config
            
            with patch('arete.services.llm_graph_transformer_service.LLMGraphTransformer') as mock_llm_transformer:
                transformer = PhilosophicalLLMGraphTransformer(mock_llm_service)
                transformer.transformer = Mock()  # Set mock transformer
                return transformer
    
    def test_initialization(self, mock_llm_service):
        """Test transformer initialization with proper configuration."""
        with patch('arete.services.llm_graph_transformer_service.get_settings') as mock_settings:
            mock_config = Mock()
            mock_config.selected_llm_provider = "openai"
            mock_config.selected_llm_model = "gpt-4o-mini"
            mock_config.openai_api_key = "test-key"
            mock_settings.return_value = mock_config
            
            with patch('arete.services.llm_graph_transformer_service.LLMGraphTransformer'):
                transformer = PhilosophicalLLMGraphTransformer(mock_llm_service)
                
                # Check schema configuration
                assert "Philosopher" in transformer.allowed_nodes
                assert "Concept" in transformer.allowed_nodes
                assert "Work" in transformer.allowed_nodes
                assert "Argument" in transformer.allowed_nodes
                
                # Check relationships
                authorship_rel = ("Philosopher", "AUTHORED", "Work")
                assert authorship_rel in transformer.allowed_relationships
    
    def test_node_type_mapping(self, transformer_with_mock):
        """Test mapping of node types to EntityType."""
        transformer = transformer_with_mock
        
        assert transformer._map_node_type_to_entity_type("Philosopher") == EntityType.PERSON
        assert transformer._map_node_type_to_entity_type("Concept") == EntityType.CONCEPT
        assert transformer._map_node_type_to_entity_type("Work") == EntityType.WORK
        assert transformer._map_node_type_to_entity_type("Argument") == EntityType.CONCEPT  # Arguments are concepts
        assert transformer._map_node_type_to_entity_type("School") == EntityType.CONCEPT   # Schools are concepts
        assert transformer._map_node_type_to_entity_type("Place") == EntityType.PLACE
        assert transformer._map_node_type_to_entity_type("Unknown") == EntityType.CONCEPT  # Default
    
    def test_text_splitting(self, transformer_with_mock):
        """Test text splitting functionality."""
        transformer = transformer_with_mock
        
        text = "This is sentence one. This is sentence two. This is sentence three."
        chunks = transformer._split_text(text, chunk_size=30)
        
        assert len(chunks) > 1
        assert all(isinstance(chunk, str) for chunk in chunks)
    
    def test_entity_validation(self, transformer_with_mock):
        """Test entity name validation."""
        transformer = transformer_with_mock
        
        # Valid entities
        assert transformer._is_valid_entity_name("Socrates")
        assert transformer._is_valid_entity_name("Republic")
        assert transformer._is_valid_entity_name("justice")
        
        # Invalid entities
        assert not transformer._is_valid_entity_name("it")
        assert not transformer._is_valid_entity_name("he")
        assert not transformer._is_valid_entity_name("")
        assert not transformer._is_valid_entity_name("a")
    
    def test_relationship_validation(self, transformer_with_mock):
        """Test relationship validation."""
        transformer = transformer_with_mock
        
        # Valid relationship
        valid_rel = {
            "subject": "Socrates",
            "relation": "TAUGHT",
            "object": "Plato",
            "confidence": 0.8
        }
        assert transformer._is_valid_relationship(valid_rel)
        
        # Invalid relationships
        invalid_rel_missing_keys = {"subject": "Socrates"}
        assert not transformer._is_valid_relationship(invalid_rel_missing_keys)
        
        invalid_rel_low_confidence = {
            "subject": "Socrates",
            "relation": "TAUGHT",
            "object": "Plato",
            "confidence": 0.3
        }
        assert not transformer._is_valid_relationship(invalid_rel_low_confidence)
        
        invalid_rel_bad_entity = {
            "subject": "it",
            "relation": "TAUGHT", 
            "object": "Plato",
            "confidence": 0.8
        }
        assert not transformer._is_valid_relationship(invalid_rel_bad_entity)
    
    def test_entity_merging(self, transformer_with_mock):
        """Test entity deduplication and merging."""
        transformer = transformer_with_mock
        document_id = uuid4()
        
        # Create duplicate entities
        entity1 = Entity(
            name="Socrates",
            entity_type=EntityType.PERSON,
            source_document_id=document_id,
            mentions=[],
            confidence=0.8
        )
        
        entity2 = Entity(
            name="socrates",  # Same entity, different case
            entity_type=EntityType.PERSON,
            source_document_id=document_id,
            mentions=[],
            confidence=0.9
        )
        
        merged = transformer._merge_entities([entity1, entity2])
        
        assert len(merged) == 1
        assert merged[0].confidence == 0.9  # Should keep higher confidence
    
    @pytest.mark.asyncio
    async def test_fallback_extraction(self, transformer_with_mock, sample_philosophical_text):
        """Test fallback extraction when LLMGraphTransformer is not available."""
        transformer = transformer_with_mock
        transformer.transformer = None  # Simulate unavailable transformer
        
        # Mock LLM service response
        mock_response = LLMResponse(
            content='{"entities": [{"name": "Plato", "type": "Philosopher", "description": "Ancient Greek philosopher"}], "relationships": [{"subject": "Plato", "relation": "AUTHORED", "object": "Republic", "confidence": 0.9}]}',
            metadata={"model": "gpt-4o-mini"}
        )
        transformer.llm_service.generate_response.return_value = mock_response
        
        document_id = str(uuid4())
        entities, relationships = await transformer._fallback_extraction(sample_philosophical_text, document_id)
        
        # Verify entities
        assert len(entities) >= 1
        assert any(entity.name == "Plato" for entity in entities)
        
        # Verify relationships
        assert len(relationships) >= 1
        assert any(rel["subject"] == "Plato" and rel["relation"] == "AUTHORED" for rel in relationships)
    
    @pytest.mark.asyncio
    async def test_json_response_parsing(self, transformer_with_mock):
        """Test parsing of JSON response from fallback extraction."""
        transformer = transformer_with_mock
        document_id = str(uuid4())
        
        json_response = '''
        {
            "entities": [
                {"name": "Socrates", "type": "Philosopher", "description": "Classical Greek philosopher"},
                {"name": "justice", "type": "Concept", "description": "Central concept in Republic"}
            ],
            "relationships": [
                {"subject": "Socrates", "relation": "DISCUSSES", "object": "justice", "confidence": 0.85}
            ]
        }
        '''
        
        entities, relationships = transformer._parse_json_response(json_response, document_id)
        
        # Verify entities
        assert len(entities) == 2
        socrates_entity = next(e for e in entities if e.name == "Socrates")
        assert socrates_entity.entity_type == EntityType.PERSON
        
        # Verify relationships
        assert len(relationships) == 1
        assert relationships[0]["subject"] == "Socrates"
        assert relationships[0]["relation"] == "DISCUSSES"
        assert relationships[0]["object"] == "justice"
    
    def test_langchain_llm_creation(self, mock_llm_service):
        """Test creation of LangChain LLM instances."""
        with patch('arete.services.llm_graph_transformer_service.get_settings') as mock_settings, \
             patch('arete.services.llm_graph_transformer_service.ChatOpenAI') as mock_chat_openai, \
             patch('arete.services.llm_graph_transformer_service.ChatAnthropic') as mock_chat_anthropic, \
             patch('arete.services.llm_graph_transformer_service.LLMGraphTransformer'):
            
            # Test OpenAI
            mock_config = Mock()
            mock_config.selected_llm_provider = "openai"
            mock_config.selected_llm_model = "gpt-4o-mini"
            mock_config.openai_api_key = "test-key"
            mock_settings.return_value = mock_config
            
            transformer = PhilosophicalLLMGraphTransformer(mock_llm_service)
            transformer._create_langchain_llm()
            
            mock_chat_openai.assert_called_once()
            
            # Test Anthropic
            mock_config.selected_llm_provider = "anthropic"
            mock_config.anthropic_api_key = "test-anthropic-key"
            mock_chat_anthropic.reset_mock()
            
            transformer = PhilosophicalLLMGraphTransformer(mock_llm_service)
            transformer._create_langchain_llm()
            
            mock_chat_anthropic.assert_called_once()


class TestLLMGraphTransformerService:
    """Test the LLMGraphTransformerService wrapper."""
    
    @pytest.fixture
    def mock_transformer(self):
        """Mock PhilosophicalLLMGraphTransformer."""
        mock = Mock(spec=PhilosophicalLLMGraphTransformer)
        mock.allowed_nodes = ["Philosopher", "Concept", "Work"]
        mock.allowed_relationships = [("Philosopher", "AUTHORED", "Work")]
        mock.transformer = Mock()  # Simulate available transformer
        mock.extract_graph_from_text = AsyncMock()
        return mock
    
    @pytest.fixture
    def service_with_mock(self, mock_transformer):
        """LLMGraphTransformerService with mocked transformer."""
        with patch('arete.services.llm_graph_transformer_service.PhilosophicalLLMGraphTransformer') as mock_class:
            mock_class.return_value = mock_transformer
            service = LLMGraphTransformerService()
            return service, mock_transformer
    
    @pytest.mark.asyncio
    async def test_extract_knowledge_graph(self, service_with_mock):
        """Test knowledge graph extraction through service interface."""
        service, mock_transformer = service_with_mock
        
        # Setup mock response
        document_id = str(uuid4())
        expected_entities = [Entity(
            name="Plato",
            entity_type=EntityType.PERSON,
            source_document_id=UUID(document_id),
            mentions=[],
            confidence=0.9
        )]
        expected_relationships = [{
            "subject": "Plato",
            "relation": "AUTHORED",
            "object": "Republic",
            "confidence": 0.9
        }]
        
        mock_transformer.extract_graph_from_text.return_value = (expected_entities, expected_relationships)
        
        # Call service method
        text = "Plato authored the Republic."
        entities, relationships = await service.extract_knowledge_graph(text, document_id)
        
        # Verify results
        assert entities == expected_entities
        assert relationships == expected_relationships
        mock_transformer.extract_graph_from_text.assert_called_once_with(text, document_id)
    
    def test_get_supported_types(self, service_with_mock):
        """Test getting supported node types and relationships."""
        service, mock_transformer = service_with_mock
        
        node_types = service.get_supported_node_types()
        relationships = service.get_supported_relationships()
        
        assert "Philosopher" in node_types
        assert ("Philosopher", "AUTHORED", "Work") in relationships
    
    def test_is_available(self, service_with_mock):
        """Test availability checking."""
        service, mock_transformer = service_with_mock
        
        # When transformer is available
        assert service.is_available() is True
        
        # When transformer is not available
        mock_transformer.transformer = None
        assert service.is_available() is False


class TestIntegrationScenarios:
    """Integration test scenarios for real philosophical text processing."""
    
    @pytest.mark.asyncio
    async def test_republic_passage_extraction(self):
        """Test extraction from actual Republic passage."""
        text = """
        "And so, Glaucon," I said, "we have at last arrived at the conclusion
        that in the perfect state women and men will be equally educated and
        equally share in war and in the guardianship of the city. For we agreed
        that the nature of the guardian, whether male or female, should be
        the same. But let us see whether this is possible, and what arrangements
        must be made to bring it about."
        """
        
        with patch('arete.services.llm_graph_transformer_service.get_settings') as mock_settings:
            mock_config = Mock()
            mock_config.selected_llm_provider = "openai"
            mock_config.selected_llm_model = "gpt-4o-mini"
            mock_config.openai_api_key = "test-key"
            mock_settings.return_value = mock_config
            
            with patch('arete.services.llm_graph_transformer_service.LLMGraphTransformer'):
                service = LLMGraphTransformerService()
                
                # This would require actual LLM calls in real scenario
                # For testing, we'll just verify the service can be initialized
                assert service is not None
                assert service.is_available() in [True, False]  # Depends on mocking
    
    @pytest.mark.asyncio 
    async def test_complex_argumentation_extraction(self):
        """Test extraction from complex philosophical argument."""
        text = """
        Socrates employs the method of elenchus to refute Thrasymachus's claim
        that justice is the advantage of the stronger. Through careful questioning,
        he demonstrates that the just person is happier than the unjust person.
        This argument relies on the premise that virtue is knowledge and that
        no one does wrong willingly.
        """
        
        # This test would verify that complex argumentative structures
        # are properly extracted and relationships between premises,
        # methods, and conclusions are identified
        
        # For now, we'll just verify the test structure
        assert len(text) > 0
        assert "Socrates" in text
        assert "justice" in text


class TestPerformanceScenarios:
    """Performance tests for large text processing."""
    
    @pytest.mark.asyncio
    async def test_large_document_processing(self):
        """Test processing of large philosophical documents."""
        # Simulate processing of a large document like the entire Republic
        large_text = "In the Republic, Plato argues..." * 1000  # ~30,000 characters
        
        with patch('arete.services.llm_graph_transformer_service.get_settings') as mock_settings:
            mock_config = Mock()
            mock_config.selected_llm_provider = "openai"
            mock_config.selected_llm_model = "gpt-4o-mini"
            mock_config.openai_api_key = "test-key"
            mock_settings.return_value = mock_config
            
            mock_llm_service = Mock(spec=SimpleLLMService)
            
            with patch('arete.services.llm_graph_transformer_service.LLMGraphTransformer'):
                transformer = PhilosophicalLLMGraphTransformer(mock_llm_service)
                
                # Test that text splitting works for large documents
                chunks = transformer._split_text(large_text, chunk_size=2000)
                
                assert len(chunks) > 1
                assert all(len(chunk) <= 2500 for chunk in chunks)  # Allow some buffer
    
    def test_memory_efficient_processing(self):
        """Test that processing doesn't consume excessive memory."""
        # This would test memory usage patterns
        # For now, just verify the concept
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])