"""
Tests for Document repository implementation.

Following focused testing methodology proven in database client implementations.
Tests cover document repository contract, dual persistence, and integration patterns.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime
from typing import List, Optional, Dict, Any

from arete.repositories.base import (
    BaseRepository,
    SearchableRepository,
    EntityNotFoundError,
    DuplicateEntityError,
    ValidationError,
    RepositoryError
)
from arete.repositories.document import DocumentRepository
from arete.models.document import Document
from arete.database.client import Neo4jClient
from arete.database.weaviate_client import WeaviateClient


class TestDocumentRepositoryInterface:
    """Test DocumentRepository interface contracts."""

    def test_document_repository_extends_searchable_repository(self):
        """Test that DocumentRepository extends SearchableRepository."""
        assert issubclass(DocumentRepository, SearchableRepository)

    def test_document_repository_extends_base_repository(self):
        """Test that DocumentRepository extends BaseRepository."""
        assert issubclass(DocumentRepository, BaseRepository)

    def test_document_repository_has_document_specific_methods(self):
        """Test that DocumentRepository has document-specific methods."""
        document_methods = {'get_by_title', 'get_by_author', 'search_content'}
        
        actual_methods = {
            name for name in dir(DocumentRepository)
            if not name.startswith('_') and callable(getattr(DocumentRepository, name))
        }
        
        assert document_methods.issubset(actual_methods)


class TestDocumentRepositoryInitialization:
    """Test DocumentRepository initialization and dependency injection."""

    def test_document_repository_requires_neo4j_client(self):
        """Test that DocumentRepository requires Neo4j client."""
        mock_neo4j = MagicMock(spec=Neo4jClient)
        mock_weaviate = MagicMock(spec=WeaviateClient)
        
        repo = DocumentRepository(
            neo4j_client=mock_neo4j,
            weaviate_client=mock_weaviate
        )
        
        assert repo._neo4j_client == mock_neo4j
        assert repo._weaviate_client == mock_weaviate

    def test_document_repository_requires_weaviate_client(self):
        """Test that DocumentRepository requires Weaviate client."""
        mock_neo4j = MagicMock(spec=Neo4jClient)
        mock_weaviate = MagicMock(spec=WeaviateClient)
        
        repo = DocumentRepository(
            neo4j_client=mock_neo4j,
            weaviate_client=mock_weaviate
        )
        
        assert repo._weaviate_client == mock_weaviate

    def test_document_repository_cannot_initialize_without_clients(self):
        """Test that DocumentRepository requires both clients."""
        with pytest.raises(TypeError):
            DocumentRepository()


class TestDocumentRepositoryBasicOperations:
    """Test basic CRUD operations for DocumentRepository."""

    @pytest.fixture
    def mock_neo4j_client(self):
        """Provide mock Neo4j client."""
        return MagicMock(spec=Neo4jClient)

    @pytest.fixture
    def mock_weaviate_client(self):
        """Provide mock Weaviate client."""
        return MagicMock(spec=WeaviateClient)

    @pytest.fixture
    def document_repository(self, mock_neo4j_client, mock_weaviate_client):
        """Provide DocumentRepository instance with mocked clients."""
        return DocumentRepository(
            neo4j_client=mock_neo4j_client,
            weaviate_client=mock_weaviate_client
        )

    @pytest.fixture
    def sample_document(self):
        """Provide sample document for testing."""
        return Document(
            id=uuid4(),
            title="Plato's Republic",
            author="Plato",
            date_published=datetime(380, 1, 1),
            content="Justice is the excellence of the soul...",
            metadata={"stephanus": "327a", "book": "I"}
        )

    @pytest.mark.asyncio
    async def test_create_document_stores_in_both_databases(
        self, 
        document_repository, 
        mock_neo4j_client, 
        mock_weaviate_client,
        sample_document
    ):
        """Test create stores document in both Neo4j and Weaviate."""
        # Mock successful storage in both databases
        mock_neo4j_client.create_node = AsyncMock(return_value=sample_document.model_dump())
        mock_weaviate_client.save_entity = AsyncMock()
        
        result = await document_repository.create(sample_document)
        
        # Verify Neo4j call
        mock_neo4j_client.create_node.assert_called_once()
        neo4j_call_args = mock_neo4j_client.create_node.call_args[1]
        assert neo4j_call_args['label'] == 'Document'
        assert neo4j_call_args['properties']['title'] == sample_document.title
        
        # Verify Weaviate call
        mock_weaviate_client.save_entity.assert_called_once()
        weaviate_call_args = mock_weaviate_client.save_entity.call_args
        assert weaviate_call_args[0][0] == sample_document
        
        assert result == sample_document

    @pytest.mark.asyncio
    async def test_create_document_handles_duplicate_error(
        self,
        document_repository,
        mock_neo4j_client,
        mock_weaviate_client,
        sample_document
    ):
        """Test create handles duplicate document errors."""
        mock_neo4j_client.create_node = AsyncMock(
            side_effect=Exception("Constraint violation")
        )
        
        with pytest.raises(DuplicateEntityError):
            await document_repository.create(sample_document)

    @pytest.mark.asyncio
    async def test_get_by_id_retrieves_from_neo4j(
        self,
        document_repository,
        mock_neo4j_client,
        sample_document
    ):
        """Test get_by_id retrieves document from Neo4j."""
        document_id = str(sample_document.id)
        mock_neo4j_client.get_node_by_id = AsyncMock(
            return_value=sample_document.model_dump()
        )
        
        result = await document_repository.get_by_id(document_id)
        
        mock_neo4j_client.get_node_by_id.assert_called_once_with(
            document_id, 'Document'
        )
        assert result.id == sample_document.id
        assert result.title == sample_document.title

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(
        self,
        document_repository,
        mock_neo4j_client
    ):
        """Test get_by_id returns None for non-existent document."""
        document_id = str(uuid4())
        mock_neo4j_client.get_node_by_id = AsyncMock(return_value=None)
        
        result = await document_repository.get_by_id(document_id)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_update_document_updates_both_databases(
        self,
        document_repository,
        mock_neo4j_client,
        mock_weaviate_client,
        sample_document
    ):
        """Test update modifies document in both databases."""
        updated_document = sample_document.model_copy()
        updated_document.title = "Updated Title"
        
        mock_neo4j_client.update_node = AsyncMock(
            return_value=updated_document.model_dump()
        )
        mock_weaviate_client.save_entity = AsyncMock()
        
        result = await document_repository.update(updated_document)
        
        # Verify Neo4j update
        mock_neo4j_client.update_node.assert_called_once()
        
        # Verify Weaviate update
        mock_weaviate_client.save_entity.assert_called_once()
        
        assert result.title == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_raises_not_found_for_missing_document(
        self,
        document_repository,
        mock_neo4j_client,
        sample_document
    ):
        """Test update raises EntityNotFoundError for missing document."""
        mock_neo4j_client.update_node = AsyncMock(
            side_effect=Exception("Node not found")
        )
        
        with pytest.raises(EntityNotFoundError):
            await document_repository.update(sample_document)

    @pytest.mark.asyncio
    async def test_delete_removes_from_both_databases(
        self,
        document_repository,
        mock_neo4j_client,
        mock_weaviate_client
    ):
        """Test delete removes document from both databases."""
        document_id = str(uuid4())
        
        mock_neo4j_client.delete_node = AsyncMock(return_value=True)
        mock_weaviate_client.delete_entity = AsyncMock()
        
        result = await document_repository.delete(document_id)
        
        mock_neo4j_client.delete_node.assert_called_once_with(
            document_id, 'Document'
        )
        mock_weaviate_client.delete_entity.assert_called_once_with(
            'Document', document_id
        )
        
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_returns_false_for_missing_document(
        self,
        document_repository,
        mock_neo4j_client,
        mock_weaviate_client
    ):
        """Test delete returns False for non-existent document."""
        document_id = str(uuid4())
        
        mock_neo4j_client.delete_node = AsyncMock(return_value=False)
        mock_weaviate_client.delete_entity = AsyncMock()
        
        result = await document_repository.delete(document_id)
        
        assert result is False


class TestDocumentRepositorySearchOperations:
    """Test search operations specific to DocumentRepository."""

    @pytest.fixture
    def mock_neo4j_client(self):
        """Provide mock Neo4j client."""
        return MagicMock(spec=Neo4jClient)

    @pytest.fixture
    def mock_weaviate_client(self):
        """Provide mock Weaviate client."""
        return MagicMock(spec=WeaviateClient)

    @pytest.fixture
    def document_repository(self, mock_neo4j_client, mock_weaviate_client):
        """Provide DocumentRepository instance."""
        return DocumentRepository(
            neo4j_client=mock_neo4j_client,
            weaviate_client=mock_weaviate_client
        )

    @pytest.fixture
    def sample_documents(self):
        """Provide sample documents for search testing."""
        return [
            Document(
                id=uuid4(),
                title="The Republic", 
                author="Plato",
                content="Justice is the excellence..."
            ),
            Document(
                id=uuid4(),
                title="Nicomachean Ethics",
                author="Aristotle", 
                content="Virtue is a disposition..."
            )
        ]

    @pytest.mark.asyncio
    async def test_search_by_text_uses_weaviate(
        self,
        document_repository,
        mock_weaviate_client,
        sample_documents
    ):
        """Test search_by_text uses Weaviate for semantic search."""
        mock_weaviate_client.search_near_text = AsyncMock(
            return_value=[doc.model_dump() for doc in sample_documents]
        )
        
        results = await document_repository.search_by_text(
            "justice and virtue", 
            limit=5,
            similarity_threshold=0.8
        )
        
        mock_weaviate_client.search_near_text.assert_called_once_with(
            collection='Document',
            query='justice and virtue',
            limit=5,
            certainty=0.8
        )
        
        assert len(results) == 2
        assert results[0].title == "The Republic"

    @pytest.mark.asyncio
    async def test_search_by_embedding_uses_weaviate(
        self,
        document_repository,
        mock_weaviate_client,
        sample_documents
    ):
        """Test search_by_embedding uses Weaviate vector search."""
        test_embedding = [0.1, 0.2, 0.3] * 128  # Mock 384-dim embedding
        mock_weaviate_client.search_near_vector = AsyncMock(
            return_value=[sample_documents[0].model_dump()]
        )
        
        results = await document_repository.search_by_embedding(
            test_embedding,
            limit=3,
            similarity_threshold=0.9
        )
        
        mock_weaviate_client.search_near_vector.assert_called_once_with(
            collection='Document',
            vector=test_embedding,
            limit=3,
            certainty=0.9
        )
        
        assert len(results) == 1
        assert results[0].title == "The Republic"

    @pytest.mark.asyncio
    async def test_get_by_title_queries_neo4j(
        self,
        document_repository,
        mock_neo4j_client,
        sample_documents
    ):
        """Test get_by_title queries Neo4j for title matches."""
        mock_neo4j_client.query = AsyncMock(
            return_value=[{"d": sample_documents[0].model_dump()}]
        )
        
        results = await document_repository.get_by_title("The Republic")
        
        # Verify Cypher query was called
        mock_neo4j_client.query.assert_called_once()
        query_call = mock_neo4j_client.query.call_args[0][0]
        assert "MATCH (d:Document)" in query_call
        assert "d.title" in query_call
        
        assert len(results) == 1
        assert results[0].title == "The Republic"

    @pytest.mark.asyncio
    async def test_get_by_author_queries_neo4j(
        self,
        document_repository,
        mock_neo4j_client,
        sample_documents
    ):
        """Test get_by_author queries Neo4j for author matches."""
        plato_docs = [sample_documents[0]]
        mock_neo4j_client.query = AsyncMock(
            return_value=[{"d": doc.model_dump()} for doc in plato_docs]
        )
        
        results = await document_repository.get_by_author("Plato")
        
        # Verify Cypher query
        mock_neo4j_client.query.assert_called_once()
        query_call = mock_neo4j_client.query.call_args[0][0]
        assert "MATCH (d:Document)" in query_call
        assert "d.author" in query_call
        
        assert len(results) == 1
        assert results[0].author == "Plato"

    @pytest.mark.asyncio
    async def test_search_content_combines_neo4j_and_weaviate(
        self,
        document_repository,
        mock_neo4j_client,
        mock_weaviate_client,
        sample_documents
    ):
        """Test search_content uses hybrid approach."""
        # Mock Neo4j keyword search
        mock_neo4j_client.query = AsyncMock(
            return_value=[{"d": sample_documents[0].model_dump()}]
        )
        
        # Mock Weaviate semantic search  
        mock_weaviate_client.search_near_text = AsyncMock(
            return_value=[sample_documents[1].model_dump()]
        )
        
        results = await document_repository.search_content(
            "virtue and excellence"
        )
        
        # Both databases should be queried
        mock_neo4j_client.query.assert_called_once()
        mock_weaviate_client.search_near_text.assert_called_once()
        
        # Results should be merged (exact logic will be implementation-specific)
        assert len(results) >= 1


class TestDocumentRepositoryErrorHandling:
    """Test error handling in DocumentRepository."""

    @pytest.fixture
    def mock_neo4j_client(self):
        """Provide mock Neo4j client for error testing."""
        return MagicMock(spec=Neo4jClient)

    @pytest.fixture
    def mock_weaviate_client(self):
        """Provide mock Weaviate client for error testing."""
        return MagicMock(spec=WeaviateClient)

    @pytest.fixture
    def document_repository(self, mock_neo4j_client, mock_weaviate_client):
        """Provide DocumentRepository for error testing."""
        return DocumentRepository(
            neo4j_client=mock_neo4j_client,
            weaviate_client=mock_weaviate_client
        )

    @pytest.fixture
    def sample_document(self):
        """Provide sample document for error testing."""
        return Document(
            id=uuid4(),
            title="Test Document",
            author="Test Author",
            content="Test content"
        )

    @pytest.mark.asyncio
    async def test_create_handles_neo4j_failures(
        self,
        document_repository,
        mock_neo4j_client,
        mock_weaviate_client,
        sample_document
    ):
        """Test create handles Neo4j database failures gracefully."""
        mock_neo4j_client.create_node = AsyncMock(
            side_effect=Exception("Database connection failed")
        )
        
        with pytest.raises(RepositoryError) as exc_info:
            await document_repository.create(sample_document)
        
        assert "Database connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_handles_weaviate_failures(
        self,
        document_repository,
        mock_neo4j_client,
        mock_weaviate_client,
        sample_document
    ):
        """Test create handles Weaviate failures gracefully."""
        # Neo4j succeeds
        mock_neo4j_client.create_node = AsyncMock(
            return_value=sample_document.model_dump()
        )
        
        # Weaviate fails
        mock_weaviate_client.save_entity = AsyncMock(
            side_effect=Exception("Vector store unavailable")
        )
        
        with pytest.raises(RepositoryError) as exc_info:
            await document_repository.create(sample_document)
        
        assert "Vector store unavailable" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_handles_weaviate_unavailable(
        self,
        document_repository,
        mock_weaviate_client
    ):
        """Test search gracefully handles Weaviate being unavailable."""
        mock_weaviate_client.search_near_text = AsyncMock(
            side_effect=Exception("Weaviate service unavailable")
        )
        
        with pytest.raises(RepositoryError):
            await document_repository.search_by_text("test query")