from typing import List, Optional

from arete.models.entity import Entity
from arete.processing import EntityExtractor


async def run_entity_extraction(
	text: str,
	document_id,
	repository,
	extractor: Optional[EntityExtractor] = None,
) -> List[Entity]:
	"""Extract entities from text and persist them using the repository.

	Args:
		text: Source text
		document_id: UUID of the document
		repository: Async repository with create(Entity) -> Entity
		extractor: Optional preconfigured EntityExtractor

	Returns:
		List of created or found Entity objects
	"""
	if extractor is None:
		extractor = EntityExtractor()

	entities = extractor.extract_entities(text=text, document_id=document_id)
	results: List[Entity] = []
	for entity in entities:
		created = await repository.create(entity)
		results.append(created)
	return results
