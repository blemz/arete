"""
Repository pattern implementation for Arete Graph-RAG system.

This package provides clean data access layer with dual persistence strategy:
- Neo4j for graph relationships and traversal
- Weaviate for vector embeddings and semantic search

Following Domain Driven Design principles with abstract repository interfaces
for testability and clean architecture.
"""
from .base import (
    BaseRepository,
    SearchableRepository,
    GraphRepository,
    RepositoryError,
    EntityNotFoundError,
    DuplicateEntityError,
    ValidationError,
)
from .document import DocumentRepository
from .entity import EntityRepository
from .embedding import EmbeddingRepository, create_embedding_repository
from .retrieval import (
    RetrievalRepository,
    RetrievalMethod,
    HybridStrategy,
    HybridRetrievalConfig,
    create_retrieval_repository
)

__all__ = [
    # Base classes and exceptions
    "BaseRepository",
    "SearchableRepository",
    "GraphRepository",
    "RepositoryError", 
    "EntityNotFoundError",
    "DuplicateEntityError",
    "ValidationError",
    # Repository implementations
    "DocumentRepository",
    "EntityRepository",
    "EmbeddingRepository",
    "RetrievalRepository",
    # Retrieval configuration
    "RetrievalMethod",
    "HybridStrategy", 
    "HybridRetrievalConfig",
    # Factory functions
    "create_embedding_repository",
    "create_retrieval_repository",
]