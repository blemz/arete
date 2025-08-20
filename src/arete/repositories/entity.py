"""
Entity repository implementation for Arete Graph-RAG system.

Provides dual persistence strategy for Entity entities:
- Neo4j for graph relationships and traversal
- Weaviate for vector embeddings and semantic search

Implements both SearchableRepository and GraphRepository interfaces for
enhanced search capabilities and philosophical relationship modeling.
"""
import logging
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
import uuid

from arete.repositories.base import (
    GraphRepository,
    SearchableRepository,
    EntityNotFoundError,
    DuplicateEntityError,
    ValidationError,
    RepositoryError,
)
from arete.models.entity import Entity, EntityType
from arete.database.client import Neo4jClient
from arete.database.weaviate_client import WeaviateClient

logger = logging.getLogger(__name__)


class EntityRepository(GraphRepository[Entity], SearchableRepository[Entity]):
    """
    Repository implementation for Entity entities with dual persistence and graph capabilities.
    
    Stores entities in both Neo4j (for graph relationships and structured queries)
    and Weaviate (for vector embeddings and semantic search).
    
    Provides CRUD operations, semantic search, and graph traversal capabilities
    specifically designed for philosophical knowledge representation.
    """
    
    def __init__(self, neo4j_client: Neo4jClient, weaviate_client: WeaviateClient):
        """
        Initialize EntityRepository with required database clients.
        
        Args:
            neo4j_client: Neo4j client for graph operations
            weaviate_client: Weaviate client for vector operations
        """
        self._neo4j_client = neo4j_client
        self._weaviate_client = weaviate_client
    
    async def create(self, entity: Entity) -> Entity:
        """
        Create a new entity in both Neo4j and Weaviate.
        
        Args:
            entity: The entity to create
            
        Returns:
            The created entity with generated metadata
            
        Raises:
            DuplicateEntityError: If entity already exists
            ValidationError: If entity validation fails
            RepositoryError: For database errors
        """
        try:
            # Store in Neo4j for graph relationships and structured queries
            # Note: relationships and mentions are stored as separate Neo4j relationships
            neo4j_data = entity.to_neo4j_dict()
            # Remove relationships and mentions from entity properties (they'll be stored separately)
            neo4j_data.pop('relationships', None)
            neo4j_data.pop('mentions', None)
            
            neo4j_result = await self._neo4j_client.create_node(
                label='Entity',
                properties=neo4j_data
            )
            
            # Store in Weaviate for vector search
            await self._weaviate_client.save_entity(entity)
            
            logger.info(f"Created entity: {entity.id}")
            return entity
            
        except Exception as e:
            error_msg = str(e)
            if "constraint violation" in error_msg.lower() or "already exists" in error_msg.lower():
                raise DuplicateEntityError(f"Entity already exists: {error_msg}")
            else:
                logger.error(f"Failed to create entity {entity.id}: {error_msg}")
                raise RepositoryError(f"Failed to create entity: {error_msg}")
    
    async def get_by_id(self, entity_id: Union[UUID, str]) -> Optional[Entity]:
        """
        Retrieve entity by ID from Neo4j.
        
        Args:
            entity_id: The entity ID
            
        Returns:
            The entity if found, None otherwise
            
        Raises:
            RepositoryError: For database errors
        """
        try:
            result = await self._neo4j_client.get_node_by_id(
                str(entity_id), 'Entity'
            )
            
            if result:
                return Entity(**result)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get entity {entity_id}: {str(e)}")
            raise RepositoryError(f"Failed to retrieve entity: {str(e)}")
    
    async def update(self, entity: Entity) -> Entity:
        """
        Update entity in both Neo4j and Weaviate.
        
        Args:
            entity: The entity with updated values
            
        Returns:
            The updated entity
            
        Raises:
            EntityNotFoundError: If entity doesn't exist
            ValidationError: If entity validation fails
            RepositoryError: For database errors
        """
        try:
            # Update in Neo4j
            neo4j_data = entity.to_neo4j_dict()
            # Remove relationships and mentions from entity properties (they'll be stored separately)
            neo4j_data.pop('relationships', None)
            neo4j_data.pop('mentions', None)
            
            neo4j_result = await self._neo4j_client.update_node(
                str(entity.id),
                'Entity',
                neo4j_data
            )
            
            # Update in Weaviate
            await self._weaviate_client.save_entity(entity)
            
            logger.info(f"Updated entity: {entity.id}")
            return entity
            
        except Exception as e:
            error_msg = str(e)
            if "not found" in error_msg.lower():
                raise EntityNotFoundError(f"Entity not found: {entity.id}")
            else:
                logger.error(f"Failed to update entity {entity.id}: {error_msg}")
                raise RepositoryError(f"Failed to update entity: {error_msg}")
    
    async def delete(self, entity_id: Union[UUID, str]) -> bool:
        """
        Delete entity from both Neo4j and Weaviate.
        
        Args:
            entity_id: The entity ID to delete
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            RepositoryError: For database errors
        """
        try:
            # Delete from Neo4j
            neo4j_deleted = await self._neo4j_client.delete_node(
                str(entity_id), 'Entity'
            )
            
            # Delete from Weaviate
            await self._weaviate_client.delete_entity(
                'Entity', str(entity_id)
            )
            
            if neo4j_deleted:
                logger.info(f"Deleted entity: {entity_id}")
            
            return neo4j_deleted
            
        except Exception as e:
            logger.error(f"Failed to delete entity {entity_id}: {str(e)}")
            raise RepositoryError(f"Failed to delete entity: {str(e)}")
    
    async def list_all(
        self, 
        limit: int = 100, 
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Entity]:
        """
        List entities from Neo4j with optional filtering.
        
        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            filters: Optional filters to apply
            
        Returns:
            List of entities matching criteria
            
        Raises:
            RepositoryError: For database errors
        """
        try:
            # Build Cypher query with optional filters
            where_clause = ""
            params = {"limit": limit, "offset": offset}
            
            if filters:
                conditions = []
                for key, value in filters.items():
                    param_key = f"filter_{key}"
                    conditions.append(f"e.{key} = ${param_key}")
                    params[param_key] = value
                
                if conditions:
                    where_clause = "WHERE " + " AND ".join(conditions)
            
            query = f"""
                MATCH (e:Entity)
                {where_clause}
                RETURN e
                ORDER BY e.created_at DESC
                SKIP $offset
                LIMIT $limit
            """
            
            results = await self._neo4j_client.query(query, params)
            return [Entity(**result["e"]) for result in results]
            
        except Exception as e:
            logger.error(f"Failed to list entities: {str(e)}")
            raise RepositoryError(f"Failed to list entities: {str(e)}")
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities matching optional filters.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Number of entities matching criteria
            
        Raises:
            RepositoryError: For database errors
        """
        try:
            where_clause = ""
            params = {}
            
            if filters:
                conditions = []
                for key, value in filters.items():
                    param_key = f"filter_{key}"
                    conditions.append(f"e.{key} = ${param_key}")
                    params[param_key] = value
                
                if conditions:
                    where_clause = "WHERE " + " AND ".join(conditions)
            
            query = f"""
                MATCH (e:Entity)
                {where_clause}
                RETURN count(e) as count
            """
            
            results = await self._neo4j_client.query(query, params)
            return results[0]["count"] if results else 0
            
        except Exception as e:
            logger.error(f"Failed to count entities: {str(e)}")
            raise RepositoryError(f"Failed to count entities: {str(e)}")
    
    async def exists(self, entity_id: Union[UUID, str]) -> bool:
        """
        Check if entity exists by ID.
        
        Args:
            entity_id: The entity ID to check
            
        Returns:
            True if entity exists, False otherwise
            
        Raises:
            RepositoryError: For database errors
        """
        try:
            query = """
                MATCH (e:Entity)
                WHERE e.id = $entity_id
                RETURN count(e) > 0 as exists
            """
            
            results = await self._neo4j_client.query(
                query, {"entity_id": str(entity_id)}
            )
            return results[0]["exists"] if results else False
            
        except Exception as e:
            logger.error(f"Failed to check entity existence {entity_id}: {str(e)}")
            raise RepositoryError(f"Failed to check entity existence: {str(e)}")
    
    async def search_by_text(
        self,
        query: str,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Entity]:
        """
        Search entities by semantic text similarity using Weaviate.
        
        Args:
            query: The search query text
            limit: Maximum number of results to return
            similarity_threshold: Minimum similarity score (0.0-1.0)
            
        Returns:
            List of entities matching the query
            
        Raises:
            RepositoryError: For database errors
        """
        try:
            results = await self._weaviate_client.search_near_text(
                collection='Entity',
                query=query,
                limit=limit,
                certainty=similarity_threshold
            )
            
            return [Entity(**result) for result in results]
            
        except Exception as e:
            logger.error(f"Failed to search entities by text: {str(e)}")
            raise RepositoryError(f"Failed to search by text: {str(e)}")
    
    async def search_by_embedding(
        self,
        embedding: List[float],
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Entity]:
        """
        Search entities by embedding vector similarity using Weaviate.
        
        Args:
            embedding: The query embedding vector
            limit: Maximum number of results to return
            similarity_threshold: Minimum similarity score (0.0-1.0)
            
        Returns:
            List of entities with similar embeddings
            
        Raises:
            RepositoryError: For database errors
        """
        try:
            results = await self._weaviate_client.search_near_vector(
                collection='Entity',
                vector=embedding,
                limit=limit,
                certainty=similarity_threshold
            )
            
            return [Entity(**result) for result in results]
            
        except Exception as e:
            logger.error(f"Failed to search entities by embedding: {str(e)}")
            raise RepositoryError(f"Failed to search by embedding: {str(e)}")
    
    async def get_related(
        self,
        entity_id: Union[UUID, str],
        relationship_type: Optional[str] = None,
        direction: str = "BOTH",  # "INCOMING", "OUTGOING", "BOTH"
        limit: int = 10
    ) -> List[Entity]:
        """
        Get entities related to the given entity.
        
        Args:
            entity_id: The source entity ID
            relationship_type: Optional relationship type filter
            direction: Relationship direction to traverse
            limit: Maximum number of results to return
            
        Returns:
            List of related entities
            
        Raises:
            RepositoryError: For repository errors
        """
        try:
            # Build relationship pattern based on direction and type
            if relationship_type:
                if direction == "OUTGOING":
                    relationship_pattern = f"-[r:{relationship_type}]->"
                elif direction == "INCOMING":
                    relationship_pattern = f"<-[r:{relationship_type}]-"
                else:  # BOTH
                    relationship_pattern = f"-[r:{relationship_type}]-"
            else:
                if direction == "OUTGOING":
                    relationship_pattern = "-[r]->"
                elif direction == "INCOMING":
                    relationship_pattern = "<-[r]-"
                else:  # BOTH
                    relationship_pattern = "-[r]-"
            
            query = f"""
                MATCH (e:Entity {{id: $entity_id}})
                {relationship_pattern}(related:Entity)
                RETURN related
                LIMIT $limit
            """
            
            params = {
                "entity_id": str(entity_id),
                "limit": limit
            }
            
            if relationship_type:
                params["relationship_type"] = relationship_type
            
            results = await self._neo4j_client.query(query, params)
            return [Entity(**result["related"]) for result in results]
            
        except Exception as e:
            logger.error(f"Failed to get related entities for {entity_id}: {str(e)}")
            raise RepositoryError(f"Failed to get related entities: {str(e)}")
    
    async def get_neighbors(
        self,
        entity_id: Union[UUID, str],
        depth: int = 1,
        limit: int = 10
    ) -> List[Entity]:
        """
        Get neighboring entities within specified depth.
        
        Args:
            entity_id: The source entity ID
            depth: Maximum traversal depth
            limit: Maximum number of results to return
            
        Returns:
            List of neighboring entities
            
        Raises:
            RepositoryError: For repository errors
        """
        try:
            query = f"""
                MATCH (e:Entity {{id: $entity_id}})
                -[*1..{depth}]-(neighbor:Entity)
                WHERE neighbor.id <> $entity_id
                RETURN DISTINCT neighbor
                LIMIT $limit
            """
            
            params = {
                "entity_id": str(entity_id),
                "depth": depth,
                "limit": limit
            }
            
            results = await self._neo4j_client.query(query, params)
            return [Entity(**result["neighbor"]) for result in results]
            
        except Exception as e:
            logger.error(f"Failed to get neighbors for {entity_id}: {str(e)}")
            raise RepositoryError(f"Failed to get neighbors: {str(e)}")
    
    # Entity-specific methods
    
    async def get_by_name(self, name: str) -> List[Entity]:
        """
        Get entities by name using Neo4j (includes canonical form and aliases).
        
        Args:
            name: The entity name to search for
            
        Returns:
            List of entities with matching name
            
        Raises:
            RepositoryError: For database errors
        """
        try:
            query = """
                MATCH (e:Entity)
                WHERE e.name CONTAINS $name 
                   OR e.canonical_form CONTAINS $name
                   OR ANY(alias IN e.aliases WHERE alias CONTAINS $name)
                RETURN e
                ORDER BY e.created_at DESC
            """
            
            results = await self._neo4j_client.query(query, {"name": name})
            return [Entity(**result["e"]) for result in results]
            
        except Exception as e:
            logger.error(f"Failed to search entities by name: {str(e)}")
            raise RepositoryError(f"Failed to search by name: {str(e)}")
    
    async def get_by_type(self, entity_type: EntityType) -> List[Entity]:
        """
        Get entities by type using Neo4j.
        
        Args:
            entity_type: The entity type to search for
            
        Returns:
            List of entities of the specified type
            
        Raises:
            RepositoryError: For database errors
        """
        try:
            query = """
                MATCH (e:Entity)
                WHERE e.entity_type = $entity_type
                RETURN e
                ORDER BY e.created_at DESC
            """
            
            results = await self._neo4j_client.query(
                query, {"entity_type": str(entity_type.value)}
            )
            return [Entity(**result["e"]) for result in results]
            
        except Exception as e:
            logger.error(f"Failed to search entities by type: {str(e)}")
            raise RepositoryError(f"Failed to search by type: {str(e)}")
    
    async def search_entities(
        self,
        query: str,
        limit: int = 10,
        hybrid_weight: float = 0.7
    ) -> List[Entity]:
        """
        Hybrid search combining Neo4j keyword search and Weaviate semantic search.
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            hybrid_weight: Weight for semantic vs keyword search (0.0-1.0)
            
        Returns:
            List of entities matching the query
            
        Raises:
            RepositoryError: For database errors
        """
        try:
            # Keyword search in Neo4j
            neo4j_query = """
                MATCH (e:Entity)
                WHERE e.name CONTAINS $query 
                   OR e.description CONTAINS $query
                   OR e.canonical_form CONTAINS $query
                   OR ANY(alias IN e.aliases WHERE alias CONTAINS $query)
                RETURN e
                LIMIT $limit
            """
            
            neo4j_results = await self._neo4j_client.query(
                neo4j_query, {"query": query, "limit": limit}
            )
            
            # Semantic search in Weaviate
            weaviate_results = await self._weaviate_client.search_near_text(
                collection='Entity',
                query=query,
                limit=limit,
                certainty=0.6
            )
            
            # Combine results (simple merge for now - can be enhanced with scoring)
            combined_results = []
            seen_ids = set()
            
            # Add Neo4j results
            for result in neo4j_results:
                entity = Entity(**result["e"])
                if entity.id not in seen_ids:
                    combined_results.append(entity)
                    seen_ids.add(entity.id)
            
            # Add Weaviate results
            for result in weaviate_results:
                entity = Entity(**result)
                if entity.id not in seen_ids:
                    combined_results.append(entity)
                    seen_ids.add(entity.id)
            
            return combined_results[:limit]
            
        except Exception as e:
            logger.error(f"Failed to perform hybrid entity search: {str(e)}")
            raise RepositoryError(f"Failed to perform hybrid search: {str(e)}")
    
    # Knowledge Graph Methods
    
    async def create_relationship(
        self,
        source_entity_id: Union[UUID, str],
        target_entity_id: Union[UUID, str],
        relationship_type: str,
        confidence: float = 0.5,
        source: Optional[str] = None,
        evidence: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create a relationship between two entities in Neo4j.
        
        Args:
            source_entity_id: ID of the source entity
            target_entity_id: ID of the target entity
            relationship_type: Type of relationship (e.g., INFLUENCES, CRITIQUES)
            confidence: Confidence score for the relationship (0.0-1.0)
            source: Source of the relationship information
            evidence: Text evidence supporting the relationship
            properties: Additional relationship properties
            
        Returns:
            True if relationship was created, False otherwise
            
        Raises:
            RepositoryError: For database errors
        """
        try:
            # Ensure both entities exist
            source_exists = await self.exists(source_entity_id)
            target_exists = await self.exists(target_entity_id)
            
            if not source_exists or not target_exists:
                raise EntityNotFoundError(f"One or both entities not found: {source_entity_id}, {target_entity_id}")
            
            # Build relationship properties
            rel_properties = {
                "confidence": confidence,
                "created_at": "datetime()",
                "updated_at": "datetime()"
            }
            
            if source:
                rel_properties["source"] = source
            if evidence:
                rel_properties["evidence"] = evidence
            if properties:
                rel_properties.update(properties)
            
            # Create relationship query
            query = f"""
                MATCH (source:Entity {{id: $source_id}})
                MATCH (target:Entity {{id: $target_id}})
                CREATE (source)-[r:`{relationship_type}`]->(target)
                SET r += $properties
                RETURN r
            """
            
            results = await self._neo4j_client.query(query, {
                "source_id": str(source_entity_id),
                "target_id": str(target_entity_id),
                "properties": rel_properties
            })
            
            success = len(results) > 0
            if success:
                logger.info(f"Created relationship: {source_entity_id} -{relationship_type}-> {target_entity_id}")
            
            return success
            
        except Exception as e:
            error_msg = str(e)
            if "not found" in error_msg.lower():
                raise EntityNotFoundError(f"Entity not found: {error_msg}")
            else:
                logger.error(f"Failed to create relationship: {error_msg}")
                raise RepositoryError(f"Failed to create relationship: {error_msg}")
    
    async def get_relationships(
        self,
        entity_id: Union[UUID, str],
        relationship_type: Optional[str] = None,
        direction: str = "BOTH"
    ) -> List[Dict[str, Any]]:
        """
        Get relationships for an entity with detailed information.
        
        Args:
            entity_id: The entity ID
            relationship_type: Optional relationship type filter
            direction: Relationship direction ("OUTGOING", "INCOMING", "BOTH")
            
        Returns:
            List of relationship dictionaries with source, target, and properties
            
        Raises:
            RepositoryError: For database errors
        """
        try:
            # Build relationship pattern based on direction and type
            if relationship_type:
                if direction == "OUTGOING":
                    relationship_pattern = f"-[r:`{relationship_type}`]->"
                elif direction == "INCOMING":
                    relationship_pattern = f"<-[r:`{relationship_type}`]-"
                else:  # BOTH
                    relationship_pattern = f"-[r:`{relationship_type}`]-"
            else:
                if direction == "OUTGOING":
                    relationship_pattern = "-[r]->"
                elif direction == "INCOMING":
                    relationship_pattern = "<-[r]-"
                else:  # BOTH
                    relationship_pattern = "-[r]-"
            
            query = f"""
                MATCH (source:Entity {{id: $entity_id}})
                {relationship_pattern}(target:Entity)
                RETURN source, r, target, type(r) as relationship_type
            """
            
            results = await self._neo4j_client.query(query, {"entity_id": str(entity_id)})
            
            relationships = []
            for result in results:
                rel_data = {
                    "source": Entity(**result["source"]),
                    "target": Entity(**result["target"]),
                    "relationship_type": result["relationship_type"],
                    "properties": dict(result["r"])
                }
                relationships.append(rel_data)
            
            return relationships
            
        except Exception as e:
            logger.error(f"Failed to get relationships for {entity_id}: {str(e)}")
            raise RepositoryError(f"Failed to get relationships: {str(e)}")
    
    async def batch_create_triples(
        self,
        triples: List[Dict[str, Any]],
        entity_name_to_id: Dict[str, UUID]
    ) -> int:
        """
        Batch create relationships from extracted triples.
        
        Args:
            triples: List of triple dictionaries with subject, relation, object, confidence
            entity_name_to_id: Mapping from entity names to their IDs
            
        Returns:
            Number of relationships successfully created
            
        Raises:
            RepositoryError: For database errors
        """
        try:
            created_count = 0
            
            for triple in triples:
                subject_name = triple.get("subject", "").strip()
                object_name = triple.get("object", "").strip()
                relation_type = triple.get("relation", "").strip()
                confidence = float(triple.get("confidence", 0.5))
                source = triple.get("source", "extracted")
                evidence = triple.get("evidence", "")
                
                # Skip invalid triples
                if not subject_name or not object_name or not relation_type:
                    continue
                
                # Look up entity IDs
                source_id = entity_name_to_id.get(subject_name)
                target_id = entity_name_to_id.get(object_name)
                
                if not source_id or not target_id:
                    logger.warning(f"Skipping triple - entities not found: {subject_name} -> {object_name}")
                    continue
                
                try:
                    # Create the relationship
                    success = await self.create_relationship(
                        source_entity_id=source_id,
                        target_entity_id=target_id,
                        relationship_type=relation_type,
                        confidence=confidence,
                        source=source,
                        evidence=evidence
                    )
                    
                    if success:
                        created_count += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to create relationship for triple {subject_name} -{relation_type}-> {object_name}: {str(e)}")
                    continue
            
            logger.info(f"Successfully created {created_count} relationships from {len(triples)} triples")
            return created_count
            
        except Exception as e:
            logger.error(f"Failed to batch create triples: {str(e)}")
            raise RepositoryError(f"Failed to batch create triples: {str(e)}")
    
    async def find_or_create_entities_by_name(
        self,
        entity_names: List[str],
        default_type: EntityType = EntityType.CONCEPT,
        document_id: Optional[UUID] = None
    ) -> Dict[str, UUID]:
        """
        Find existing entities by name or create new ones.
        
        Args:
            entity_names: List of entity names to find or create
            default_type: Default entity type for new entities
            document_id: Source document ID for new entities
            
        Returns:
            Dictionary mapping entity names to their IDs
            
        Raises:
            RepositoryError: For database errors
        """
        try:
            name_to_id = {}
            
            for name in entity_names:
                if not name or not name.strip():
                    continue
                
                name = name.strip()
                
                # First try to find existing entity
                existing_entities = await self.get_by_name(name)
                
                if existing_entities:
                    # Use the first matching entity
                    name_to_id[name] = existing_entities[0].id
                else:
                    # Create new entity
                    new_entity = Entity(
                        name=name,
                        entity_type=default_type,
                        source_document_id=document_id or uuid.UUID("00000000-0000-0000-0000-000000000000"),
                        confidence=0.7,  # Default confidence for auto-created entities
                        description=f"Auto-generated {default_type.value} entity"
                    )
                    
                    created_entity = await self.create(new_entity)
                    name_to_id[name] = created_entity.id
                    logger.info(f"Created new entity: {name} ({default_type.value})")
            
            return name_to_id
            
        except Exception as e:
            logger.error(f"Failed to find or create entities: {str(e)}")
            raise RepositoryError(f"Failed to find or create entities: {str(e)}")