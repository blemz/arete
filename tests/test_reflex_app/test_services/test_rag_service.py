"""
Pragmatic Contract-Based Tests for RAG Service

Following "Quality over Quantity" testing methodology proven in Phase 8 redesign.
Focus: Test what the service promises (contracts), not implementation details.

Current Minimal API Coverage:
- Dependency injection via constructor
- Lazy initialization with initialize()
- RAG query with get_rag_response()
- Fallback responses when RAG fails

Test Philosophy:
- 17 focused tests > 1,500 exhaustive tests
- Contract-based over implementation testing
- Critical paths over edge case exhaustion
- Maintainable and readable over comprehensive

Reference: Phase 8 Test Redesign Success
- Weaviate Client: 1,529 → 17 tests (98.9% reduction, 84% coverage maintained)
- Neo4j Client: 1,359 → 108 tests (92% reduction, 74% coverage maintained)

Date: 2025-11-06
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from uuid import uuid4

from src.arete.ui.reflex_app.services.rag_service import RAGService
from src.arete.models import CitationWithScore


class TestRAGServiceConstruction:
    """Test RAG service construction and dependency injection."""

    def test_constructor_accepts_no_arguments(self):
        """Service can be constructed without dependencies for production use."""
        service = RAGService()

        assert service is not None
        assert service.settings is not None
        assert service._initialized is False

    def test_constructor_accepts_injected_dependencies(self):
        """Service accepts injected dependencies for testing."""
        mock_neo4j = Mock()
        mock_weaviate = Mock()
        mock_embedding = Mock()
        mock_llm = Mock()
        mock_settings = Mock()

        service = RAGService(
            neo4j_client=mock_neo4j,
            weaviate_client=mock_weaviate,
            embedding_service=mock_embedding,
            llm_service=mock_llm,
            settings=mock_settings
        )

        assert service.neo4j_client is mock_neo4j
        assert service.weaviate_client is mock_weaviate
        assert service.embedding_service is mock_embedding
        assert service.llm_service is mock_llm
        assert service.settings is mock_settings
        assert service._initialized is True  # Auto-initialized when dependencies provided

    def test_constructor_partial_dependency_injection(self):
        """Service handles partial dependency injection gracefully."""
        mock_neo4j = Mock()

        service = RAGService(neo4j_client=mock_neo4j)

        assert service.neo4j_client is mock_neo4j
        assert service.weaviate_client is None
        assert service.embedding_service is None
        assert service._initialized is False  # Not fully initialized


class TestRAGServiceInitialization:
    """Test RAG service initialization."""

    @pytest.mark.asyncio
    async def test_initialize_creates_clients_when_not_injected(self):
        """Initialize creates clients and services when not injected."""
        service = RAGService()

        with patch('src.arete.ui.reflex_app.services.rag_service.Neo4jClient') as mock_neo4j_class, \
             patch('src.arete.ui.reflex_app.services.rag_service.WeaviateClient') as mock_weaviate_class, \
             patch('src.arete.ui.reflex_app.services.rag_service.get_embedding_service') as mock_get_embedding, \
             patch('src.arete.ui.reflex_app.services.rag_service.get_llm_service') as mock_get_llm, \
             patch.object(service, '_test_connectivity'):

            mock_get_embedding.return_value = Mock()
            mock_get_llm.return_value = Mock()

            result = await service.initialize()

            assert result is True
            assert service._initialized is True
            mock_neo4j_class.assert_called_once()
            mock_weaviate_class.assert_called_once()
            mock_get_embedding.assert_called_once()
            mock_get_llm.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_skips_when_already_initialized(self):
        """Initialize is idempotent - returns immediately if already initialized."""
        mock_neo4j = Mock()
        mock_weaviate = Mock()
        mock_embedding = Mock()

        service = RAGService(
            neo4j_client=mock_neo4j,
            weaviate_client=mock_weaviate,
            embedding_service=mock_embedding
        )

        assert service._initialized is True

        # Should return immediately without creating new clients
        with patch('src.arete.ui.reflex_app.services.rag_service.Neo4jClient') as mock_neo4j_class:
            result = await service.initialize()

            assert result is True
            mock_neo4j_class.assert_not_called()

    @pytest.mark.asyncio
    async def test_initialize_returns_false_on_failure(self):
        """Initialize returns False when client creation fails."""
        service = RAGService()

        with patch('src.arete.ui.reflex_app.services.rag_service.Neo4jClient', side_effect=Exception("Connection failed")):
            result = await service.initialize()

            assert result is False
            assert service._initialized is False


class TestRAGServiceQuerying:
    """Test RAG service query functionality."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for RAG service."""
        mock_neo4j = Mock()
        mock_weaviate = Mock()
        mock_embedding = Mock()
        mock_llm = Mock()

        return {
            'neo4j_client': mock_neo4j,
            'weaviate_client': mock_weaviate,
            'embedding_service': mock_embedding,
            'llm_service': mock_llm
        }

    @pytest.mark.asyncio
    async def test_get_rag_response_returns_response_and_citations(self, mock_dependencies):
        """get_rag_response returns response text and citations."""
        service = RAGService(**mock_dependencies)

        # Mock the embedding generation
        mock_dependencies['embedding_service'].get_embeddings.return_value = [[0.1] * 1536]

        # Mock Weaviate search results
        mock_search_results = [
            {
                'properties': {
                    'content': 'Virtue is excellence of character.',
                    'position_index': 1
                },
                '_additional': {
                    'certainty': 0.95
                }
            }
        ]
        mock_dependencies['weaviate_client'].search_by_vector.return_value = mock_search_results

        # Mock LLM response
        mock_dependencies['llm_service'].generate_text.return_value = "Virtue, according to Socrates, is knowledge."

        response, citations = await service.get_rag_response("What is virtue?")

        assert isinstance(response, str)
        assert len(response) > 0
        assert isinstance(citations, list)
        assert len(citations) > 0
        assert all(isinstance(c, CitationWithScore) for c in citations)

    @pytest.mark.asyncio
    async def test_get_rag_response_initializes_if_needed(self, mock_dependencies):
        """get_rag_response initializes service if not already initialized."""
        # Create service without pre-initialization
        mock_dependencies['neo4j_client'] = None
        mock_dependencies['weaviate_client'] = None
        mock_dependencies['embedding_service'] = None

        service = RAGService(**mock_dependencies)
        assert service._initialized is False

        with patch.object(service, 'initialize', new_callable=AsyncMock) as mock_init:
            mock_init.return_value = False  # Simulate initialization failure

            response, citations = await service.get_rag_response("What is virtue?")

            # Should fall back to fallback response
            mock_init.assert_called_once()
            assert isinstance(response, str)
            assert len(response) > 0

    @pytest.mark.asyncio
    async def test_get_rag_response_returns_fallback_on_pipeline_failure(self, mock_dependencies):
        """get_rag_response returns fallback response when RAG pipeline fails."""
        service = RAGService(**mock_dependencies)

        # Make the pipeline fail
        mock_dependencies['embedding_service'].get_embeddings.side_effect = Exception("Embedding failed")

        response, citations = await service.get_rag_response("What is virtue?")

        assert isinstance(response, str)
        assert len(response) > 0
        assert isinstance(citations, list)
        # Fallback returns empty citations
        assert len(citations) == 0

    @pytest.mark.asyncio
    async def test_fallback_response_covers_common_philosophical_topics(self, mock_dependencies):
        """Fallback responses cover common philosophical topics."""
        service = RAGService(**mock_dependencies)

        topics = ["virtue", "socrates", "justice", "happiness", "knowledge"]

        for topic in topics:
            response, citations = service._get_fallback_response(f"What is {topic}?")

            assert isinstance(response, str)
            assert len(response) > 50  # Meaningful response, not just "unavailable"
            assert topic.lower() in response.lower() or "philosophical" in response.lower()


class TestRAGServiceResponseProcessing:
    """Test RAG service response processing and formatting."""

    def test_clean_response_removes_xml_tags(self):
        """_clean_response removes XML tags from LLM output."""
        service = RAGService()

        dirty_response = "Virtue is <concept>excellence</concept> of character."
        cleaned = service._clean_response(dirty_response)

        assert "<concept>" not in cleaned
        assert "</concept>" not in cleaned
        assert "excellence" in cleaned

    def test_clean_response_removes_xml_entities(self):
        """_clean_response removes XML entities from LLM output."""
        service = RAGService()

        dirty_response = "Virtue &amp; knowledge are &lt;related&gt;"
        cleaned = service._clean_response(dirty_response)

        assert "&amp;" not in cleaned
        assert "&lt;" not in cleaned
        assert "&gt;" not in cleaned

    def test_clean_response_strips_whitespace(self):
        """_clean_response strips leading/trailing whitespace."""
        service = RAGService()

        dirty_response = "  \n  Virtue is excellence.  \n  "
        cleaned = service._clean_response(dirty_response)

        assert not cleaned.startswith(" ")
        assert not cleaned.endswith(" ")
        assert not cleaned.startswith("\n")


class TestRAGServiceGlobalInstance:
    """Test global RAG service instance management."""

    @pytest.mark.asyncio
    async def test_get_rag_service_returns_singleton(self):
        """get_rag_service returns the same instance on multiple calls."""
        from src.arete.ui.reflex_app.services.rag_service import get_rag_service

        service1 = await get_rag_service()
        service2 = await get_rag_service()

        assert service1 is service2

    @pytest.mark.asyncio
    async def test_get_rag_service_returns_rag_service_instance(self):
        """get_rag_service returns a RAGService instance."""
        from src.arete.ui.reflex_app.services.rag_service import get_rag_service

        service = await get_rag_service()

        assert isinstance(service, RAGService)
