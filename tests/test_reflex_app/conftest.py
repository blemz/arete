"""Shared test fixtures for Reflex app tests."""
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
import reflex as rx
from src.arete.models.chunk import Chunk
from src.arete.models.entity import Entity
from src.arete.services.prompt_template import Citation
from src.arete.ui.reflex_app.state.chat_state import ChatState
from src.arete.ui.reflex_app.state.document_state import DocumentState
from src.arete.ui.reflex_app.state.layout_state import LayoutState


@pytest.fixture
def mock_neo4j_client():
    """Mock Neo4j client."""
    client = Mock()
    client.session = Mock()
    session_mock = Mock()
    session_mock.__enter__ = Mock(return_value=session_mock)
    session_mock.__exit__ = Mock(return_value=None)
    client.session.return_value = session_mock
    return client


@pytest.fixture
def mock_weaviate_client():
    """Mock Weaviate client."""
    client = Mock()
    client.search_by_vector = AsyncMock()
    client.get_chunk = AsyncMock()
    return client


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service."""
    service = Mock()
    service.get_embedding = AsyncMock(return_value=[0.1] * 1536)
    return service


@pytest.fixture
def mock_rag_service(mock_neo4j_client, mock_weaviate_client, mock_embedding_service):
    """Mock RAG service with all dependencies."""
    service = Mock()
    service.neo4j_client = mock_neo4j_client
    service.weaviate_client = mock_weaviate_client
    service.embedding_service = mock_embedding_service
    service.generate_response = AsyncMock()
    service.search_similar_chunks = AsyncMock()
    service.get_related_entities = AsyncMock()
    return service


@pytest.fixture
def sample_chunk():
    """Sample chunk for testing."""
    return Chunk(
        id="chunk_1",
        content="This is a test chunk about virtue and wisdom.",
        metadata={"source": "plato_apology.txt", "page": 1},
        embedding=[0.1] * 1536,
        position=0.0
    )


@pytest.fixture
def sample_entity():
    """Sample entity for testing."""
    return Entity(
        id="entity_1",
        name="Virtue",
        type="Concept",
        description="Moral excellence and righteousness",
        properties={"philosopher": "Aristotle"}
    )


@pytest.fixture
def sample_citation():
    """Sample citation for testing."""
    return Citation(
        chunk_id="chunk_1",
        source_text="This is the cited text",
        relevance_score=0.85,
        page_number=42,
        line_range="10-15"
    )


@pytest.fixture
def chat_state():
    """ChatState instance for testing."""
    return ChatState()


@pytest.fixture
def document_state():
    """DocumentState instance for testing."""
    return DocumentState()


@pytest.fixture
def layout_state():
    """LayoutState instance for testing."""
    return LayoutState()


@pytest.fixture
def mock_chat_response():
    """Mock chat response with citations."""
    return {
        "response": "Virtue, according to Socrates, is a form of knowledge.",
        "citations": [
            {
                "chunk_id": "chunk_1",
                "source_text": "Socrates argues that virtue is knowledge",
                "relevance_score": 0.9,
                "source": "Plato's Meno",
                "position": 145.0
            }
        ],
        "entities": [
            {
                "id": "virtue",
                "name": "Virtue",
                "type": "Concept",
                "description": "Moral excellence"
            }
        ]
    }


@pytest.fixture
def mock_analytics_data():
    """Mock analytics data."""
    return {
        "centrality_scores": {
            "virtue": {"degree": 10, "betweenness": 0.5, "closeness": 0.8},
            "justice": {"degree": 8, "betweenness": 0.3, "closeness": 0.6}
        },
        "communities": [
            {"id": 0, "nodes": ["virtue", "justice"], "modularity": 0.7}
        ],
        "influence_networks": {
            "socrates": {"influence_score": 0.9, "connections": ["virtue", "knowledge"]}
        }
    }