"""Weaviate vector database client for Arete Graph-RAG system.

Modern implementation following Weaviate v4+ patterns with focused Graph-RAG operations.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from urllib.parse import urlparse

import weaviate
import weaviate.classes.config as wvc
from weaviate.exceptions import (
    AuthenticationFailedException,
    WeaviateConnectionError,
    WeaviateBaseError,
)

from ..config import get_settings
from ..models.document import Document
from ..models.entity import Entity
from .exceptions import DatabaseConnectionError, DatabaseQueryError


class WeaviateClient:
    """Modern Weaviate vector database client for Graph-RAG operations."""
    
    def __init__(
        self, 
        url: Optional[str] = None, 
        headers: Optional[Dict[str, str]] = None
    ) -> None:
        """Initialize Weaviate client with configuration integration.
        
        Args:
            url: Weaviate server URL. If None, uses settings.
            headers: HTTP headers including auth. If None, uses default.
        """
        settings = get_settings()
        self.url = url or settings.weaviate_url
        self.headers = headers or {}
        self.client: Optional[weaviate.WeaviateClient] = None
        
    # Connection Management
    def connect(self) -> None:
        """Establish connection to Weaviate using modern patterns."""
        try:
            # Parse URL to extract connection details
            parsed = urlparse(self.url)
            host = parsed.hostname or 'localhost'
            port = parsed.port or 8080
            
            # Use modern Weaviate client connection with skip_init_checks for Docker setup
            self.client = weaviate.connect_to_local(
                host=host,
                port=port,
                headers=self.headers,
                skip_init_checks=True  # Skip gRPC health check for Docker compatibility
            )
        except (WeaviateConnectionError, AuthenticationFailedException) as e:
            self.client = None
            raise DatabaseConnectionError(f"Failed to connect to Weaviate: {str(e)}") from e
            
    def close(self) -> None:
        """Close Weaviate connection."""
        if self.client:
            self.client.close()
            self.client = None
            
    async def async_connect(self) -> None:
        """Establish asynchronous connection to Weaviate."""
        # Run sync connect in executor for async context
        await asyncio.get_event_loop().run_in_executor(None, self.connect)
        
    async def async_close(self) -> None:
        """Close asynchronous connection."""
        await asyncio.get_event_loop().run_in_executor(None, self.close)
            
    # Context Managers
    def __enter__(self) -> 'WeaviateClient':
        """Sync context manager entry."""
        self.connect()
        return self
        
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Sync context manager exit."""
        self.close()
        
    async def __aenter__(self) -> 'WeaviateClient':
        """Async context manager entry."""
        await self.async_connect()
        return self
        
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.async_close()
        
    # Health Check
    def health_check(self) -> bool:
        """Perform health check on Weaviate connection."""
        if not self.client:
            return False
        try:
            return self.client.is_ready()
        except Exception:
            return False
            
    # Document Operations for Graph-RAG
    def save_document(self, document: Document) -> str:
        """Save Document to Weaviate vector database.
        
        Args:
            document: Document model instance to save
            
        Returns:
            str: ID of saved document
            
        Raises:
            DatabaseQueryError: If save operation fails
        """
        if not self.client:
            raise DatabaseConnectionError("Client not connected. Call connect() first.")
            
        try:
            collection = self.client.collections.get("Document")
            
            # Convert Document model to Weaviate properties
            properties = {
                "title": document.title,
                "author": document.author,
                "content": document.content,
                "language": document.language,
                "created_at": document.created_at.isoformat(),
                "metadata": document.metadata or {},
                "neo4j_id": str(document.id)  # Use Document ID as neo4j_id reference
            }
            
            # Insert document with vectorization
            result = collection.data.insert(
                properties=properties,
                uuid=document.id
            )
            
            return str(result.uuid) if hasattr(result, 'uuid') else str(document.id)
            
        except WeaviateBaseError as e:
            raise DatabaseQueryError(f"Failed to save document: {str(e)}") from e
            
    def get_document_by_id(self, doc_id: str) -> Optional[Document]:
        """Retrieve Document by ID from Weaviate.
        
        Args:
            doc_id: Document ID to retrieve
            
        Returns:
            Optional[Document]: Document model instance or None if not found
            
        Raises:
            DatabaseQueryError: If query fails
        """
        if not self.client:
            raise DatabaseConnectionError("Client not connected. Call connect() first.")
            
        try:
            collection = self.client.collections.get("Document")
            
            # Fetch object by ID
            result = collection.query.fetch_object_by_id(doc_id)
            
            if not result:
                return None
                
            # Convert Weaviate result to Document model
            props = result.properties
            return Document(
                id=str(result.uuid),
                title=props["title"],
                author=props["author"],
                content=props["content"],
                language=props["language"],
                created_at=datetime.fromisoformat(props["created_at"]),
                metadata=props.get("metadata", {}),
                neo4j_id=props.get("neo4j_id")
            )
            
        except WeaviateBaseError as e:
            raise DatabaseQueryError(f"Failed to get document: {str(e)}") from e
            
    def search_documents_by_text(self, query_text: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform semantic search for documents using vector similarity.
        
        Args:
            query_text: Text query for semantic search
            limit: Maximum number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of results with document and similarity score
            
        Raises:
            DatabaseQueryError: If search fails
        """
        if not self.client:
            raise DatabaseConnectionError("Client not connected. Call connect() first.")
            
        try:
            collection = self.client.collections.get("Document")
            
            # Perform near text search with modern Weaviate API
            response = collection.query.near_text(
                query=query_text,
                limit=limit,
                return_metadata=["score"]
            )
            
            results = []
            for obj in response.objects:
                # Convert to Document model
                props = obj.properties
                document = Document(
                    id=str(obj.uuid),
                    title=props["title"],
                    author=props["author"],
                    content=props["content"],
                    language=props["language"],
                    created_at=datetime.fromisoformat(props["created_at"]),
                    metadata=props.get("metadata", {}),
                    neo4j_id=props.get("neo4j_id")
                )
                
                results.append({
                    "document": document,
                    "score": obj.metadata.score if hasattr(obj, 'metadata') else 0.0
                })
                
            return results
            
        except WeaviateBaseError as e:
            raise DatabaseQueryError(f"Failed to search documents: {str(e)}") from e
            
    # Batch Operations for Efficient Processing
    def batch_save_documents(self, documents: List[Document]) -> List[str]:
        """Save multiple documents using Weaviate batch operations.
        
        Args:
            documents: List of Document model instances to save
            
        Returns:
            List[str]: List of saved document IDs
            
        Raises:
            DatabaseQueryError: If batch operation fails
        """
        if not self.client:
            raise DatabaseConnectionError("Client not connected. Call connect() first.")
            
        try:
            collection = self.client.collections.get("Document")
            saved_ids = []
            
            # Use Weaviate's batch context manager
            with self.client.batch as batch:
                for document in documents:
                    properties = {
                        "title": document.title,
                        "author": document.author,
                        "content": document.content,
                        "language": document.language,
                        "created_at": document.created_at.isoformat(),
                        "metadata": document.metadata or {},
                        "neo4j_id": str(document.id)  # Use Document ID as neo4j_id reference
                    }
                    
                    batch.add_object(
                        class_name="Document",
                        properties=properties,
                        uuid=document.id
                    )
                    saved_ids.append(str(document.id))
                    
            return saved_ids
            
        except WeaviateBaseError as e:
            raise DatabaseQueryError(f"Failed to batch save documents: {str(e)}") from e
            
    # Entity Operations for Graph-RAG
    def save_entity(self, entity: Entity) -> str:
        """Save Entity to Weaviate vector database.
        
        Args:
            entity: Entity model instance to save
            
        Returns:
            str: ID of saved entity
            
        Raises:
            DatabaseQueryError: If save operation fails
        """
        if not self.client:
            raise DatabaseConnectionError("Client not connected. Call connect() first.")
            
        try:
            collection = self.client.collections.get("Entity")
            
            # Convert Entity model to Weaviate properties
            properties = entity.to_weaviate_dict()
            
            # Insert entity with vectorization
            result = collection.data.insert(
                properties=properties,
                uuid=entity.id
            )
            
            return str(result.uuid) if hasattr(result, 'uuid') else str(entity.id)
            
        except WeaviateBaseError as e:
            raise DatabaseQueryError(f"Failed to save entity: {str(e)}") from e
            
    # Generic Object Operations
    def create_object(self, class_name: str, properties: Dict[str, Any], vector: Optional[List[float]] = None) -> str:
        """Create a generic object in Weaviate.
        
        Args:
            class_name: Name of the Weaviate class/collection
            properties: Object properties dictionary
            vector: Optional vector for the object
            
        Returns:
            str: ID of created object
            
        Raises:
            DatabaseQueryError: If creation fails
        """
        if not self.client:
            raise DatabaseConnectionError("Client not connected. Call connect() first.")
            
        try:
            collection = self.client.collections.get(class_name)
            
            # Insert object with optional vector
            if vector:
                result = collection.data.insert(
                    properties=properties,
                    vector=vector
                )
            else:
                result = collection.data.insert(
                    properties=properties
                )
            
            return str(result.uuid) if hasattr(result, 'uuid') else "created"
            
        except WeaviateBaseError as e:
            raise DatabaseQueryError(f"Failed to create {class_name} object: {str(e)}") from e
            
    def create_objects_batch(self, class_name: str, objects: List[Dict[str, Any]]) -> List[str]:
        """Create multiple objects in Weaviate using batch operations.
        
        Args:
            class_name: Name of the Weaviate class/collection
            objects: List of objects with 'properties' and optional 'vector' keys
            
        Returns:
            List[str]: List of created object IDs
            
        Raises:
            DatabaseQueryError: If batch creation fails
        """
        if not self.client:
            raise DatabaseConnectionError("Client not connected. Call connect() first.")
            
        try:
            collection = self.client.collections.get(class_name)
            ids = []
            
            # Prepare batch data
            batch_data = []
            for obj in objects:
                properties = obj.get("properties", {})
                vector = obj.get("vector")
                
                if vector:
                    batch_data.append({
                        "properties": properties,
                        "vector": vector
                    })
                else:
                    batch_data.append({
                        "properties": properties
                    })
            
            # Insert batch
            result = collection.data.insert_many(batch_data)
            
            # Extract IDs from result
            if hasattr(result, 'uuids'):
                ids = [str(uuid) for uuid in result.uuids]
            else:
                ids = [f"batch_item_{i}" for i in range(len(objects))]
                
            return ids
            
        except WeaviateBaseError as e:
            raise DatabaseQueryError(f"Failed to batch create {class_name} objects: {str(e)}") from e

    def search_by_vector(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        min_certainty: float = 0.7,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for objects using a vector query.
        
        Args:
            collection_name: Name of the collection to search
            query_vector: Query vector
            limit: Maximum number of results
            min_certainty: Minimum certainty threshold
            where_filter: Optional where filter
            
        Returns:
            List of search results with metadata
            
        Raises:
            DatabaseQueryError: If search fails
        """
        try:
            if not self.client:
                self.connect()
            
            # Get collection
            collection = self.client.collections.get(collection_name)
            
            # Build query with proper Weaviate v4 syntax
            if where_filter:
                query = collection.query.near_vector(
                    near_vector=query_vector,
                    limit=limit,
                    certainty=min_certainty,
                    return_metadata=['certainty']
                ).where(where_filter)
            else:
                query = collection.query.near_vector(
                    near_vector=query_vector,
                    limit=limit,
                    certainty=min_certainty,
                    return_metadata=['certainty']
                )
            
            # Execute query
            response = query.objects
            
            # Format results
            results = []
            for obj in response:
                result = {
                    "id": str(obj.uuid),
                    "properties": obj.properties,
                    "vector": obj.vector,
                    "_additional": {
                        "certainty": obj.metadata.certainty if obj.metadata else min_certainty
                    },
                    "metadata": {
                        "certainty": obj.metadata.certainty if obj.metadata else min_certainty
                    }
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            raise DatabaseQueryError(f"Vector search failed for {collection_name}: {str(e)}") from e