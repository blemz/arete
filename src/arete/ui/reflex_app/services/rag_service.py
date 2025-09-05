"""
RAG Service for integration with existing Arete RAG pipeline.
"""

import asyncio
from typing import List, Dict, Any, Optional
import sys
import os

# Add the project root to Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

try:
    from src.arete.core.database.neo4j_client import Neo4jClient
    from src.arete.core.database.weaviate_client import WeaviateClient
    from src.arete.services.embedding_service import get_embedding_service
    from src.arete.services.llm_service import get_llm_service
    from src.arete.core.config import get_settings
except ImportError as e:
    print(f"Warning: Could not import Arete RAG components: {e}")
    # Fallback for development/testing
    pass


class RAGService:
    """Service for integrating with the existing Arete RAG pipeline."""
    
    def __init__(self):
        """Initialize RAG service with existing pipeline components."""
        self.settings = None
        self.neo4j_client = None
        self.weaviate_client = None
        self.embedding_service = None
        self.llm_service = None
        self.initialized = False
        
    async def initialize(self) -> bool:
        """Initialize RAG pipeline components."""
        try:
            self.settings = get_settings()
            
            # Initialize database clients
            self.neo4j_client = Neo4jClient(
                uri=self.settings.neo4j_uri,
                username=self.settings.neo4j_username,
                password=self.settings.neo4j_password
            )
            
            self.weaviate_client = WeaviateClient(
                url=self.settings.weaviate_url,
                api_key=self.settings.weaviate_api_key
            )
            
            # Initialize services
            self.embedding_service = get_embedding_service()
            self.llm_service = get_llm_service()
            
            self.initialized = True
            return True
            
        except Exception as e:
            print(f"Error initializing RAG service: {e}")
            self.initialized = False
            return False
    
    async def search_similar_chunks(
        self, 
        query: str, 
        limit: int = 5, 
        min_score: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for similar text chunks using vector similarity."""
        if not self.initialized:
            return []
            
        try:
            # Generate query embedding
            query_embedding = await self.embedding_service.get_embedding(query)
            
            # Search similar chunks in Weaviate
            results = await self.weaviate_client.search_by_vector(
                class_name="Chunk",
                vector=query_embedding,
                limit=limit,
                min_score=min_score
            )
            
            return [
                {
                    "content": result.get("content", ""),
                    "score": result.get("score", 0.0),
                    "document_id": result.get("document_id", ""),
                    "position": result.get("position", 0),
                    "metadata": result.get("metadata", {})
                }
                for result in results
            ]
            
        except Exception as e:
            print(f"Error searching chunks: {e}")
            return []
    
    async def get_related_entities(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get entities related to the query from knowledge graph."""
        if not self.initialized:
            return []
            
        try:
            # Simple entity matching query
            cypher = """
            MATCH (e:Entity)
            WHERE toLower(e.name) CONTAINS toLower($query) 
               OR toLower(e.canonical_form) CONTAINS toLower($query)
               OR any(alias in e.aliases WHERE toLower(alias) CONTAINS toLower($query))
            RETURN e.name as name, e.canonical_form as canonical_form, 
                   e.entity_type as type, e.aliases as aliases
            LIMIT $limit
            """
            
            results = await self.neo4j_client.execute_query(
                cypher, 
                {"query": query, "limit": limit}
            )
            
            return [
                {
                    "name": record["name"],
                    "canonical_form": record["canonical_form"],
                    "type": record["type"],
                    "aliases": record["aliases"] or []
                }
                for record in results
            ]
            
        except Exception as e:
            print(f"Error getting related entities: {e}")
            return []
    
    async def generate_response(
        self, 
        query: str, 
        context_chunks: List[Dict[str, Any]], 
        entities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate response using LLM with retrieved context."""
        if not self.initialized:
            return {"response": "RAG system not initialized", "citations": []}
            
        try:
            # Build context from chunks and entities
            context_text = "\n\n".join([
                f"Passage (Score: {chunk['score']:.2f}): {chunk['content']}"
                for chunk in context_chunks
            ])
            
            entity_text = ", ".join([
                f"{entity['name']} ({entity['type']})"
                for entity in entities
            ])
            
            # Create prompt
            prompt = f"""You are Arete, an AI tutor for classical philosophy. Answer the following question using the provided context from classical texts.

Question: {query}

Context from classical texts:
{context_text}

Related philosophical concepts: {entity_text}

Please provide a comprehensive answer with proper citations. Format your response in a scholarly manner appropriate for philosophical education."""

            # Generate response
            response = await self.llm_service.generate_response(prompt)
            
            # Create citations from chunks
            citations = [
                {
                    "content": chunk["content"][:500] + "..." if len(chunk["content"]) > 500 else chunk["content"],
                    "document_id": chunk["document_id"],
                    "position": chunk["position"],
                    "score": chunk["score"]
                }
                for chunk in context_chunks
            ]
            
            return {
                "response": response,
                "citations": citations,
                "entities": entities
            }
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return {
                "response": f"Error generating response: {str(e)}",
                "citations": [],
                "entities": []
            }
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process a complete RAG query with retrieval and generation."""
        if not self.initialized:
            if not await self.initialize():
                return {
                    "response": "Could not initialize RAG system. Please check configuration.",
                    "citations": [],
                    "entities": []
                }
        
        try:
            # Search for similar chunks
            chunks = await self.search_similar_chunks(query)
            
            # Get related entities
            entities = await self.get_related_entities(query)
            
            # Generate response with context
            result = await self.generate_response(query, chunks, entities)
            
            return result
            
        except Exception as e:
            return {
                "response": f"Error processing query: {str(e)}",
                "citations": [],
                "entities": []
            }


# Global RAG service instance
_rag_service = None

def get_rag_service() -> RAGService:
    """Get the global RAG service instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service