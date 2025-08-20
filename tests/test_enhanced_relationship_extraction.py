"""
Comprehensive tests for enhanced relationship extraction with philosophical patterns.
"""

import pytest
from typing import List, Dict, Any

from arete.processing.extractors import RelationshipExtractor


class TestEnhancedRelationshipExtractor:
    """Test enhanced RelationshipExtractor with philosophical patterns."""
    
    def test_basic_philosophical_relationships(self):
        """Test extraction of basic philosophical relationships."""
        extractor = RelationshipExtractor()
        text = "Socrates influences Plato. Aristotle critiques Plato's theory."
        
        triples = extractor.extract_relationships(text)
        
        assert len(triples) >= 2
        
        # Check for influence relationship
        influence_triple = next((t for t in triples if "influences" in t["relation"].lower()), None)
        assert influence_triple is not None
        assert "Socrates" in influence_triple["subject"]
        assert "Plato" in influence_triple["object"]
        assert influence_triple["relation"] == "INFLUENCES"
        
        # Check for critique relationship
        critique_triple = next((t for t in triples if "critiques" in t["relation"].lower()), None)
        assert critique_triple is not None
        assert "Aristotle" in critique_triple["subject"]
        assert "Plato" in critique_triple["object"]
        assert critique_triple["relation"] == "CRITIQUES"
    
    def test_expanded_philosophical_verbs(self):
        """Test extraction with expanded set of philosophical verbs."""
        extractor = RelationshipExtractor()
        test_cases = [
            ("Plato develops Socrates' ideas", "DEVELOPS"),
            ("Aristotle extends Plato's theory", "EXTENDS"),
            ("Kant synthesizes rationalism and empiricism", "SYNTHESIZES"),
            ("Hume challenges traditional metaphysics", "CHALLENGES"),
            ("Descartes establishes methodological doubt", "ESTABLISHES"),
            ("Mill advocates for utilitarianism", "ADVOCATES"),
            ("Nietzsche questions traditional morality", "QUESTIONS")
        ]
        
        for text, expected_relation in test_cases:
            triples = extractor.extract_relationships(text)
            
            # Should extract at least one triple
            assert len(triples) >= 1
            
            # Should find the expected relationship type
            found_relation = any(t["relation"] == expected_relation for t in triples)
            assert found_relation, f"Expected {expected_relation} not found in {text}"
    
    def test_multi_word_relationships(self):
        """Test extraction of multi-word relationship phrases."""
        extractor = RelationshipExtractor()
        test_cases = [
            ("Plato agrees with Socrates", "AGREES_WITH"),
            ("Hume disagrees with Descartes", "DISAGREES_WITH"),
            ("Mill builds on Bentham's work", "BUILDS_ON"),
            ("Kant responds to Hume", "RESPONDS_TO"),
            ("Russell learns from Frege", "LEARNS_FROM")
        ]
        
        for text, expected_relation in test_cases:
            triples = extractor.extract_relationships(text)
            
            assert len(triples) >= 1
            found_relation = any(t["relation"] == expected_relation for t in triples)
            assert found_relation, f"Expected {expected_relation} not found in {text}"
    
    def test_confidence_scores(self):
        """Test that confidence scores are appropriate."""
        extractor = RelationshipExtractor()
        text = "Socrates influences Plato. Aristotle critiques idealism."
        
        triples = extractor.extract_relationships(text)
        
        for triple in triples:
            assert 0.0 <= triple["confidence"] <= 1.0
            assert triple["confidence"] >= 0.5  # Should be reasonably confident for rule-based
    
    def test_evidence_inclusion(self):
        """Test that evidence text is included in results."""
        extractor = RelationshipExtractor()
        text = "In the Phaedo, Socrates refutes materialist arguments."
        
        triples = extractor.extract_relationships(text)
        
        refute_triple = next((t for t in triples if t["relation"] == "REFUTES"), None)
        assert refute_triple is not None
        assert "evidence" in refute_triple
        assert refute_triple["evidence"]  # Should contain the matched text
    
    def test_entity_filtering(self):
        """Test filtering relationships to known entities."""
        extractor = RelationshipExtractor()
        text = "Socrates influences Plato. RandomName criticizes something."
        known_entities = ["Socrates", "Plato"]
        
        triples = extractor.extract_relationships(text, known_entities)
        
        # Should only extract relationships involving known entities
        for triple in triples:
            subject_known = any(entity.lower() in triple["subject"].lower() for entity in known_entities)
            object_known = any(entity.lower() in triple["object"].lower() for entity in known_entities)
            assert subject_known and object_known, f"Unknown entities in triple: {triple}"
    
    def test_complex_philosophical_text(self):
        """Test extraction from complex philosophical text."""
        extractor = RelationshipExtractor()
        text = """
        Plato develops Socrates' method of questioning and extends it into a comprehensive 
        philosophical system. Aristotle, who studies under Plato, later critiques many 
        of his teacher's ideas and proposes alternative theories. The Stoics build on 
        Aristotelian logic while disagreeing with Platonic idealism.
        """
        
        triples = extractor.extract_relationships(text)
        
        # Should extract multiple relationships
        assert len(triples) >= 3
        
        # Check for various relationship types
        relation_types = {t["relation"] for t in triples}
        expected_types = {"DEVELOPS", "EXTENDS", "STUDIES_UNDER", "CRITIQUES", "BUILDS_ON", "DISAGREES_WITH"}
        
        # Should find several of the expected relationship types
        found_types = relation_types.intersection(expected_types)
        assert len(found_types) >= 2, f"Expected multiple relationship types, found: {relation_types}"
    
    def test_entity_name_cleaning(self):
        """Test that entity names are properly cleaned."""
        extractor = RelationshipExtractor()
        text = "Ancient Socrates    influences    young Plato greatly."
        
        triples = extractor.extract_relationships(text)
        
        if triples:
            triple = triples[0]
            # Subject and object should be cleaned (no extra whitespace)
            assert "  " not in triple["subject"]
            assert "  " not in triple["object"]
            assert triple["subject"].strip() == triple["subject"]
            assert triple["object"].strip() == triple["object"]
    
    def test_relationship_standardization(self):
        """Test that relationships are properly standardized."""
        extractor = RelationshipExtractor()
        test_cases = [
            ("Socrates teaches Plato", "TEACHES"),
            ("Plato instructs students", "TEACHES"),  # Should map to TEACHES
            ("Aristotle guides Alexander", "GUIDES"),
            ("Hume inspires Kant", "INSPIRES"),
            ("Kant affects modern philosophy", "INFLUENCES"),  # Should map to INFLUENCES
        ]
        
        for text, expected_standard in test_cases:
            triples = extractor.extract_relationships(text)
            if triples:
                found_standard = any(t["relation"] == expected_standard for t in triples)
                assert found_standard, f"Expected standardized relation {expected_standard} not found in {text}"
    
    def test_source_attribution(self):
        """Test that source is properly attributed."""
        extractor = RelationshipExtractor()
        text = "Socrates refutes Thrasymachus in the Republic."
        
        triples = extractor.extract_relationships(text)
        
        for triple in triples:
            assert triple["source"] == "rule_based"
    
    def test_empty_and_invalid_input(self):
        """Test handling of empty and invalid input."""
        extractor = RelationshipExtractor()
        
        # Empty text
        assert extractor.extract_relationships("") == []
        assert extractor.extract_relationships("   ") == []
        
        # Text with no relationships
        no_rel_text = "This text contains no philosophical relationships at all."
        triples = extractor.extract_relationships(no_rel_text)
        assert len(triples) == 0
    
    def test_llm_fallback_mode(self):
        """Test LLM mode initialization (even if not implemented)."""
        # Test that LLM mode can be initialized without errors
        extractor = RelationshipExtractor(use_llm=True, llm_client=None)
        text = "Socrates influences Plato."
        
        # Should fallback to rule-based extraction
        triples = extractor.extract_relationships(text)
        assert len(triples) >= 1
        
        # Should still extract the relationship using rules
        influence_triple = next((t for t in triples if t["relation"] == "INFLUENCES"), None)
        assert influence_triple is not None
    
    def test_prompt_building(self):
        """Test LLM prompt building functionality."""
        extractor = RelationshipExtractor(use_llm=True)
        text = "Socrates influences Plato."
        entities = ["Socrates", "Plato"]
        
        prompt = extractor._build_relationship_extraction_prompt(text, entities)
        
        assert prompt is not None
        assert text in prompt
        assert "Socrates" in prompt
        assert "Plato" in prompt
        assert "INFLUENCES" in prompt  # Should mention standardized relationship types
    
    def test_duplicate_prevention(self):
        """Test that similar relationships are not duplicated excessively."""
        extractor = RelationshipExtractor()
        text = "Socrates influences Plato. Socrates greatly influences Plato's thinking."
        
        triples = extractor.extract_relationships(text)
        
        # Even if multiple similar patterns are found, should be manageable
        influence_triples = [t for t in triples if t["relation"] == "INFLUENCES"]
        
        # Might find multiple instances, but should not be excessive
        assert len(influence_triples) <= 3
    
    def test_special_characters_handling(self):
        """Test handling of special characters in text."""
        extractor = RelationshipExtractor()
        text = "Socrates—the great philosopher—influences Plato's Academy."
        
        # Should not crash with special characters
        triples = extractor.extract_relationships(text)
        
        # May or may not extract relationships depending on regex patterns,
        # but should not raise exceptions
        assert isinstance(triples, list)