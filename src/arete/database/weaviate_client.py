"""Weaviate vector database client for Arete Graph-RAG system.

Modern implementation following Weaviate v4+ patterns with focused Graph-RAG operations.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from urllib.parse import urlparse

import weaviate
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
            
            # Use modern Weaviate client connection
            self.client = weaviate.connect_to_local(
                host=host,
                port=port,
                headers=self.headers
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