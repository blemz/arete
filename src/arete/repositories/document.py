"""
Document repository implementation for Arete Graph-RAG system.

Provides dual persistence strategy for Document entities:
- Neo4j for graph relationships and metadata queries
- Weaviate for vector embeddings and semantic search

Implements SearchableRepository interface for enhanced search capabilities.
"""
import logging
from typing import List, Optional, Dict, Any, Union
from uuid import UUID

from arete.repositories.base import (
    SearchableRepository,
    EntityNotFoundError,
    DuplicateEntityError,
    ValidationError,
    RepositoryError,
)
from arete.models.document import Document
from arete.database.client import Neo4jClient
from arete.database.weaviate_client import WeaviateClient

logger = logging.getLogger(__name__)


class DocumentRepository(SearchableRepository[Document]):
    """
    Repository implementation for Document entities with dual persistence.
    
    Stores documents in both Neo4j (for graph relationships and structured queries)
    and Weaviate (for vector embeddings and semantic search).
    
    Provides both traditional CRUD operations and advanced search capabilities
    leveraging the strengths of each database system.
    """
    
    def __init__(self, neo4j_client: Neo4jClient, weaviate_client: WeaviateClient):
        """
        Initialize DocumentRepository with required database clients.
        
        Args:
            neo4j_client: Neo4j client for graph operations
            weaviate_client: Weaviate client for vector operations
        """
        self._neo4j_client = neo4j_client
        self._weaviate_client = weaviate_client
    
    async def create(self, entity: Document) -> Document:
        """
        Create a new document in both Neo4j and Weaviate.
        
        Args:
            entity: The document to create
            
        Returns:
            The created document with generated metadata
            
        Raises:
            DuplicateEntityError: If document already exists
            ValidationError: If document validation fails
            RepositoryError: For database errors
        """
        try:
            # Store in Neo4j for graph relationships and structured queries
            neo4j_result = await self._neo4j_client.create_node(
                label='Document',
                properties=entity.model_dump(exclude={'embeddings'})
            )
            
            # Store in Weaviate for vector search
            await self._weaviate_client.save_entity(entity)
            
            logger.info(f"Created document: {entity.id}")
            return entity
            
        except Exception as e:
            error_msg = str(e)
            if "constraint violation" in error_msg.lower() or "already exists" in error_msg.lower():
                raise DuplicateEntityError(f"Document already exists: {error_msg}")
            else:
                logger.error(f"Failed to create document {entity.id}: {error_msg}")
                raise RepositoryError(f"Failed to create document: {error_msg}")
    
    async def get_by_id(self, entity_id: Union[UUID, str]) -> Optional[Document]:
        """
        Retrieve document by ID from Neo4j.
        
        Args:
            entity_id: The document ID
            
        Returns:
            The document if found, None otherwise
            
        Raises:
            RepositoryError: For database errors
        """
        try:
            result = await self._neo4j_client.get_node_by_id(
                str(entity_id), 'Document'
            )
            
            if result:
                return Document(**result)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get document {entity_id}: {str(e)}")
            raise RepositoryError(f"Failed to retrieve document: {str(e)}")
    
    async def update(self, entity: Document) -> Document:
        """
        Update document in both Neo4j and Weaviate.
        
        Args:
            entity: The document with updated values
            
        Returns:
            The updated document
            
        Raises:
            EntityNotFoundError: If document doesn't exist
            ValidationError: If entity validation fails
            RepositoryError: For database errors
        """
        try:
            # Update in Neo4j
            neo4j_result = await self._neo4j_client.update_node(
                str(entity.id),
                'Document',
                entity.model_dump(exclude={'embeddings'})
            )
            
            # Update in Weaviate
            await self._weaviate_client.save_entity(entity)
            
            logger.info(f"Updated document: {entity.id}")
            return entity
            
        except Exception as e:
            error_msg = str(e)
            if "not found" in error_msg.lower():
                raise EntityNotFoundError(f"Document not found: {entity.id}")
            else:
                logger.error(f"Failed to update document {entity.id}: {error_msg}")
                raise RepositoryError(f"Failed to update document: {error_msg}")
    
    async def delete(self, entity_id: Union[UUID, str]) -> bool:
        """
        Delete document from both Neo4j and Weaviate.
        
        Args:
            entity_id: The document ID to delete
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            RepositoryError: For database errors
        """
        try:
            # Delete from Neo4j
            neo4j_deleted = await self._neo4j_client.delete_node(
                str(entity_id), 'Document'
            )
            
            # Delete from Weaviate
            await self._weaviate_client.delete_entity(
                'Document', str(entity_id)
            )
            
            if neo4j_deleted:
                logger.info(f"Deleted document: {entity_id}")
            
            return neo4j_deleted
            
        except Exception as e:
            logger.error(f"Failed to delete document {entity_id}: {str(e)}")
            raise RepositoryError(f"Failed to delete document: {str(e)}")
    
    async def list_all(
        self, 
        limit: int = 100, 
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        List documents from Neo4j with optional filtering.
        
        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            filters: Optional filters to apply
            
        Returns:
            List of documents matching criteria
            
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
                    conditions.append(f"d.{key} = ${param_key}")
                    params[param_key] = value
                
                if conditions:
                    where_clause = "WHERE " + " AND ".join(conditions)
            
            query = f"""
                MATCH (d:Document)
                {where_clause}
                RETURN d
                ORDER BY d.created_at DESC
                SKIP $offset
                LIMIT $limit
            """
            
            results = await self._neo4j_client.query(query, params)
            return [Document(**result["d"]) for result in results]
            
        except Exception as e:
            logger.error(f"Failed to list documents: {str(e)}")
            raise RepositoryError(f"Failed to list documents: {str(e)}")
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count documents matching optional filters.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Number of documents matching criteria
            
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
                    conditions.append(f"d.{key} = ${param_key}")
                    params[param_key] = value
                
                if conditions:
                    where_clause = "WHERE " + " AND ".join(conditions)
            
            query = f"""
                MATCH (d:Document)
                {where_clause}
                RETURN count(d) as count
            """
            
            results = await self._neo4j_client.query(query, params)
            return results[0]["count"] if results else 0
            
        except Exception as e:
            logger.error(f"Failed to count documents: {str(e)}")
            raise RepositoryError(f"Failed to count documents: {str(e)}")
    
    async def exists(self, entity_id: Union[UUID, str]) -> bool:
        """
        Check if document exists by ID.
        
        Args:
            entity_id: The document ID to check
            
        Returns:
            True if document exists, False otherwise
            
        Raises:
            RepositoryError: For database errors
        """
        try:
            query = """
                MATCH (d:Document)
                WHERE d.id = $entity_id
                RETURN count(d) > 0 as exists
            """
            
            results = await self._neo4j_client.query(
                query, {"entity_id": str(entity_id)}
            )
            return results[0]["exists"] if results else False
            
        except Exception as e:
            logger.error(f"Failed to check document existence {entity_id}: {str(e)}")
            raise RepositoryError(f"Failed to check document existence: {str(e)}")
    
    async def search_by_text(
        self,
        query: str,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Document]:
        """
        Search documents by semantic text similarity using Weaviate.
        
        Args:
            query: The search query text
            limit: Maximum number of results to return
            similarity_threshold: Minimum similarity score (0.0-1.0)
            
        Returns:
            List of documents matching the query
            
        Raises:
            RepositoryError: For database errors
        """
        try:
            results = await self._weaviate_client.search_near_text(
                collection='Document',
                query=query,
                limit=limit,
                certainty=similarity_threshold
            )
            
            return [Document(**result) for result in results]
            
        except Exception as e:
            logger.error(f"Failed to search documents by text: {str(e)}")
            raise RepositoryError(f"Failed to search by text: {str(e)}")
    
    async def search_by_embedding(
        self,
        embedding: List[float],
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Document]:
        """
        Search documents by embedding vector similarity using Weaviate.
        
        Args:
            embedding: The query embedding vector
            limit: Maximum number of results to return
            similarity_threshold: Minimum similarity score (0.0-1.0)
            
        Returns:
            List of documents with similar embeddings
            
        Raises:
            RepositoryError: For database errors
        """
        try:
            results = await self._weaviate_client.search_near_vector(
                collection='Document',
                vector=embedding,
                limit=limit,
                certainty=similarity_threshold
            )
            
            return [Document(**result) for result in results]
            
        except Exception as e:
            logger.error(f"Failed to search documents by embedding: {str(e)}")
            raise RepositoryError(f"Failed to search by embedding: {str(e)}")
    
    # Document-specific methods
    
    async def get_by_title(self, title: str) -> List[Document]:
        """
        Get documents by title using Neo4j.
        
        Args:
            title: The document title to search for
            
        Returns:
            List of documents with matching title
            
        Raises:
            RepositoryError: For database errors
        """
        try:
            query = """
                MATCH (d:Document)
                WHERE d.title CONTAINS $title
                RETURN d
                ORDER BY d.created_at DESC
            """
            
            results = await self._neo4j_client.query(query, {"title": title})
            return [Document(**result["d"]) for result in results]
            
        except Exception as e:
            logger.error(f"Failed to search documents by title: {str(e)}")
            raise RepositoryError(f"Failed to search by title: {str(e)}")
    
    async def get_by_author(self, author: str) -> List[Document]:
        """
        Get documents by author using Neo4j.
        
        Args:
            author: The author name to search for
            
        Returns:
            List of documents by the author
            
        Raises:
            RepositoryError: For database errors
        """
        try:
            query = """
                MATCH (d:Document)
                WHERE d.author = $author
                RETURN d
                ORDER BY d.date_published ASC
            """
            
            results = await self._neo4j_client.query(query, {"author": author})
            return [Document(**result["d"]) for result in results]
            
        except Exception as e:
            logger.error(f"Failed to search documents by author: {str(e)}")
            raise RepositoryError(f"Failed to search by author: {str(e)}")
    
    async def search_content(
        self,
        query: str,
        limit: int = 10,
        hybrid_weight: float = 0.7
    ) -> List[Document]:
        """
        Hybrid search combining Neo4j keyword search and Weaviate semantic search.
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            hybrid_weight: Weight for semantic vs keyword search (0.0-1.0)
            
        Returns:
            List of documents matching the query
            
        Raises:
            RepositoryError: For database errors
        """
        try:
            # Keyword search in Neo4j
            neo4j_query = """
                MATCH (d:Document)
                WHERE d.content CONTAINS $query OR d.title CONTAINS $query
                RETURN d
                LIMIT $limit
            """
            
            neo4j_results = await self._neo4j_client.query(
                neo4j_query, {"query": query, "limit": limit}
            )
            
            # Semantic search in Weaviate
            weaviate_results = await self._weaviate_client.search_near_text(
                collection='Document',
                query=query,
                limit=limit,
                certainty=0.6
            )
            
            # Combine results (simple merge for now - can be enhanced with scoring)
            combined_results = []
            seen_ids = set()
            
            # Add Neo4j results
            for result in neo4j_results:
                doc = Document(**result["d"])
                if doc.id not in seen_ids:
                    combined_results.append(doc)
                    seen_ids.add(doc.id)
            
            # Add Weaviate results
            for result in weaviate_results:
                doc = Document(**result)
                if doc.id not in seen_ids:
                    combined_results.append(doc)
                    seen_ids.add(doc.id)
            
            return combined_results[:limit]
            
        except Exception as e:
            logger.error(f"Failed to perform hybrid search: {str(e)}")
            raise RepositoryError(f"Failed to perform hybrid search: {str(e)}")