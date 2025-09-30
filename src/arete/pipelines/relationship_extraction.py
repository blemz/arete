
from arete.processing import RelationshipExtractor, TripleValidator


async def run_relationship_extraction(
    text: str,
    extractor: RelationshipExtractor | None = None,
    validator: TripleValidator | None = None,
    min_confidence: float = 0.6,
) -> list[dict[str, object]]:
    if extractor is None:
        extractor = RelationshipExtractor()
    if validator is None:
        validator = TripleValidator()

    raw = extractor.extract_relationships(text)
    return validator.validate(raw, min_confidence=min_confidence)
