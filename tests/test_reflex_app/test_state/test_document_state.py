"""Tests for document state management."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.arete.ui.reflex_app.state.document_state import DocumentState


class TestDocumentState:
    """Test cases for DocumentState."""

    @pytest.fixture
    def document_state(self):
        """DocumentState instance for testing."""
        return DocumentState()

    def test_initial_state(self, document_state):
        """Test initial state values."""
        assert document_state.current_document is None
        assert document_state.search_query == ""
        assert document_state.search_results == []
        assert document_state.is_loading == False
        assert document_state.error_message == ""
        assert document_state.selected_citations == []

    def test_set_current_document(self, document_state, sample_chunk):
        """Test setting current document."""
        document_state.set_current_document(sample_chunk)
        
        assert document_state.current_document == sample_chunk
        assert document_state.current_document.id == "chunk_1"

    def test_clear_current_document(self, document_state, sample_chunk):
        """Test clearing current document."""
        document_state.set_current_document(sample_chunk)
        assert document_state.current_document is not None
        
        document_state.clear_current_document()
        assert document_state.current_document is None

    def test_update_search_query(self, document_state):
        """Test updating search query."""
        document_state.update_search_query("virtue")
        assert document_state.search_query == "virtue"
        
        document_state.update_search_query("justice and virtue")
        assert document_state.search_query == "justice and virtue"

    @pytest.mark.asyncio
    async def test_perform_search(self, document_state, sample_chunk):
        """Test performing document search."""
        document_state.search_query = "virtue"
        
        with patch.object(document_state, 'document_service') as mock_service:
            mock_service.search_documents.return_value = [
                {"chunk": sample_chunk, "score": 0.85}
            ]
            
            await document_state.perform_search()
            
            assert len(document_state.search_results) == 1
            assert document_state.search_results[0]["score"] == 0.85
            assert document_state.is_loading == False

    @pytest.mark.asyncio
    async def test_perform_search_error(self, document_state):
        """Test search error handling."""
        document_state.search_query = "virtue"
        
        with patch.object(document_state, 'document_service') as mock_service:
            mock_service.search_documents.side_effect = Exception("Search failed")
            
            await document_state.perform_search()
            
            assert document_state.error_message == "Search failed"
            assert document_state.search_results == []
            assert document_state.is_loading == False

    @pytest.mark.asyncio
    async def test_perform_empty_search(self, document_state):
        """Test search with empty query."""
        document_state.search_query = ""
        
        await document_state.perform_search()
        
        assert document_state.search_results == []
        assert document_state.error_message == "Search query cannot be empty"

    def test_clear_search_results(self, document_state):
        """Test clearing search results."""
        document_state.search_results = [{"chunk": "test", "score": 0.8}]
        document_state.search_query = "test query"
        
        document_state.clear_search_results()
        
        assert document_state.search_results == []
        assert document_state.search_query == ""

    def test_add_selected_citation(self, document_state, sample_citation):
        """Test adding selected citation."""
        document_state.add_selected_citation(sample_citation)
        
        assert len(document_state.selected_citations) == 1
        assert document_state.selected_citations[0] == sample_citation

    def test_remove_selected_citation(self, document_state, sample_citation):
        """Test removing selected citation."""
        document_state.add_selected_citation(sample_citation)
        assert len(document_state.selected_citations) == 1
        
        document_state.remove_selected_citation(sample_citation.chunk_id)
        assert len(document_state.selected_citations) == 0

    def test_clear_selected_citations(self, document_state, sample_citation):
        """Test clearing all selected citations."""
        document_state.add_selected_citation(sample_citation)
        document_state.add_selected_citation(sample_citation)
        assert len(document_state.selected_citations) == 2
        
        document_state.clear_selected_citations()
        assert document_state.selected_citations == []

    def test_is_citation_selected(self, document_state, sample_citation):
        """Test checking if citation is selected."""
        assert document_state.is_citation_selected(sample_citation.chunk_id) == False
        
        document_state.add_selected_citation(sample_citation)
        assert document_state.is_citation_selected(sample_citation.chunk_id) == True

    @pytest.mark.asyncio
    async def test_load_document_by_id(self, document_state, sample_chunk):
        """Test loading document by ID."""
        with patch.object(document_state, 'document_service') as mock_service:
            mock_service.get_document.return_value = sample_chunk
            
            await document_state.load_document_by_id("chunk_1")
            
            assert document_state.current_document == sample_chunk
            mock_service.get_document.assert_called_once_with("chunk_1")

    @pytest.mark.asyncio
    async def test_load_document_not_found(self, document_state):
        """Test loading non-existent document."""
        with patch.object(document_state, 'document_service') as mock_service:
            mock_service.get_document.return_value = None
            
            await document_state.load_document_by_id("nonexistent")
            
            assert document_state.current_document is None
            assert document_state.error_message == "Document not found"

    @pytest.mark.asyncio
    async def test_get_related_documents(self, document_state, sample_chunk):
        """Test getting related documents."""
        document_state.current_document = sample_chunk
        
        with patch.object(document_state, 'document_service') as mock_service:
            mock_service.get_related_documents.return_value = [
                {"chunk": sample_chunk, "similarity": 0.75}
            ]
            
            await document_state.get_related_documents()
            
            assert len(document_state.related_documents) == 1
            assert document_state.related_documents[0]["similarity"] == 0.75

    @pytest.mark.asyncio
    async def test_get_related_documents_no_current(self, document_state):
        """Test getting related documents with no current document."""
        await document_state.get_related_documents()
        
        assert document_state.related_documents == []
        assert document_state.error_message == "No current document selected"

    def test_highlight_text_in_document(self, document_state, sample_chunk):
        """Test text highlighting in document."""
        document_state.current_document = sample_chunk
        document_state.search_query = "virtue"
        
        highlighted = document_state.highlight_text_in_document()
        
        assert "<mark>" in highlighted or "virtue" in highlighted.lower()

    def test_get_document_statistics(self, document_state, sample_chunk):
        """Test getting document statistics."""
        document_state.current_document = sample_chunk
        
        stats = document_state.get_document_statistics()
        
        assert "word_count" in stats
        assert "character_count" in stats
        assert stats["word_count"] > 0
        assert stats["character_count"] > 0

    def test_get_document_outline(self, document_state, sample_chunk):
        """Test generating document outline."""
        document_state.current_document = sample_chunk
        
        with patch.object(document_state, '_extract_outline') as mock_outline:
            mock_outline.return_value = [
                {"level": 1, "text": "Introduction", "position": 0},
                {"level": 2, "text": "About Virtue", "position": 100}
            ]
            
            outline = document_state.get_document_outline()
            
            assert len(outline) == 2
            assert outline[0]["level"] == 1

    @pytest.mark.asyncio
    async def test_bookmark_document(self, document_state, sample_chunk):
        """Test bookmarking document."""
        document_state.current_document = sample_chunk
        
        with patch.object(document_state, 'document_service') as mock_service:
            mock_service.bookmark_document.return_value = True
            
            result = await document_state.bookmark_document("user_123")
            
            assert result == True
            mock_service.bookmark_document.assert_called_once_with("chunk_1", "user_123")

    @pytest.mark.asyncio
    async def test_get_bookmarks(self, document_state):
        """Test getting user bookmarks."""
        with patch.object(document_state, 'document_service') as mock_service:
            mock_service.get_bookmarked_documents.return_value = [
                {"chunk_id": "chunk_1", "title": "About Virtue", "bookmarked_at": "2025-01-01"}
            ]
            
            await document_state.get_bookmarks("user_123")
            
            assert len(document_state.bookmarks) == 1
            assert document_state.bookmarks[0]["title"] == "About Virtue"

    def test_set_reading_position(self, document_state):
        """Test setting reading position."""
        document_state.set_reading_position(150)
        assert document_state.reading_position == 150

    def test_get_reading_progress(self, document_state, sample_chunk):
        """Test calculating reading progress."""
        document_state.current_document = sample_chunk
        document_state.reading_position = 50
        
        progress = document_state.get_reading_progress()
        
        assert 0 <= progress <= 100
        assert isinstance(progress, (int, float))

    @pytest.mark.asyncio
    async def test_full_text_search(self, document_state):
        """Test full-text search functionality."""
        document_state.search_query = "virtue ethics"
        
        with patch.object(document_state, 'document_service') as mock_service:
            mock_service.full_text_search.return_value = [
                {
                    "chunk_id": "chunk_1",
                    "content": "Virtue ethics is important",
                    "score": 0.95,
                    "matches": [{"term": "virtue", "positions": [0]}]
                }
            ]
            
            await document_state.full_text_search()
            
            assert len(document_state.search_results) == 1
            assert document_state.search_results[0]["score"] == 0.95

    def test_filter_search_results(self, document_state):
        """Test filtering search results."""
        document_state.search_results = [
            {"chunk": {"metadata": {"source": "plato.txt"}}, "score": 0.9},
            {"chunk": {"metadata": {"source": "aristotle.txt"}}, "score": 0.8},
            {"chunk": {"metadata": {"source": "plato.txt"}}, "score": 0.7}
        ]
        
        filtered = document_state.filter_search_results(source="plato.txt")
        
        assert len(filtered) == 2
        assert all("plato.txt" in result["chunk"]["metadata"]["source"] for result in filtered)

    def test_sort_search_results(self, document_state):
        """Test sorting search results."""
        document_state.search_results = [
            {"score": 0.7}, {"score": 0.9}, {"score": 0.8}
        ]
        
        document_state.sort_search_results(by="score", ascending=False)
        
        scores = [result["score"] for result in document_state.search_results]
        assert scores == [0.9, 0.8, 0.7]

    def test_get_search_result_preview(self, document_state):
        """Test getting search result preview."""
        result = {
            "chunk": {
                "content": "This is a very long document content that should be truncated for preview purposes."
            },
            "score": 0.85
        }
        
        preview = document_state.get_search_result_preview(result, max_length=50)
        
        assert len(preview) <= 53  # 50 + "..."
        assert preview.endswith("...")

    @pytest.mark.asyncio
    async def test_export_search_results(self, document_state):
        """Test exporting search results."""
        document_state.search_results = [
            {"chunk": {"id": "chunk_1", "content": "Test content"}, "score": 0.8}
        ]
        
        exported = await document_state.export_search_results(format="json")
        
        assert "results" in exported
        assert "exported_at" in exported
        assert len(exported["results"]) == 1

    def test_get_document_metadata(self, document_state, sample_chunk):
        """Test getting document metadata."""
        document_state.current_document = sample_chunk
        
        metadata = document_state.get_document_metadata()
        
        assert "source" in metadata
        assert "page" in metadata
        assert metadata["source"] == "plato_apology.txt"

    @pytest.mark.asyncio
    async def test_annotate_document(self, document_state, sample_chunk):
        """Test document annotation."""
        document_state.current_document = sample_chunk
        
        with patch.object(document_state, 'document_service') as mock_service:
            mock_service.add_annotation.return_value = {
                "id": "ann_1",
                "text": "Important passage",
                "position": 100
            }
            
            annotation = await document_state.annotate_document(
                "Important passage", 100, "user_123"
            )
            
            assert annotation["text"] == "Important passage"
            assert len(document_state.annotations) == 1

    @pytest.mark.asyncio
    async def test_get_annotations(self, document_state, sample_chunk):
        """Test getting document annotations."""
        document_state.current_document = sample_chunk
        
        with patch.object(document_state, 'document_service') as mock_service:
            mock_service.get_document_annotations.return_value = [
                {"id": "ann_1", "text": "Note 1", "position": 50},
                {"id": "ann_2", "text": "Note 2", "position": 150}
            ]
            
            await document_state.get_annotations("user_123")
            
            assert len(document_state.annotations) == 2
            assert document_state.annotations[0]["text"] == "Note 1"

    def test_validate_search_query(self, document_state):
        """Test search query validation."""
        assert document_state.validate_search_query("virtue") == True
        assert document_state.validate_search_query("virtue AND justice") == True
        assert document_state.validate_search_query("") == False
        assert document_state.validate_search_query("   ") == False
        
        # Test very long query
        long_query = "virtue " * 100
        assert document_state.validate_search_query(long_query) == False

    def test_get_search_suggestions(self, document_state):
        """Test getting search suggestions."""
        with patch.object(document_state, '_generate_suggestions') as mock_suggestions:
            mock_suggestions.return_value = [
                "virtue ethics",
                "virtue and happiness",
                "virtue in Aristotle"
            ]
            
            suggestions = document_state.get_search_suggestions("virtue")
            
            assert len(suggestions) == 3
            assert "virtue ethics" in suggestions

    def test_calculate_reading_time(self, document_state, sample_chunk):
        """Test calculating reading time."""
        document_state.current_document = sample_chunk
        
        reading_time = document_state.calculate_reading_time()
        
        assert reading_time > 0
        assert isinstance(reading_time, (int, float))

    def test_format_search_results_for_display(self, document_state):
        """Test formatting search results for display."""
        results = [
            {
                "chunk": {"content": "Test content about virtue", "metadata": {"source": "test.txt"}},
                "score": 0.85
            }
        ]
        
        formatted = document_state.format_search_results_for_display(results)
        
        assert len(formatted) == 1
        assert "preview" in formatted[0]
        assert "display_score" in formatted[0]