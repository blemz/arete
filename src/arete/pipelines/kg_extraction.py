from typing import List, Dict, Tuple, Optional

from arete.models.entity import Entity, EntityType, MentionData
from arete.processing import EntityExtractor, RelationshipExtractor, TripleValidator


def _map_label_to_entity_type(label: str) -> EntityType:
    u = label.upper()
    if u == "PERSON":
        return EntityType.PERSON
    if u in {"ORG"}:
        return EntityType.CONCEPT
    if u in {"GPE", "LOC"}:
        return EntityType.PLACE
    if u in {"WORK_OF_ART"}:
        return EntityType.WORK
    return EntityType.CONCEPT


async def run_kg_extraction(
    text: str,
    document_id,
    entity_patterns: Optional[List[Dict[str, str]]] = None,
    min_triple_confidence: float = 0.6,
) -> Tuple[List[Entity], List[Dict[str, object]]]:
    entity_extractor = EntityExtractor(patterns=entity_patterns)
    rel_extractor = RelationshipExtractor()
    validator = TripleValidator()

    entities: List[Entity] = entity_extractor.extract_entities(text=text, document_id=document_id)

    # Deterministic fallback: if spaCy pipeline unavailable, build entities from patterns
    if not entities and entity_patterns:
        name_to_mentions: Dict[str, List[MentionData]] = {}
        for pat in entity_patterns:
            name = pat.get("pattern", "").strip()
            if not name:
                continue
            start = text.find(name)
            while start != -1:
                end = start + len(name)
                context_window = 80
                ctx_start = max(0, start - context_window)
                ctx_end = min(len(text), end + context_window)
                mention = MentionData(
                    text=name,
                    context=text[ctx_start:ctx_end].strip(),
                    start_position=start,
                    end_position=end,
                    document_id=document_id,
                    confidence=0.9,
                )
                name_to_mentions.setdefault(name, []).append(mention)
                start = text.find(name, end)
        entities = []
        for name, mentions in name_to_mentions.items():
            e = Entity(
                name=name,
                entity_type=_map_label_to_entity_type(pat.get("label", "CONCEPT")),
                source_document_id=document_id,
                mentions=mentions,
                confidence=0.9,
            )
            entities.append(e)

    raw_triples = rel_extractor.extract_relationships(text)
    triples = validator.validate(raw_triples, min_confidence=min_triple_confidence)
    return entities, triples
