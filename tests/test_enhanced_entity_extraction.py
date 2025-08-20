"""
Comprehensive tests for enhanced entity extraction with philosophical patterns.
"""

import uuid
import pytest
from typing import List

from arete.models.entity import Entity, EntityType
from arete.processing.extractors import EntityExtractor


class TestEnhancedEntityExtractor:
    """Test enhanced EntityExtractor with philosophical patterns."""
    
    def test_philosophical_patterns_loaded_by_default(self):
        """Test that philosophical patterns are loaded by default."""
        extractor = EntityExtractor()
        
        # Test that patterns were loaded (indicated by _has_patterns)
        assert extractor._has_patterns is True
    
    def test_extract_classical_philosophers(self):
        """Test extraction of classical philosophers."""
        extractor = EntityExtractor(use_philosophical_patterns=True)
        text = "Socrates taught Plato, who in turn taught Aristotle. Pythagoras developed mathematical philosophy."
        document_id = uuid.uuid4()
        
        entities = extractor.extract_entities(text, document_id)
        
        # Should extract known philosophers
        entity_names = {e.name for e in entities}
        expected_philosophers = {"Socrates", "Plato", "Aristotle", "Pythagoras"}
        
        assert expected_philosophers.issubset(entity_names)
        
        # Check that philosophers are correctly typed
        for entity in entities:
            if entity.name in expected_philosophers:
                assert entity.entity_type == EntityType.PERSON
    
    def test_extract_philosophical_works(self):
        """Test extraction of philosophical works."""
        extractor = EntityExtractor(use_philosophical_patterns=True)
        text = "In the Republic, Plato discusses justice. Aristotle's Nicomachean Ethics examines virtue."
        document_id = uuid.uuid4()
        
        entities = extractor.extract_entities(text, document_id)
        
        entity_names = {e.name for e in entities}
        expected_works = {"Republic", "Nicomachean Ethics"}
        
        assert expected_works.issubset(entity_names)
        
        # Check that works are correctly typed
        for entity in entities:
            if entity.name in expected_works:
                assert entity.entity_type == EntityType.WORK
    
    def test_extract_philosophical_concepts(self):
        """Test extraction of philosophical concepts."""
        extractor = EntityExtractor(use_philosophical_patterns=True)
        text = "The discussion centers on virtue, justice, and wisdom. Eudaimonia is the highest good."
        document_id = uuid.uuid4()
        
        entities = extractor.extract_entities(text, document_id)
        
        entity_names = {e.name for e in entities}
        expected_concepts = {"virtue", "justice", "wisdom", "eudaimonia"}
        
        # Should extract at least some of these concepts
        assert len(expected_concepts.intersection(entity_names)) > 0
        
        # Check that concepts are correctly typed
        for entity in entities:
            if entity.name in expected_concepts:
                assert entity.entity_type == EntityType.CONCEPT
    
    def test_extract_places(self):
        """Test extraction of philosophical places."""
        extractor = EntityExtractor(use_philosophical_patterns=True)
        text = "Socrates taught in Athens at the Academy. The Lyceum was Aristotle's school."
        document_id = uuid.uuid4()
        
        entities = extractor.extract_entities(text, document_id)
        
        entity_names = {e.name for e in entities}
        expected_places = {"Athens", "Academy", "Lyceum"}
        
        assert len(expected_places.intersection(entity_names)) > 0
        
        # Check typing (Athens should be GPE, Academy/Lyceum should be LOC -> PLACE)
        for entity in entities:
            if entity.name in expected_places:
                assert entity.entity_type == EntityType.PLACE
    
    def test_custom_patterns_override(self):
        """Test that custom patterns can be added alongside philosophical patterns."""
        custom_patterns = [
            {"label": "PERSON", "pattern": "TestPhilosopher"},
            {"label": "CONCEPT", "pattern": "TestConcept"}
        ]
        
        extractor = EntityExtractor(patterns=custom_patterns, use_philosophical_patterns=True)
        text = "TestPhilosopher discussed TestConcept with Socrates about virtue."
        document_id = uuid.uuid4()
        
        entities = extractor.extract_entities(text, document_id)
        
        entity_names = {e.name for e in entities}
        
        # Should extract both custom and philosophical patterns
        assert "TestPhilosopher" in entity_names
        assert "TestConcept" in entity_names
        assert "Socrates" in entity_names
        assert "virtue" in entity_names
    
    def test_disable_philosophical_patterns(self):
        """Test that philosophical patterns can be disabled."""
        custom_patterns = [
            {"label": "PERSON", "pattern": "CustomPerson"}
        ]
        
        extractor = EntityExtractor(patterns=custom_patterns, use_philosophical_patterns=False)
        text = "CustomPerson discussed virtue with Socrates."
        document_id = uuid.uuid4()
        
        entities = extractor.extract_entities(text, document_id)
        
        entity_names = {e.name for e in entities}
        
        # Should only extract custom patterns, not philosophical ones
        assert "CustomPerson" in entity_names
        # Without philosophical patterns, Socrates and virtue might not be extracted
        # (depending on the base spaCy model capabilities)
    
    def test_confidence_scores_with_patterns(self):
        """Test that confidence scores are higher with patterns."""
        extractor = EntityExtractor(use_philosophical_patterns=True)
        text = "Socrates refutes Thrasymachus in the Republic."
        document_id = uuid.uuid4()
        
        entities = extractor.extract_entities(text, document_id)
        
        # Entities extracted with patterns should have higher confidence
        for entity in entities:
            if entity.name in ["Socrates", "Thrasymachus", "Republic"]:
                assert entity.confidence >= 0.8  # High confidence for pattern matches
    
    def test_mention_context_extraction(self):
        """Test that mention context is properly extracted."""
        extractor = EntityExtractor(use_philosophical_patterns=True)
        text = "In ancient Athens, Socrates was known for his wisdom and questioning method."
        document_id = uuid.uuid4()
        
        entities = extractor.extract_entities(text, document_id)
        
        socrates_entity = next((e for e in entities if e.name == "Socrates"), None)
        assert socrates_entity is not None
        assert len(socrates_entity.mentions) > 0
        
        mention = socrates_entity.mentions[0]
        assert mention.text == "Socrates"
        assert mention.context
        assert "Athens" in mention.context or "wisdom" in mention.context
        assert mention.start_position >= 0
        assert mention.end_position > mention.start_position
    
    def test_fallback_to_blank_model(self):
        """Test graceful fallback when full spaCy model is not available."""
        # This test simulates the case where en_core_web_sm is not installed
        extractor = EntityExtractor(model_name="nonexistent_model", use_philosophical_patterns=True)
        text = "Socrates taught Plato."
        document_id = uuid.uuid4()
        
        # Should not crash, should still extract entities with patterns
        entities = extractor.extract_entities(text, document_id)
        
        # With pattern matching, should still extract known entities
        entity_names = {e.name for e in entities}
        assert "Socrates" in entity_names or "Plato" in entity_names
    
    def test_empty_text_handling(self):
        """Test handling of empty text."""
        extractor = EntityExtractor(use_philosophical_patterns=True)
        document_id = uuid.uuid4()
        
        entities = extractor.extract_entities("", document_id)
        assert entities == []
        
        entities = extractor.extract_entities("   ", document_id)
        assert entities == []
    
    def test_complex_philosophical_text(self):
        """Test extraction from complex philosophical text."""
        extractor = EntityExtractor(use_philosophical_patterns=True)
        text = """
        In Plato's Republic, Socrates engages with Thrasymachus and Glaucon about the nature of justice.
        The dialogue explores the concept of virtue and the ideal state. Aristotle later critiques
        this view in his Politics, arguing for a different understanding of eudaimonia and the good life.
        The Academy in Athens was where these ideas were discussed and developed.
        """
        document_id = uuid.uuid4()
        
        entities = extractor.extract_entities(text, document_id)
        
        entity_names = {e.name for e in entities}
        
        # Should extract multiple philosophers
        philosophers = {"Plato", "Socrates", "Thrasymachus", "Glaucon", "Aristotle"}
        assert len(philosophers.intersection(entity_names)) >= 3
        
        # Should extract works
        works = {"Republic", "Politics"}
        assert len(works.intersection(entity_names)) >= 1
        
        # Should extract concepts
        concepts = {"justice", "virtue", "eudaimonia"}
        assert len(concepts.intersection(entity_names)) >= 1
        
        # Should extract places
        places = {"Academy", "Athens"}
        assert len(places.intersection(entity_names)) >= 1
    
    def test_entity_aggregation_multiple_mentions(self):
        """Test that multiple mentions of the same entity are aggregated."""
        extractor = EntityExtractor(use_philosophical_patterns=True)
        text = """
        Socrates was born in Athens. Socrates became a philosopher. 
        Many students came to learn from Socrates in Athens.
        """
        document_id = uuid.uuid4()
        
        entities = extractor.extract_entities(text, document_id)
        
        socrates_entities = [e for e in entities if e.name == "Socrates"]
        assert len(socrates_entities) == 1  # Should be aggregated into one entity
        
        socrates = socrates_entities[0]
        assert socrates.mention_count >= 2  # Should have multiple mentions
        
        # Mentions should have different positions
        positions = {(m.start_position, m.end_position) for m in socrates.mentions}
        assert len(positions) >= 2  # Multiple distinct positions