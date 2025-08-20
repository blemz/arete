from typing import List, Dict

from arete.processing import TripleValidator


def test_valid_triple_passes():
    triples: List[Dict[str, object]] = [
        {"subject": "Socrates", "relation": "refutes", "object": "Thrasymachus", "confidence": 0.8}
    ]
    validator = TripleValidator()
    filtered = validator.validate(triples)
    assert filtered == triples


def test_invalid_empty_fields_filtered():
    triples = [
        {"subject": "", "relation": "refutes", "object": "X", "confidence": 0.8},
        {"subject": "A", "relation": "", "object": "B", "confidence": 0.8},
        {"subject": "A", "relation": "cites", "object": "", "confidence": 0.8},
    ]
    validator = TripleValidator()
    filtered = validator.validate(triples)
    assert filtered == []


def test_confidence_threshold_and_dedup():
    triples = [
        {"subject": "Plato", "relation": "cites", "object": "Socrates", "confidence": 0.55},  # below default 0.6
        {"subject": "Plato", "relation": "cites", "object": "Socrates", "confidence": 0.9},   # duplicate higher conf
        {"subject": "Aristotle", "relation": "criticizes", "object": "Plato", "confidence": 0.7},
    ]
    validator = TripleValidator()
    filtered = validator.validate(triples, min_confidence=0.6)

    assert len(filtered) == 2
    # The higher-confidence duplicate should remain
    assert any(t["subject"] == "Plato" and t["relation"] == "cites" and t["object"] == "Socrates" and t["confidence"] == 0.9 for t in filtered)
    assert any(t["subject"] == "Aristotle" and t["relation"] == "criticizes" and t["object"] == "Plato" for t in filtered)
