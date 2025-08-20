from typing import List, Dict, Optional

from arete.processing import RelationshipExtractor, TripleValidator


async def run_relationship_extraction(
    text: str,
    extractor: Optional[RelationshipExtractor] = None,
    validator: Optional[TripleValidator] = None,
    min_confidence: float = 0.6,
) -> List[Dict[str, object]]:
    if extractor is None:
        extractor = RelationshipExtractor()
    if validator is None:
        validator = TripleValidator()

    raw = extractor.extract_relationships(text)
    return validator.validate(raw, min_confidence=min_confidence)
