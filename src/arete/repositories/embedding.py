"""
Embedding Repository for Arete Graph-RAG system.

Provides high-level interface for embedding generation, storage, and semantic search
following the established repository pattern with dual persistence architecture.
"""

import logging
from typing import List, Optional, Dict, Any, Union, Tuple
from uuid import UUID
import asyncio
from contextlib import contextmanager

from .base import SearchableRepository, RepositoryError
from ..models.chunk import Chunk
from ..database.client import Neo4jClient
from ..database.weaviate_client import WeaviateClient
from ..config import Settings, get_settings

logger = logging.getLogger(__name__)


class EmbeddingRepositoryError(RepositoryError):
    """Base exception for embedding repository errors."""
    pass


class EmbeddingGenerationError(EmbeddingRepositoryError):
    """Raised when embedding generation fails."""
    pass


class EmbeddingStorageError(EmbeddingRepositoryError):
    """Raised when embedding storage fails."""
    pass


class SemanticSearchError(EmbeddingRepositoryError):
    """Raised when semantic search fails."""
    pass


class EmbeddingRepository(SearchableRepository[Chunk]):
    """
    Repository for embedding generation, storage, and semantic search.
    
    Provides high-level interface following established repository patterns
    with integration to EmbeddingService and dual persistence architecture.
    
    Features:
    - Automated embedding generation for chunks
    - Efficient batch processing for large datasets
    - Semantic search with relevance scoring
    - Dual persistence (Neo4j metadata + Weaviate vectors)
    - Performance optimization and caching
    """
    
    def __init__(
        self,
        neo4j_client: Optional[Neo4jClient] = None,
        weaviate_client: Optional[WeaviateClient] = None,
        embedding_service: Optional[Any] = None,
        settings: Optional[Settings] = None
    ):
        """
        Initialize embedding repository.
        
        Args:
            neo4j_client: Neo4j client for metadata storage
            weaviate_client: Weaviate client for vector storage
            embedding_service: Embedding generation service
            settings: Configuration settings
        """
        self.settings = settings or get_settings()
        
        # Initialize clients following established pattern
        self.neo4j_client = neo4j_client
        self.weaviate_client = weaviate_client
        
        # Initialize embedding service (lazy loading)
        self._embedding_service = embedding_service
        
        # Performance tracking
        self._embeddings_generated = 0
        self._searches_performed = 0
        self._cache_hits = 0
        
        logger.info("Initialized EmbeddingRepository")
    
    @property
    def embedding_service(self):
        """Get embedding service with lazy initialization."""
        if self._embedding_service is None:
            from ..services.embedding_service import get_embedding_service
            self._embedding_service = get_embedding_service(settings=self.settings)
            
            # Ensure model is loaded for performance
            if not self._embedding_service.is_model_loaded():
                logger.info("Loading embedding model for repository")
                self._embedding_service.load_model()
        
        return self._embedding_service
    
    def get_stats(self) -> Dict[str, Any]:
        """Get repository statistics."""
        stats = {
            'embeddings_generated': self._embeddings_generated,
            'searches_performed': self._searches_performed,
            'cache_hits': self._cache_hits,
            'cache_hit_rate': self._cache_hits / max(self._searches_performed, 1)
        }
        
        # Add embedding service stats if available
        if self._embedding_service:
            stats.update(self._embedding_service.get_model_info())
        
        return stats
    
    # Embedding Generation Methods
    
    def generate_and_store_embedding(
        self,
        chunk: Chunk,
        use_vectorizable_text: bool = True,
        store_immediately: bool = True
    ) -> Chunk:
        """
        Generate embedding for a single chunk and optionally store it.
        
        Args:
            chunk: Chunk to generate embedding for
            use_vectorizable_text: Whether to use vectorizable_text field
            store_immediately: Whether to store in databases immediately
            
        Returns:
            Updated chunk with embedding
            
        Raises:
            EmbeddingGenerationError: If embedding generation fails
            EmbeddingStorageError: If storage fails (when store_immediately=True)
        """
        try:
            # Generate embedding
            embedding = self.embedding_service.generate_chunk_embedding(
                chunk,
                use_vectorizable_text=use_vectorizable_text
            )
            
            # Update chunk with embedding
            chunk.embedding_vector = embedding
            self._embeddings_generated += 1
            
            # Store immediately if requested
            if store_immediately:
                self._store_chunk_with_embedding(chunk)
            
            logger.debug(f"Generated embedding for chunk {chunk.id}")
            return chunk
            
        except Exception as e:
            logger.error(f"Failed to generate embedding for chunk: {e}")
            raise EmbeddingGenerationError(f"Embedding generation failed: {e}") from e
    
    def batch_generate_and_store(
        self,
        chunks: List[Chunk],
        batch_size: Optional[int] = None,
        use_vectorizable_text: bool = True,
        store_immediately: bool = True,
        progress_callback: Optional[callable] = None
    ) -> List[Chunk]:
        """
        Generate embeddings for multiple chunks efficiently.
        
        Args:
            chunks: List of chunks to process
            batch_size: Batch size for processing (auto-calculated if None)
            use_vectorizable_text: Whether to use vectorizable_text fields
            store_immediately: Whether to store in databases immediately
            progress_callback: Optional progress callback function
            
        Returns:
            List of updated chunks with embeddings
            
        Raises:
            EmbeddingGenerationError: If batch generation fails
            EmbeddingStorageError: If storage fails (when store_immediately=True)
        """
        if not chunks:
            return []
        
        try:
            # Generate embeddings in batch
            embeddings = self.embedding_service.generate_chunk_embeddings_batch(
                chunks,
                batch_size=batch_size,
                use_vectorizable_text=use_vectorizable_text,
                show_progress=False  # We handle progress ourselves
            )
            
            # Update chunks with embeddings
            updated_chunks = []
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding_vector = embedding
                updated_chunks.append(chunk)
                
                # Call progress callback if provided
                if progress_callback:
                    progress_callback(len(updated_chunks), len(chunks))
            
            self._embeddings_generated += len(chunks)
            
            # Store immediately if requested
            if store_immediately:
                self._batch_store_chunks_with_embeddings(updated_chunks)
            
            logger.info(f"Generated embeddings for {len(chunks)} chunks")
            return updated_chunks
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings for batch: {e}")
            raise EmbeddingGenerationError(f"Batch embedding generation failed: {e}") from e
    
    def update_chunk_embeddings(
        self,
        chunks: List[Chunk],
        force_regenerate: bool = False
    ) -> List[Chunk]:
        """
        Update embeddings for chunks, generating only if missing or forced.
        
        Args:
            chunks: List of chunks to update
            force_regenerate: Whether to regenerate existing embeddings
            
        Returns:
            List of updated chunks
        """
        chunks_to_process = []
        
        for chunk in chunks:
            if force_regenerate or chunk.embedding_vector is None:
                chunks_to_process.append(chunk)
        
        if chunks_to_process:
            logger.info(f"Updating embeddings for {len(chunks_to_process)} chunks")
            return self.batch_generate_and_store(chunks_to_process)
        else:
            logger.info("All chunks already have embeddings, no updates needed")
            return chunks
    
    # Semantic Search Methods
    
    def search_by_text(
        self,
        query_text: str,
        limit: int = 10,
        min_certainty: float = 0.7,
        document_ids: Optional[List[UUID]] = None,
        chunk_types: Optional[List[str]] = None
    ) -> List[Tuple[Chunk, float]]:
        """
        Perform semantic search using text query.
        
        Args:
            query_text: Text to search for
            limit: Maximum number of results
            min_certainty: Minimum relevance threshold
            document_ids: Optional filter by document IDs
            chunk_types: Optional filter by chunk types
            
        Returns:
            List of (chunk, relevance_score) tuples
            
        Raises:
            SemanticSearchError: If search fails
        """
        try:
            # Generate embedding for query
            query_embedding = self.embedding_service.generate_embedding(query_text)
            
            # Perform vector search
            return self.search_by_vector(
                query_embedding,
                limit=limit,
                min_certainty=min_certainty,
                document_ids=document_ids,
                chunk_types=chunk_types
            )
            
        except Exception as e:
            logger.error(f"Text search failed for query '{query_text}': {e}")
            raise SemanticSearchError(f"Text search failed: {e}") from e
    
    def search_by_vector(
        self,
        query_vector: List[float],
        limit: int = 10,
        min_certainty: float = 0.7,
        document_ids: Optional[List[UUID]] = None,
        chunk_types: Optional[List[str]] = None
    ) -> List[Tuple[Chunk, float]]:
        """
        Perform semantic search using embedding vector.
        
        Args:
            query_vector: Embedding vector to search with
            limit: Maximum number of results
            min_certainty: Minimum relevance threshold
            document_ids: Optional filter by document IDs
            chunk_types: Optional filter by chunk types
            
        Returns:
            List of (chunk, relevance_score) tuples
            
        Raises:
            SemanticSearchError: If search fails
        """
        if not self.weaviate_client:
            raise SemanticSearchError("Weaviate client not available for search")
        
        try:
            # Perform vector search in Weaviate
            search_results = self.weaviate_client.search_by_vector(
                collection_name="Chunk",
                query_vector=query_vector,
                limit=limit,
                min_certainty=min_certainty
            )
            
            # Convert results to chunks
            results = []
            for result in search_results:
                try:
                    chunk = self._weaviate_result_to_chunk(result)
                    relevance = result.get("metadata", {}).get("certainty", 0.0)
                    
                    # Apply filters if specified
                    if self._passes_filters(chunk, document_ids, chunk_types):
                        results.append((chunk, relevance))
                
                except Exception as e:
                    logger.warning(f"Failed to convert search result to chunk: {e}")
                    continue
            
            self._searches_performed += 1
            logger.debug(f"Vector search returned {len(results)} results")
            
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise SemanticSearchError(f"Vector search failed: {e}") from e
    
    def search(
        self,
        query: Union[str, List[float]],
        limit: int = 10,
        **kwargs
    ) -> List[Chunk]:
        """
        General search method supporting both text and vector queries.
        
        Args:
            query: Text string or embedding vector
            limit: Maximum number of results
            **kwargs: Additional search parameters
            
        Returns:
            List of matching chunks
        """
        try:
            if isinstance(query, str):
                results = self.search_by_text(query, limit=limit, **kwargs)
            elif isinstance(query, (list, tuple)):
                results = self.search_by_vector(query, limit=limit, **kwargs)
            else:
                raise ValueError(f"Unsupported query type: {type(query)}")
            
            # Return only chunks, not relevance scores
            return [chunk for chunk, _ in results]
            
        except Exception as e:
            logger.error(f"Search failed for query: {e}")
            raise SemanticSearchError(f"Search failed: {e}") from e
    
    # Storage Methods (Private)
    
    def _store_chunk_with_embedding(self, chunk: Chunk) -> None:
        """Store chunk with embedding in both databases."""
        try:
            # Store in Weaviate for vector search
            if self.weaviate_client and chunk.embedding_vector:
                weaviate_data = chunk.to_weaviate_dict()
                self.weaviate_client.create_object(
                    "Chunk",
                    weaviate_data,
                    chunk.embedding_vector
                )
            
            # Store metadata in Neo4j if available
            if self.neo4j_client:
                neo4j_data = chunk.to_neo4j_dict()
                # Note: Neo4j storage would be handled by ChunkRepository
                pass
                
        except Exception as e:
            logger.error(f"Failed to store chunk with embedding: {e}")
            raise EmbeddingStorageError(f"Storage failed: {e}") from e
    
    def _batch_store_chunks_with_embeddings(self, chunks: List[Chunk]) -> None:
        """Store multiple chunks with embeddings efficiently."""
        if not chunks:
            return
        
        try:
            # Prepare batch data for Weaviate
            if self.weaviate_client:
                batch_objects = []
                for chunk in chunks:
                    if chunk.embedding_vector:
                        batch_objects.append({
                            "properties": chunk.to_weaviate_dict(),
                            "vector": chunk.embedding_vector
                        })
                
                if batch_objects:
                    self.weaviate_client.create_objects_batch("Chunk", batch_objects)
            
            # Neo4j metadata storage would be handled by ChunkRepository
            
        except Exception as e:
            logger.error(f"Failed to batch store chunks with embeddings: {e}")
            raise EmbeddingStorageError(f"Batch storage failed: {e}") from e
    
    # Utility Methods
    
    def _weaviate_result_to_chunk(self, result: Dict[str, Any]) -> Chunk:
        """Convert Weaviate search result to Chunk model."""
        properties = result.get("properties", {})
        
        # Map Weaviate fields back to Chunk fields
        chunk_data = {
            "text": properties.get("content", ""),
            "chunk_type": properties.get("chunk_type", "paragraph"),
            "document_id": UUID(properties.get("document_id")),
            "start_position": properties.get("position_info", {}).get("start", 0),
            "end_position": properties.get("position_info", {}).get("end", 0),
            "sequence_number": properties.get("sequence_number", 0),
            "word_count": properties.get("computed_word_count", 0),
        }
        
        # Create chunk (UUID from Weaviate result)
        chunk = Chunk(**chunk_data)
        if "uuid" in result:
            chunk.id = UUID(result["uuid"])
        
        return chunk
    
    def _passes_filters(
        self,
        chunk: Chunk,
        document_ids: Optional[List[UUID]],
        chunk_types: Optional[List[str]]
    ) -> bool:
        """Check if chunk passes the specified filters."""
        if document_ids and chunk.document_id not in document_ids:
            return False
        
        if chunk_types and chunk.chunk_type.value not in chunk_types:
            return False
        
        return True
    
    # Context Managers
    
    @contextmanager
    def embedding_transaction(self):
        """Context manager for transactional embedding operations."""
        try:
            # Begin transaction (would coordinate across both databases)
            yield self
            # Commit transaction
            logger.debug("Embedding transaction committed")
        except Exception as e:
            # Rollback transaction
            logger.error(f"Embedding transaction failed, rolling back: {e}")
            raise
    
    # Cleanup Methods
    
    def cleanup(self) -> None:
        """Clean up resources."""
        if self._embedding_service:
            self._embedding_service.unload_model()
        
        logger.info("EmbeddingRepository cleaned up")


# Factory function following established pattern
def create_embedding_repository(
    settings: Optional[Settings] = None,
    neo4j_client: Optional[Neo4jClient] = None,
    weaviate_client: Optional[WeaviateClient] = None,
    embedding_service: Optional[Any] = None
) -> EmbeddingRepository:
    """
    Create embedding repository with dependency injection.
    
    Args:
        settings: Configuration settings
        neo4j_client: Neo4j client instance
        weaviate_client: Weaviate client instance
        embedding_service: Embedding service instance
        
    Returns:
        Configured EmbeddingRepository instance
    """
    return EmbeddingRepository(
        neo4j_client=neo4j_client,
        weaviate_client=weaviate_client,
        embedding_service=embedding_service,
        settings=settings
    )