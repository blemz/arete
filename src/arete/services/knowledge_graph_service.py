"""
Knowledge Graph Service for Arete Graph-RAG system.

Provides high-level interface for knowledge graph extraction and population
with batch processing capabilities for large philosophical documents.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from uuid import UUID
import asyncio

from arete.models.entity import Entity, EntityType
from arete.processing.extractors import EntityExtractor, RelationshipExtractor, TripleValidator
from arete.repositories.entity import EntityRepository
from arete.processing.chunker import ChunkingStrategy

logger = logging.getLogger(__name__)


class KnowledgeGraphExtractionResult:
    """Result container for knowledge graph extraction operations."""
    
    def __init__(self):
        self.entities_created: int = 0
        self.entities_found: int = 0
        self.relationships_created: int = 0
        self.triples_extracted: int = 0
        self.triples_validated: int = 0
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.processing_time: float = 0.0
    
    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        logger.error(f"KG Extraction Error: {error}")
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)
        logger.warning(f"KG Extraction Warning: {warning}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            "entities_created": self.entities_created,
            "entities_found": self.entities_found,
            "relationships_created": self.relationships_created,
            "triples_extracted": self.triples_extracted,
            "triples_validated": self.triples_validated,
            "errors": self.errors,
            "warnings": self.warnings,
            "processing_time": self.processing_time,
            "success": len(self.errors) == 0
        }


class KnowledgeGraphService:
    """
    High-level service for knowledge graph extraction and population.
    
    Orchestrates entity extraction, relationship extraction, validation,
    and storage in Neo4j with support for batch processing of large documents.
    """
    
    def __init__(
        self,
        entity_repository: EntityRepository,
        entity_extractor: Optional[EntityExtractor] = None,
        relationship_extractor: Optional[RelationshipExtractor] = None,
        triple_validator: Optional[TripleValidator] = None
    ):
        """
        Initialize KnowledgeGraphService.
        
        Args:
            entity_repository: Repository for entity storage and retrieval
            entity_extractor: Optional entity extractor (creates default if None)
            relationship_extractor: Optional relationship extractor (creates default if None)
            triple_validator: Optional triple validator (creates default if None)
        """
        self.entity_repository = entity_repository
        self.entity_extractor = entity_extractor or EntityExtractor(use_philosophical_patterns=True)
        self.relationship_extractor = relationship_extractor or RelationshipExtractor()
        self.triple_validator = triple_validator or TripleValidator()
    
    async def extract_knowledge_graph(
        self,
        text: str,
        document_id: UUID,
        min_confidence: float = 0.6,
        chunk_size: Optional[int] = None,
        enable_batching: bool = True
    ) -> KnowledgeGraphExtractionResult:
        """
        Extract knowledge graph from text with entities and relationships.
        
        Args:
            text: Text to extract knowledge from
            document_id: ID of the source document
            min_confidence: Minimum confidence threshold for triples
            chunk_size: Optional chunk size for large texts (enables chunking if provided)
            enable_batching: Whether to enable batch processing optimizations
            
        Returns:
            KnowledgeGraphExtractionResult with extraction statistics
        """
        import time
        start_time = time.time()
        result = KnowledgeGraphExtractionResult()
        
        try:
            if chunk_size and len(text) > chunk_size:
                # Process large text in chunks
                return await self._extract_from_chunks(
                    text, document_id, min_confidence, chunk_size, result
                )
            else:
                # Process text as single unit
                return await self._extract_from_text(
                    text, document_id, min_confidence, enable_batching, result
                )
        
        except Exception as e:
            result.add_error(f"Knowledge graph extraction failed: {str(e)}")
            result.processing_time = time.time() - start_time
            return result
        
        finally:
            result.processing_time = time.time() - start_time
    
    async def _extract_from_text(
        self,
        text: str,
        document_id: UUID,
        min_confidence: float,
        enable_batching: bool,
        result: KnowledgeGraphExtractionResult
    ) -> KnowledgeGraphExtractionResult:
        """Extract knowledge graph from a single text."""
        
        # Step 1: Extract entities
        entities = self.entity_extractor.extract_entities(text, document_id)
        logger.info(f"Extracted {len(entities)} entities from text")
        
        # Step 2: Store entities and build name mapping
        entity_name_to_id = {}
        
        if enable_batching:
            # Batch process entities
            entity_names = [entity.name for entity in entities]
            entity_name_to_id = await self.entity_repository.find_or_create_entities_by_name(
                entity_names, EntityType.CONCEPT, document_id
            )
            result.entities_found = len([name for name in entity_names if name in entity_name_to_id])
            result.entities_created = len(entity_name_to_id) - result.entities_found
        else:
            # Process entities individually
            for entity in entities:
                try:
                    existing_entities = await self.entity_repository.get_by_name(entity.name)
                    
                    if existing_entities:
                        entity_name_to_id[entity.name] = existing_entities[0].id
                        result.entities_found += 1
                    else:
                        created_entity = await self.entity_repository.create(entity)
                        entity_name_to_id[entity.name] = created_entity.id
                        result.entities_created += 1
                        
                except Exception as e:
                    result.add_warning(f"Failed to process entity {entity.name}: {str(e)}")
        
        # Step 3: Extract relationships
        entity_names = list(entity_name_to_id.keys())
        raw_triples = self.relationship_extractor.extract_relationships(text, entity_names)
        result.triples_extracted = len(raw_triples)
        logger.info(f"Extracted {len(raw_triples)} raw relationship triples")
        
        # Step 4: Validate triples
        validated_triples = self.triple_validator.validate(raw_triples, min_confidence)
        result.triples_validated = len(validated_triples)
        logger.info(f"Validated {len(validated_triples)} relationship triples")
        
        # Step 5: Store relationships
        if validated_triples:
            if enable_batching:
                result.relationships_created = await self.entity_repository.batch_create_triples(
                    validated_triples, entity_name_to_id
                )
            else:
                # Process relationships individually
                for triple in validated_triples:
                    try:
                        subject_id = entity_name_to_id.get(triple["subject"])
                        object_id = entity_name_to_id.get(triple["object"])
                        
                        if subject_id and object_id:
                            success = await self.entity_repository.create_relationship(
                                source_entity_id=subject_id,
                                target_entity_id=object_id,
                                relationship_type=triple["relation"],
                                confidence=triple["confidence"],
                                source=triple.get("source", "extracted"),
                                evidence=triple.get("evidence", "")
                            )
                            
                            if success:
                                result.relationships_created += 1
                                
                    except Exception as e:
                        result.add_warning(f"Failed to create relationship: {str(e)}")
        
        logger.info(f"Knowledge graph extraction completed: {result.entities_created} entities created, "
                   f"{result.relationships_created} relationships created")
        
        return result
    
    async def _extract_from_chunks(
        self,
        text: str,
        document_id: UUID,
        min_confidence: float,
        chunk_size: int,
        result: KnowledgeGraphExtractionResult
    ) -> KnowledgeGraphExtractionResult:
        """Extract knowledge graph from text using chunking strategy."""
        
        # Create chunking strategy
        chunker = ChunkingStrategy.get_chunker("sliding_window", 
                                             chunk_size=chunk_size, 
                                             overlap=chunk_size // 4)
        
        # Split text into chunks
        from arete.models.chunk import ChunkType
        chunks = chunker.chunk_text(text, document_id)
        logger.info(f"Split text into {len(chunks)} chunks for processing")
        
        # Track entities across chunks to avoid duplicates
        global_entity_names: Set[str] = set()
        global_triples: List[Dict[str, Any]] = []
        
        # Process each chunk
        for i, chunk in enumerate(chunks):
            try:
                logger.info(f"Processing chunk {i+1}/{len(chunks)}")
                
                # Extract entities from chunk
                chunk_entities = self.entity_extractor.extract_entities(chunk.text, document_id)
                chunk_entity_names = [entity.name for entity in chunk_entities]
                global_entity_names.update(chunk_entity_names)
                
                # Extract relationships from chunk
                chunk_triples = self.relationship_extractor.extract_relationships(
                    chunk.text, chunk_entity_names
                )
                global_triples.extend(chunk_triples)
                
            except Exception as e:
                result.add_warning(f"Failed to process chunk {i+1}: {str(e)}")
        
        result.triples_extracted = len(global_triples)
        
        # Validate all triples
        validated_triples = self.triple_validator.validate(global_triples, min_confidence)
        result.triples_validated = len(validated_triples)
        
        # Create/find all entities
        entity_name_to_id = await self.entity_repository.find_or_create_entities_by_name(
            list(global_entity_names), EntityType.CONCEPT, document_id
        )
        
        result.entities_found = len([name for name in global_entity_names if name in entity_name_to_id])
        result.entities_created = len(entity_name_to_id) - result.entities_found
        
        # Batch create relationships
        result.relationships_created = await self.entity_repository.batch_create_triples(
            validated_triples, entity_name_to_id
        )
        
        logger.info(f"Chunked knowledge graph extraction completed: {result.entities_created} entities created, "
                   f"{result.relationships_created} relationships created from {len(chunks)} chunks")
        
        return result
    
    async def get_entity_relationships(
        self,
        entity_id: UUID,
        relationship_type: Optional[str] = None,
        max_depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get comprehensive relationship information for an entity.
        
        Args:
            entity_id: ID of the entity
            relationship_type: Optional filter for relationship type
            max_depth: Maximum traversal depth for relationships
            
        Returns:
            Dictionary with entity and relationship information
        """
        try:
            # Get the entity
            entity = await self.entity_repository.get_by_id(entity_id)
            if not entity:
                raise ValueError(f"Entity not found: {entity_id}")
            
            # Get direct relationships
            direct_relationships = await self.entity_repository.get_relationships(
                entity_id, relationship_type
            )
            
            # Get neighbors within max_depth
            neighbors = await self.entity_repository.get_neighbors(
                entity_id, depth=max_depth
            )
            
            # Get related entities with same relationship type
            related_entities = await self.entity_repository.get_related(
                entity_id, relationship_type, limit=20
            )
            
            return {
                "entity": entity,
                "direct_relationships": direct_relationships,
                "neighbors": neighbors,
                "related_entities": related_entities,
                "relationship_count": len(direct_relationships),
                "neighbor_count": len(neighbors)
            }
            
        except Exception as e:
            logger.error(f"Failed to get entity relationships for {entity_id}: {str(e)}")
            raise
    
    async def analyze_philosophical_network(
        self,
        entity_types: Optional[List[EntityType]] = None,
        min_relationships: int = 1
    ) -> Dict[str, Any]:
        """
        Analyze the philosophical knowledge network.
        
        Args:
            entity_types: Optional filter for entity types
            min_relationships: Minimum number of relationships for inclusion
            
        Returns:
            Network analysis results
        """
        try:
            # Get entities with relationship counts
            filters = {}
            if entity_types:
                # For now, we'll filter after retrieval since the repository
                # doesn't support complex filters yet
                pass
            
            entities = await self.entity_repository.list_all(limit=1000, filters=filters)
            
            # Filter by entity type and relationship count
            filtered_entities = []
            for entity in entities:
                if entity_types and entity.entity_type not in entity_types:
                    continue
                
                relationships = await self.entity_repository.get_relationships(entity.id)
                if len(relationships) >= min_relationships:
                    filtered_entities.append({
                        "entity": entity,
                        "relationship_count": len(relationships)
                    })
            
            # Sort by relationship count
            filtered_entities.sort(key=lambda x: x["relationship_count"], reverse=True)
            
            # Calculate network statistics
            total_entities = len(filtered_entities)
            total_relationships = sum(e["relationship_count"] for e in filtered_entities)
            avg_relationships = total_relationships / total_entities if total_entities > 0 else 0
            
            # Get most connected entities
            most_connected = filtered_entities[:10]
            
            return {
                "total_entities": total_entities,
                "total_relationships": total_relationships,
                "average_relationships_per_entity": avg_relationships,
                "most_connected_entities": most_connected,
                "entity_type_distribution": self._get_entity_type_distribution(filtered_entities)
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze philosophical network: {str(e)}")
            raise
    
    def _get_entity_type_distribution(self, entities: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of entity types."""
        distribution = {}
        for entity_data in entities:
            entity = entity_data["entity"]
            # Handle both enum and string entity types
            if hasattr(entity.entity_type, 'value'):
                entity_type = entity.entity_type.value
            else:
                entity_type = str(entity.entity_type)
            distribution[entity_type] = distribution.get(entity_type, 0) + 1
        return distribution