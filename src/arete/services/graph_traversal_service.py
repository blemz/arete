"""
Graph Traversal Service for Arete Graph-RAG system.

Provides graph-based retrieval capabilities by:
- Detecting entities in user queries
- Generating dynamic Cypher queries for Neo4j
- Executing graph traversals to find related entities and relationships
- Integrating graph results with existing dense/sparse retrieval

Follows the established service pattern with proper abstractions,
error handling, and performance optimization.
"""

import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Tuple
from uuid import UUID, uuid4
from contextlib import contextmanager

# Import types to avoid circular imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..database.client import Neo4jClient
    from ..services.dense_retrieval_service import SearchResult

from ..config import Settings, get_settings
from ..models.entity import Entity, EntityType
from .base import ServiceError

logger = logging.getLogger(__name__)


class RelationshipType(str, Enum):
    """Types of relationships in the philosophical knowledge graph."""
    
    RELATES_TO = "RELATES_TO"
    MENTIONS = "MENTIONS"
    CONTAINS = "CONTAINS"
    CITES = "CITES"
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    DEFINES = "DEFINES"
    EXEMPLIFIES = "EXEMPLIFIES"
    TEACHER_STUDENT = "TEACHER_STUDENT"
    INFLUENCED_BY = "INFLUENCED_BY"
    CONTEMPORARY_OF = "CONTEMPORARY_OF"


class GraphTraversalError(ServiceError):
    """Base exception for graph traversal service errors."""
    pass


class CypherQueryError(GraphTraversalError):
    """Exception for Cypher query generation or execution errors."""
    pass


class EntityDetectionError(GraphTraversalError):
    """Exception for entity detection errors."""
    pass


@dataclass
class EntityMention:
    """Represents a detected entity mention in query text."""
    
    text: str
    entity_type: EntityType
    confidence: float
    start_position: int
    end_position: int
    entity_id: Optional[UUID] = None
    normalized_text: Optional[str] = None
    
    def __post_init__(self):
        """Validate entity mention data."""
        if self.end_position <= self.start_position:
            raise ValueError("end_position must be greater than start_position")
        
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
            
        if not self.normalized_text:
            self.normalized_text = self._normalize_text(self.text)
    
    def _normalize_text(self, text: str) -> str:
        """Normalize entity text for matching."""
        return text.lower().strip()
    
    def is_valid(self) -> bool:
        """Check if entity mention is valid."""
        return (
            len(self.text.strip()) > 0 and
            self.confidence > 0.0 and
            self.end_position > self.start_position
        )


@dataclass
class CypherQuery:
    """Represents a Cypher query with parameters and metadata."""
    
    cypher: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    estimated_complexity: int = 1
    timeout_seconds: int = 30
    query_type: str = "general"
    
    def __post_init__(self):
        """Calculate estimated complexity if not provided."""
        if self.estimated_complexity == 1 and self.cypher:
            self.estimated_complexity = self._estimate_complexity()
    
    def _estimate_complexity(self) -> int:
        """Estimate query complexity based on Cypher syntax."""
        complexity = 1
        
        # Count patterns and operations
        match_count = len(re.findall(r'\bMATCH\b', self.cypher, re.IGNORECASE))
        relationship_count = len(re.findall(r'-\[.*?\]-', self.cypher))
        variable_length = len(re.findall(r'\[\*\d*\.\.\d*\]', self.cypher))
        
        complexity += match_count
        complexity += relationship_count * 2
        complexity += variable_length * 5  # Variable length paths are expensive
        
        return min(complexity, 10)  # Cap at 10
    
    def is_valid(self) -> bool:
        """Basic Cypher query syntax validation."""
        if not self.cypher:
            return False
            
        # Basic syntax checks
        required_keywords = ['MATCH', 'RETURN']
        cypher_upper = self.cypher.upper()
        
        return any(keyword in cypher_upper for keyword in required_keywords)
    
    def get_cache_key(self) -> str:
        """Generate cache key for this query."""
        import hashlib
        query_str = f"{self.cypher}_{str(sorted(self.parameters.items()))}"
        return hashlib.md5(query_str.encode()).hexdigest()


@dataclass
class GraphResult:
    """Represents a result from graph traversal."""
    
    entity: Entity
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    path_length: int = 1
    relevance_score: float = 0.0
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate graph result data."""
        if not 0.0 <= self.relevance_score <= 1.0:
            raise ValueError("relevance_score must be between 0.0 and 1.0")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")


class EntityDetector:
    """Detects entities in query text using pattern matching and NER."""
    
    def __init__(self, settings: Optional[Settings] = None):
        """Initialize entity detector."""
        self.settings = settings or get_settings()
        
        # Philosophical entity patterns (expandable)
        self.person_patterns = [
            r'\b(Socrates|Plato|Aristotle|Kant|Hume|Descartes|Nietzsche)\b',
            r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'  # Proper names
        ]
        
        self.concept_patterns = [
            r'\b(justice|virtue|knowledge|truth|beauty|good|evil|wisdom)\b',
            r'\b(ethics|morality|metaphysics|epistemology|logic|aesthetics)\b'
        ]
        
        self.work_patterns = [
            r'\b(Republic|Ethics|Critique|Meditations|Apology)\b'
        ]
        
        self.place_patterns = [
            r'\b(Athens|Rome|Alexandria|Paris|Vienna)\b'
        ]
    
    def detect_entities(self, text: str) -> List[EntityMention]:
        """Detect entities in query text."""
        entities = []
        
        # Detect persons
        entities.extend(self._detect_by_patterns(
            text, self.person_patterns, EntityType.PERSON, 0.8
        ))
        
        # Detect concepts
        entities.extend(self._detect_by_patterns(
            text, self.concept_patterns, EntityType.CONCEPT, 0.7
        ))
        
        # Detect works
        entities.extend(self._detect_by_patterns(
            text, self.work_patterns, EntityType.WORK, 0.9
        ))
        
        # Detect places
        entities.extend(self._detect_by_patterns(
            text, self.place_patterns, EntityType.PLACE, 0.8
        ))
        
        # Remove overlapping entities (keep highest confidence)
        entities = self._remove_overlaps(entities)
        
        return entities
    
    def _detect_by_patterns(
        self, 
        text: str, 
        patterns: List[str], 
        entity_type: EntityType, 
        base_confidence: float
    ) -> List[EntityMention]:
        """Detect entities using regex patterns."""
        entities = []
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                entity = EntityMention(
                    text=match.group(0),
                    entity_type=entity_type,
                    confidence=base_confidence,
                    start_position=match.start(),
                    end_position=match.end()
                )
                entities.append(entity)
        
        return entities
    
    def _remove_overlaps(self, entities: List[EntityMention]) -> List[EntityMention]:
        """Remove overlapping entities, keeping highest confidence."""
        if not entities:
            return entities
        
        # Sort by position
        sorted_entities = sorted(entities, key=lambda e: e.start_position)
        
        result = []
        current = sorted_entities[0]
        
        for next_entity in sorted_entities[1:]:
            # Check for overlap
            if next_entity.start_position < current.end_position:
                # Keep entity with higher confidence
                if next_entity.confidence > current.confidence:
                    current = next_entity
            else:
                result.append(current)
                current = next_entity
        
        result.append(current)
        return result


class CypherQueryGenerator:
    """Generates Cypher queries for different traversal patterns."""
    
    def __init__(self, settings: Optional[Settings] = None):
        """Initialize query generator."""
        self.settings = settings or get_settings()
        self.max_path_length = 3
        self.max_results = 50
    
    def generate_entity_lookup(self, entities: List[EntityMention]) -> CypherQuery:
        """Generate query for direct entity lookup."""
        if not entities:
            return CypherQuery(cypher="", parameters={})
        
        # Build WHERE clauses for entities
        where_clauses = []
        parameters = {}
        
        for i, entity in enumerate(entities):
            param_name = f"name_{i}"
            where_clauses.append(f"e.name = ${param_name}")
            parameters[param_name] = entity.normalized_text
        
        where_clause = " OR ".join(where_clauses)
        
        cypher = f"""
        MATCH (e:Entity)
        WHERE {where_clause}
        RETURN e, e.name as name, e.type as type, e.description as description
        ORDER BY e.name
        LIMIT {self.max_results}
        """
        
        return CypherQuery(
            cypher=cypher.strip(),
            parameters=parameters,
            query_type="entity_lookup"
        )
    
    def generate_relationship_traversal(self, entities: List[EntityMention]) -> CypherQuery:
        """Generate query for relationship traversal between entities."""
        if len(entities) < 2:
            # Single entity - find related entities
            return self._generate_single_entity_relations(entities[0] if entities else None)
        
        # Multiple entities - find paths between them
        return self._generate_multi_entity_paths(entities)
    
    def _generate_single_entity_relations(self, entity: Optional[EntityMention]) -> CypherQuery:
        """Generate query to find entities related to a single entity."""
        if not entity:
            return CypherQuery(cypher="", parameters={})
        
        cypher = f"""
        MATCH (e1:Entity {{name: $name}})-[r:RELATES_TO|MENTIONS]-(e2:Entity)
        RETURN e1, r, e2, 
               r.strength as relationship_strength,
               type(r) as relationship_type
        ORDER BY r.strength DESC
        LIMIT {self.max_results}
        """
        
        return CypherQuery(
            cypher=cypher.strip(),
            parameters={"name": entity.normalized_text},
            query_type="single_entity_relations",
            estimated_complexity=3
        )
    
    def _generate_multi_entity_paths(self, entities: List[EntityMention]) -> CypherQuery:
        """Generate query to find paths between multiple entities."""
        if len(entities) < 2:
            return CypherQuery(cypher="", parameters={})
        
        # Take first two entities for path finding
        entity1, entity2 = entities[0], entities[1]
        
        cypher = f"""
        MATCH path = (e1:Entity {{name: $name1}})-[r:RELATES_TO|MENTIONS*1..{self.max_path_length}]-(e2:Entity {{name: $name2}})
        RETURN path, 
               length(path) as path_length,
               [rel in relationships(path) | rel.strength] as relationship_strengths,
               [rel in relationships(path) | type(rel)] as relationship_types
        ORDER BY length(path), reduce(s = 0, rel in relationships(path) | s + rel.strength) DESC
        LIMIT {min(self.max_results, 20)}
        """
        
        return CypherQuery(
            cypher=cypher.strip(),
            parameters={
                "name1": entity1.normalized_text,
                "name2": entity2.normalized_text
            },
            query_type="multi_entity_paths",
            estimated_complexity=5
        )
    
    def generate_deep_traversal(self, entities: List[EntityMention], max_depth: int = 2) -> CypherQuery:
        """Generate query for deep graph traversal (use with caution)."""
        if not entities:
            return CypherQuery(cypher="", parameters={})
        
        entity = entities[0]  # Start from first entity
        
        cypher = f"""
        MATCH path = (start:Entity {{name: $start_name}})-[r:RELATES_TO*1..{max_depth}]-(connected:Entity)
        WHERE connected.name <> start.name
        RETURN start, connected, path,
               length(path) as depth,
               reduce(s = 0, rel in relationships(path) | s + rel.strength) as path_strength
        ORDER BY path_strength DESC
        LIMIT {min(self.max_results, 30)}
        """
        
        return CypherQuery(
            cypher=cypher.strip(),
            parameters={"start_name": entity.normalized_text},
            query_type="deep_traversal",
            estimated_complexity=max_depth * 2 + 1
        )


class GraphTraversalService:
    """Main service for graph-based retrieval operations."""
    
    def __init__(
        self,
        neo4j_client: Optional["Neo4jClient"] = None,
        settings: Optional[Settings] = None
    ):
        """Initialize graph traversal service."""
        self.settings = settings or get_settings()
        self.neo4j_client = neo4j_client
        
        # Initialize components
        self.entity_detector = EntityDetector(self.settings)
        self.query_generator = CypherQueryGenerator(self.settings)
        
        # Performance settings
        self.max_query_complexity = 8
        self.cache_ttl_seconds = 300  # 5 minutes
        self._query_cache: Dict[str, Tuple[List[GraphResult], float]] = {}
        
        logger.info("Initialized GraphTraversalService")
    
    @property
    def is_initialized(self) -> bool:
        """Check if service is properly initialized."""
        return (
            self.neo4j_client is not None and
            self.entity_detector is not None and
            self.query_generator is not None
        )
    
    def detect_entities(self, query_text: str) -> List[EntityMention]:
        """Detect entities in user query text."""
        try:
            entities = self.entity_detector.detect_entities(query_text)
            logger.debug(f"Detected {len(entities)} entities in query: {query_text[:50]}...")
            return entities
            
        except Exception as e:
            logger.error(f"Entity detection failed: {e}")
            raise EntityDetectionError(f"Failed to detect entities: {e}") from e
    
    def generate_cypher_query(
        self,
        entities: List[EntityMention],
        query_type: str = "auto"
    ) -> CypherQuery:
        """Generate Cypher query based on detected entities and query type."""
        try:
            if query_type == "auto":
                query_type = self._determine_query_type(entities)
            
            if query_type == "entity_lookup":
                query = self.query_generator.generate_entity_lookup(entities)
            elif query_type == "relationship_traversal":
                query = self.query_generator.generate_relationship_traversal(entities)
            elif query_type == "deep_traversal":
                query = self.query_generator.generate_deep_traversal(entities)
            else:
                # Default to entity lookup
                query = self.query_generator.generate_entity_lookup(entities)
            
            # Validate complexity
            if query.estimated_complexity > self.max_query_complexity:
                logger.warning(f"Query complexity {query.estimated_complexity} exceeds limit {self.max_query_complexity}")
                # Fall back to simpler query
                query = self.query_generator.generate_entity_lookup(entities)
            
            logger.debug(f"Generated {query_type} query with complexity {query.estimated_complexity}")
            return query
            
        except Exception as e:
            logger.error(f"Cypher query generation failed: {e}")
            raise CypherQueryError(f"Failed to generate query: {e}") from e
    
    def _determine_query_type(self, entities: List[EntityMention]) -> str:
        """Automatically determine the best query type for entities."""
        if not entities:
            return "entity_lookup"
        elif len(entities) == 1:
            return "relationship_traversal"  # Find related entities
        else:
            return "relationship_traversal"  # Find connections
    
    def execute_traversal(self, query: CypherQuery) -> List[GraphResult]:
        """Execute graph traversal query and return results."""
        if not self.neo4j_client or not self.neo4j_client.is_connected:
            raise GraphTraversalError("Neo4j client not connected")
        
        # Check cache first
        cache_key = query.get_cache_key()
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            logger.debug("Returning cached query result")
            return cached_result
        
        try:
            logger.debug(f"Executing graph traversal: {query.cypher[:100]}...")
            
            # Execute query with timeout
            with self._query_timeout(query.timeout_seconds):
                with self.neo4j_client.session() as session:
                    result = session.run(query.cypher, query.parameters)
                    records = list(result)
            
            # Convert records to GraphResult objects
            results = self._convert_records_to_results(records, query.query_type)
            
            # Cache results
            self._cache_result(cache_key, results)
            
            logger.debug(f"Graph traversal returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Graph traversal execution failed: {e}")
            raise GraphTraversalError(f"Query execution failed: {e}") from e
    
    def integrate_with_search_results(
        self,
        search_results: List["SearchResult"],
        graph_results: List[GraphResult]
    ) -> List["SearchResult"]:
        """Integrate graph results with existing search results."""
        try:
            # Import SearchResult here to avoid circular import
            from ..services.dense_retrieval_service import SearchResult
            
            integrated_results = list(search_results)  # Copy existing results
            
            # Convert graph results to SearchResult format
            for graph_result in graph_results:
                # Create a synthetic chunk representing the graph entity
                # This is a simplified integration - would be more sophisticated in practice
                enhanced_score = self._calculate_graph_enhanced_score(
                    graph_result, search_results
                )
                
                # Add metadata about graph enhancement
                metadata = {
                    "graph_enhanced": True,
                    "entity_name": graph_result.entity.name,
                    "entity_type": str(graph_result.entity.entity_type),
                    "path_length": graph_result.path_length,
                    "relationship_count": len(graph_result.relationships),
                    "graph_confidence": graph_result.confidence
                }
                
                # Update existing results that match this entity
                for result in integrated_results:
                    if self._entity_matches_chunk(graph_result.entity, result.chunk):
                        result.enhanced_score = enhanced_score
                        result.metadata.update(metadata)
            
            # Sort by enhanced scores
            integrated_results.sort(key=lambda r: getattr(r, 'enhanced_score', r.final_score), reverse=True)
            
            return integrated_results
            
        except Exception as e:
            logger.error(f"Graph result integration failed: {e}")
            return search_results  # Return original results on error
    
    def _calculate_graph_enhanced_score(
        self, 
        graph_result: GraphResult, 
        search_results: List["SearchResult"]
    ) -> float:
        """Calculate enhanced score based on graph information."""
        base_score = graph_result.relevance_score
        
        # Boost based on relationship count
        relationship_boost = min(len(graph_result.relationships) * 0.1, 0.3)
        
        # Boost based on confidence
        confidence_boost = graph_result.confidence * 0.2
        
        # Penalty for longer paths (farther from query intent)
        path_penalty = max(0, (graph_result.path_length - 1) * 0.1)
        
        enhanced_score = min(base_score + relationship_boost + confidence_boost - path_penalty, 1.0)
        return enhanced_score
    
    def _entity_matches_chunk(self, entity: Entity, chunk) -> bool:
        """Check if an entity is mentioned in a chunk."""
        # Simple text matching - would use more sophisticated NLP in practice
        entity_name = entity.name.lower()
        chunk_text = chunk.text.lower()
        return entity_name in chunk_text
    
    @contextmanager
    def _query_timeout(self, timeout_seconds: int):
        """Context manager for query timeout."""
        # Simple timeout implementation - would use more robust timeout in production
        start_time = time.time()
        try:
            yield
        finally:
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                logger.warning(f"Query exceeded timeout: {elapsed:.2f}s > {timeout_seconds}s")
    
    def _get_cached_result(self, cache_key: str) -> Optional[List[GraphResult]]:
        """Get cached query result if still valid."""
        if cache_key in self._query_cache:
            results, timestamp = self._query_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl_seconds:
                return results
            else:
                # Remove expired cache entry
                del self._query_cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, results: List[GraphResult]) -> None:
        """Cache query results."""
        self._query_cache[cache_key] = (results, time.time())
        
        # Simple cache size management
        if len(self._query_cache) > 100:
            # Remove oldest entries
            oldest_keys = sorted(
                self._query_cache.keys(),
                key=lambda k: self._query_cache[k][1]
            )[:20]
            for key in oldest_keys:
                del self._query_cache[key]
    
    def _convert_records_to_results(self, records: List[Any], query_type: str) -> List[GraphResult]:
        """Convert Neo4j records to GraphResult objects."""
        results = []
        
        for record in records:
            try:
                # Extract entity information
                entity_data = record.get('e', {})
                if not entity_data:
                    continue
                
                # Create Entity object
                entity = Entity(
                    id=UUID(entity_data.get('id', str(uuid4()))),
                    name=entity_data.get('name', ''),
                    entity_type=EntityType(entity_data.get('type', 'concept')),
                    description=entity_data.get('description', ''),
                    source_document_id=UUID(entity_data.get('source_document_id', str(uuid4())))
                )
                
                # Extract relationship information if present
                relationships = []
                if 'r' in record:
                    relationship_data = record['r']
                    relationships.append({
                        'type': relationship_data.get('type', ''),
                        'strength': relationship_data.get('strength', 0.0),
                        'properties': relationship_data
                    })
                
                # Calculate relevance and confidence
                relevance_score = self._calculate_relevance_score(record, query_type)
                confidence = self._calculate_confidence_score(record, query_type)
                path_length = record.get('path_length', 1)
                
                result = GraphResult(
                    entity=entity,
                    relationships=relationships,
                    path_length=path_length,
                    relevance_score=relevance_score,
                    confidence=confidence,
                    metadata={'query_type': query_type, 'record_data': dict(record)}
                )
                
                results.append(result)
                
            except Exception as e:
                logger.warning(f"Failed to convert record to GraphResult: {e}")
                continue
        
        return results
    
    def _calculate_relevance_score(self, record: Any, query_type: str) -> float:
        """Calculate relevance score for a graph result."""
        base_score = 0.5
        
        # Boost based on relationship strength
        if 'r' in record and hasattr(record['r'], 'get'):
            strength = record['r'].get('strength', 0.0)
            base_score += strength * 0.3
        
        # Boost based on path length (shorter is better)
        path_length = record.get('path_length', 1)
        path_bonus = max(0.2 - (path_length - 1) * 0.05, 0)
        base_score += path_bonus
        
        return min(base_score, 1.0)
    
    def _calculate_confidence_score(self, record: Any, query_type: str) -> float:
        """Calculate confidence score for a graph result."""
        base_confidence = 0.7
        
        # Higher confidence for direct entity matches
        if query_type == "entity_lookup":
            base_confidence = 0.9
        elif query_type == "relationship_traversal":
            base_confidence = 0.8
        
        return base_confidence
    
    def clear_cache(self) -> None:
        """Clear query result cache."""
        self._query_cache.clear()
        logger.info("Query cache cleared")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics."""
        return {
            "cache_size": len(self._query_cache),
            "max_complexity": self.max_query_complexity,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "is_initialized": self.is_initialized
        }


# Factory function following established pattern
def create_graph_traversal_service(
    neo4j_client: Optional["Neo4jClient"] = None,
    settings: Optional[Settings] = None
) -> GraphTraversalService:
    """
    Create graph traversal service with dependency injection.
    
    Args:
        neo4j_client: Optional Neo4j client instance
        settings: Optional configuration settings
        
    Returns:
        Configured GraphTraversalService instance
    """
    if neo4j_client is None:
        # Import at runtime to avoid circular import
        from ..database.client import Neo4jClient
        neo4j_client = Neo4jClient()
        neo4j_client.connect()
    
    return GraphTraversalService(
        neo4j_client=neo4j_client,
        settings=settings
    )