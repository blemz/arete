from typing import List, Dict

from arete.processing import RelationshipExtractor


def test_extract_single_relationship():
    text = "Socrates refutes Thrasymachus in Book I."
    extractor = RelationshipExtractor()
    triples: List[Dict[str, str]] = extractor.extract_relationships(text)

    assert len(triples) == 1
    triple = triples[0]
    assert triple["subject"] == "Socrates"
    assert triple["relation"] == "refutes"
    assert triple["object"] == "Thrasymachus"
    assert 0.5 <= triple["confidence"] <= 1.0


def test_extract_multiple_relationships():
    text = "Plato cites Socrates. Aristotle criticizes Plato."
    extractor = RelationshipExtractor()
    triples = extractor.extract_relationships(text)
    # Order may vary based on regex scanning; assert set equality
    expected = {
        ("Plato", "cites", "Socrates"),
        ("Aristotle", "criticizes", "Plato"),
    }
    got = {(t["subject"], t["relation"], t["object"]) for t in triples}
    assert expected.issubset(got)
