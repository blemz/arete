"""
Analytics Service for knowledge graph analysis and visualization data.
"""

import asyncio
from typing import Dict, List, Any, Optional
import sys
import os

# Add the project root to Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

try:
    from src.arete.core.database.neo4j_client import Neo4jClient
    from src.arete.core.config import get_settings
except ImportError as e:
    print(f"Warning: Could not import Arete components: {e}")


class AnalyticsService:
    """Service for knowledge graph analytics and insights."""
    
    def __init__(self):
        """Initialize analytics service."""
        self.settings = None
        self.neo4j_client = None
        self.initialized = False
        
        # Mock analytics data for development
        self.mock_data = {
            "entity_count": 83,
            "relationship_count": 109, 
            "document_count": 2,
            "chunk_count": 227,
            "top_concepts": [
                {"name": "Virtue (ἀρετή)", "centrality": 0.85, "type": "CONCEPT"},
                {"name": "Justice (δικαιοσύνη)", "centrality": 0.78, "type": "CONCEPT"},
                {"name": "Knowledge (ἐπιστήμη)", "centrality": 0.72, "type": "CONCEPT"},
                {"name": "Temperance (σωφροσύνη)", "centrality": 0.68, "type": "CONCEPT"},
                {"name": "Courage (ἀνδρεία)", "centrality": 0.65, "type": "CONCEPT"}
            ],
            "historical_timeline": [
                {"year": "470 BCE", "event": "Birth of Socrates", "significance": "Beginning of systematic philosophical inquiry"},
                {"year": "428 BCE", "event": "Birth of Plato", "significance": "Development of idealist philosophy"},
                {"year": "399 BCE", "event": "Death of Socrates", "significance": "Martyrdom for philosophical principles"},
                {"year": "384 BCE", "event": "Birth of Aristotle", "significance": "Systematic classification of knowledge"}
            ]
        }
    
    async def initialize(self) -> bool:
        """Initialize analytics service with database connections."""
        try:
            self.settings = get_settings()
            
            self.neo4j_client = Neo4jClient(
                uri=self.settings.neo4j_uri,
                username=self.settings.neo4j_username,
                password=self.settings.neo4j_password
            )
            
            self.initialized = True
            return True
            
        except Exception as e:
            print(f"Error initializing analytics service: {e}")
            self.initialized = False
            return False
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get overall system metrics and statistics."""
        if not self.initialized:
            if not await self.initialize():
                return self.mock_data
        
        try:
            # Get entity count
            entity_result = await self.neo4j_client.execute_query(
                "MATCH (e:Entity) RETURN count(e) as count"
            )
            entity_count = entity_result[0]["count"] if entity_result else 0
            
            # Get relationship count
            rel_result = await self.neo4j_client.execute_query(
                "MATCH ()-[r]->() RETURN count(r) as count"
            )
            relationship_count = rel_result[0]["count"] if rel_result else 0
            
            # Get document count
            doc_result = await self.neo4j_client.execute_query(
                "MATCH (d:Document) RETURN count(d) as count"
            )
            document_count = doc_result[0]["count"] if doc_result else 0
            
            # Get chunk count (if stored in Neo4j)
            chunk_result = await self.neo4j_client.execute_query(
                "MATCH (c:Chunk) RETURN count(c) as count"
            )
            chunk_count = chunk_result[0]["count"] if chunk_result else 227  # Fallback
            
            return {
                "entity_count": entity_count,
                "relationship_count": relationship_count,
                "document_count": document_count,
                "chunk_count": chunk_count,
                "last_updated": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            print(f"Error getting system metrics: {e}")
            return self.mock_data
    
    async def get_top_concepts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top philosophical concepts by centrality/importance."""
        if not self.initialized:
            if not await self.initialize():
                return self.mock_data["top_concepts"][:limit]
        
        try:
            # Calculate degree centrality for concepts
            cypher = """
            MATCH (e:Entity)
            WHERE e.entity_type = 'CONCEPT'
            OPTIONAL MATCH (e)-[r]-()
            WITH e, count(r) as degree
            RETURN e.name as name, e.canonical_form as canonical_form,
                   e.entity_type as type, degree
            ORDER BY degree DESC
            LIMIT $limit
            """
            
            results = await self.neo4j_client.execute_query(
                cypher, {"limit": limit}
            )
            
            if results:
                return [
                    {
                        "name": record["canonical_form"] or record["name"],
                        "centrality": min(record["degree"] / 20.0, 1.0),  # Normalize to 0-1
                        "type": record["type"],
                        "degree": record["degree"]
                    }
                    for record in results
                ]
            else:
                return self.mock_data["top_concepts"][:limit]
                
        except Exception as e:
            print(f"Error getting top concepts: {e}")
            return self.mock_data["top_concepts"][:limit]
    
    async def get_concept_relationships(self, concept_name: str) -> Dict[str, Any]:
        """Get relationships for a specific concept."""
        if not self.initialized:
            if not await self.initialize():
                return {"concept": concept_name, "relationships": []}
        
        try:
            cypher = """
            MATCH (e:Entity)
            WHERE toLower(e.name) CONTAINS toLower($concept)
               OR toLower(e.canonical_form) CONTAINS toLower($concept)
            OPTIONAL MATCH (e)-[r]-(related:Entity)
            RETURN e.name as concept, type(r) as relationship_type,
                   related.name as related_concept, related.entity_type as related_type
            LIMIT 20
            """
            
            results = await self.neo4j_client.execute_query(
                cypher, {"concept": concept_name}
            )
            
            relationships = []
            for record in results:
                if record["related_concept"]:
                    relationships.append({
                        "type": record["relationship_type"] or "RELATED_TO",
                        "target": record["related_concept"],
                        "target_type": record["related_type"]
                    })
            
            return {
                "concept": concept_name,
                "relationships": relationships
            }
            
        except Exception as e:
            print(f"Error getting concept relationships: {e}")
            return {"concept": concept_name, "relationships": []}
    
    async def get_network_visualization_data(self) -> Dict[str, Any]:
        """Get data for network graph visualization."""
        if not self.initialized:
            if not await self.initialize():
                return {"nodes": [], "edges": []}
        
        try:
            # Get top entities and their relationships
            cypher = """
            MATCH (e:Entity)-[r]-(related:Entity)
            WHERE e.entity_type = 'CONCEPT' AND related.entity_type = 'CONCEPT'
            WITH e, related, r, rand() as random
            ORDER BY random
            LIMIT 50
            RETURN e.name as source, e.entity_type as source_type,
                   related.name as target, related.entity_type as target_type,
                   type(r) as relationship_type
            """
            
            results = await self.neo4j_client.execute_query(cypher)
            
            nodes = set()
            edges = []
            
            for record in results:
                # Add nodes
                nodes.add((record["source"], record["source_type"]))
                nodes.add((record["target"], record["target_type"]))
                
                # Add edge
                edges.append({
                    "source": record["source"],
                    "target": record["target"],
                    "type": record["relationship_type"]
                })
            
            # Convert nodes to list format
            node_list = [
                {
                    "id": name,
                    "label": name,
                    "type": node_type,
                    "size": 10 + len([e for e in edges if e["source"] == name or e["target"] == name])
                }
                for name, node_type in nodes
            ]
            
            return {
                "nodes": node_list,
                "edges": edges
            }
            
        except Exception as e:
            print(f"Error getting network data: {e}")
            return {"nodes": [], "edges": []}
    
    async def get_historical_timeline(self) -> List[Dict[str, Any]]:
        """Get historical timeline of philosophical developments."""
        # For now, return mock data as this would require temporal modeling
        return self.mock_data["historical_timeline"]
    
    async def get_query_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get analytics about recent queries and usage patterns."""
        # This would typically track user queries and responses
        # For now, return simulated analytics
        return {
            "total_queries": 245,
            "unique_topics": 38,
            "avg_response_time": 2.3,
            "popular_queries": [
                "What is virtue?",
                "How does Socrates define justice?",
                "What is the allegory of the cave?",
                "Can virtue be taught?",
                "What is the good life?"
            ],
            "query_success_rate": 0.94
        }


# Global analytics service instance
_analytics_service = None

def get_analytics_service() -> AnalyticsService:
    """Get the global analytics service instance."""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service