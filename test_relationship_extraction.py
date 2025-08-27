#!/usr/bin/env python3
"""
Test relationship extraction to debug the low relationship count.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arete.processing.extractors import RelationshipExtractor, TripleValidator

def test_relationship_extraction():
    """Test relationship extraction with sample philosophical text."""
    
    # Sample text from The Republic with clear relationships
    test_text = """
    Socrates argues with Thrasymachus about the nature of justice. Plato writes about the ideal state 
    in The Republic. Glaucon challenges Socrates' views on morality. Adeimantus supports Glaucon's 
    position on justice. Socrates refutes Thrasymachus' claim that might makes right. 
    Plato influences later philosophical thought through his dialogues. Aristotle critiques 
    Plato's theory of Forms. The Republic demonstrates Plato's political philosophy.
    Socrates teaches his students through questioning. Thrasymachus disagrees with Socrates 
    about justice being advantageous to the stronger.
    """
    
    print("Testing Relationship Extraction")
    print("=" * 50)
    print(f"Sample text ({len(test_text)} chars):")
    print(test_text.strip())
    print()
    
    # Test relationship extraction
    extractor = RelationshipExtractor()
    raw_relationships = extractor.extract_relationships(test_text)
    
    print(f"Raw relationships extracted: {len(raw_relationships)}")
    for i, rel in enumerate(raw_relationships):
        print(f"  {i+1}. {rel['subject']} -> {rel['relation']} -> {rel['object']} (conf: {rel['confidence']})")
    print()
    
    # Test validation with different confidence thresholds
    validator = TripleValidator()
    
    for min_conf in [0.1, 0.3, 0.5, 0.6, 0.7, 0.9]:
        validated = validator.validate(raw_relationships, min_confidence=min_conf)
        print(f"Validated with min_confidence={min_conf}: {len(validated)} relationships")
        if min_conf == 0.6:  # Show details for default threshold
            for i, rel in enumerate(validated):
                print(f"  {i+1}. {rel['subject']} -> {rel['relation']} -> {rel['object']} (conf: {rel['confidence']})")
    
    print()
    print("Analysis:")
    print(f"- Rule-based extractor found {len(raw_relationships)} raw relationships")
    print(f"- Validator with default threshold (0.6) kept {len(validator.validate(raw_relationships, 0.6))} relationships")
    
    return raw_relationships, validator.validate(raw_relationships, 0.6)


if __name__ == "__main__":
    test_relationship_extraction()