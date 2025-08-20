import uuid
from typing import List

import pytest

from arete.models.entity import Entity, EntityType
from arete.processing import EntityExtractor


class FakeEntityRepository:
    def __init__(self):
        self.created: List[Entity] = []

    async def create(self, entity: Entity) -> Entity:
        self.created.append(entity)
        return entity


@pytest.mark.asyncio
async def test_pipeline_creates_entities(monkeypatch):
    from arete.pipelines.entity_extraction import run_entity_extraction

    repo = FakeEntityRepository()
    extractor = EntityExtractor(patterns=[{"label": "PERSON", "pattern": "Socrates"}])

    doc_id = uuid.uuid4()
    text = "Socrates speaks in the dialogue."

    result: List[Entity] = await run_entity_extraction(
        text=text,
        document_id=doc_id,
        repository=repo,
        extractor=extractor,
    )

    assert len(result) == 1
    assert len(repo.created) == 1
    assert result[0].name == "Socrates"
    assert result[0].entity_type == EntityType.PERSON
    assert result[0].source_document_id == doc_id


@pytest.mark.asyncio
async def test_pipeline_no_entities_calls_no_create():
    from arete.pipelines.entity_extraction import run_entity_extraction

    repo = FakeEntityRepository()
    extractor = EntityExtractor(patterns=[{"label": "PERSON", "pattern": "Plato"}])

    doc_id = uuid.uuid4()
    text = "No named entities here."

    result: List[Entity] = await run_entity_extraction(
        text=text,
        document_id=doc_id,
        repository=repo,
        extractor=extractor,
    )

    assert result == []
    assert repo.created == []
