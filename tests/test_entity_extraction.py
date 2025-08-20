import uuid
from typing import List

import pytest

from arete.models.entity import Entity, EntityType
from arete.processing import EntityExtractor


class TestEntityExtractor:
	def test_extract_single_person_with_ruler(self):
		patterns = [
			{"label": "PERSON", "pattern": "Socrates"},
		]
		extractor = EntityExtractor(patterns=patterns)
		text = "Socrates engages in dialogue about virtue."
		document_id = uuid.uuid4()

		entities: List[Entity] = extractor.extract_entities(text=text, document_id=document_id)

		assert isinstance(entities, list)
		assert len(entities) == 1

		entity = entities[0]
		assert entity.name == "Socrates"
		assert entity.entity_type == EntityType.PERSON
		assert entity.source_document_id == document_id
		assert entity.confidence >= 0.5 and entity.confidence <= 1.0
		assert entity.mention_count == 1
		mention = entity.mentions[0]
		assert mention.text == "Socrates"
		assert 0 <= mention.start_position < mention.end_position <= len(text)
		assert mention.document_id == document_id
		assert isinstance(mention.context, str) and len(mention.context) > 0

	def test_aggregates_multiple_mentions_same_entity(self):
		patterns = [
			{"label": "PERSON", "pattern": "Socrates"},
		]
		extractor = EntityExtractor(patterns=patterns)
		text = "Socrates argues about justice. Many say Socrates was wise."
		document_id = uuid.uuid4()

		entities: List[Entity] = extractor.extract_entities(text=text, document_id=document_id)

		assert len(entities) == 1
		entity = entities[0]
		assert entity.name == "Socrates"
		assert entity.mention_count == 2
		# Ensure mentions have distinct positions
		positions = {(m.start_position, m.end_position) for m in entity.mentions}
		assert len(positions) == 2

	def test_empty_text_returns_empty_list(self):
		extractor = EntityExtractor()
		entities = extractor.extract_entities(text="", document_id=uuid.uuid4())
		assert entities == []

	def test_label_mapping_for_multiple_types(self):
		patterns = [
			{"label": "PERSON", "pattern": "Socrates"},
			{"label": "ORG", "pattern": "Academy"},
			{"label": "GPE", "pattern": "Athens"},
			{"label": "WORK_OF_ART", "pattern": "Republic"},
		]
		extractor = EntityExtractor(patterns=patterns)
		text = "In Athens, Socrates taught at the Academy and discussed the Republic."
		document_id = uuid.uuid4()

		entities: List[Entity] = extractor.extract_entities(text=text, document_id=document_id)

		by_name = {e.name: e for e in entities}
		assert by_name["Socrates"].entity_type == EntityType.PERSON
		assert by_name["Academy"].entity_type == EntityType.CONCEPT
		assert by_name["Athens"].entity_type == EntityType.PLACE
		assert by_name["Republic"].entity_type == EntityType.WORK

	def test_multiple_distinct_entities_in_text(self):
		patterns = [
			{"label": "PERSON", "pattern": "Plato"},
			{"label": "PERSON", "pattern": "Socrates"},
		]
		extractor = EntityExtractor(patterns=patterns)
		text = "Plato was a student of Socrates."
		document_id = uuid.uuid4()

		entities: List[Entity] = extractor.extract_entities(text=text, document_id=document_id)

		assert {e.name for e in entities} == {"Plato", "Socrates"}
		for e in entities:
			assert e.entity_type == EntityType.PERSON 