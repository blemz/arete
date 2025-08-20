import uuid
from typing import List, Dict, Tuple

import pytest

from arete.models.entity import Entity, EntityType


@pytest.mark.asyncio
async def test_kg_pipeline_entities_and_triples():
    from arete.pipelines.kg_extraction import run_kg_extraction

    text = "Socrates refutes Thrasymachus in the Republic."
    document_id = uuid.uuid4()

    # Deterministic entity patterns for test
    entity_patterns = [
        {"label": "PERSON", "pattern": "Socrates"},
        {"label": "PERSON", "pattern": "Thrasymachus"},
        {"label": "WORK_OF_ART", "pattern": "Republic"},
    ]

    entities, triples = await run_kg_extraction(
        text=text,
        document_id=document_id,
        entity_patterns=entity_patterns,
        min_triple_confidence=0.6,
    )

    # Entities assertions
    by_name = {e.name: e for e in entities}
    assert by_name["Socrates"].entity_type == EntityType.PERSON
    assert by_name["Thrasymachus"].entity_type == EntityType.PERSON
    assert by_name["Republic"].entity_type == EntityType.WORK

    # Triples assertions
    tuples: List[Tuple[str, str, str]] = [
        (t["subject"], t["relation"], t["object"]) for t in triples
    ]
    assert ("Socrates", "refutes", "Thrasymachus") in tuples


@pytest.mark.asyncio
async def test_kg_pipeline_filters_low_confidence_triples():
    from arete.pipelines.kg_extraction import run_kg_extraction

    text = "Plato cites Socrates."
    document_id = uuid.uuid4()

    entity_patterns = [
        {"label": "PERSON", "pattern": "Plato"},
        {"label": "PERSON", "pattern": "Socrates"},
    ]

    # Set threshold above extractor's default 0.7 to force filtering
    entities, triples = await run_kg_extraction(
        text=text,
        document_id=document_id,
        entity_patterns=entity_patterns,
        min_triple_confidence=0.8,
    )

    assert len(triples) == 0
    assert {e.name for e in entities} == {"Plato", "Socrates"}
