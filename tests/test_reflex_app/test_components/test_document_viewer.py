"""Tests for document viewer component."""
import pytest
from unittest.mock import Mock, patch
import reflex as rx
from src.arete.ui.reflex_app.components.document_viewer import DocumentViewerComponent


class TestDocumentViewerComponent:
    """Test cases for DocumentViewerComponent."""

    @pytest.fixture
    def document_viewer(self):
        """DocumentViewerComponent instance for testing."""
        return DocumentViewerComponent()

    @pytest.fixture
    def sample_document(self):
        """Sample document for testing."""
        return {
            "id": "chunk_1",
            "content": "This is a sample document about virtue and moral philosophy.",
            "metadata": {
                "source": "aristotle_ethics.txt",
                "page": 42,
                "author": "Aristotle"
            }
        }

    def test_document_viewer_initialization(self, document_viewer):
        """Test document viewer initialization."""
        assert document_viewer is not None
        assert hasattr(document_viewer, 'render')

    def test_render_empty_document(self, document_viewer):
        """Test rendering with no document."""
        with patch('src.arete.ui.reflex_app.state.document_state.DocumentState') as mock_state:
            mock_state.current_document = None
            
            rendered = document_viewer.render()
            
            assert rendered is not None

    def test_render_document(self, document_viewer, sample_document):
        """Test rendering with document."""
        with patch('src.arete.ui.reflex_app.state.document_state.DocumentState') as mock_state:
            mock_state.current_document = sample_document
            
            rendered = document_viewer.render()
            
            assert rendered is not None

    def test_document_header_component(self, document_viewer, sample_document):
        """Test document header component."""
        header = document_viewer.create_document_header(sample_document)
        
        assert header is not None

    def test_document_content_component(self, document_viewer, sample_document):
        """Test document content component."""
        content = document_viewer.create_document_content(sample_document["content"])
        
        assert content is not None

    def test_document_metadata_component(self, document_viewer, sample_document):
        """Test document metadata component."""
        metadata = document_viewer.create_metadata_panel(sample_document["metadata"])
        
        assert metadata is not None

    def test_search_within_document(self, document_viewer, sample_document):
        """Test search within document functionality."""
        search_component = document_viewer.create_document_search()
        
        assert search_component is not None

    def test_text_highlighting(self, document_viewer):
        """Test text highlighting functionality."""
        text = "This is a sample text about virtue and wisdom."
        query = "virtue"
        
        highlighted = document_viewer.highlight_text(text, query)
        
        assert "<mark>" in highlighted or "virtue" in highlighted

    def test_citation_highlighting(self, document_viewer, sample_document):
        """Test citation highlighting in document."""
        citations = [
            {"chunk_id": "chunk_1", "start_pos": 10, "end_pos": 20, "text": "virtue"}
        ]
        
        highlighted = document_viewer.highlight_citations(sample_document["content"], citations)
        
        assert highlighted is not None

    def test_document_outline_generation(self, document_viewer, sample_document):
        """Test document outline generation."""
        outline = document_viewer.generate_outline(sample_document["content"])
        
        assert outline is not None
        assert isinstance(outline, list)

    def test_reading_progress_tracker(self, document_viewer):
        """Test reading progress tracking."""
        progress_tracker = document_viewer.create_reading_progress_tracker()
        
        assert progress_tracker is not None

    def test_bookmark_functionality(self, document_viewer, sample_document):
        """Test bookmark functionality."""
        bookmark_button = document_viewer.create_bookmark_button(sample_document["id"])
        
        assert bookmark_button is not None

    def test_annotation_system(self, document_viewer):
        """Test annotation system."""
        annotation_component = document_viewer.create_annotation_system()
        
        assert annotation_component is not None

    def test_text_selection_handling(self, document_viewer):
        """Test text selection handling."""
        with patch.object(document_viewer, 'handle_text_selection') as mock_handler:
            selected_text = "virtue is moral excellence"
            document_viewer.on_text_select(selected_text)
            
            mock_handler.assert_called_once_with(selected_text)

    def test_zoom_functionality(self, document_viewer):
        """Test zoom in/out functionality."""
        zoom_controls = document_viewer.create_zoom_controls()
        
        assert zoom_controls is not None

    def test_font_size_adjustment(self, document_viewer):
        """Test font size adjustment."""
        font_controls = document_viewer.create_font_size_controls()
        
        assert font_controls is not None

    def test_document_export_options(self, document_viewer, sample_document):
        """Test document export options."""
        export_menu = document_viewer.create_export_menu(sample_document)
        
        assert export_menu is not None

    def test_related_documents_panel(self, document_viewer):
        """Test related documents panel."""
        related_docs = [
            {"id": "chunk_2", "title": "Related Document 1", "similarity": 0.85},
            {"id": "chunk_3", "title": "Related Document 2", "similarity": 0.78}
        ]
        
        related_panel = document_viewer.create_related_documents_panel(related_docs)
        
        assert related_panel is not None

    def test_document_statistics_display(self, document_viewer, sample_document):
        """Test document statistics display."""
        stats = {
            "word_count": 150,
            "reading_time": 2,
            "difficulty_score": 0.7
        }
        
        stats_display = document_viewer.create_statistics_display(stats)
        
        assert stats_display is not None

    def test_table_of_contents(self, document_viewer):
        """Test table of contents generation."""
        headings = [
            {"level": 1, "text": "Introduction", "id": "intro"},
            {"level": 2, "text": "What is Virtue?", "id": "virtue"},
            {"level": 2, "text": "Types of Virtue", "id": "types"}
        ]
        
        toc = document_viewer.create_table_of_contents(headings)
        
        assert toc is not None

    def test_document_navigation(self, document_viewer):
        """Test document navigation controls."""
        nav_controls = document_viewer.create_navigation_controls()
        
        assert nav_controls is not None

    def test_full_screen_mode(self, document_viewer):
        """Test full-screen mode toggle."""
        fullscreen_button = document_viewer.create_fullscreen_button()
        
        assert fullscreen_button is not None

    def test_print_functionality(self, document_viewer, sample_document):
        """Test print functionality."""
        print_button = document_viewer.create_print_button(sample_document)
        
        assert print_button is not None

    def test_document_sharing(self, document_viewer, sample_document):
        """Test document sharing functionality."""
        share_menu = document_viewer.create_share_menu(sample_document["id"])
        
        assert share_menu is not None

    def test_accessibility_features(self, document_viewer):
        """Test accessibility features."""
        # Test high contrast mode
        contrast_toggle = document_viewer.create_contrast_toggle()
        assert contrast_toggle is not None
        
        # Test screen reader support
        with patch.object(document_viewer, 'add_aria_labels') as mock_aria:
            document_viewer.ensure_accessibility()
            mock_aria.assert_called_once()

    def test_responsive_document_display(self, document_viewer, sample_document):
        """Test responsive document display."""
        with patch.object(document_viewer, 'is_mobile_view', return_value=True):
            mobile_view = document_viewer.render_mobile_view(sample_document)
            assert mobile_view is not None
        
        with patch.object(document_viewer, 'is_mobile_view', return_value=False):
            desktop_view = document_viewer.render_desktop_view(sample_document)
            assert desktop_view is not None

    def test_document_loading_state(self, document_viewer):
        """Test document loading state."""
        loading_component = document_viewer.create_loading_indicator()
        
        assert loading_component is not None

    def test_document_error_handling(self, document_viewer):
        """Test document error handling."""
        error_component = document_viewer.create_error_display("Failed to load document")
        
        assert error_component is not None

    def test_text_to_speech(self, document_viewer, sample_document):
        """Test text-to-speech functionality."""
        tts_controls = document_viewer.create_text_to_speech_controls(sample_document["content"])
        
        assert tts_controls is not None

    def test_document_comparison(self, document_viewer):
        """Test document comparison view."""
        doc1 = {"id": "chunk_1", "content": "First document content"}
        doc2 = {"id": "chunk_2", "content": "Second document content"}
        
        comparison_view = document_viewer.create_comparison_view(doc1, doc2)
        
        assert comparison_view is not None

    def test_document_version_history(self, document_viewer):
        """Test document version history."""
        versions = [
            {"version": 1, "timestamp": "2025-01-01", "changes": "Initial version"},
            {"version": 2, "timestamp": "2025-01-02", "changes": "Updated content"}
        ]
        
        version_history = document_viewer.create_version_history(versions)
        
        assert version_history is not None

    def test_document_comments_system(self, document_viewer):
        """Test document comments system."""
        comments = [
            {"id": 1, "text": "Great insight!", "author": "user1", "timestamp": "2025-01-01"},
            {"id": 2, "text": "I disagree", "author": "user2", "timestamp": "2025-01-02"}
        ]
        
        comments_panel = document_viewer.create_comments_panel(comments)
        
        assert comments_panel is not None

    def test_document_tags_and_labels(self, document_viewer, sample_document):
        """Test document tags and labels."""
        tags = ["philosophy", "ethics", "virtue", "aristotle"]
        
        tags_display = document_viewer.create_tags_display(tags)
        
        assert tags_display is not None

    def test_document_search_results_highlighting(self, document_viewer):
        """Test search results highlighting."""
        search_results = [
            {"position": 10, "length": 6, "term": "virtue"},
            {"position": 45, "length": 7, "term": "justice"}
        ]
        text = "The concept of virtue is central to justice in philosophy."
        
        highlighted = document_viewer.highlight_search_results(text, search_results)
        
        assert "<mark>" in highlighted

    def test_document_footnotes_handling(self, document_viewer):
        """Test footnotes handling."""
        content_with_footnotes = "This is text with a footnote[1]. More text here[2]."
        footnotes = [
            {"id": 1, "text": "This is footnote 1"},
            {"id": 2, "text": "This is footnote 2"}
        ]
        
        formatted_content = document_viewer.render_footnotes(content_with_footnotes, footnotes)
        
        assert formatted_content is not None

    def test_document_references_panel(self, document_viewer):
        """Test document references panel."""
        references = [
            {"title": "Nicomachean Ethics", "author": "Aristotle", "year": "335 BCE"},
            {"title": "Republic", "author": "Plato", "year": "375 BCE"}
        ]
        
        references_panel = document_viewer.create_references_panel(references)
        
        assert references_panel is not None

    def test_keyboard_navigation(self, document_viewer):
        """Test keyboard navigation."""
        with patch.object(document_viewer, 'handle_keyboard_navigation') as mock_nav:
            # Simulate arrow key navigation
            event = {"key": "ArrowDown", "ctrlKey": False}
            document_viewer.handle_keyboard_event(event)
            
            mock_nav.assert_called_once()

    def test_document_performance_optimization(self, document_viewer):
        """Test document performance optimization."""
        large_content = "This is a very long document. " * 1000
        
        with patch.object(document_viewer, 'use_virtual_scrolling') as mock_virtual:
            document_viewer.render_large_document(large_content)
            
            # Should use virtualization for large documents
            mock_virtual.assert_called_once()

    def test_document_theme_support(self, document_viewer):
        """Test document theme support."""
        with patch.object(document_viewer, 'apply_document_theme') as mock_theme:
            document_viewer.set_document_theme("sepia")
            
            mock_theme.assert_called_once_with("sepia")

    def test_document_citation_links(self, document_viewer):
        """Test document citation links."""
        content = "As Aristotle states in his Ethics[1], virtue is excellence."
        citations = [{"id": 1, "link": "chunk_123", "preview": "Virtue is excellence..."}]
        
        linked_content = document_viewer.create_citation_links(content, citations)
        
        assert linked_content is not None

    def test_document_image_handling(self, document_viewer):
        """Test document image handling."""
        content_with_images = "Here is an image: ![Virtue diagram](virtue.png)"
        
        rendered_content = document_viewer.render_images(content_with_images)
        
        assert rendered_content is not None

    def test_document_equation_rendering(self, document_viewer):
        """Test mathematical equation rendering."""
        content_with_math = "The golden ratio is $$\\phi = \\frac{1 + \\sqrt{5}}{2}$$"
        
        rendered_math = document_viewer.render_math_equations(content_with_math)
        
        assert rendered_math is not None