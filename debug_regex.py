#!/usr/bin/env python3
"""
Debug the relationship extraction regex patterns.
"""

import re

def test_regex_patterns():
    """Test regex patterns against sample text."""
    
    # Sample sentences with expected relationships
    test_cases = [
        ("Socrates argues with Thrasymachus about justice.", "argues with", "Socrates", "Thrasymachus"),
        ("Plato influences later philosophical thought.", "influences", "Plato", "later philosophical thought"),
        ("Aristotle critiques Plato's theory of Forms.", "critiques", "Aristotle", "Plato"),
        ("Glaucon challenges Socrates' views.", "challenges", "Glaucon", "Socrates"), 
        ("Socrates refutes Thrasymachus' claim.", "refutes", "Socrates", "Thrasymachus")
    ]
    
    for sentence, verb, expected_subj, expected_obj in test_cases:
        print(f"\nTesting: {sentence}")
        print(f"Expected: {expected_subj} -> {verb} -> {expected_obj}")
        
        if " " in verb:
            # Multi-word verb
            escaped_verb = re.escape(verb)
            pattern = rf"\b([A-Z][a-zA-Z]+(?:\s+[a-zA-Z]+)*)\s+{escaped_verb}\s+([A-Z][a-zA-Z]+(?:\s+[a-zA-Z]+)*)"
        else:
            # Single word verb  
            pattern = rf"\b([A-Z][a-zA-Z]+)\s+{re.escape(verb)}\s+([A-Z][a-zA-Z]+(?:\s+[a-zA-Z]+)*)"
            
        print(f"Pattern: {pattern}")
        
        matches = list(re.finditer(pattern, sentence, re.IGNORECASE))
        if matches:
            for match in matches:
                subj = match.group(1).strip()
                obj = match.group(2).strip()
                print(f"    FOUND: '{subj}' -> {verb} -> '{obj}'")
        else:
            print(f"    NO MATCH")
            
        # Try simpler pattern
        simple_pattern = rf"\b([A-Z]\w+)\s+{re.escape(verb.split()[0])}\s+([A-Z]\w+)"
        simple_matches = list(re.finditer(simple_pattern, sentence, re.IGNORECASE))
        if simple_matches:
            print(f"    SIMPLE MATCH: '{simple_matches[0].group(1)}' -> {verb.split()[0]} -> '{simple_matches[0].group(2)}'")

if __name__ == "__main__":
    test_regex_patterns()