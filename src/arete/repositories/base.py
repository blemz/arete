"""
Base repository interfaces and contracts for Arete system.

Provides abstract base classes that define the repository pattern contracts
for all data access operations. Enables clean architecture with dependency
inversion and testability through interface segregation.
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar
from uuid import UUID

from arete.models.base import BaseModel

# Generic type for model classes
ModelType = TypeVar("ModelType", bound=BaseModel)


class RepositoryError(Exception):
    """Base exception for repository operations."""



class EntityNotFoundError(RepositoryError):
    """Raised when an entity is not found."""



class DuplicateEntityError(RepositoryError):
    """Raised when attempting to create a duplicate entity."""



class ValidationError(RepositoryError):
    """Raised when entity validation fails."""



class BaseRepository(ABC, Generic[ModelType]):
    """
    Abstract base repository defining core CRUD operations.

    Provides common interface for all repository implementations with
    support for dual persistence (Neo4j + Weaviate) through concrete
    implementations.
    """

    @abstractmethod
    async def create(self, entity: ModelType) -> ModelType:
        """
        Create a new entity in the repository.

        Args:
            entity: The entity to create

        Returns:
            The created entity with generated ID and timestamps

        Raises:
            DuplicateEntityError: If entity already exists
            ValidationError: If entity validation fails
            RepositoryError: For other repository errors
        """

    @abstractmethod
    async def get_by_id(self, entity_id: UUID | str) -> ModelType | None:
        """
        Retrieve entity by its unique identifier.

        Args:
            entity_id: The unique identifier of the entity

        Returns:
            The entity if found, None otherwise

        Raises:
            RepositoryError: For repository errors
        """

    @abstractmethod
    async def update(self, entity: ModelType) -> ModelType:
        """
        Update an existing entity.

        Args:
            entity: The entity with updated values

        Returns:
            The updated entity

        Raises:
            EntityNotFoundError: If entity doesn't exist
            ValidationError: If entity validation fails
            RepositoryError: For other repository errors
        """

    @abstractmethod
    async def delete(self, entity_id: UUID | str) -> bool:
        """
        Delete an entity by ID.

        Args:
            entity_id: The unique identifier of the entity to delete

        Returns:
            True if entity was deleted, False if not found

        Raises:
            RepositoryError: For repository errors
        """

    @abstractmethod
    async def list_all(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: dict[str, Any] | None = None,
    ) -> list[ModelType]:
        """
        List entities with optional pagination and filtering.

        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            filters: Optional filters to apply

        Returns:
            List of entities matching criteria

        Raises:
            RepositoryError: For repository errors
        """

    @abstractmethod
    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """
        Count entities matching optional filters.

        Args:
            filters: Optional filters to apply

        Returns:
            Number of entities matching criteria

        Raises:
            RepositoryError: For repository errors
        """

    @abstractmethod
    async def exists(self, entity_id: UUID | str) -> bool:
        """
        Check if entity exists by ID.

        Args:
            entity_id: The unique identifier to check

        Returns:
            True if entity exists, False otherwise

        Raises:
            RepositoryError: For repository errors
        """


class SearchableRepository(BaseRepository[ModelType]):
    """
    Extended repository interface for entities supporting text search.

    Provides additional methods for semantic search capabilities
    leveraging vector embeddings in Weaviate.
    """

    @abstractmethod
    async def search_by_text(
        self, query: str, limit: int = 10, similarity_threshold: float = 0.7
    ) -> list[ModelType]:
        """
        Search entities by semantic text similarity.

        Args:
            query: The search query text
            limit: Maximum number of results to return
            similarity_threshold: Minimum similarity score (0.0-1.0)

        Returns:
            List of entities matching the query

        Raises:
            RepositoryError: For repository errors
        """

    @abstractmethod
    async def search_by_embedding(
        self, embedding: list[float], limit: int = 10, similarity_threshold: float = 0.7
    ) -> list[ModelType]:
        """
        Search entities by embedding vector similarity.

        Args:
            embedding: The query embedding vector
            limit: Maximum number of results to return
            similarity_threshold: Minimum similarity score (0.0-1.0)

        Returns:
            List of entities with similar embeddings

        Raises:
            RepositoryError: For repository errors
        """


class GraphRepository(BaseRepository[ModelType]):
    """
    Extended repository interface for entities with graph relationships.

    Provides additional methods for graph traversal and relationship
    queries leveraging Neo4j graph capabilities.
    """

    @abstractmethod
    async def get_related(
        self,
        entity_id: UUID | str,
        relationship_type: str | None = None,
        direction: str = "BOTH",  # "INCOMING", "OUTGOING", "BOTH"
        limit: int = 10,
    ) -> list[ModelType]:
        """
        Get entities related to the given entity.

        Args:
            entity_id: The source entity ID
            relationship_type: Optional relationship type filter
            direction: Relationship direction to traverse
            limit: Maximum number of results to return

        Returns:
            List of related entities

        Raises:
            RepositoryError: For repository errors
        """

    @abstractmethod
    async def get_neighbors(
        self, entity_id: UUID | str, depth: int = 1, limit: int = 10
    ) -> list[ModelType]:
        """
        Get neighboring entities within specified depth.

        Args:
            entity_id: The source entity ID
            depth: Maximum traversal depth
            limit: Maximum number of results to return

        Returns:
            List of neighboring entities

        Raises:
            RepositoryError: For repository errors
        """
