"""
Tests for base repository interface contracts.

Following focused testing methodology proven in database client implementations.
Tests cover repository interface contracts, error handling, and integration patterns.
"""
import pytest
from abc import ABC
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from typing import List, Optional, Dict, Any, Union
from uuid import UUID

from arete.repositories.base import (
    BaseRepository,
    SearchableRepository, 
    GraphRepository,
    RepositoryError,
    EntityNotFoundError,
    DuplicateEntityError,
    ValidationError,
    ModelType
)
from arete.models.base import BaseModel


class MockModel(BaseModel):
    """Mock model for testing repository interfaces."""
    name: str
    description: Optional[str] = None


class TestRepositoryInterfaceContracts:
    """Test that repository interfaces define correct contracts."""

    def test_base_repository_is_abstract(self):
        """Test that BaseRepository is abstract and cannot be instantiated."""
        with pytest.raises(TypeError):
            BaseRepository()

    def test_searchable_repository_is_abstract(self):
        """Test that SearchableRepository is abstract and cannot be instantiated.""" 
        with pytest.raises(TypeError):
            SearchableRepository()

    def test_graphable_repository_is_abstract(self):
        """Test that GraphRepository is abstract and cannot be instantiated."""
        with pytest.raises(TypeError):
            GraphRepository()

    def test_base_repository_has_required_methods(self):
        """Test that BaseRepository defines all required abstract methods."""
        required_methods = {
            'create', 'get_by_id', 'update', 'delete', 
            'list_all', 'count', 'exists'
        }
        
        actual_methods = {
            name for name in dir(BaseRepository) 
            if not name.startswith('_') and callable(getattr(BaseRepository, name))
        }
        
        assert required_methods.issubset(actual_methods)

    def test_searchable_repository_extends_base(self):
        """Test that SearchableRepository extends BaseRepository."""
        assert issubclass(SearchableRepository, BaseRepository)

    def test_searchable_repository_has_search_methods(self):
        """Test that SearchableRepository defines search methods."""
        search_methods = {'search_by_text', 'search_by_embedding'}
        
        actual_methods = {
            name for name in dir(SearchableRepository)
            if not name.startswith('_') and callable(getattr(SearchableRepository, name))
        }
        
        assert search_methods.issubset(actual_methods)

    def test_graph_repository_extends_base(self):
        """Test that GraphRepository extends BaseRepository."""
        assert issubclass(GraphRepository, BaseRepository)

    def test_graph_repository_has_graph_methods(self):
        """Test that GraphRepository defines graph traversal methods."""
        graph_methods = {'get_related', 'get_neighbors'}
        
        actual_methods = {
            name for name in dir(GraphRepository)
            if not name.startswith('_') and callable(getattr(GraphRepository, name))
        }
        
        assert graph_methods.issubset(actual_methods)


class TestRepositoryExceptions:
    """Test repository exception hierarchy."""

    def test_repository_error_is_base_exception(self):
        """Test that RepositoryError is the base exception."""
        error = RepositoryError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"

    def test_entity_not_found_error_extends_repository_error(self):
        """Test EntityNotFoundError inheritance."""
        error = EntityNotFoundError("Entity not found")
        assert isinstance(error, RepositoryError)
        assert isinstance(error, Exception)

    def test_duplicate_entity_error_extends_repository_error(self):
        """Test DuplicateEntityError inheritance."""
        error = DuplicateEntityError("Entity exists")
        assert isinstance(error, RepositoryError)
        assert isinstance(error, Exception)

    def test_validation_error_extends_repository_error(self):
        """Test ValidationError inheritance."""
        error = ValidationError("Invalid entity")
        assert isinstance(error, RepositoryError)
        assert isinstance(error, Exception)


class MockBaseRepository(BaseRepository[MockModel]):
    """Concrete implementation of BaseRepository for testing."""
    
    def __init__(self):
        self.data = {}
        self.create_mock = AsyncMock()
        self.get_by_id_mock = AsyncMock()
        self.update_mock = AsyncMock()
        self.delete_mock = AsyncMock()
        self.list_all_mock = AsyncMock()
        self.count_mock = AsyncMock()
        self.exists_mock = AsyncMock()

    async def create(self, entity: MockModel) -> MockModel:
        return await self.create_mock(entity)

    async def get_by_id(self, entity_id: Union[UUID, str]) -> Optional[MockModel]:
        return await self.get_by_id_mock(entity_id)

    async def update(self, entity: MockModel) -> MockModel:
        return await self.update_mock(entity)

    async def delete(self, entity_id: Union[UUID, str]) -> bool:
        return await self.delete_mock(entity_id)

    async def list_all(
        self, 
        limit: int = 100, 
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MockModel]:
        return await self.list_all_mock(limit, offset, filters)

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        return await self.count_mock(filters)

    async def exists(self, entity_id: Union[UUID, str]) -> bool:
        return await self.exists_mock(entity_id)


class TestBaseRepositoryImplementation:
    """Test BaseRepository interface through concrete implementation."""

    @pytest.fixture
    def repository(self):
        """Provide mock repository instance."""
        return MockBaseRepository()

    @pytest.fixture
    def mock_entity(self):
        """Provide mock entity for testing."""
        return MockModel(
            id=uuid4(),
            name="Test Entity",
            description="Test description"
        )

    @pytest.mark.asyncio
    async def test_create_method_contract(self, repository, mock_entity):
        """Test create method follows contract."""
        repository.create_mock.return_value = mock_entity
        
        result = await repository.create(mock_entity)
        
        repository.create_mock.assert_called_once_with(mock_entity)
        assert result == mock_entity

    @pytest.mark.asyncio
    async def test_get_by_id_method_contract(self, repository, mock_entity):
        """Test get_by_id method follows contract."""
        entity_id = uuid4()
        repository.get_by_id_mock.return_value = mock_entity
        
        result = await repository.get_by_id(entity_id)
        
        repository.get_by_id_mock.assert_called_once_with(entity_id)
        assert result == mock_entity

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(self, repository):
        """Test get_by_id returns None for non-existent entity."""
        entity_id = uuid4()
        repository.get_by_id_mock.return_value = None
        
        result = await repository.get_by_id(entity_id)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_update_method_contract(self, repository, mock_entity):
        """Test update method follows contract."""
        repository.update_mock.return_value = mock_entity
        
        result = await repository.update(mock_entity)
        
        repository.update_mock.assert_called_once_with(mock_entity)
        assert result == mock_entity

    @pytest.mark.asyncio
    async def test_delete_method_contract(self, repository):
        """Test delete method follows contract."""
        entity_id = uuid4()
        repository.delete_mock.return_value = True
        
        result = await repository.delete(entity_id)
        
        repository.delete_mock.assert_called_once_with(entity_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_returns_false_when_not_found(self, repository):
        """Test delete returns False for non-existent entity."""
        entity_id = uuid4()
        repository.delete_mock.return_value = False
        
        result = await repository.delete(entity_id)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_list_all_method_contract(self, repository, mock_entity):
        """Test list_all method follows contract."""
        repository.list_all_mock.return_value = [mock_entity]
        
        result = await repository.list_all(limit=10, offset=5, filters={"name": "test"})
        
        repository.list_all_mock.assert_called_once_with(10, 5, {"name": "test"})
        assert result == [mock_entity]

    @pytest.mark.asyncio
    async def test_list_all_with_defaults(self, repository):
        """Test list_all uses default parameters."""
        repository.list_all_mock.return_value = []
        
        result = await repository.list_all()
        
        repository.list_all_mock.assert_called_once_with(100, 0, None)
        assert result == []

    @pytest.mark.asyncio
    async def test_count_method_contract(self, repository):
        """Test count method follows contract."""
        repository.count_mock.return_value = 5
        
        result = await repository.count(filters={"active": True})
        
        repository.count_mock.assert_called_once_with({"active": True})
        assert result == 5

    @pytest.mark.asyncio
    async def test_count_without_filters(self, repository):
        """Test count method without filters."""
        repository.count_mock.return_value = 10
        
        result = await repository.count()
        
        repository.count_mock.assert_called_once_with(None)
        assert result == 10

    @pytest.mark.asyncio
    async def test_exists_method_contract(self, repository):
        """Test exists method follows contract."""
        entity_id = uuid4()
        repository.exists_mock.return_value = True
        
        result = await repository.exists(entity_id)
        
        repository.exists_mock.assert_called_once_with(entity_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_exists_returns_false_for_missing_entity(self, repository):
        """Test exists returns False for missing entity."""
        entity_id = uuid4()
        repository.exists_mock.return_value = False
        
        result = await repository.exists(entity_id)
        
        assert result is False


class TestRepositoryErrorHandling:
    """Test repository error handling contracts."""

    @pytest.fixture
    def repository(self):
        """Provide mock repository for error testing."""
        return MockBaseRepository()

    @pytest.mark.asyncio
    async def test_create_raises_duplicate_entity_error(self, repository, mock_entity):
        """Test create raises DuplicateEntityError for duplicate entities."""
        repository.create_mock.side_effect = DuplicateEntityError("Entity already exists")
        
        with pytest.raises(DuplicateEntityError):
            await repository.create(mock_entity)

    @pytest.mark.asyncio
    async def test_create_raises_validation_error(self, repository, mock_entity):
        """Test create raises ValidationError for invalid entities."""
        repository.create_mock.side_effect = ValidationError("Invalid entity data")
        
        with pytest.raises(ValidationError):
            await repository.create(mock_entity)

    @pytest.mark.asyncio
    async def test_update_raises_entity_not_found_error(self, repository, mock_entity):
        """Test update raises EntityNotFoundError for missing entities."""
        repository.update_mock.side_effect = EntityNotFoundError("Entity not found")
        
        with pytest.raises(EntityNotFoundError):
            await repository.update(mock_entity)

    @pytest.mark.asyncio
    async def test_repository_operations_raise_base_error(self, repository):
        """Test that repository operations can raise base RepositoryError."""
        repository.get_by_id_mock.side_effect = RepositoryError("Database connection failed")
        
        with pytest.raises(RepositoryError):
            await repository.get_by_id(uuid4())

    @pytest.fixture
    def mock_entity(self):
        """Provide mock entity for error testing."""
        return MockModel(
            id=uuid4(),
            name="Test Entity",
            description="Test description"
        )


class TestRepositoryTypeSystem:
    """Test repository generic type system."""

    def test_repository_is_generic(self):
        """Test that BaseRepository is generic with ModelType."""
        # This test verifies the type system works
        repository_type = BaseRepository[MockModel]
        assert repository_type.__origin__ is BaseRepository

    def test_repository_preserves_model_type(self):
        """Test that repository implementations preserve model type."""
        mock_repo = MockBaseRepository()
        # Type checking would catch issues here in a real IDE
        assert isinstance(mock_repo, BaseRepository)