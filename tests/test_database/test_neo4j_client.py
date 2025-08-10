"""
Comprehensive tests for Neo4j database client.

Following TDD principles - these tests define the expected interface and behavior
of the Neo4j client before implementation. Tests cover all critical functionality:

- Connection management and health checks
- Session context manager functionality
- Error handling and retry logic
- Integration with Document and Entity models
- Transaction management
- Connection pooling behavior
- Configuration integration

Test Categories:
- TestNeo4jClient: Basic client functionality
- TestHealthCheck: Database connectivity and health monitoring  
- TestSessionManagement: Context manager and session handling
- TestModelIntegration: Document/Entity database operations
- TestErrorHandling: Connection failures, retries, timeouts
- TestTransactions: ACID transaction management
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from neo4j import Driver, Session, Transaction
from neo4j.exceptions import (
    AuthError,
    CypherSyntaxError,
    DatabaseError, 
    Neo4jError,
    ServiceUnavailable,
    SessionExpired,
    TransientError,
)
from pydantic import ValidationError

from arete.config import get_settings
from arete.models.document import Document
from arete.models.entity import Entity, EntityType
from arete.database.exceptions import CypherError


class TestNeo4jClient:
    """Test suite for Neo4jClient basic functionality."""

    def test_client_initialization_with_default_config(self):
        """Test client initialization with default configuration."""
        from arete.database.client import Neo4jClient
        
        client = Neo4jClient()
        
        assert client is not None
        assert client.uri == get_settings().neo4j_uri
        assert client.auth == get_settings().neo4j_auth
        assert client.driver is None  # Not connected yet
        assert client.is_connected is False
        
    def test_client_initialization_with_custom_config(self):
        """Test client initialization with custom configuration."""
        from arete.database.client import Neo4jClient
        
        custom_uri = "bolt://custom.neo4j.com:7687"
        custom_auth = ("custom_user", "custom_pass")
        
        client = Neo4jClient(uri=custom_uri, auth=custom_auth)
        
        assert client.uri == custom_uri
        assert client.auth == custom_auth
        assert client.driver is None
        assert client.is_connected is False
        
    def test_client_string_representation(self):
        """Test client string representation for debugging."""
        from arete.database.client import Neo4jClient
        
        client = Neo4jClient()
        client_str = str(client)
        client_repr = repr(client)
        
        assert "Neo4jClient" in client_str
        assert client.uri in client_str
        assert "password" not in client_str.lower()  # Security: no password in string
        assert "Neo4jClient" in client_repr
        assert client.uri in client_repr
        
    @pytest.mark.asyncio
    async def test_async_connect_success(self):
        """Test successful async database connection."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.AsyncGraphDatabase.driver') as mock_driver_factory:
            mock_driver = MagicMock()
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            await client.async_connect()
            
            assert client.driver == mock_driver
            assert client.is_connected is True
            mock_driver_factory.assert_called_once_with(
                client.uri, auth=client.auth
            )
            
    @pytest.mark.asyncio
    async def test_async_connect_failure(self):
        """Test async connection failure handling."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.AsyncGraphDatabase.driver') as mock_driver_factory:
            mock_driver_factory.side_effect = ServiceUnavailable("Database unavailable")
            
            client = Neo4jClient()
            
            with pytest.raises(ServiceUnavailable):
                await client.async_connect()
            
            assert client.driver is None
            assert client.is_connected is False
            
    def test_sync_connect_success(self):
        """Test successful sync database connection."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.GraphDatabase.driver') as mock_driver_factory:
            mock_driver = Mock()
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            client.connect()
            
            assert client.driver == mock_driver
            assert client.is_connected is True
            mock_driver_factory.assert_called_once_with(
                client.uri, auth=client.auth
            )
            
    def test_sync_connect_failure(self):
        """Test sync connection failure handling."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.GraphDatabase.driver') as mock_driver_factory:
            mock_driver_factory.side_effect = AuthError("Invalid credentials")
            
            client = Neo4jClient()
            
            with pytest.raises(AuthError):
                client.connect()
            
            assert client.driver is None
            assert client.is_connected is False
            
    @pytest.mark.asyncio
    async def test_async_close_connection(self):
        """Test async connection closing."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.AsyncGraphDatabase.driver') as mock_driver_factory:
            mock_driver = AsyncMock()  # FIX: Use AsyncMock for awaitable methods
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            await client.async_connect()
            await client.async_close()
            
            assert client.driver is None
            assert client.is_connected is False
            mock_driver.close.assert_awaited_once()  # FIX: Use assert_awaited_once for AsyncMock
            
    def test_sync_close_connection(self):
        """Test sync connection closing."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.GraphDatabase.driver') as mock_driver_factory:
            mock_driver = Mock()
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            client.connect()
            client.close()
            
            assert client.driver is None
            assert client.is_connected is False
            mock_driver.close.assert_called_once()
            
    def test_context_manager_sync(self):
        """Test sync context manager functionality."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.GraphDatabase.driver') as mock_driver_factory:
            mock_driver = Mock()
            mock_driver_factory.return_value = mock_driver
            
            with Neo4jClient() as client:
                assert client.is_connected is True
                assert client.driver == mock_driver
                
            mock_driver.close.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_context_manager_async(self):
        """Test async context manager functionality."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.AsyncGraphDatabase.driver') as mock_driver_factory:
            mock_driver = AsyncMock()  # FIX: Use AsyncMock for awaitable methods
            mock_driver_factory.return_value = mock_driver
            
            async with Neo4jClient() as client:
                assert client.is_connected is True
                assert client.driver == mock_driver
                
            mock_driver.close.assert_awaited_once()  # FIX: Use assert_awaited_once for AsyncMock


class TestHealthCheck:
    """Test suite for database health monitoring."""
    
    @pytest.mark.asyncio
    async def test_async_health_check_success(self):
        """Test successful async health check."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.AsyncGraphDatabase.driver') as mock_driver_factory:
            mock_driver = MagicMock()  # Use regular Mock for driver
            mock_session = AsyncMock()
            mock_result = AsyncMock()
            mock_record = MagicMock()
            # Mock record access for "1" key specifically
            mock_record.__getitem__.side_effect = lambda key: 1 if key == "1" else None
            mock_record.data.return_value = {"1": 1}
            
            mock_result.single = AsyncMock(return_value=mock_record)
            mock_session.run = AsyncMock(return_value=mock_result)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_driver.session = MagicMock(return_value=mock_session)
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            await client.async_connect()
            
            health_result = await client.async_health_check()
            
            assert health_result is True
            mock_session.run.assert_called_once_with("RETURN 1")
            
    @pytest.mark.asyncio
    async def test_async_health_check_failure(self):
        """Test async health check failure."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.AsyncGraphDatabase.driver') as mock_driver_factory:
            mock_driver = MagicMock()
            mock_session = AsyncMock()
            mock_session.run.side_effect = ServiceUnavailable("Connection lost")
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_driver.session = MagicMock(return_value=mock_session)
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            await client.async_connect()
            
            health_result = await client.async_health_check()
            
            assert health_result is False
            
    def test_sync_health_check_success(self):
        """Test successful sync health check."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.GraphDatabase.driver') as mock_driver_factory:
            mock_driver = Mock()
            mock_session = Mock()
            mock_result = Mock()
            mock_record = MagicMock()
            # Mock record access for "1" key specifically  
            mock_record.__getitem__.side_effect = lambda key: 1 if key == "1" else None
            mock_record.data.return_value = {"1": 1}
            
            mock_result.single.return_value = mock_record
            mock_session.run.return_value = mock_result
            mock_driver.session.return_value.__enter__.return_value = mock_session
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            client.connect()
            
            health_result = client.health_check()
            
            assert health_result is True
            mock_session.run.assert_called_once_with("RETURN 1")
            
    def test_sync_health_check_failure(self):
        """Test sync health check failure."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.GraphDatabase.driver') as mock_driver_factory:
            mock_driver = Mock()
            mock_session = Mock()
            mock_session.run.side_effect = DatabaseError("Query failed")
            mock_driver.session.return_value.__enter__.return_value = mock_session
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            client.connect()
            
            health_result = client.health_check()
            
            assert health_result is False
            
    @pytest.mark.asyncio
    async def test_async_health_check_not_connected(self):
        """Test async health check when not connected."""
        from arete.database.client import Neo4jClient
        
        client = Neo4jClient()
        
        health_result = await client.async_health_check()
        
        assert health_result is False
        
    def test_sync_health_check_not_connected(self):
        """Test sync health check when not connected."""
        from arete.database.client import Neo4jClient
        
        client = Neo4jClient()
        
        health_result = client.health_check()
        
        assert health_result is False
        
    @pytest.mark.asyncio
    async def test_async_detailed_health_check(self):
        """Test detailed async health check with metrics."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.AsyncGraphDatabase.driver') as mock_driver_factory:
            mock_driver = MagicMock()
            mock_session = AsyncMock()
            mock_result = AsyncMock()
            
            # Mock database information query
            mock_record = MagicMock()
            mock_data = {
                "version": "5.15.0",
                "edition": "community", 
                "nodes": 100,
                "relationships": 200
            }
            mock_record.__getitem__.side_effect = lambda key: mock_data[key]
            mock_record.data.return_value = mock_data
            
            mock_result.single = AsyncMock(return_value=mock_record)
            mock_session.run = AsyncMock(return_value=mock_result)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_driver.session = MagicMock(return_value=mock_session)
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            await client.async_connect()
            
            health_info = await client.async_detailed_health_check()
            
            assert health_info["connected"] is True
            assert health_info["version"] == "5.15.0"
            assert health_info["edition"] == "community"
            assert health_info["node_count"] == 100
            assert health_info["relationship_count"] == 200
            assert "response_time_ms" in health_info


class TestSessionManagement:
    """Test suite for session management and context handling."""
    
    def test_get_session_sync(self):
        """Test getting synchronous session."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.GraphDatabase.driver') as mock_driver_factory:
            mock_driver = Mock()
            mock_session = Mock()
            mock_driver.session.return_value = mock_session
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            client.connect()
            
            session = client.get_session()
            
            assert session == mock_session
            mock_driver.session.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_get_async_session(self):
        """Test getting asynchronous session."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.AsyncGraphDatabase.driver') as mock_driver_factory:
            mock_driver = MagicMock()
            mock_session = AsyncMock()
            mock_driver.session.return_value = mock_session
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            await client.async_connect()
            
            session = await client.get_async_session()
            
            assert session == mock_session
            mock_driver.session.assert_called_once()
            
    def test_session_context_manager_sync(self):
        """Test synchronous session context manager."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.GraphDatabase.driver') as mock_driver_factory:
            mock_driver = Mock()
            mock_session = Mock()
            mock_driver.session.return_value.__enter__.return_value = mock_session
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            client.connect()
            
            with client.session() as session:
                assert session == mock_session
                
            # Verify session was properly closed through context manager
            mock_driver.session.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_session_context_manager_async(self):
        """Test asynchronous session context manager."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.AsyncGraphDatabase.driver') as mock_driver_factory:
            mock_driver = MagicMock()
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_driver.session = MagicMock(return_value=mock_session)
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            await client.async_connect()
            
            async with client.async_session() as session:
                assert session == mock_session
                
            # Verify session was properly closed through context manager
            mock_driver.session.assert_called_once()
            
    def test_session_with_database_parameter(self):
        """Test session creation with specific database parameter."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.GraphDatabase.driver') as mock_driver_factory:
            mock_driver = Mock()
            mock_session = Mock()
            mock_driver.session.return_value = mock_session
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            client.connect()
            
            session = client.get_session(database="arete")
            
            assert session == mock_session
            mock_driver.session.assert_called_once_with(database="arete")
            
    def test_multiple_concurrent_sessions(self):
        """Test creating multiple concurrent sessions."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.GraphDatabase.driver') as mock_driver_factory:
            mock_driver = Mock()
            mock_session1 = Mock()
            mock_session2 = Mock()
            mock_driver.session.side_effect = [mock_session1, mock_session2]
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            client.connect()
            
            session1 = client.get_session()
            session2 = client.get_session()
            
            assert session1 == mock_session1
            assert session2 == mock_session2
            assert session1 != session2
            assert mock_driver.session.call_count == 2


class TestModelIntegration:
    """Test suite for Document and Entity model database operations."""
    
    @pytest.fixture
    def sample_document(self):
        """Fixture providing sample document for testing."""
        return Document(
            title="Republic",
            author="Plato", 
            content="Justice is the excellence of the soul and governs the harmony of all virtues.",
            language="English",
            source="Perseus Digital Library",
            translator="Benjamin Jowett",
            publication_year=-380
        )
        
    @pytest.fixture 
    def sample_entity(self):
        """Fixture providing sample entity for testing."""
        document_id = uuid.uuid4()
        return Entity(
            name="Socrates",
            entity_type=EntityType.PERSON,
            confidence=0.95,
            description="Classical Greek philosopher",
            source_document_id=document_id
        )
        
    @pytest.mark.asyncio
    async def test_async_save_document(self, sample_document):
        """Test async document saving to Neo4j."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.AsyncGraphDatabase.driver') as mock_driver_factory:
            mock_driver = MagicMock()
            mock_session = AsyncMock()
            mock_result = AsyncMock()
            mock_record = MagicMock()
            doc_data = {"id": str(sample_document.id)}
            mock_record.__getitem__.return_value = doc_data
            mock_record.data.return_value = {"d": doc_data}
            
            mock_result.single = AsyncMock(return_value=mock_record)
            mock_session.run = AsyncMock(return_value=mock_result)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_driver.session = MagicMock(return_value=mock_session)
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            await client.async_connect()
            
            result = await client.async_save_document(sample_document)
            
            assert result["id"] == str(sample_document.id)
            # Verify the Cypher query includes document properties
            call_args = mock_session.run.call_args
            cypher_query = call_args[0][0]
            assert "CREATE (d:Document" in cypher_query
            assert "RETURN d" in cypher_query
            
            # Verify document data passed correctly
            params = call_args[1]
            assert "doc_data" in params
            doc_data = params["doc_data"]
            assert doc_data["title"] == "Republic"
            assert doc_data["author"] == "Plato"
            
    def test_sync_save_document(self, sample_document):
        """Test sync document saving to Neo4j."""
        from arete.database.client import Neo4jClient
        
        # FIX: Use the proper Neo4j mocking pattern from guidance
        with patch('neo4j.GraphDatabase.driver') as mock_driver_factory:
            mock_driver = MagicMock()  # Need MagicMock for context manager support
            mock_session = Mock()  
            doc_data = {"id": str(sample_document.id)}
            
            # FIX: Configure the mock chain correctly for Neo4j client pattern:
            # session.run() -> result.single() -> record["d"] -> doc_data
            mock_result = Mock()
            mock_record = {"d": doc_data}  # Use real dict for record
            mock_result.single.return_value = mock_record
            mock_session.run.return_value = mock_result
            
            # FIX: Properly configure context manager for sync operations
            mock_driver.session.return_value.__enter__.return_value = mock_session
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            client.connect()
            
            result = client.save_document(sample_document)
            
            # The save_document method should return the document data
            assert result["id"] == str(sample_document.id)
            # Verify the Cypher query was executed
            mock_session.run.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_async_save_entity(self, sample_entity):
        """Test async entity saving to Neo4j."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.AsyncGraphDatabase.driver') as mock_driver_factory:
            mock_driver = MagicMock()
            mock_session = AsyncMock()
            mock_result = AsyncMock()
            mock_record = MagicMock()
            entity_data = {"id": str(sample_entity.id)}
            mock_record.__getitem__.return_value = entity_data
            mock_record.data.return_value = {"e": entity_data}
            
            mock_result.single = AsyncMock(return_value=mock_record)
            mock_session.run = AsyncMock(return_value=mock_result)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_driver.session = MagicMock(return_value=mock_session)
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            await client.async_connect()
            
            result = await client.async_save_entity(sample_entity)
            
            assert result["id"] == str(sample_entity.id)
            # Verify the Cypher query includes entity properties
            call_args = mock_session.run.call_args
            cypher_query = call_args[0][0]
            assert "CREATE (e:Entity" in cypher_query
            assert "RETURN e" in cypher_query
            
    def test_sync_save_entity(self, sample_entity):
        """Test sync entity saving to Neo4j."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.GraphDatabase.driver') as mock_driver_factory:
            mock_driver = Mock()
            mock_session = Mock()
            mock_result = Mock()
            mock_record = MagicMock()
            entity_data = {"id": str(sample_entity.id)}
            mock_record.__getitem__.return_value = entity_data
            mock_record.data.return_value = {"e": entity_data}
            
            mock_result.single.return_value = mock_record
            mock_session.run.return_value = mock_result
            mock_driver.session.return_value.__enter__.return_value = mock_session
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            client.connect()
            
            result = client.save_entity(sample_entity)
            
            assert result["id"] == str(sample_entity.id)
            mock_session.run.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_async_get_document_by_id(self, sample_document):
        """Test async document retrieval by ID."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.AsyncGraphDatabase.driver') as mock_driver_factory:
            mock_driver = MagicMock()
            mock_session = AsyncMock()
            mock_result = AsyncMock()
            mock_record = Mock()
            
            # Mock document data from database
            doc_data = sample_document.to_neo4j_dict()
            mock_record.__getitem__.return_value = doc_data
            mock_record.data.return_value = {"d": doc_data}
            mock_result.single = AsyncMock(return_value=mock_record)
            mock_session.run = AsyncMock(return_value=mock_result)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_driver.session = MagicMock(return_value=mock_session)
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            await client.async_connect()
            
            result = await client.async_get_document(sample_document.id)
            
            assert result is not None
            assert result["id"] == str(sample_document.id)
            assert result["title"] == "Republic"
            
            # Verify query structure
            call_args = mock_session.run.call_args
            cypher_query = call_args[0][0]
            assert "MATCH (d:Document" in cypher_query
            assert "WHERE d.id = $doc_id" in cypher_query
            assert "RETURN d" in cypher_query
            
    def test_sync_get_document_by_id(self, sample_document):
        """Test sync document retrieval by ID."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.GraphDatabase.driver') as mock_driver_factory:
            mock_driver = Mock()
            mock_session = Mock()
            mock_result = Mock()
            mock_record = Mock()
            
            doc_data = sample_document.to_neo4j_dict()
            mock_record.__getitem__.return_value = doc_data
            mock_record.data.return_value = {"d": doc_data}
            mock_result.single.return_value = mock_record
            mock_session.run.return_value = mock_result
            mock_driver.session.return_value.__enter__.return_value = mock_session
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            client.connect()
            
            result = client.get_document(sample_document.id)
            
            assert result is not None
            assert result["id"] == str(sample_document.id)
            mock_session.run.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_async_get_entity_by_id(self, sample_entity):
        """Test async entity retrieval by ID."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.AsyncGraphDatabase.driver') as mock_driver_factory:
            mock_driver = MagicMock()
            mock_session = AsyncMock()
            mock_result = AsyncMock()
            mock_record = Mock()
            
            entity_data = sample_entity.to_neo4j_dict()
            mock_record.__getitem__.return_value = entity_data
            mock_record.data.return_value = {"e": entity_data}
            mock_result.single = AsyncMock(return_value=mock_record)
            mock_session.run = AsyncMock(return_value=mock_result)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_driver.session = MagicMock(return_value=mock_session)
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            await client.async_connect()
            
            result = await client.async_get_entity(sample_entity.id)
            
            assert result is not None
            assert result["id"] == str(sample_entity.id)
            assert result["name"] == "Socrates"
            
    def test_sync_get_entity_by_id(self, sample_entity):
        """Test sync entity retrieval by ID."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.GraphDatabase.driver') as mock_driver_factory:
            mock_driver = Mock()
            mock_session = Mock()
            mock_result = Mock()
            mock_record = Mock()
            
            entity_data = sample_entity.to_neo4j_dict()
            mock_record.__getitem__.return_value = entity_data
            mock_record.data.return_value = {"e": entity_data}
            mock_result.single.return_value = mock_record
            mock_session.run.return_value = mock_result
            mock_driver.session.return_value.__enter__.return_value = mock_session
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            client.connect()
            
            result = client.get_entity(sample_entity.id)
            
            assert result is not None
            assert result["id"] == str(sample_entity.id)
            mock_session.run.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_async_document_not_found(self):
        """Test async document retrieval when document doesn't exist."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.AsyncGraphDatabase.driver') as mock_driver_factory:
            mock_driver = MagicMock()
            mock_session = AsyncMock()
            mock_result = AsyncMock()
            mock_result.single = AsyncMock(return_value=None)  # Document not found
            
            mock_session.run = AsyncMock(return_value=mock_result)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_driver.session = MagicMock(return_value=mock_session)
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            await client.async_connect()
            
            nonexistent_id = uuid.uuid4()
            result = await client.async_get_document(nonexistent_id)
            
            assert result is None
            
    def test_sync_entity_not_found(self):
        """Test sync entity retrieval when entity doesn't exist."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.GraphDatabase.driver') as mock_driver_factory:
            mock_driver = Mock()
            mock_session = Mock()
            mock_result = Mock()
            mock_result.single.return_value = None  # Entity not found
            
            mock_session.run.return_value = mock_result
            mock_driver.session.return_value.__enter__.return_value = mock_session
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            client.connect()
            
            nonexistent_id = uuid.uuid4()
            result = client.get_entity(nonexistent_id)
            
            assert result is None
            
    @pytest.mark.asyncio
    async def test_async_batch_save_documents(self):
        """Test async batch saving of multiple documents."""
        from arete.database.client import Neo4jClient
        
        documents = [
            Document(title="Republic", author="Plato", content="Justice is virtue."),
            Document(title="Phaedo", author="Plato", content="The soul is immortal."),
            Document(title="Ethics", author="Aristotle", content="Virtue is excellence.")
        ]
        
        with patch('neo4j.AsyncGraphDatabase.driver') as mock_driver_factory:
            mock_driver = MagicMock()
            mock_session = AsyncMock()
            mock_result = AsyncMock()
            
            # Mock successful batch insert
            created_records = [{"id": str(doc.id)} for doc in documents]
            mock_result.data.return_value = created_records
            mock_session.run = AsyncMock(return_value=mock_result)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_driver.session = MagicMock(return_value=mock_session)
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            await client.async_connect()
            
            results = await client.async_batch_save_documents(documents)
            
            assert len(results) == 3
            assert all("id" in result for result in results)
            
            # Verify batch query execution
            call_args = mock_session.run.call_args
            cypher_query = call_args[0][0]
            assert "UNWIND $documents AS doc" in cypher_query
            assert "CREATE (d:Document" in cypher_query
            
    def test_sync_batch_save_entities(self):
        """Test sync batch saving of multiple entities."""
        from arete.database.client import Neo4jClient
        
        doc_id = uuid.uuid4()
        entities = [
            Entity(name="Socrates", entity_type=EntityType.PERSON, source_document_id=doc_id),
            Entity(name="Justice", entity_type=EntityType.CONCEPT, source_document_id=doc_id),
            Entity(name="Athens", entity_type=EntityType.PLACE, source_document_id=doc_id)
        ]
        
        with patch('neo4j.GraphDatabase.driver') as mock_driver_factory:
            mock_driver = Mock()
            mock_session = Mock()
            mock_result = Mock()
            
            created_records = [{"id": str(entity.id)} for entity in entities]
            mock_result.data.return_value = created_records
            mock_session.run.return_value = mock_result
            mock_driver.session.return_value.__enter__.return_value = mock_session
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            client.connect()
            
            results = client.batch_save_entities(entities)
            
            assert len(results) == 3
            assert all("id" in result for result in results)
            mock_session.run.assert_called_once()


class TestErrorHandling:
    """Test suite for error handling, retries, and timeouts."""
    
    def test_connection_timeout_handling(self):
        """Test handling of connection timeouts."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.GraphDatabase.driver') as mock_driver_factory:
            mock_driver_factory.side_effect = ServiceUnavailable("Connection timeout")
            
            client = Neo4jClient()
            
            with pytest.raises(ServiceUnavailable) as exc_info:
                client.connect()
                
            assert "Connection timeout" in str(exc_info.value)
            assert client.is_connected is False
            
    @pytest.mark.asyncio
    async def test_session_expired_handling(self):
        """Test handling of expired sessions."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.AsyncGraphDatabase.driver') as mock_driver_factory:
            mock_driver = MagicMock()
            mock_session = AsyncMock()
            mock_session.run.side_effect = SessionExpired("Session has expired")
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_driver.session = MagicMock(return_value=mock_session)
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            await client.async_connect()
            
            with pytest.raises(SessionExpired):
                async with client.async_session() as session:
                    await session.run("RETURN 1")
                    
    def test_cypher_error_handling(self):
        """Test handling of Cypher syntax errors."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.GraphDatabase.driver') as mock_driver_factory:
            mock_driver = Mock()
            mock_session = Mock()
            mock_session.run.side_effect = CypherSyntaxError("Invalid Cypher syntax")
            mock_driver.session.return_value.__enter__.return_value = mock_session
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            client.connect()
            
            with pytest.raises(CypherSyntaxError):
                with client.session() as session:
                    session.run("INVALID CYPHER QUERY")
                    
    def test_auth_error_handling(self):
        """Test handling of authentication errors."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.GraphDatabase.driver') as mock_driver_factory:
            mock_driver_factory.side_effect = AuthError("Authentication failed")
            
            client = Neo4jClient()
            
            with pytest.raises(AuthError) as exc_info:
                client.connect()
                
            assert "Authentication failed" in str(exc_info.value)
            assert client.is_connected is False
            
    @pytest.mark.asyncio
    async def test_transient_error_retry(self):
        """Test retry logic for transient errors."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.AsyncGraphDatabase.driver') as mock_driver_factory:
            mock_driver = MagicMock()
            mock_session = AsyncMock()
            
            # First call fails, second succeeds
            mock_session.run.side_effect = [
                TransientError("Temporary failure"),
                AsyncMock()
            ]
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_driver.session = MagicMock(return_value=mock_session)
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            await client.async_connect()
            
            # Should retry and succeed on second attempt
            result = await client.async_run_query_with_retry("RETURN 1", max_retries=2)
            
            assert result is not None
            assert mock_session.run.call_count == 2
            
    def test_max_retries_exceeded(self):
        """Test behavior when max retries are exceeded."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.GraphDatabase.driver') as mock_driver_factory:
            mock_driver = Mock()
            mock_session = Mock()
            mock_session.run.side_effect = TransientError("Persistent failure")
            mock_driver.session.return_value.__enter__.return_value = mock_session
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            client.connect()
            
            with pytest.raises(TransientError):
                client.run_query_with_retry("RETURN 1", max_retries=3)
                
            # Should attempt initial + 3 retries = 4 total attempts
            assert mock_session.run.call_count == 4
            
    @pytest.mark.asyncio
    async def test_database_unavailable_handling(self):
        """Test handling of database unavailable errors."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.AsyncGraphDatabase.driver') as mock_driver_factory:
            mock_driver_factory.side_effect = ServiceUnavailable("Database is unavailable")
            
            client = Neo4jClient()
            
            # Test both initial connection and retry scenarios
            with pytest.raises(ServiceUnavailable):
                await client.async_connect()
                
            assert client.is_connected is False
            
    def test_connection_pool_exhausted(self):
        """Test handling of connection pool exhaustion."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.GraphDatabase.driver') as mock_driver_factory:
            mock_driver = Mock()
            mock_driver.session.side_effect = Neo4jError("Connection pool exhausted")
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            client.connect()
            
            with pytest.raises(Neo4jError) as exc_info:
                client.get_session()
                
            assert "Connection pool exhausted" in str(exc_info.value)
            
    def test_invalid_configuration_error(self):
        """Test handling of invalid configuration parameters."""
        from arete.database.client import Neo4jClient
        
        # Test invalid URI format
        with pytest.raises(ValueError) as exc_info:
            Neo4jClient(uri="invalid-uri-format")
            
        assert "Invalid URI" in str(exc_info.value)
        
        # Test invalid auth format  
        with pytest.raises(ValueError) as exc_info:
            Neo4jClient(auth="invalid-auth")
            
        assert "Invalid authentication" in str(exc_info.value)


class TestTransactions:
    """Test suite for ACID transaction management."""
    
    @pytest.mark.asyncio
    async def test_async_transaction_context_manager(self):
        """Test async transaction context manager."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.AsyncGraphDatabase.driver') as mock_driver_factory:
            mock_driver = MagicMock()
            mock_session = AsyncMock()
            mock_tx = AsyncMock()
            
            mock_session.begin_transaction.return_value.__aenter__.return_value = mock_tx
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_driver.session = MagicMock(return_value=mock_session)
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            await client.async_connect()
            
            async with client.async_transaction() as tx:
                assert tx == mock_tx
                await tx.run("CREATE (n:Node {name: 'test'})")
                
            # Verify transaction was committed
            mock_session.begin_transaction.assert_called_once()
            
    def test_sync_transaction_context_manager(self):
        """Test sync transaction context manager."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.GraphDatabase.driver') as mock_driver_factory:
            mock_driver = Mock()
            mock_session = Mock()
            mock_tx = Mock()
            
            mock_session.begin_transaction.return_value.__enter__.return_value = mock_tx
            mock_driver.session.return_value.__enter__.return_value = mock_session
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            client.connect()
            
            with client.transaction() as tx:
                assert tx == mock_tx
                tx.run("CREATE (n:Node {name: 'test'})")
                
            mock_session.begin_transaction.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_async_transaction_rollback_on_error(self):
        """Test async transaction rollback on error."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.AsyncGraphDatabase.driver') as mock_driver_factory:
            mock_driver = MagicMock()
            mock_session = AsyncMock()
            mock_tx = AsyncMock()
            
            # Configure mock to raise error during transaction
            mock_tx.run.side_effect = CypherSyntaxError("Syntax error")
            mock_session.begin_transaction.return_value.__aenter__.return_value = mock_tx
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_driver.session = MagicMock(return_value=mock_session)
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            await client.async_connect()
            
            with pytest.raises(CypherSyntaxError):
                async with client.async_transaction() as tx:
                    await tx.run("INVALID CYPHER")
                    
            # Transaction should have been rolled back automatically
            mock_session.begin_transaction.assert_called_once()
            
    def test_sync_transaction_rollback_on_error(self):
        """Test sync transaction rollback on error."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.GraphDatabase.driver') as mock_driver_factory:
            mock_driver = Mock()
            mock_session = Mock()
            mock_tx = Mock()
            
            mock_tx.run.side_effect = DatabaseError("Constraint violation")
            mock_session.begin_transaction.return_value.__enter__.return_value = mock_tx
            mock_driver.session.return_value.__enter__.return_value = mock_session
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            client.connect()
            
            with pytest.raises(DatabaseError):
                with client.transaction() as tx:
                    tx.run("CREATE (n:Node)")
                    
            mock_session.begin_transaction.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_async_manual_transaction_control(self):
        """Test manual async transaction control (begin, commit, rollback)."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.AsyncGraphDatabase.driver') as mock_driver_factory:
            mock_driver = MagicMock()
            mock_session = AsyncMock()
            mock_tx = AsyncMock()
            
            mock_session.begin_transaction.return_value = mock_tx
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_driver.session = MagicMock(return_value=mock_session)
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            await client.async_connect()
            
            async with client.async_session() as session:
                tx = await session.begin_transaction()
                await tx.run("CREATE (n:Node {name: 'test'})")
                await tx.commit()
                
            mock_session.begin_transaction.assert_called_once()
            mock_tx.run.assert_called_once()
            mock_tx.commit.assert_called_once()
            
    def test_sync_manual_transaction_control(self):
        """Test manual sync transaction control."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.GraphDatabase.driver') as mock_driver_factory:
            mock_driver = Mock()
            mock_session = Mock()
            mock_tx = Mock()
            
            mock_session.begin_transaction.return_value = mock_tx
            mock_driver.session.return_value.__enter__.return_value = mock_session
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            client.connect()
            
            with client.session() as session:
                tx = session.begin_transaction()
                tx.run("CREATE (n:Node {name: 'test'})")
                tx.commit()
                
            mock_session.begin_transaction.assert_called_once()
            mock_tx.run.assert_called_once()
            mock_tx.commit.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_async_transaction_with_document_operations(self, sample_document):
        """Test async transaction with document operations."""
        from arete.database.client import Neo4jClient
        
        with patch('neo4j.AsyncGraphDatabase.driver') as mock_driver_factory:
            mock_driver = MagicMock()
            mock_session = AsyncMock()
            mock_tx = AsyncMock()
            mock_result = AsyncMock()
            
            # Mock successful document creation
            mock_record = MagicMock()
            doc_data = {"id": str(sample_document.id)}
            mock_record.__getitem__.return_value = doc_data
            mock_record.data.return_value = {"d": doc_data}
            mock_result.single = AsyncMock(return_value=mock_record)
            mock_tx.run.return_value = mock_result
            mock_session.begin_transaction.return_value.__aenter__.return_value = mock_tx
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_driver.session = MagicMock(return_value=mock_session)
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            await client.async_connect()
            
            async with client.async_transaction() as tx:
                result = await client.async_save_document_in_transaction(
                    sample_document, tx
                )
                
            assert result["id"] == str(sample_document.id)
            mock_tx.run.assert_called_once()
            
    def test_sync_transaction_with_batch_operations(self):
        """Test sync transaction with batch operations."""
        from arete.database.client import Neo4jClient
        
        documents = [
            Document(title="Republic", author="Plato", content="Justice is virtue."),
            Document(title="Phaedo", author="Plato", content="Soul is immortal.")
        ]
        
        with patch('neo4j.GraphDatabase.driver') as mock_driver_factory:
            mock_driver = Mock()
            mock_session = Mock()
            mock_tx = Mock()
            mock_result = Mock()
            
            created_records = [{"id": str(doc.id)} for doc in documents]
            mock_result.data.return_value = created_records
            mock_tx.run.return_value = mock_result
            mock_session.begin_transaction.return_value.__enter__.return_value = mock_tx
            mock_driver.session.return_value.__enter__.return_value = mock_session
            mock_driver_factory.return_value = mock_driver
            
            client = Neo4jClient()
            client.connect()
            
            with client.transaction() as tx:
                results = client.batch_save_documents_in_transaction(documents, tx)
                
            assert len(results) == 2
            mock_tx.run.assert_called_once()

            
# FIX: Removed conflicting global sample_document fixture that returned dict instead of Document object
# The class-level fixture in TestModelIntegration properly returns a Document instance


# Integration test markers for real database testing
@pytest.mark.integration
class TestNeo4jClientIntegration:
    """Integration tests that require real Neo4j database connection.
    
    These tests are marked as 'integration' and can be run selectively:
    pytest -m integration
    
    Or excluded from regular test runs:
    pytest -m "not integration"
    """
    
    @pytest.mark.asyncio
    async def test_real_database_connection(self):
        """Test actual connection to Neo4j database."""
        from arete.database.client import Neo4jClient
        
        # This test requires actual Neo4j running
        client = Neo4jClient()
        
        try:
            await client.async_connect()
            assert client.is_connected is True
            
            health_result = await client.async_health_check()
            assert health_result is True
            
        except ServiceUnavailable:
            pytest.skip("Neo4j database not available for integration testing")
        finally:
            await client.async_close()
            
    def test_real_database_document_crud(self):
        """Test real document CRUD operations.""" 
        from arete.database.client import Neo4jClient
        
        document = Document(
            title="Test Document",
            author="Test Author", 
            content="Test content for integration testing."
        )
        
        client = Neo4jClient()
        
        try:
            client.connect()
            
            # Create document
            result = client.save_document(document)
            assert result["id"] == str(document.id)
            
            # Read document
            retrieved = client.get_document(document.id)
            assert retrieved is not None
            assert retrieved["title"] == document.title
            
            # Clean up - delete test document
            with client.session() as session:
                session.run("MATCH (d:Document {id: $id}) DELETE d", id=str(document.id))
                
        except ServiceUnavailable:
            pytest.skip("Neo4j database not available for integration testing")
        finally:
            client.close()