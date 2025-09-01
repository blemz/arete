"""
Advanced Graph Analytics Service for Arete Graph-RAG System.

This service provides comprehensive graph analytics capabilities for analyzing
the philosophical knowledge graph structure, including:
- Centrality analysis for identifying key concepts and thinkers
- Community detection for philosophical schools and movements
- Historical timeline analysis for tracking concept development
- Influence network analysis for understanding philosophical relationships
- Topic clustering and concept similarity analysis

The service integrates with Neo4j to perform graph algorithms on the
philosophical knowledge graph, providing insights for educational content
and research analysis.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from collections import defaultdict, Counter

from neo4j import AsyncSession
from pydantic import BaseModel, Field, ConfigDict

from arete.config import get_settings
from arete.database.client import Neo4jClient
from arete.models.entity import Entity, EntityType

logger = logging.getLogger(__name__)

class CentralityMetric(str, Enum):
    """Available centrality metrics for graph analysis."""
    DEGREE = "degree"
    BETWEENNESS = "betweenness" 
    CLOSENESS = "closeness"
    EIGENVECTOR = "eigenvector"
    PAGE_RANK = "pagerank"

class AnalysisError(Exception):
    """Base exception for graph analytics errors."""
    pass

class CentralityAnalysisError(AnalysisError):
    """Exception raised during centrality analysis."""
    pass

class CommunityDetectionError(AnalysisError):
    """Exception raised during community detection."""
    pass

@dataclass
class CentralityResult:
    """Result of centrality analysis."""
    metric: CentralityMetric
    scores: Dict[str, float] = field(default_factory=dict)  # entity_id -> score
    top_entities: List[Tuple[str, str, float]] = field(default_factory=list)  # (id, name, score)
    analysis_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    total_entities: int = 0
    
    def get_top_n(self, n: int = 10) -> List[Tuple[str, str, float]]:
        """Get top N entities by centrality score."""
        return self.top_entities[:n]

@dataclass
class CommunityResult:
    """Result of community detection analysis."""
    algorithm: str
    communities: Dict[int, List[str]] = field(default_factory=dict)  # community_id -> entity_ids
    entity_community: Dict[str, int] = field(default_factory=dict)  # entity_id -> community_id
    modularity_score: float = 0.0
    analysis_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    total_communities: int = 0

@dataclass
class InfluenceNetwork:
    """Result of influence network analysis."""
    influences: Dict[str, List[str]] = field(default_factory=dict)  # influencer -> influenced_list
    influence_scores: Dict[Tuple[str, str], float] = field(default_factory=dict)  # (from, to) -> strength
    temporal_influences: Dict[str, List[Tuple[str, datetime]]] = field(default_factory=dict)  # chronological
    analysis_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class ConceptCluster:
    """Result of concept clustering analysis."""
    cluster_id: int
    entities: List[str]
    central_concept: str
    similarity_threshold: float
    cluster_keywords: List[str] = field(default_factory=list)
    
@dataclass
class TopicClusteringResult:
    """Result of topic clustering analysis."""
    clusters: List[ConceptCluster] = field(default_factory=list)
    outliers: List[str] = field(default_factory=list)  # entities not assigned to clusters
    silhouette_score: float = 0.0
    analysis_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class GraphAnalyticsService:
    """Service for advanced graph analytics on philosophical knowledge graphs."""
    
    def __init__(
        self,
        neo4j_client: Optional[Neo4jClient] = None,
        settings: Optional[Any] = None
    ):
        """Initialize graph analytics service."""
        self.settings = settings or get_settings()
        self.neo4j_client = neo4j_client
        self.logger = logging.getLogger(__name__)
        
    @property
    def client(self) -> Neo4jClient:
        """Get or create Neo4j client."""
        if self.neo4j_client is None:
            from arete.database.client import Neo4jClient
            self.neo4j_client = Neo4jClient()
        return self.neo4j_client
        
    async def analyze_centrality(
        self,
        metric: CentralityMetric,
        entity_types: Optional[List[EntityType]] = None,
        limit: int = 100
    ) -> CentralityResult:
        """
        Perform centrality analysis on the knowledge graph.
        
        Args:
            metric: The centrality metric to compute
            entity_types: Optional list to filter by entity types
            limit: Maximum number of top entities to return
            
        Returns:
            CentralityResult containing scores and rankings
        """
        self.logger.info(f"Starting centrality analysis with metric: {metric}")
        
        try:
            async with self.client.session() as session:
                if metric == CentralityMetric.DEGREE:
                    return await self._analyze_degree_centrality(session, entity_types, limit)
                elif metric == CentralityMetric.BETWEENNESS:
                    return await self._analyze_betweenness_centrality(session, entity_types, limit)
                elif metric == CentralityMetric.CLOSENESS:
                    return await self._analyze_closeness_centrality(session, entity_types, limit)
                elif metric == CentralityMetric.EIGENVECTOR:
                    return await self._analyze_eigenvector_centrality(session, entity_types, limit)
                elif metric == CentralityMetric.PAGE_RANK:
                    return await self._analyze_pagerank_centrality(session, entity_types, limit)
                else:
                    raise CentralityAnalysisError(f"Unsupported centrality metric: {metric}")
                    
        except Exception as e:
            self.logger.error(f"Centrality analysis failed: {e}")
            raise CentralityAnalysisError(f"Failed to compute {metric} centrality: {str(e)}")
    
    async def _analyze_degree_centrality(
        self,
        session: AsyncSession,
        entity_types: Optional[List[EntityType]],
        limit: int
    ) -> CentralityResult:
        """Compute degree centrality for entities."""
        type_filter = ""
        if entity_types:
            type_labels = [f"'{et.value}'" for et in entity_types]
            type_filter = f"AND e.type IN [{','.join(type_labels)}]"
        
        query = f"""
        MATCH (e:Entity)
        WHERE e.id IS NOT NULL {type_filter}
        OPTIONAL MATCH (e)-[r]-(connected)
        WITH e, count(r) as degree
        WHERE degree > 0
        RETURN e.id as entity_id, e.name as entity_name, degree
        ORDER BY degree DESC
        LIMIT {limit}
        """
        
        result = await session.run(query)
        records = await result.data()
        
        scores = {}
        top_entities = []
        
        for record in records:
            entity_id = record["entity_id"]
            entity_name = record["entity_name"] or entity_id
            degree = float(record["degree"])
            
            scores[entity_id] = degree
            top_entities.append((entity_id, entity_name, degree))
        
        return CentralityResult(
            metric=CentralityMetric.DEGREE,
            scores=scores,
            top_entities=top_entities,
            total_entities=len(scores)
        )
    
    async def _analyze_betweenness_centrality(
        self,
        session: AsyncSession,
        entity_types: Optional[List[EntityType]],
        limit: int
    ) -> CentralityResult:
        """Compute betweenness centrality using Neo4j GDS library if available."""
        # Note: This requires Neo4j Graph Data Science library
        # For now, implement a simplified version
        self.logger.warning("Betweenness centrality using simplified algorithm")
        
        # Get all entities and their connections
        type_filter = ""
        if entity_types:
            type_labels = [f"'{et.value}'" for et in entity_types]
            type_filter = f"AND e.type IN [{','.join(type_labels)}]"
        
        query = f"""
        MATCH (e:Entity)
        WHERE e.id IS NOT NULL {type_filter}
        OPTIONAL MATCH path = (start:Entity)-[*2]-(e)-[*2]-(end:Entity)
        WHERE start <> end AND start.id IS NOT NULL AND end.id IS NOT NULL
        WITH e, count(DISTINCT path) as paths_through
        RETURN e.id as entity_id, e.name as entity_name, paths_through
        ORDER BY paths_through DESC
        LIMIT {limit}
        """
        
        result = await session.run(query)
        records = await result.data()
        
        scores = {}
        top_entities = []
        
        for record in records:
            entity_id = record["entity_id"]
            entity_name = record["entity_name"] or entity_id
            paths = float(record["paths_through"])
            
            scores[entity_id] = paths
            top_entities.append((entity_id, entity_name, paths))
        
        return CentralityResult(
            metric=CentralityMetric.BETWEENNESS,
            scores=scores,
            top_entities=top_entities,
            total_entities=len(scores)
        )
    
    async def _analyze_closeness_centrality(
        self,
        session: AsyncSession,
        entity_types: Optional[List[EntityType]],
        limit: int
    ) -> CentralityResult:
        """Compute closeness centrality."""
        # Simplified implementation - average shortest path length
        type_filter = ""
        if entity_types:
            type_labels = [f"'{et.value}'" for et in entity_types]
            type_filter = f"AND e.type IN [{','.join(type_labels)}]"
        
        query = f"""
        MATCH (e:Entity)
        WHERE e.id IS NOT NULL {type_filter}
        OPTIONAL MATCH path = shortestPath((e)-[*1..4]-(other:Entity))
        WHERE other <> e AND other.id IS NOT NULL
        WITH e, avg(length(path)) as avg_distance
        WHERE avg_distance IS NOT NULL
        WITH e, 1.0/avg_distance as closeness
        RETURN e.id as entity_id, e.name as entity_name, closeness
        ORDER BY closeness DESC
        LIMIT {limit}
        """
        
        result = await session.run(query)
        records = await result.data()
        
        scores = {}
        top_entities = []
        
        for record in records:
            entity_id = record["entity_id"]
            entity_name = record["entity_name"] or entity_id
            closeness = float(record["closeness"])
            
            scores[entity_id] = closeness
            top_entities.append((entity_id, entity_name, closeness))
        
        return CentralityResult(
            metric=CentralityMetric.CLOSENESS,
            scores=scores,
            top_entities=top_entities,
            total_entities=len(scores)
        )
    
    async def _analyze_eigenvector_centrality(
        self,
        session: AsyncSession,
        entity_types: Optional[List[EntityType]],
        limit: int
    ) -> CentralityResult:
        """Compute eigenvector centrality (simplified)."""
        # For full implementation, would use iterative algorithm
        # This is a simplified version based on connected high-degree nodes
        type_filter = ""
        if entity_types:
            type_labels = [f"'{et.value}'" for et in entity_types]
            type_filter = f"AND e.type IN [{','.join(type_labels)}]"
        
        query = f"""
        MATCH (e:Entity)
        WHERE e.id IS NOT NULL {type_filter}
        OPTIONAL MATCH (e)-[r]-(connected:Entity)-[r2]-(second_level:Entity)
        WHERE connected.id IS NOT NULL
        WITH e, count(DISTINCT connected) as direct_connections, 
             count(DISTINCT second_level) as second_level_connections
        WITH e, direct_connections + (second_level_connections * 0.5) as eigenvector_score
        WHERE eigenvector_score > 0
        RETURN e.id as entity_id, e.name as entity_name, eigenvector_score
        ORDER BY eigenvector_score DESC
        LIMIT {limit}
        """
        
        result = await session.run(query)
        records = await result.data()
        
        scores = {}
        top_entities = []
        
        for record in records:
            entity_id = record["entity_id"]
            entity_name = record["entity_name"] or entity_id
            score = float(record["eigenvector_score"])
            
            scores[entity_id] = score
            top_entities.append((entity_id, entity_name, score))
        
        return CentralityResult(
            metric=CentralityMetric.EIGENVECTOR,
            scores=scores,
            top_entities=top_entities,
            total_entities=len(scores)
        )
    
    async def _analyze_pagerank_centrality(
        self,
        session: AsyncSession,
        entity_types: Optional[List[EntityType]],
        limit: int
    ) -> CentralityResult:
        """Compute PageRank centrality (simplified)."""
        # Simplified PageRank based on weighted connections
        type_filter = ""
        if entity_types:
            type_labels = [f"'{et.value}'" for et in entity_types]
            type_filter = f"AND e.type IN [{','.join(type_labels)}]"
        
        query = f"""
        MATCH (e:Entity)
        WHERE e.id IS NOT NULL {type_filter}
        OPTIONAL MATCH (incoming:Entity)-[r]->(e)
        WHERE incoming.id IS NOT NULL
        WITH e, count(r) as incoming_links
        OPTIONAL MATCH (e)-[r2]->(outgoing:Entity)
        WHERE outgoing.id IS NOT NULL
        WITH e, incoming_links, count(r2) as outgoing_links
        WITH e, incoming_links, 
             CASE WHEN outgoing_links = 0 THEN 1 ELSE outgoing_links END as out_degree
        WITH e, toFloat(incoming_links) / out_degree as pagerank_score
        WHERE pagerank_score > 0
        RETURN e.id as entity_id, e.name as entity_name, pagerank_score
        ORDER BY pagerank_score DESC
        LIMIT {limit}
        """
        
        result = await session.run(query)
        records = await result.data()
        
        scores = {}
        top_entities = []
        
        for record in records:
            entity_id = record["entity_id"]
            entity_name = record["entity_name"] or entity_id
            score = float(record["pagerank_score"])
            
            scores[entity_id] = score
            top_entities.append((entity_id, entity_name, score))
        
        return CentralityResult(
            metric=CentralityMetric.PAGE_RANK,
            scores=scores,
            top_entities=top_entities,
            total_entities=len(scores)
        )
    
    async def detect_communities(
        self,
        algorithm: str = "label_propagation",
        min_community_size: int = 3
    ) -> CommunityResult:
        """
        Detect communities/clusters in the knowledge graph.
        
        Args:
            algorithm: Community detection algorithm to use
            min_community_size: Minimum size for a valid community
            
        Returns:
            CommunityResult containing detected communities
        """
        self.logger.info(f"Starting community detection with algorithm: {algorithm}")
        
        try:
            async with self.client.session() as session:
                if algorithm == "label_propagation":
                    return await self._detect_communities_label_propagation(
                        session, min_community_size
                    )
                else:
                    raise CommunityDetectionError(f"Unsupported algorithm: {algorithm}")
                    
        except Exception as e:
            self.logger.error(f"Community detection failed: {e}")
            raise CommunityDetectionError(f"Failed to detect communities: {str(e)}")
    
    async def _detect_communities_label_propagation(
        self,
        session: AsyncSession,
        min_community_size: int
    ) -> CommunityResult:
        """Implement simplified label propagation for community detection."""
        # Get all entities and their connections
        query = """
        MATCH (e:Entity)-[r]-(connected:Entity)
        WHERE e.id IS NOT NULL AND connected.id IS NOT NULL
        RETURN DISTINCT e.id as entity1, connected.id as entity2, e.name as name1, connected.name as name2
        """
        
        result = await session.run(query)
        records = await result.data()
        
        # Build adjacency list
        graph = defaultdict(set)
        entity_names = {}
        
        for record in records:
            e1, e2 = record["entity1"], record["entity2"]
            entity_names[e1] = record["name1"] or e1
            entity_names[e2] = record["name2"] or e2
            graph[e1].add(e2)
            graph[e2].add(e1)
        
        # Simple label propagation
        labels = {entity: i for i, entity in enumerate(graph.keys())}
        
        # Iterate until convergence or max iterations
        max_iterations = 10
        for iteration in range(max_iterations):
            new_labels = labels.copy()
            changed = False
            
            for entity in graph:
                if not graph[entity]:
                    continue
                    
                # Count neighbor labels
                neighbor_labels = Counter(labels[neighbor] for neighbor in graph[entity])
                most_common_label = neighbor_labels.most_common(1)[0][0]
                
                if labels[entity] != most_common_label:
                    new_labels[entity] = most_common_label
                    changed = True
            
            labels = new_labels
            if not changed:
                break
        
        # Group entities by label
        communities = defaultdict(list)
        for entity, label in labels.items():
            communities[label].append(entity)
        
        # Filter by minimum size
        valid_communities = {
            i: entities for i, (label, entities) in enumerate(communities.items())
            if len(entities) >= min_community_size
        }
        
        # Create reverse mapping
        entity_community = {}
        for community_id, entities in valid_communities.items():
            for entity in entities:
                entity_community[entity] = community_id
        
        return CommunityResult(
            algorithm="label_propagation",
            communities=valid_communities,
            entity_community=entity_community,
            total_communities=len(valid_communities)
        )
    
    async def analyze_influence_network(
        self,
        temporal_analysis: bool = True
    ) -> InfluenceNetwork:
        """
        Analyze influence networks between philosophers and concepts.
        
        Args:
            temporal_analysis: Whether to include temporal ordering
            
        Returns:
            InfluenceNetwork containing influence relationships
        """
        self.logger.info("Starting influence network analysis")
        
        try:
            async with self.client.session() as session:
                # Find influence relationships
                query = """
                MATCH (influencer:Entity)-[r:INFLUENCES|INSPIRED|PRECEDED]->(influenced:Entity)
                WHERE influencer.id IS NOT NULL AND influenced.id IS NOT NULL
                OPTIONAL MATCH (influencer)-[:HAS_ATTRIBUTE]->(birth_attr:Entity {type: 'DATE'})
                OPTIONAL MATCH (influenced)-[:HAS_ATTRIBUTE]->(influenced_birth:Entity {type: 'DATE'})
                RETURN influencer.id as influencer_id, influencer.name as influencer_name,
                       influenced.id as influenced_id, influenced.name as influenced_name,
                       type(r) as relationship_type,
                       birth_attr.value as influencer_date,
                       influenced_birth.value as influenced_date
                """
                
                result = await session.run(query)
                records = await result.data()
                
                influences = defaultdict(list)
                influence_scores = {}
                temporal_influences = defaultdict(list)
                
                for record in records:
                    influencer_id = record["influencer_id"]
                    influenced_id = record["influenced_id"]
                    rel_type = record["relationship_type"]
                    
                    influences[influencer_id].append(influenced_id)
                    
                    # Simple scoring based on relationship type
                    score = 1.0
                    if rel_type == "INFLUENCES":
                        score = 1.0
                    elif rel_type == "INSPIRED":
                        score = 0.8
                    elif rel_type == "PRECEDED":
                        score = 0.6
                    
                    influence_scores[(influencer_id, influenced_id)] = score
                    
                    # Add temporal data if available
                    if temporal_analysis and record["influencer_date"]:
                        try:
                            date_str = record["influencer_date"]
                            # Simple date parsing - in real implementation would be more robust
                            if len(date_str) >= 4 and date_str[:4].isdigit():
                                year = int(date_str[:4])
                                date = datetime(year, 1, 1)
                                temporal_influences[influencer_id].append((influenced_id, date))
                        except (ValueError, TypeError):
                            pass
                
                return InfluenceNetwork(
                    influences=dict(influences),
                    influence_scores=influence_scores,
                    temporal_influences=dict(temporal_influences)
                )
                
        except Exception as e:
            self.logger.error(f"Influence network analysis failed: {e}")
            raise AnalysisError(f"Failed to analyze influence network: {str(e)}")
    
    async def cluster_topics(
        self,
        similarity_threshold: float = 0.7,
        min_cluster_size: int = 3
    ) -> TopicClusteringResult:
        """
        Perform topic clustering based on concept similarity.
        
        Args:
            similarity_threshold: Minimum similarity for clustering
            min_cluster_size: Minimum entities per cluster
            
        Returns:
            TopicClusteringResult containing clustered concepts
        """
        self.logger.info("Starting topic clustering analysis")
        
        try:
            async with self.client.session() as session:
                # Get concepts and their attributes
                query = """
                MATCH (concept:Entity {type: 'CONCEPT'})
                WHERE concept.id IS NOT NULL
                OPTIONAL MATCH (concept)-[:HAS_ATTRIBUTE]->(attr:Entity)
                RETURN concept.id as concept_id, concept.name as concept_name,
                       collect(DISTINCT attr.value) as attributes
                """
                
                result = await session.run(query)
                records = await result.data()
                
                # Simple clustering based on shared attributes
                concepts = {}
                for record in records:
                    concept_id = record["concept_id"]
                    concept_name = record["concept_name"] or concept_id
                    attributes = set(record["attributes"] or [])
                    concepts[concept_id] = (concept_name, attributes)
                
                # Create clusters based on attribute similarity
                clusters = []
                clustered = set()
                cluster_id = 0
                
                for concept_id, (concept_name, attributes) in concepts.items():
                    if concept_id in clustered or len(attributes) == 0:
                        continue
                    
                    cluster_concepts = [concept_id]
                    clustered.add(concept_id)
                    
                    # Find similar concepts
                    for other_id, (other_name, other_attrs) in concepts.items():
                        if other_id in clustered:
                            continue
                        
                        # Calculate Jaccard similarity
                        if len(attributes) > 0 and len(other_attrs) > 0:
                            intersection = len(attributes & other_attrs)
                            union = len(attributes | other_attrs)
                            similarity = intersection / union if union > 0 else 0
                            
                            if similarity >= similarity_threshold:
                                cluster_concepts.append(other_id)
                                clustered.add(other_id)
                    
                    if len(cluster_concepts) >= min_cluster_size:
                        # Find central concept (most connected)
                        central_concept = concept_id  # Simplified - could use centrality
                        
                        # Extract common keywords
                        all_attrs = set()
                        for cid in cluster_concepts:
                            all_attrs.update(concepts[cid][1])
                        
                        cluster = ConceptCluster(
                            cluster_id=cluster_id,
                            entities=cluster_concepts,
                            central_concept=central_concept,
                            similarity_threshold=similarity_threshold,
                            cluster_keywords=list(all_attrs)[:10]  # Top 10 keywords
                        )
                        clusters.append(cluster)
                        cluster_id += 1
                
                # Find outliers (unclustered concepts)
                all_concept_ids = set(concepts.keys())
                outliers = list(all_concept_ids - clustered)
                
                return TopicClusteringResult(
                    clusters=clusters,
                    outliers=outliers
                )
                
        except Exception as e:
            self.logger.error(f"Topic clustering failed: {e}")
            raise AnalysisError(f"Failed to perform topic clustering: {str(e)}")

def create_graph_analytics_service(
    neo4j_client: Optional[Neo4jClient] = None,
    settings: Optional[Any] = None
) -> GraphAnalyticsService:
    """Create a GraphAnalyticsService instance."""
    return GraphAnalyticsService(neo4j_client=neo4j_client, settings=settings)