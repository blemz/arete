"""
Focused TDD tests for Weaviate vector database client.

Following proven TDD Red-Green-Refactor methodology from Neo4j client success.
These tests define the essential Weaviate client interface needed for Graph-RAG.

Focus Areas (RED phase):
- Core client operations with configuration integration
- Context manager support for resource management  
- Document operations for vector storage and retrieval
- Entity operations for semantic search
- Batch processing for efficient ingestion
- Essential error handling for Graph-RAG scenarios

Target: ~300 lines of focused tests, not comprehensive Weaviate API coverage.
Test our client contract, not Weaviate's internal behavior.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest
from weaviate.exceptions import (
    AuthenticationFailedException,
    WeaviateConnectionError,
    WeaviateBaseError,
)

from arete.config import get_settings
from arete.models.document import Document
from arete.models.entity import Entity, EntityType
from arete.database.exceptions import DatabaseConnectionError, DatabaseQueryError


class TestWeaviateClientCore:
    """Test suite for WeaviateClient core functionality."""
    
    def test_client_initialization_with_config(self):
        """Test client initialization with configuration integration."""
        from arete.database.weaviate_client import WeaviateClient
        
        client = WeaviateClient()
        
        assert client is not None
        assert client.url == get_settings().weaviate_url
        assert client.client is None  # Not connected yet
        assert not hasattr(client, 'is_connected') or client.is_connected is False
        
    def test_client_initialization_custom_params(self):
        """Test client initialization with custom parameters."""
        from arete.database.weaviate_client import WeaviateClient
        
        custom_url = "http://localhost:8081"
        custom_headers = {"Authorization": "Bearer test"}
        
        client = WeaviateClient(url=custom_url, headers=custom_headers)
        
        assert client.url == custom_url
        assert client.headers == custom_headers
        
    def test_client_connect_success(self):
        """Test successful connection to Weaviate."""
        from arete.database.weaviate_client import WeaviateClient
        
        with patch('weaviate.connect_to_local') as mock_connect:
            mock_client = MagicMock()
            mock_client.is_ready.return_value = True
            mock_connect.return_value = mock_client
            
            client = WeaviateClient()
            client.connect()
            
            assert client.client is mock_client
            mock_connect.assert_called_once()
            
    def test_client_connect_failure(self):
        """Test connection failure handling."""
        from arete.database.weaviate_client import WeaviateClient
        
        with patch('weaviate.connect_to_local') as mock_connect:
            mock_connect.side_effect = WeaviateConnectionError("Connection failed")
            
            client = WeaviateClient()
            
            with pytest.raises(DatabaseConnectionError):
                client.connect()
                
    def test_health_check_connected(self):
        """Test health check when connected."""
        from arete.database.weaviate_client import WeaviateClient
        
        with patch('weaviate.connect_to_local') as mock_connect:
            mock_client = MagicMock()
            mock_client.is_ready.return_value = True
            mock_connect.return_value = mock_client
            
            client = WeaviateClient()
            client.connect()
            
            assert client.health_check() is True
            
    def test_health_check_disconnected(self):
        """Test health check when not connected."""
        from arete.database.weaviate_client import WeaviateClient
        
        client = WeaviateClient()
        
        assert client.health_check() is False


class TestWeaviateContextManager:
    """Test context manager functionality."""
    
    def test_sync_context_manager(self):
        """Test synchronous context manager."""
        from arete.database.weaviate_client import WeaviateClient
        
        with patch('weaviate.connect_to_local') as mock_connect:
            mock_client = MagicMock()
            mock_client.is_ready.return_value = True
            mock_connect.return_value = mock_client
            
            client = WeaviateClient()
            
            with client as ctx_client:
                assert ctx_client is client
                assert client.client is mock_client
                
            # Should close on exit
            mock_client.close.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test asynchronous context manager."""
        from arete.database.weaviate_client import WeaviateClient
        
        with patch('weaviate.connect_to_local') as mock_connect:
            mock_client = MagicMock()
            mock_client.is_ready.return_value = True
            mock_connect.return_value = mock_client
            
            client = WeaviateClient()
            
            async with client as ctx_client:
                assert ctx_client is client
                assert client.client is mock_client
                
            # Should close on exit
            mock_client.close.assert_called_once()


class TestWeaviateDocumentOperations:
    """Test Document model operations for Graph-RAG."""
    
    def test_save_document_success(self):
        """Test saving Document to Weaviate."""
        from arete.database.weaviate_client import WeaviateClient
        
        # Create test document
        doc = Document(
            id=str(uuid.uuid4()),
            title="Republic",
            author="Plato",
            content="The famous cave allegory...",
            language="English",
            created_at=datetime.now(),
            metadata={"source": "test"}
        )
        
        with patch('weaviate.connect_to_local') as mock_connect:
            mock_client = MagicMock()
            mock_client.is_ready.return_value = True
            mock_collection = MagicMock()
            mock_client.collections.get.return_value = mock_collection
            mock_collection.data.insert.return_value = MagicMock(uuid=doc.id)
            mock_connect.return_value = mock_client
            
            client = WeaviateClient()
            client.connect()
            
            result_id = client.save_document(doc)
            
            assert result_id == str(doc.id)
            mock_collection.data.insert.assert_called_once()
            
    def test_get_document_by_id_success(self):
        """Test retrieving Document by ID."""
        from arete.database.weaviate_client import WeaviateClient
        
        doc_id = str(uuid.uuid4())
        
        with patch('weaviate.connect_to_local') as mock_connect:
            mock_client = MagicMock()
            mock_client.is_ready.return_value = True
            mock_collection = MagicMock()
            mock_client.collections.get.return_value = mock_collection
            
            # Mock document data from Weaviate
            mock_doc_data = MagicMock()
            mock_doc_data.uuid = doc_id
            mock_doc_data.properties = {
                'title': 'Republic',
                'author': 'Plato',
                'content': 'The famous cave allegory...',
                'language': 'English',
                'created_at': datetime.now().isoformat(),
                'metadata': {'source': 'test'},
                'neo4j_id': None
            }
            mock_collection.query.fetch_object_by_id.return_value = mock_doc_data
            mock_connect.return_value = mock_client
            
            client = WeaviateClient()
            client.connect()
            
            document = client.get_document_by_id(doc_id)
            
            assert document is not None
            assert str(document.id) == doc_id
            assert document.title == 'Republic'
            assert document.author == 'Plato'
            
    def test_get_document_by_id_not_found(self):
        """Test retrieving non-existent Document."""
        from arete.database.weaviate_client import WeaviateClient
        
        with patch('weaviate.connect_to_local') as mock_connect:
            mock_client = MagicMock()
            mock_client.is_ready.return_value = True
            mock_collection = MagicMock()
            mock_client.collections.get.return_value = mock_collection
            mock_collection.query.fetch_object_by_id.return_value = None
            mock_connect.return_value = mock_client
            
            client = WeaviateClient()
            client.connect()
            
            document = client.get_document_by_id("nonexistent-id")
            
            assert document is None
            
    def test_search_documents_by_text(self):
        """Test semantic search for documents."""
        from arete.database.weaviate_client import WeaviateClient
        
        with patch('weaviate.connect_to_local') as mock_connect:
            mock_client = MagicMock()
            mock_client.is_ready.return_value = True
            mock_collection = MagicMock()
            mock_client.collections.get.return_value = mock_collection
            
            # Mock search results
            mock_result = MagicMock()
            mock_result.objects = [
                MagicMock(
                    uuid=str(uuid.uuid4()),
                    properties={
                        'title': 'Republic',
                        'author': 'Plato',
                        'content': 'Justice and the ideal state',
                        'language': 'English',
                        'created_at': datetime.now().isoformat(),
                        'metadata': {},
                        'neo4j_id': None
                    },
                    metadata=MagicMock(score=0.85)
                )
            ]
            mock_collection.query.near_text.return_value = mock_result
            mock_connect.return_value = mock_client
            
            client = WeaviateClient()
            client.connect()
            
            results = client.search_documents_by_text("justice", limit=5)
            
            assert len(results) == 1
            assert results[0]['document'].title == 'Republic'
            assert results[0]['score'] == 0.85


class TestWeaviateBatchOperations:
    """Test batch operations for efficient document processing."""
    
    def test_batch_save_documents(self):
        """Test batch saving multiple documents."""
        from arete.database.weaviate_client import WeaviateClient
        
        # Create test documents
        docs = [
            Document(
                id=str(uuid.uuid4()),
                title=f"Document {i}",
                author="Test Author",
                content=f"Content for document {i}",
                language="English",
                created_at=datetime.now(),
                metadata={}
            ) for i in range(3)
        ]
        
        with patch('weaviate.connect_to_local') as mock_connect:
            mock_client = MagicMock()
            mock_client.is_ready.return_value = True
            mock_batch = MagicMock()
            mock_client.batch = mock_batch
            mock_batch.__enter__ = Mock(return_value=mock_batch)
            mock_batch.__exit__ = Mock(return_value=None)
            mock_collection = MagicMock()
            mock_client.collections.get.return_value = mock_collection
            mock_connect.return_value = mock_client
            
            client = WeaviateClient()
            client.connect()
            
            result_ids = client.batch_save_documents(docs)
            
            assert len(result_ids) == 3
            # Verify batch was used
            mock_batch.__enter__.assert_called_once()
            mock_batch.__exit__.assert_called_once()


class TestWeaviateEntityOperations:
    """Test Entity model operations."""
    
    def test_save_entity_success(self):
        """Test saving Entity to Weaviate."""
        from arete.database.weaviate_client import WeaviateClient
        
        entity = Entity(
            id=str(uuid.uuid4()),
            name="Socrates",
            entity_type=EntityType.PERSON,
            description="Ancient Greek philosopher",
            properties={"birth_year": "470 BCE"},
            confidence=0.95,
            source_document_id=str(uuid.uuid4())  # Required field
        )
        
        with patch('weaviate.connect_to_local') as mock_connect:
            mock_client = MagicMock()
            mock_client.is_ready.return_value = True
            mock_collection = MagicMock()
            mock_client.collections.get.return_value = mock_collection
            mock_collection.data.insert.return_value = MagicMock(uuid=entity.id)
            mock_connect.return_value = mock_client
            
            client = WeaviateClient()
            client.connect()
            
            result_id = client.save_entity(entity)
            
            assert result_id == str(entity.id)
            mock_collection.data.insert.assert_called_once()


class TestWeaviateErrorHandling:
    """Test error handling for Graph-RAG scenarios."""
    
    def test_connection_error_handling(self):
        """Test handling of connection errors."""
        from arete.database.weaviate_client import WeaviateClient
        
        with patch('weaviate.connect_to_local') as mock_connect:
            mock_connect.side_effect = WeaviateConnectionError("Server unavailable")
            
            client = WeaviateClient()
            
            with pytest.raises(DatabaseConnectionError) as exc_info:
                client.connect()
                
            assert "Server unavailable" in str(exc_info.value)
            
    def test_authentication_error_handling(self):
        """Test handling of authentication errors."""
        from arete.database.weaviate_client import WeaviateClient
        
        with patch('weaviate.connect_to_local') as mock_connect:
            mock_connect.side_effect = AuthenticationFailedException("Invalid token")
            
            client = WeaviateClient()
            
            with pytest.raises(DatabaseConnectionError) as exc_info:
                client.connect()
                
            assert "Invalid token" in str(exc_info.value)
            
    def test_query_error_handling(self):
        """Test handling of query errors."""
        from arete.database.weaviate_client import WeaviateClient
        
        with patch('weaviate.connect_to_local') as mock_connect:
            mock_client = MagicMock()
            mock_client.is_ready.return_value = True
            mock_collection = MagicMock()
            mock_client.collections.get.return_value = mock_collection
            mock_collection.query.fetch_object_by_id.side_effect = WeaviateBaseError("Query failed")
            mock_connect.return_value = mock_client
            
            client = WeaviateClient()
            client.connect()
            
            with pytest.raises(DatabaseQueryError) as exc_info:
                client.get_document_by_id("test-id")
                
            assert "Query failed" in str(exc_info.value)