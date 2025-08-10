"""
Tests for Arete Entity model.
Following TDD principles - tests written before implementation (RED phase).
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List

import pytest
from pydantic import ValidationError

from arete.models.entity import Entity, EntityType, MentionData, RelationshipData


class TestEntityType:
    """Test suite for EntityType enum."""

    def test_entity_type_values(self):
        """Test all EntityType enum values."""
        assert EntityType.PERSON == "person"
        assert EntityType.CONCEPT == "concept"
        assert EntityType.PLACE == "place"
        assert EntityType.WORK == "work"

    def test_entity_type_iteration(self):
        """Test that all entity types can be iterated."""
        entity_types = list(EntityType)
        assert len(entity_types) == 4
        assert EntityType.PERSON in entity_types
        assert EntityType.CONCEPT in entity_types
        assert EntityType.PLACE in entity_types
        assert EntityType.WORK in entity_types

    def test_entity_type_case_insensitive(self):
        """Test that entity types handle case variations."""
        # This will test that the enum can handle string inputs properly
        assert EntityType("person") == EntityType.PERSON
        assert EntityType("CONCEPT") == EntityType.CONCEPT


class TestMentionData:
    """Test suite for MentionData model."""

    def test_mention_data_creation_with_valid_data(self, sample_mention_data):
        """Test basic MentionData creation with valid data."""
        mention = MentionData(**sample_mention_data)
        
        assert mention.text == "Socrates"
        assert mention.context == "As Socrates once said, the unexamined life is not worth living."
        assert mention.start_position == 3
        assert mention.end_position == 11
        assert mention.confidence == 0.95
        assert isinstance(mention.document_id, uuid.UUID)

    def test_mention_data_validation_text_required(self):
        """Test that text field is required."""
        mention_data = {
            "context": "Some context",
            "start_position": 0,
            "end_position": 5,
            "confidence": 0.8,
            "document_id": uuid.uuid4()
        }
        
        with pytest.raises(ValidationError) as exc_info:
            MentionData(**mention_data)
        assert "text" in str(exc_info.value)

    def test_mention_data_validation_empty_text(self):
        """Test that empty text is not allowed."""
        mention_data = {
            "text": "",
            "context": "Some context",
            "start_position": 0,
            "end_position": 5,
            "confidence": 0.8,
            "document_id": uuid.uuid4()
        }
        
        with pytest.raises(ValidationError) as exc_info:
            MentionData(**mention_data)
        assert "at least 1 character" in str(exc_info.value)

    def test_mention_data_confidence_range_validation(self):
        """Test confidence score validation (0.0-1.0)."""
        base_data = {
            "text": "Plato",
            "context": "Plato wrote the Republic",
            "start_position": 0,
            "end_position": 5,
            "document_id": uuid.uuid4()
        }

        # Test confidence too low
        with pytest.raises(ValidationError) as exc_info:
            MentionData(confidence=-0.1, **base_data)
        assert "greater than or equal to 0" in str(exc_info.value)

        # Test confidence too high
        with pytest.raises(ValidationError) as exc_info:
            MentionData(confidence=1.1, **base_data)
        assert "less than or equal to 1" in str(exc_info.value)

        # Test valid boundary values
        low_mention = MentionData(confidence=0.0, **base_data)
        assert low_mention.confidence == 0.0

        high_mention = MentionData(confidence=1.0, **base_data)
        assert high_mention.confidence == 1.0

    def test_mention_data_position_validation(self):
        """Test start and end position validation."""
        base_data = {
            "text": "Aristotle",
            "context": "Aristotle was Plato's student",
            "confidence": 0.9,
            "document_id": uuid.uuid4()
        }

        # Test negative start position
        with pytest.raises(ValidationError) as exc_info:
            MentionData(start_position=-1, end_position=5, **base_data)
        assert "greater than or equal to 0" in str(exc_info.value)

        # Test negative end position
        with pytest.raises(ValidationError) as exc_info:
            MentionData(start_position=0, end_position=-1, **base_data)
        assert "greater than or equal to 0" in str(exc_info.value)

        # Test end position less than start position
        with pytest.raises(ValidationError) as exc_info:
            MentionData(start_position=10, end_position=5, **base_data)
        assert "end_position must be greater than start_position" in str(exc_info.value)

        # Test valid positions
        mention = MentionData(start_position=0, end_position=9, **base_data)
        assert mention.start_position == 0
        assert mention.end_position == 9

    def test_mention_data_text_length_property(self):
        """Test computed text_length property."""
        mention_data = {
            "text": "Socrates",
            "context": "Context",
            "start_position": 0,
            "end_position": 8,
            "confidence": 0.9,
            "document_id": uuid.uuid4()
        }
        
        mention = MentionData(**mention_data)
        assert mention.text_length == 8


class TestRelationshipData:
    """Test suite for RelationshipData model."""

    def test_relationship_data_creation_with_valid_data(self, sample_relationship_data):
        """Test basic RelationshipData creation with valid data."""
        relationship = RelationshipData(**sample_relationship_data)
        
        assert isinstance(relationship.target_entity_id, uuid.UUID)
        assert relationship.relationship_type == "STUDENT_OF"
        assert relationship.confidence == 0.85
        assert relationship.source == "historical_records"
        assert relationship.bidirectional is False

    def test_relationship_data_validation_required_fields(self):
        """Test that required fields are validated."""
        # Missing target_entity_id
        with pytest.raises(ValidationError) as exc_info:
            RelationshipData(
                relationship_type="RELATED_TO",
                confidence=0.8
            )
        assert "target_entity_id" in str(exc_info.value)

        # Missing relationship_type
        with pytest.raises(ValidationError) as exc_info:
            RelationshipData(
                target_entity_id=uuid.uuid4(),
                confidence=0.8
            )
        assert "relationship_type" in str(exc_info.value)

    def test_relationship_data_confidence_validation(self):
        """Test confidence score validation for relationships."""
        base_data = {
            "target_entity_id": uuid.uuid4(),
            "relationship_type": "INFLUENCED_BY"
        }

        # Test confidence out of range
        with pytest.raises(ValidationError):
            RelationshipData(confidence=-0.1, **base_data)

        with pytest.raises(ValidationError):
            RelationshipData(confidence=1.5, **base_data)

        # Test valid confidence
        relationship = RelationshipData(confidence=0.75, **base_data)
        assert relationship.confidence == 0.75

    def test_relationship_data_type_validation(self):
        """Test relationship type validation."""
        base_data = {
            "target_entity_id": uuid.uuid4(),
            "confidence": 0.8
        }

        # Test empty relationship type
        with pytest.raises(ValidationError) as exc_info:
            RelationshipData(relationship_type="", **base_data)
        assert "at least 1 character" in str(exc_info.value)

        # Test whitespace-only relationship type
        with pytest.raises(ValidationError) as exc_info:
            RelationshipData(relationship_type="   ", **base_data)
        assert "at least 1 character" in str(exc_info.value)

    def test_relationship_data_defaults(self):
        """Test default values for optional fields."""
        relationship = RelationshipData(
            target_entity_id=uuid.uuid4(),
            relationship_type="RELATES_TO"
        )
        
        assert relationship.confidence == 0.5  # Default confidence
        assert relationship.source is None
        assert relationship.bidirectional is False


class TestEntity:
    """Test suite for Entity model following TDD principles."""

    def test_entity_creation_with_valid_data(self, sample_entity_data):
        """Test basic entity creation with valid data."""
        entity = Entity(**sample_entity_data)

        assert entity.name == "Socrates"
        assert entity.entity_type == EntityType.PERSON
        assert entity.confidence == 0.95
        assert entity.description == "Classical Greek philosopher"
        assert isinstance(entity.source_document_id, uuid.UUID)
        assert len(entity.mentions) == 1
        assert len(entity.relationships) == 0
        assert entity.aliases == ["Socrates of Athens"]
        assert entity.canonical_form == "Socrates"

        # Test auto-generated fields from base model
        assert isinstance(entity.id, uuid.UUID)
        assert isinstance(entity.created_at, datetime)
        assert entity.updated_at is None
        assert isinstance(entity.metadata, dict)

    def test_entity_creation_with_minimal_data(self):
        """Test entity creation with only required fields."""
        minimal_data = {
            "name": "Justice",
            "entity_type": EntityType.CONCEPT,
            "source_document_id": uuid.uuid4()
        }

        entity = Entity(**minimal_data)

        assert entity.name == "Justice"
        assert entity.entity_type == EntityType.CONCEPT
        assert entity.confidence == 0.5  # Default value
        assert entity.description is None
        assert len(entity.mentions) == 0  # Default empty list
        assert len(entity.relationships) == 0  # Default empty list
        assert entity.aliases is None
        assert entity.canonical_form == "Justice"  # Auto-computed from name

    def test_entity_name_validation(self):
        """Test name field validation rules."""
        base_data = {
            "entity_type": EntityType.PERSON,
            "source_document_id": uuid.uuid4()
        }

        # Test empty name
        with pytest.raises(ValidationError) as exc_info:
            Entity(name="", **base_data)
        assert "at least 1 character" in str(exc_info.value)

        # Test whitespace-only name
        with pytest.raises(ValidationError) as exc_info:
            Entity(name="   ", **base_data)
        assert "at least 1 character" in str(exc_info.value)

        # Test name too long (assuming max 200 chars)
        long_name = "A" * 201
        with pytest.raises(ValidationError) as exc_info:
            Entity(name=long_name, **base_data)
        assert "at most 200 characters" in str(exc_info.value)

        # Test valid name at boundary (200 chars)
        boundary_name = "A" * 200
        entity = Entity(name=boundary_name, **base_data)
        assert entity.name == boundary_name

    def test_entity_type_validation(self):
        """Test entity_type field validation."""
        base_data = {
            "name": "Aristotle",
            "source_document_id": uuid.uuid4()
        }

        # Test all valid entity types
        for entity_type in EntityType:
            entity = Entity(entity_type=entity_type, **base_data)
            assert entity.entity_type == entity_type

        # Test invalid entity type (should be handled by Pydantic)
        with pytest.raises(ValidationError):
            Entity(entity_type="INVALID_TYPE", **base_data)

    def test_entity_confidence_validation(self):
        """Test confidence score validation (0.0-1.0 range)."""
        base_data = {
            "name": "Plato",
            "entity_type": EntityType.PERSON,
            "source_document_id": uuid.uuid4()
        }

        # Test confidence too low
        with pytest.raises(ValidationError) as exc_info:
            Entity(confidence=-0.1, **base_data)
        assert "greater than or equal to 0" in str(exc_info.value)

        # Test confidence too high
        with pytest.raises(ValidationError) as exc_info:
            Entity(confidence=1.1, **base_data)
        assert "less than or equal to 1" in str(exc_info.value)

        # Test valid boundary values
        low_entity = Entity(confidence=0.0, **base_data)
        assert low_entity.confidence == 0.0

        high_entity = Entity(confidence=1.0, **base_data)
        assert high_entity.confidence == 1.0

        # Test precision (3 decimal places)
        precise_entity = Entity(confidence=0.785, **base_data)
        assert precise_entity.confidence == 0.785

    def test_entity_description_validation(self):
        """Test description field validation."""
        base_data = {
            "name": "Republic",
            "entity_type": EntityType.WORK,
            "source_document_id": uuid.uuid4()
        }

        # Test empty description should be converted to None
        entity = Entity(description="", **base_data)
        assert entity.description is None

        # Test whitespace-only description should be converted to None
        entity = Entity(description="   ", **base_data)
        assert entity.description is None

        # Test description too long
        long_description = "A" * 1001  # Assuming max 1000 chars
        with pytest.raises(ValidationError) as exc_info:
            Entity(description=long_description, **base_data)
        assert "at most 1000 characters" in str(exc_info.value)

        # Test valid description
        valid_description = "Plato's dialogue on justice and the ideal state."
        entity = Entity(description=valid_description, **base_data)
        assert entity.description == valid_description

    def test_entity_mentions_validation(self):
        """Test mentions list validation."""
        base_data = {
            "name": "Athens",
            "entity_type": EntityType.PLACE,
            "source_document_id": uuid.uuid4()
        }

        # Test valid mentions list
        mentions = [
            MentionData(
                text="Athens",
                context="The city of Athens was home to great philosophers",
                start_position=12,
                end_position=18,
                confidence=0.9,
                document_id=uuid.uuid4()
            )
        ]
        entity = Entity(mentions=mentions, **base_data)
        assert len(entity.mentions) == 1
        assert entity.mentions[0].text == "Athens"

        # Test empty mentions list
        entity = Entity(mentions=[], **base_data)
        assert len(entity.mentions) == 0

        # Test invalid mention data should raise validation error
        invalid_mentions = [
            {"text": "", "context": "invalid"}  # Missing required fields
        ]
        with pytest.raises(ValidationError):
            Entity(mentions=invalid_mentions, **base_data)

    def test_entity_relationships_validation(self):
        """Test relationships list validation."""
        base_data = {
            "name": "Plato",
            "entity_type": EntityType.PERSON,
            "source_document_id": uuid.uuid4()
        }

        # Test valid relationships list
        relationships = [
            RelationshipData(
                target_entity_id=uuid.uuid4(),
                relationship_type="TEACHER_OF",
                confidence=0.9,
                source="historical_records"
            )
        ]
        entity = Entity(relationships=relationships, **base_data)
        assert len(entity.relationships) == 1
        assert entity.relationships[0].relationship_type == "TEACHER_OF"

        # Test empty relationships list
        entity = Entity(relationships=[], **base_data)
        assert len(entity.relationships) == 0

    def test_entity_aliases_validation(self):
        """Test aliases list validation."""
        base_data = {
            "name": "Aristotle",
            "entity_type": EntityType.PERSON,
            "source_document_id": uuid.uuid4()
        }

        # Test valid aliases
        aliases = ["The Stagirite", "Aristoteles", "The Philosopher"]
        entity = Entity(aliases=aliases, **base_data)
        assert len(entity.aliases) == 3
        assert "The Stagirite" in entity.aliases

        # Test empty aliases list should convert to None
        entity = Entity(aliases=[], **base_data)
        assert entity.aliases is None

        # Test aliases with empty strings should be filtered out
        aliases_with_empty = ["Valid Alias", "", "   ", "Another Valid"]
        entity = Entity(aliases=aliases_with_empty, **base_data)
        assert len(entity.aliases) == 2
        assert "Valid Alias" in entity.aliases
        assert "Another Valid" in entity.aliases

    def test_entity_canonical_form_property(self):
        """Test canonical_form computed property."""
        base_data = {
            "entity_type": EntityType.PERSON,
            "source_document_id": uuid.uuid4()
        }

        # Test canonical form defaults to name when not provided
        entity = Entity(name="Socrates", **base_data)
        assert entity.canonical_form == "Socrates"

        # Test explicit canonical form
        entity = Entity(
            name="Socrates", 
            canonical_form="Socrates of Athens",
            **base_data
        )
        assert entity.canonical_form == "Socrates of Athens"

        # Test canonical form normalization
        entity = Entity(
            name="plato",
            canonical_form="  PLATO  ",
            **base_data
        )
        assert entity.canonical_form == "Plato"  # Should be title case and trimmed

    def test_entity_mention_count_property(self):
        """Test computed mention_count property."""
        base_data = {
            "name": "Justice",
            "entity_type": EntityType.CONCEPT,
            "source_document_id": uuid.uuid4()
        }

        # Test with no mentions
        entity = Entity(**base_data)
        assert entity.mention_count == 0

        # Test with multiple mentions
        mentions = [
            MentionData(
                text="Justice",
                context="Justice is virtue",
                start_position=0,
                end_position=7,
                confidence=0.9,
                document_id=uuid.uuid4()
            ),
            MentionData(
                text="justice",
                context="The concept of justice",
                start_position=15,
                end_position=22,
                confidence=0.8,
                document_id=uuid.uuid4()
            )
        ]
        entity = Entity(mentions=mentions, **base_data)
        assert entity.mention_count == 2

    def test_entity_relationship_count_property(self):
        """Test computed relationship_count property."""
        base_data = {
            "name": "Socrates",
            "entity_type": EntityType.PERSON,
            "source_document_id": uuid.uuid4()
        }

        # Test with no relationships
        entity = Entity(**base_data)
        assert entity.relationship_count == 0

        # Test with multiple relationships
        relationships = [
            RelationshipData(
                target_entity_id=uuid.uuid4(),
                relationship_type="TEACHER_OF",
                confidence=0.9
            ),
            RelationshipData(
                target_entity_id=uuid.uuid4(),
                relationship_type="INFLUENCED",
                confidence=0.8
            )
        ]
        entity = Entity(relationships=relationships, **base_data)
        assert entity.relationship_count == 2

    def test_entity_average_mention_confidence(self):
        """Test computed average mention confidence."""
        base_data = {
            "name": "Wisdom",
            "entity_type": EntityType.CONCEPT,
            "source_document_id": uuid.uuid4()
        }

        # Test with no mentions
        entity = Entity(**base_data)
        assert entity.average_mention_confidence == 0.0

        # Test with single mention
        mentions = [
            MentionData(
                text="Wisdom",
                context="Wisdom is knowledge",
                start_position=0,
                end_position=6,
                confidence=0.8,
                document_id=uuid.uuid4()
            )
        ]
        entity = Entity(mentions=mentions, **base_data)
        assert entity.average_mention_confidence == 0.8

        # Test with multiple mentions
        mentions.append(
            MentionData(
                text="wisdom",
                context="True wisdom comes from experience",
                start_position=5,
                end_position=11,
                confidence=0.6,
                document_id=uuid.uuid4()
            )
        )
        entity = Entity(mentions=mentions, **base_data)
        assert entity.average_mention_confidence == 0.7  # (0.8 + 0.6) / 2

    def test_entity_add_mention_method(self):
        """Test adding mentions to entity."""
        entity_data = {
            "name": "Republic",
            "entity_type": EntityType.WORK,
            "source_document_id": uuid.uuid4()
        }
        entity = Entity(**entity_data)

        # Test adding valid mention
        mention = MentionData(
            text="Republic",
            context="Plato's Republic discusses justice",
            start_position=8,
            end_position=16,
            confidence=0.9,
            document_id=uuid.uuid4()
        )
        
        entity.add_mention(mention)
        assert len(entity.mentions) == 1
        assert entity.mentions[0].text == "Republic"

        # Test adding duplicate mention (should not add if exact match)
        entity.add_mention(mention)
        assert len(entity.mentions) == 1  # Should not duplicate

        # Test adding different mention
        different_mention = MentionData(
            text="the Republic",
            context="In the Republic, Plato explores",
            start_position=7,
            end_position=19,
            confidence=0.85,
            document_id=uuid.uuid4()
        )
        entity.add_mention(different_mention)
        assert len(entity.mentions) == 2

    def test_entity_add_relationship_method(self):
        """Test adding relationships to entity."""
        entity_data = {
            "name": "Aristotle",
            "entity_type": EntityType.PERSON,
            "source_document_id": uuid.uuid4()
        }
        entity = Entity(**entity_data)

        # Test adding valid relationship
        relationship = RelationshipData(
            target_entity_id=uuid.uuid4(),
            relationship_type="STUDENT_OF",
            confidence=0.95,
            source="historical_records"
        )
        
        entity.add_relationship(relationship)
        assert len(entity.relationships) == 1
        assert entity.relationships[0].relationship_type == "STUDENT_OF"

        # Test adding relationship to same target with different type
        different_relationship = RelationshipData(
            target_entity_id=relationship.target_entity_id,
            relationship_type="INFLUENCED_BY",
            confidence=0.8
        )
        entity.add_relationship(different_relationship)
        assert len(entity.relationships) == 2

    def test_entity_neo4j_serialization(self, sample_entity_data):
        """Test Neo4j dictionary serialization format."""
        entity = Entity(**sample_entity_data)
        neo4j_dict = entity.to_neo4j_dict()

        # Test required fields present
        assert neo4j_dict["name"] == "Socrates"
        assert neo4j_dict["entity_type"] == "person"
        assert neo4j_dict["confidence"] == 0.95
        assert neo4j_dict["description"] == "Classical Greek philosopher"

        # Test UUID converted to string
        assert isinstance(neo4j_dict["id"], str)
        assert isinstance(neo4j_dict["source_document_id"], str)
        uuid.UUID(neo4j_dict["id"])  # Should not raise exception

        # Test datetime converted to timestamp
        assert isinstance(neo4j_dict["created_at"], float)
        assert neo4j_dict["created_at"] > 0

        # Test mentions and relationships as separate fields for Neo4j relationships
        assert "mention_count" in neo4j_dict
        assert "relationship_count" in neo4j_dict
        assert "average_mention_confidence" in neo4j_dict

        # Test canonical form included
        assert "canonical_form" in neo4j_dict

    def test_entity_weaviate_serialization(self, sample_entity_data):
        """Test Weaviate dictionary serialization format."""
        entity = Entity(**sample_entity_data)
        weaviate_dict = entity.to_weaviate_dict()

        # Test required fields present
        assert weaviate_dict["name"] == "Socrates"
        assert weaviate_dict["entity_type"] == "person"
        assert weaviate_dict["confidence"] == 0.95
        assert weaviate_dict["description"] == "Classical Greek philosopher"

        # Test UUID excluded (Weaviate manages its own IDs)
        assert "id" not in weaviate_dict

        # Test Neo4j reference included for cross-referencing
        assert weaviate_dict["neo4j_id"] == str(entity.id)

        # Test vectorizable text included
        assert "vectorizable_text" in weaviate_dict
        vectorizable = weaviate_dict["vectorizable_text"]
        assert entity.name in vectorizable
        assert entity.description in vectorizable

        # Test computed properties included
        assert "mention_count" in weaviate_dict
        assert "relationship_count" in weaviate_dict
        assert "canonical_form" in weaviate_dict

    def test_entity_get_vectorizable_text(self, sample_entity_data):
        """Test vectorizable text generation for embeddings."""
        entity = Entity(**sample_entity_data)
        vectorizable_text = entity.get_vectorizable_text()

        assert isinstance(vectorizable_text, str)
        assert len(vectorizable_text) > 0

        # Should combine name, description, and aliases
        assert entity.name in vectorizable_text
        if entity.description:
            assert entity.description in vectorizable_text
        if entity.aliases:
            for alias in entity.aliases:
                assert alias in vectorizable_text

    def test_entity_string_field_sanitization(self):
        """Test that string fields are properly sanitized."""
        entity_data = {
            "name": "  Socrates  ",
            "entity_type": EntityType.PERSON,
            "description": "  Classical Greek philosopher  ",
            "source_document_id": uuid.uuid4(),
            "canonical_form": "  Socrates of Athens  ",
            "aliases": ["  The Gadfly  ", "  Socrates the Wise  "]
        }

        entity = Entity(**entity_data)

        # Test all string fields are trimmed
        assert entity.name == "Socrates"
        assert entity.description == "Classical Greek philosopher"
        assert entity.canonical_form == "Socrates of Athens"
        assert "The Gadfly" in entity.aliases
        assert "Socrates the Wise" in entity.aliases

    def test_entity_get_related_entities_method(self):
        """Test method to get related entity IDs."""
        entity_data = {
            "name": "Plato",
            "entity_type": EntityType.PERSON,
            "source_document_id": uuid.uuid4()
        }
        
        aristotle_id = uuid.uuid4()
        socrates_id = uuid.uuid4()
        
        relationships = [
            RelationshipData(
                target_entity_id=aristotle_id,
                relationship_type="TEACHER_OF",
                confidence=0.9
            ),
            RelationshipData(
                target_entity_id=socrates_id,
                relationship_type="STUDENT_OF",
                confidence=0.95
            )
        ]
        
        entity = Entity(relationships=relationships, **entity_data)
        related_ids = entity.get_related_entity_ids()
        
        assert len(related_ids) == 2
        assert aristotle_id in related_ids
        assert socrates_id in related_ids

    def test_entity_find_relationships_by_type(self):
        """Test finding relationships by type."""
        entity_data = {
            "name": "Socrates",
            "entity_type": EntityType.PERSON,
            "source_document_id": uuid.uuid4()
        }
        
        relationships = [
            RelationshipData(
                target_entity_id=uuid.uuid4(),
                relationship_type="TEACHER_OF",
                confidence=0.9
            ),
            RelationshipData(
                target_entity_id=uuid.uuid4(),
                relationship_type="TEACHER_OF",
                confidence=0.8
            ),
            RelationshipData(
                target_entity_id=uuid.uuid4(),
                relationship_type="INFLUENCED",
                confidence=0.7
            )
        ]
        
        entity = Entity(relationships=relationships, **entity_data)
        
        # Find by specific type
        teacher_rels = entity.get_relationships_by_type("TEACHER_OF")
        assert len(teacher_rels) == 2
        assert all(rel.relationship_type == "TEACHER_OF" for rel in teacher_rels)

        # Find by non-existent type
        missing_rels = entity.get_relationships_by_type("INVENTED_BY")
        assert len(missing_rels) == 0

    def test_entity_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Test with special characters in name
        special_name = "Αριστοτέλης"  # Aristotle in Greek
        entity_data = {
            "name": special_name,
            "entity_type": EntityType.PERSON,
            "source_document_id": uuid.uuid4(),
            "description": "Ἀριστοτέλης - Greek philosopher"
        }

        entity = Entity(**entity_data)
        assert entity.name == special_name
        assert entity.canonical_form == special_name

        # Test with very long valid description (at boundary)
        long_description = "A" * 1000  # Exactly at max length
        entity = Entity(
            name="Test Entity",
            entity_type=EntityType.CONCEPT,
            source_document_id=uuid.uuid4(),
            description=long_description
        )
        assert entity.description == long_description

    def test_entity_repr_security(self):
        """Test that entity representation doesn't leak sensitive data."""
        entity_data = {
            "name": "Secret Entity",
            "entity_type": EntityType.PERSON,
            "source_document_id": uuid.uuid4(),
            "metadata": {"api_key": "secret123", "user_data": "sensitive"}
        }

        entity = Entity(**entity_data)
        repr_str = repr(entity)

        # Basic fields should be visible
        assert "Secret Entity" in repr_str
        assert str(entity.id) in repr_str

        # Sensitive metadata should not be exposed in basic repr

    def test_entity_model_validation_assignment(self):
        """Test that validate_assignment=True works correctly."""
        entity_data = {
            "name": "Plato",
            "entity_type": EntityType.PERSON,
            "source_document_id": uuid.uuid4()
        }
        entity = Entity(**entity_data)

        # Test that assignment validation works
        with pytest.raises(ValidationError):
            entity.name = ""  # Should fail validation

        with pytest.raises(ValidationError):
            entity.confidence = 1.5  # Should fail validation

        # Test valid assignments
        entity.name = "Platon"
        assert entity.name == "Platon"

        entity.confidence = 0.8
        assert entity.confidence == 0.8


class TestEntityIntegration:
    """Integration tests for Entity model with complex scenarios."""

    def test_full_entity_lifecycle_with_mentions_and_relationships(self):
        """Test complete entity lifecycle with mentions and relationships."""
        # 1. Create entity
        entity_data = {
            "name": "Aristotle",
            "entity_type": EntityType.PERSON,
            "source_document_id": uuid.uuid4(),
            "description": "Greek philosopher and polymath"
        }
        entity = Entity(**entity_data)

        # 2. Add mentions
        mention1 = MentionData(
            text="Aristotle",
            context="Aristotle was born in Stagira",
            start_position=0,
            end_position=9,
            confidence=0.95,
            document_id=uuid.uuid4()
        )
        entity.add_mention(mention1)

        # 3. Add relationships
        plato_id = uuid.uuid4()
        relationship = RelationshipData(
            target_entity_id=plato_id,
            relationship_type="STUDENT_OF",
            confidence=0.9,
            source="historical_records"
        )
        entity.add_relationship(relationship)

        # 4. Verify computed properties
        assert entity.mention_count == 1
        assert entity.relationship_count == 1
        assert entity.average_mention_confidence == 0.95

        # 5. Test serialization for both databases
        neo4j_data = entity.to_neo4j_dict()
        weaviate_data = entity.to_weaviate_dict()

        # Verify both serializations are valid
        assert neo4j_data["entity_type"] == "person"
        assert neo4j_data["mention_count"] == 1
        assert weaviate_data["relationship_count"] == 1
        assert weaviate_data["neo4j_id"] == str(entity.id)

    def test_entity_batch_processing_simulation(self):
        """Test batch processing of multiple entities."""
        entities_data = [
            {
                "name": f"Entity {i}",
                "entity_type": EntityType.CONCEPT,
                "source_document_id": uuid.uuid4(),
                "confidence": 0.5 + (i * 0.1)  # Varying confidence
            }
            for i in range(5)
        ]

        entities = [Entity(**data) for data in entities_data]

        # Simulate batch processing with mentions
        for i, entity in enumerate(entities):
            mention = MentionData(
                text=f"Entity {i}",
                context=f"Context for entity {i}",
                start_position=0,
                end_position=len(f"Entity {i}"),
                confidence=0.8,
                document_id=uuid.uuid4()
            )
            entity.add_mention(mention)

        # Verify all entities processed
        assert len(entities) == 5
        assert all(entity.mention_count == 1 for entity in entities)
        assert all(entity.average_mention_confidence == 0.8 for entity in entities)

    def test_complex_relationship_network(self):
        """Test complex entity relationship networks."""
        # Create entities for a philosophical school
        socrates_id = uuid.uuid4()
        plato_id = uuid.uuid4() 
        aristotle_id = uuid.uuid4()

        # Create Socrates entity with student relationships
        socrates = Entity(
            name="Socrates",
            entity_type=EntityType.PERSON,
            source_document_id=uuid.uuid4()
        )
        
        socrates.add_relationship(RelationshipData(
            target_entity_id=plato_id,
            relationship_type="TEACHER_OF",
            confidence=0.95
        ))

        # Create Plato entity with teacher and student relationships
        plato = Entity(
            name="Plato",
            entity_type=EntityType.PERSON,
            source_document_id=uuid.uuid4()
        )
        
        plato.add_relationship(RelationshipData(
            target_entity_id=socrates_id,
            relationship_type="STUDENT_OF",
            confidence=0.95
        ))
        plato.add_relationship(RelationshipData(
            target_entity_id=aristotle_id,
            relationship_type="TEACHER_OF",
            confidence=0.9
        ))

        # Verify relationship networks
        assert socrates.relationship_count == 1
        assert plato.relationship_count == 2
        
        # Test relationship type filtering
        teacher_rels = plato.get_relationships_by_type("TEACHER_OF")
        assert len(teacher_rels) == 1
        assert teacher_rels[0].target_entity_id == aristotle_id


# Test fixtures for reusable test data
@pytest.fixture
def sample_mention_data() -> Dict[str, Any]:
    """Sample mention data for testing."""
    return {
        "text": "Socrates",
        "context": "As Socrates once said, the unexamined life is not worth living.",
        "start_position": 3,
        "end_position": 11,
        "confidence": 0.95,
        "document_id": uuid.uuid4()
    }


@pytest.fixture
def sample_relationship_data() -> Dict[str, Any]:
    """Sample relationship data for testing."""
    return {
        "target_entity_id": uuid.uuid4(),
        "relationship_type": "STUDENT_OF",
        "confidence": 0.85,
        "source": "historical_records",
        "bidirectional": False
    }


@pytest.fixture
def sample_entity_data() -> Dict[str, Any]:
    """Sample entity data for testing."""
    return {
        "name": "Socrates",
        "entity_type": EntityType.PERSON,
        "confidence": 0.95,
        "description": "Classical Greek philosopher",
        "source_document_id": uuid.uuid4(),
        "mentions": [
            MentionData(
                text="Socrates",
                context="Socrates taught through questioning",
                start_position=0,
                end_position=8,
                confidence=0.9,
                document_id=uuid.uuid4()
            )
        ],
        "relationships": [],
        "aliases": ["Socrates of Athens"],
        "canonical_form": "Socrates"
    }


@pytest.fixture
def minimal_entity_data() -> Dict[str, Any]:
    """Minimal valid entity data for testing."""
    return {
        "name": "Justice",
        "entity_type": EntityType.CONCEPT,
        "source_document_id": uuid.uuid4()
    }


@pytest.fixture
def sample_complex_entity() -> Dict[str, Any]:
    """Sample complex entity with multiple mentions and relationships."""
    document_id = uuid.uuid4()
    
    return {
        "name": "Aristotle",
        "entity_type": EntityType.PERSON,
        "confidence": 0.98,
        "description": "Greek philosopher and polymath, student of Plato",
        "source_document_id": document_id,
        "mentions": [
            MentionData(
                text="Aristotle",
                context="Aristotle founded the Lyceum in Athens",
                start_position=0,
                end_position=9,
                confidence=0.95,
                document_id=document_id
            ),
            MentionData(
                text="The Stagirite",
                context="The Stagirite wrote extensively on logic",
                start_position=0,
                end_position=13,
                confidence=0.85,
                document_id=document_id
            )
        ],
        "relationships": [
            RelationshipData(
                target_entity_id=uuid.uuid4(),  # Plato
                relationship_type="STUDENT_OF",
                confidence=0.95,
                source="historical_records"
            ),
            RelationshipData(
                target_entity_id=uuid.uuid4(),  # Alexander the Great
                relationship_type="TEACHER_OF",
                confidence=0.9,
                source="historical_records"
            )
        ],
        "aliases": ["The Stagirite", "Aristoteles", "The Philosopher"],
        "canonical_form": "Aristotle of Stagira"
    }