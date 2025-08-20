from typing import List, Dict

import pytest

from arete.processing import RelationshipExtractor, TripleValidator


@pytest.mark.asyncio
async def test_relationship_pipeline_validates_and_returns(monkeypatch):
    from arete.pipelines.relationship_extraction import run_relationship_extraction

    extractor = RelationshipExtractor()
    validator = TripleValidator()

    text = "Plato cites Socrates. Aristotle criticizes Plato."

    triples: List[Dict[str, object]] = await run_relationship_extraction(
        text=text,
        extractor=extractor,
        validator=validator,
        min_confidence=0.6,
    )

    assert any(t["subject"] == "Plato" and t["relation"] == "cites" and t["object"] == "Socrates" for t in triples)
    assert any(t["subject"] == "Aristotle" and t["relation"] == "criticizes" and t["object"] == "Plato" for t in triples)


@pytest.mark.asyncio
async def test_relationship_pipeline_filters_low_confidence(monkeypatch):
    from arete.pipelines.relationship_extraction import run_relationship_extraction

    extractor = RelationshipExtractor()
    validator = TripleValidator()

    text = "Plato cites Socrates."  # extractor assigns 0.7 conf

    triples = await run_relationship_extraction(
        text=text,
        extractor=extractor,
        validator=validator,
        min_confidence=0.8,  # above extractor's default
    )

    assert triples == []
