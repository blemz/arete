"""Tests for document service."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.arete.ui.reflex_app.services.document_service import DocumentService


class TestDocumentService:
    """Test cases for DocumentService."""

    @pytest.fixture
    def document_service(self, mock_weaviate_client, mock_neo4j_client):
        """DocumentService instance for testing."""
        return DocumentService(
            weaviate_client=mock_weaviate_client,
            neo4j_client=mock_neo4j_client
        )

    @pytest.mark.asyncio
    async def test_get_document_success(self, document_service, sample_chunk):
        """Test successful document retrieval."""
        document_service.weaviate_client.get_chunk.return_value = sample_chunk
        
        result = await document_service.get_document("chunk_1")
        
        assert result.id == "chunk_1"
        assert result.content == "This is a test chunk about virtue and wisdom."
        document_service.weaviate_client.get_chunk.assert_called_once_with("chunk_1")

    @pytest.mark.asyncio
    async def test_get_document_not_found(self, document_service):
        """Test document not found scenario."""
        document_service.weaviate_client.get_chunk.return_value = None
        
        result = await document_service.get_document("nonexistent")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_document_error(self, document_service):
        """Test error handling in document retrieval."""
        document_service.weaviate_client.get_chunk.side_effect = Exception("Database error")
        
        with pytest.raises(Exception, match="Database error"):
            await document_service.get_document("chunk_1")

    @pytest.mark.asyncio
    async def test_search_documents(self, document_service, sample_chunk):
        """Test document search functionality."""
        document_service.weaviate_client.search_by_vector.return_value = [
            (sample_chunk, 0.85)
        ]
        
        with patch.object(document_service, '_get_search_embedding') as mock_embedding:
            mock_embedding.return_value = [0.1] * 1536
            
            results = await document_service.search_documents("virtue")
            
            assert len(results) == 1
            assert results[0]["chunk"].id == "chunk_1"
            assert results[0]["score"] == 0.85

    @pytest.mark.asyncio
    async def test_search_documents_empty_query(self, document_service):
        """Test search with empty query."""
        results = await document_service.search_documents("")
        
        assert results == []

    @pytest.mark.asyncio
    async def test_get_related_documents(self, document_service, sample_chunk):
        """Test getting related documents."""
        document_service.weaviate_client.search_by_vector.return_value = [
            (sample_chunk, 0.75)
        ]
        
        with patch.object(document_service, '_get_chunk_embedding') as mock_embedding:
            mock_embedding.return_value = [0.1] * 1536
            
            results = await document_service.get_related_documents("chunk_1")
            
            assert len(results) == 1
            assert results[0]["chunk"].id == "chunk_1"
            assert results[0]["similarity"] == 0.75

    def test_highlight_text(self, document_service):
        """Test text highlighting functionality."""
        text = "Virtue is the highest form of moral excellence."
        query = "virtue moral"
        
        highlighted = document_service.highlight_text(text, query)
        
        assert "<mark>" in highlighted
        assert "</mark>" in highlighted
        assert "Virtue" in highlighted or "virtue" in highlighted

    def test_highlight_text_no_matches(self, document_service):
        """Test highlighting with no matches."""
        text = "Justice is important in philosophy."
        query = "virtue"
        
        highlighted = document_service.highlight_text(text, query)
        
        assert highlighted == text
        assert "<mark>" not in highlighted

    @pytest.mark.asyncio
    async def test_get_document_citations(self, document_service):
        """Test retrieving document citations."""
        with patch.object(document_service.neo4j_client, 'session') as mock_session:
            mock_result = Mock()
            mock_result.data.return_value = [
                {
                    "citation": {
                        "chunk_id": "chunk_1",
                        "source_text": "Test citation",
                        "relevance_score": 0.9
                    }
                }
            ]
            mock_session.return_value.__enter__.return_value.run.return_value = mock_result
            
            citations = await document_service.get_document_citations("chunk_1")
            
            assert len(citations) == 1
            assert citations[0]["chunk_id"] == "chunk_1"
            assert citations[0]["relevance_score"] == 0.9

    @pytest.mark.asyncio
    async def test_get_document_metadata(self, document_service, sample_chunk):
        """Test retrieving document metadata."""
        document_service.weaviate_client.get_chunk.return_value = sample_chunk
        
        metadata = await document_service.get_document_metadata("chunk_1")
        
        assert metadata["source"] == "plato_apology.txt"
        assert metadata["page"] == 1
        assert "word_count" in metadata
        assert "created_at" in metadata

    @pytest.mark.asyncio
    async def test_get_document_outline(self, document_service):
        """Test generating document outline."""
        with patch.object(document_service, '_extract_headings') as mock_headings:
            mock_headings.return_value = [
                {"level": 1, "text": "Introduction", "position": 0},
                {"level": 2, "text": "What is Virtue?", "position": 100},
                {"level": 2, "text": "Types of Virtue", "position": 200}
            ]
            
            outline = await document_service.get_document_outline("chunk_1")
            
            assert len(outline) == 3
            assert outline[0]["level"] == 1
            assert outline[0]["text"] == "Introduction"

    def test_extract_key_passages(self, document_service):
        """Test key passage extraction."""
        text = """
        This is a long document about virtue. Virtue is moral excellence.
        Aristotle defines virtue as a disposition to act in ways that promote human flourishing.
        Plato believed that virtue is a form of knowledge.
        """
        
        passages = document_service.extract_key_passages(text, max_passages=2)
        
        assert len(passages) <= 2
        for passage in passages:
            assert "importance_score" in passage
            assert "text" in passage
            assert passage["importance_score"] > 0

    @pytest.mark.asyncio
    async def test_get_document_statistics(self, document_service, sample_chunk):
        """Test document statistics calculation."""
        document_service.weaviate_client.get_chunk.return_value = sample_chunk
        
        stats = await document_service.get_document_statistics("chunk_1")
        
        assert "word_count" in stats
        assert "character_count" in stats
        assert "reading_time" in stats
        assert stats["word_count"] > 0

    @pytest.mark.asyncio
    async def test_bookmark_document(self, document_service):
        """Test document bookmarking."""
        with patch.object(document_service, '_save_bookmark') as mock_save:
            mock_save.return_value = True
            
            result = await document_service.bookmark_document("chunk_1", "user_123")
            
            assert result is True
            mock_save.assert_called_once_with("chunk_1", "user_123")

    @pytest.mark.asyncio
    async def test_get_bookmarked_documents(self, document_service):
        """Test retrieving bookmarked documents."""
        with patch.object(document_service, '_get_user_bookmarks') as mock_bookmarks:
            mock_bookmarks.return_value = [
                {"chunk_id": "chunk_1", "title": "About Virtue", "bookmarked_at": "2025-01-01"},
                {"chunk_id": "chunk_2", "title": "About Justice", "bookmarked_at": "2025-01-02"}
            ]
            
            bookmarks = await document_service.get_bookmarked_documents("user_123")
            
            assert len(bookmarks) == 2
            assert bookmarks[0]["chunk_id"] == "chunk_1"

    def test_format_document_preview(self, document_service):
        """Test document preview formatting."""
        long_text = "This is a very long document text that needs to be truncated. " * 10
        
        preview = document_service.format_document_preview(long_text, max_length=100)
        
        assert len(preview) <= 103  # 100 + "..."
        assert preview.endswith("...")

    @pytest.mark.asyncio
    async def test_get_document_versions(self, document_service):
        """Test retrieving document versions."""
        with patch.object(document_service, '_query_document_versions') as mock_versions:
            mock_versions.return_value = [
                {"version": 1, "created_at": "2025-01-01", "changes": "Initial version"},
                {"version": 2, "created_at": "2025-01-02", "changes": "Updated content"}
            ]
            
            versions = await document_service.get_document_versions("chunk_1")
            
            assert len(versions) == 2
            assert versions[1]["version"] == 2

    @pytest.mark.asyncio
    async def test_export_document(self, document_service, sample_chunk):
        """Test document export functionality."""
        document_service.weaviate_client.get_chunk.return_value = sample_chunk
        
        exported = await document_service.export_document("chunk_1", format="markdown")
        
        assert "# Document Export" in exported or "content" in exported.lower()
        assert sample_chunk.content in exported

    def test_validate_document_id(self, document_service):
        """Test document ID validation."""
        assert document_service.validate_document_id("chunk_1") is True
        assert document_service.validate_document_id("") is False
        assert document_service.validate_document_id(None) is False
        assert document_service.validate_document_id("chunk_with_special!@#") is False

    @pytest.mark.asyncio
    async def test_get_document_references(self, document_service):
        """Test getting document references."""
        with patch.object(document_service.neo4j_client, 'session') as mock_session:
            mock_result = Mock()
            mock_result.data.return_value = [
                {
                    "reference": {
                        "source_id": "chunk_2",
                        "target_id": "chunk_1",
                        "relationship": "CITES",
                        "context": "References virtue definition"
                    }
                }
            ]
            mock_session.return_value.__enter__.return_value.run.return_value = mock_result
            
            references = await document_service.get_document_references("chunk_1")
            
            assert len(references) == 1
            assert references[0]["relationship"] == "CITES"

    @pytest.mark.asyncio
    async def test_full_text_search(self, document_service):
        """Test full-text search functionality."""
        with patch.object(document_service, '_execute_full_text_search') as mock_search:
            mock_search.return_value = [
                {
                    "chunk_id": "chunk_1",
                    "content": "Virtue is moral excellence",
                    "score": 0.95,
                    "matches": [{"term": "virtue", "positions": [0]}]
                }
            ]
            
            results = await document_service.full_text_search("virtue")
            
            assert len(results) == 1
            assert results[0]["score"] == 0.95
            assert len(results[0]["matches"]) == 1

    @pytest.mark.asyncio
    async def test_get_document_annotations(self, document_service):
        """Test retrieving document annotations."""
        with patch.object(document_service, '_get_user_annotations') as mock_annotations:
            mock_annotations.return_value = [
                {
                    "id": "ann_1",
                    "text": "Important passage about virtue",
                    "position": 100,
                    "created_at": "2025-01-01",
                    "user_id": "user_123"
                }
            ]
            
            annotations = await document_service.get_document_annotations("chunk_1", "user_123")
            
            assert len(annotations) == 1
            assert annotations[0]["text"] == "Important passage about virtue"

    def test_calculate_reading_difficulty(self, document_service):
        """Test reading difficulty calculation."""
        text = "This is a simple sentence. This is another simple sentence for testing."
        
        difficulty = document_service.calculate_reading_difficulty(text)
        
        assert "flesch_score" in difficulty
        assert "grade_level" in difficulty
        assert "difficulty_label" in difficulty
        assert 0 <= difficulty["flesch_score"] <= 100