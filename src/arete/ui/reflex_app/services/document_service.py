"""
Document Service for managing and retrieving classical texts.
"""

import asyncio
from typing import Dict, List, Any, Optional
import sys
import os

# Add the project root to Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

try:
    from src.arete.core.database.neo4j_client import Neo4jClient
    from src.arete.core.database.weaviate_client import WeaviateClient
    from src.arete.core.config import get_settings
except ImportError as e:
    print(f"Warning: Could not import Arete components: {e}")


class DocumentService:
    """Service for managing classical philosophical documents."""
    
    def __init__(self):
        """Initialize document service."""
        self.settings = None
        self.neo4j_client = None
        self.weaviate_client = None
        self.initialized = False
        
        # Mock document data for development
        self.mock_documents = {
            "apology": {
                "id": "apology",
                "title": "Plato's Apology",
                "author": "Plato",
                "period": "Classical",
                "description": "Socrates' defense speech at his trial",
                "word_count": 11683,
                "chapters": [
                    {
                        "id": "apology_ch1",
                        "title": "Opening Defense",
                        "content": "How you, O Athenians, have been affected by my accusers, I cannot tell..."
                    }
                ]
            },
            "charmides": {
                "id": "charmides", 
                "title": "Plato's Charmides",
                "author": "Plato",
                "period": "Classical",
                "description": "Dialogue on temperance and self-knowledge",
                "word_count": 39700,
                "chapters": [
                    {
                        "id": "charmides_ch1",
                        "title": "Return from Potidaea",
                        "content": "Yesterday evening I returned from the army at Potidaea..."
                    }
                ]
            }
        }
    
    async def initialize(self) -> bool:
        """Initialize document service with database connections."""
        try:
            self.settings = get_settings()
            
            self.neo4j_client = Neo4jClient(
                uri=self.settings.neo4j_uri,
                username=self.settings.neo4j_username, 
                password=self.settings.neo4j_password
            )
            
            self.weaviate_client = WeaviateClient(
                url=self.settings.weaviate_url,
                api_key=self.settings.weaviate_api_key
            )
            
            self.initialized = True
            return True
            
        except Exception as e:
            print(f"Error initializing document service: {e}")
            self.initialized = False
            return False
    
    async def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get list of all available documents."""
        if not self.initialized:
            if not await self.initialize():
                # Return mock data if initialization fails
                return list(self.mock_documents.values())
        
        try:
            # Query Neo4j for document metadata
            cypher = """
            MATCH (d:Document)
            RETURN d.id as id, d.title as title, d.author as author,
                   d.period as period, d.description as description,
                   d.word_count as word_count
            ORDER BY d.title
            """
            
            results = await self.neo4j_client.execute_query(cypher)
            
            if results:
                return [
                    {
                        "id": record["id"],
                        "title": record["title"],
                        "author": record["author"],
                        "period": record["period"],
                        "description": record["description"],
                        "word_count": record["word_count"]
                    }
                    for record in results
                ]
            else:
                # Fallback to mock data
                return list(self.mock_documents.values())
                
        except Exception as e:
            print(f"Error getting documents: {e}")
            return list(self.mock_documents.values())
    
    async def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed document information by ID."""
        if document_id in self.mock_documents:
            return self.mock_documents[document_id]
            
        if not self.initialized:
            if not await self.initialize():
                return None
        
        try:
            cypher = """
            MATCH (d:Document {id: $document_id})
            RETURN d.id as id, d.title as title, d.author as author,
                   d.period as period, d.description as description,
                   d.word_count as word_count, d.content as content
            """
            
            results = await self.neo4j_client.execute_query(
                cypher, {"document_id": document_id}
            )
            
            if results:
                record = results[0]
                return {
                    "id": record["id"],
                    "title": record["title"],
                    "author": record["author"],
                    "period": record["period"],
                    "description": record["description"],
                    "word_count": record["word_count"],
                    "content": record["content"]
                }
            
            return None
            
        except Exception as e:
            print(f"Error getting document {document_id}: {e}")
            return None
    
    async def search_document_content(
        self, 
        query: str, 
        document_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for content within documents."""
        if not self.initialized:
            if not await self.initialize():
                return []
        
        try:
            # Search in Weaviate for relevant chunks
            base_filters = {}
            if document_id:
                base_filters["document_id"] = document_id
            
            # This would use the RAG service for proper vector search
            from .rag_service import get_rag_service
            rag_service = get_rag_service()
            
            chunks = await rag_service.search_similar_chunks(
                query, limit=limit, min_score=0.6
            )
            
            # Filter by document if specified
            if document_id:
                chunks = [
                    chunk for chunk in chunks
                    if chunk.get("document_id") == document_id
                ]
            
            return chunks
            
        except Exception as e:
            print(f"Error searching documents: {e}")
            return []
    
    async def get_document_statistics(self) -> Dict[str, Any]:
        """Get overall document collection statistics."""
        try:
            documents = await self.get_all_documents()
            
            total_docs = len(documents)
            total_words = sum(doc.get("word_count", 0) for doc in documents)
            
            authors = list(set(doc.get("author", "Unknown") for doc in documents))
            periods = list(set(doc.get("period", "Unknown") for doc in documents))
            
            return {
                "total_documents": total_docs,
                "total_words": total_words,
                "unique_authors": len(authors),
                "time_periods": periods,
                "authors": authors,
                "average_document_length": total_words // total_docs if total_docs > 0 else 0
            }
            
        except Exception as e:
            return {
                "total_documents": 0,
                "total_words": 0,
                "unique_authors": 0,
                "time_periods": [],
                "authors": [],
                "average_document_length": 0,
                "error": str(e)
            }


# Global document service instance
_document_service = None

def get_document_service() -> DocumentService:
    """Get the global document service instance."""
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service