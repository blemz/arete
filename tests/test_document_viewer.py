"""Tests for document viewer functionality."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from ..state.document_state import (
    DocumentState, DocumentMetadata, Citation, DocumentSection,
    DocumentParagraph, DocumentContent, Bookmark, SearchResult
)
from ..state.ui_state import UIState
from ..components.rag_integration import RAGIntegrationState


class TestDocumentState:
    """Test document state management."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.state = DocumentState()
    
    def test_initialization(self):
        """Test state initialization."""
        assert self.state.current_document.id == ""
        assert len(self.state.documents) > 0  # Should load mock library
        assert self.state.show_search is False
        assert self.state.reading_progress == 0
    
    def test_library_search_filtering(self):
        """Test document library search functionality."""
        # Test empty query returns all documents
        self.state.set_library_search("")
        assert len(self.state.filtered_documents) == len(self.state.documents)
        
        # Test title search
        self.state.set_library_search("Apology")
        assert len(self.state.filtered_documents) == 1
        assert self.state.filtered_documents[0].title == "Apology"
        
        # Test author search
        self.state.set_library_search("Plato")
        plato_docs = [d for d in self.state.filtered_documents if d.author == "Plato"]
        assert len(plato_docs) > 0
        
        # Test case insensitive search
        self.state.set_library_search("aristotle")
        aristotle_docs = [d for d in self.state.filtered_documents if "Aristotle" in d.author]
        assert len(aristotle_docs) > 0
    
    def test_document_loading(self):
        """Test loading specific documents."""
        # Load existing document
        self.state.load_document("plato_apology")
        assert self.state.current_document.id == "plato_apology"
        assert self.state.current_document.title == "Apology"
        assert len(self.state.current_document.paragraphs) > 0
        assert len(self.state.current_document.citations) > 0
        
        # Test loading non-existent document
        self.state.load_document("non_existent")
        # Should not change current document
        assert self.state.current_document.id == "plato_apology"
    
    def test_search_functionality(self):
        """Test document search features."""
        # Load document first
        self.state.load_document("plato_apology")
        
        # Test search toggle
        assert self.state.show_search is False
        self.state.toggle_search()
        assert self.state.show_search is True
        
        # Test search execution
        self.state.set_search_query("wisdom")
        self.state.search_document()
        
        # Should find results in mock content
        assert len(self.state.search_results) > 0
        assert self.state.current_search_index == 0
        
        # Test search navigation
        if len(self.state.search_results) > 1:
            self.state.next_search_result()
            assert self.state.current_search_index == 1
            
            self.state.previous_search_result()
            assert self.state.current_search_index == 0
        
        # Test search clearing
        self.state.clear_search()
        assert self.state.search_query == ""
        assert len(self.state.search_results) == 0
    
    def test_citation_management(self):
        """Test citation modal and navigation."""
        # Load document with citations
        self.state.load_document("plato_apology")
        
        # Test opening citation modal
        citation_id = self.state.current_document.citations[0].id
        self.state.open_citation_modal(citation_id)
        
        assert self.state.show_citation_modal is True
        assert self.state.selected_citation.id == citation_id
        
        # Test citation navigation
        if len(self.state.current_document.citations) > 1:
            assert self.state.has_next_citation is True
            self.state.next_citation()
            assert self.state.selected_citation.id != citation_id
            
            self.state.previous_citation()
            assert self.state.selected_citation.id == citation_id
        
        # Test closing modal
        self.state.close_citation_modal()
        assert self.state.show_citation_modal is False
    
    def test_section_navigation(self):
        """Test table of contents navigation."""
        # Load document
        self.state.load_document("plato_apology")
        
        # Test jumping to section
        section_id = self.state.current_document.sections[0].id
        section_position = self.state.current_document.sections[0].position
        
        self.state.jump_to_section(section_id)
        assert self.state.current_position == section_position
    
    def test_bookmark_management(self):
        """Test bookmark functionality."""
        # Test adding bookmark
        self.state.add_bookmark("Test Bookmark", "Preview text", 100)
        assert len(self.state.bookmarks) == 1
        assert self.state.bookmarks[0].title == "Test Bookmark"
        
        # Test bookmark navigation
        bookmark_id = self.state.bookmarks[0].id
        self.state.jump_to_bookmark(bookmark_id)
        assert self.state.current_position == 100
        
        # Test removing bookmark
        self.state.remove_bookmark(bookmark_id)
        assert len(self.state.bookmarks) == 0
    
    def test_reading_progress_calculation(self):
        """Test reading progress tracking."""
        # Load document
        self.state.load_document("plato_apology")
        
        # Test progress calculation
        initial_progress = self.state.reading_progress
        
        # Simulate reading progress
        self.state.current_position = len(self.state.current_document.paragraphs) // 2
        self.state._calculate_reading_progress()
        
        assert self.state.reading_progress >= initial_progress
        assert 0 <= self.state.reading_progress <= 100


class TestUIState:
    """Test UI state management."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.state = UIState()
    
    def test_theme_management(self):
        """Test theme switching."""
        # Test initial state
        assert self.state.dark_mode is False
        assert self.state.theme == "light"
        
        # Test toggle
        self.state.toggle_dark_mode()
        assert self.state.dark_mode is True
        assert self.state.theme == "dark"
        
        # Test direct setting
        self.state.set_theme("auto")
        assert self.state.theme == "auto"
    
    def test_navigation_state(self):
        """Test navigation state management."""
        # Test sidebar toggle
        assert self.state.sidebar_open is True
        self.state.toggle_sidebar()
        assert self.state.sidebar_open is False
        
        # Test page navigation
        self.state.set_current_page("documents")
        assert self.state.current_page == "documents"
        assert self.state.mobile_menu_open is False  # Should close on navigation
    
    def test_layout_preferences(self):
        """Test layout preference management."""
        # Test split view toggle
        self.state.toggle_chat_document_split()
        assert self.state.chat_document_split is True
        
        # Test panel width setting
        self.state.set_document_panel_width(60)
        assert self.state.document_panel_width == 60
        
        # Test bounds checking
        self.state.set_document_panel_width(10)  # Too small
        assert self.state.document_panel_width == 20
        
        self.state.set_document_panel_width(90)  # Too large
        assert self.state.document_panel_width == 80
    
    def test_accessibility_features(self):
        """Test accessibility state management."""
        # Test high contrast toggle
        self.state.toggle_high_contrast()
        assert self.state.high_contrast is True
        
        # Test motion reduction
        self.state.toggle_reduce_motion()
        assert self.state.reduce_motion is True
        
        # Test focus indicators
        self.state.toggle_focus_indicators()
        assert self.state.focus_indicators is False
    
    def test_computed_properties(self):
        """Test computed CSS class properties."""
        # Test theme class
        self.state.dark_mode = True
        self.state.high_contrast = True
        theme_class = self.state.theme_class
        assert "dark" in theme_class
        assert "high-contrast" in theme_class
        
        # Test font size class
        self.state.set_font_size("lg")
        assert self.state.font_size_class == "text-lg"
        
        # Test line height class
        self.state.set_line_height("loose")
        assert self.state.line_height_class == "leading-loose"


class TestRAGIntegration:
    """Test RAG system integration."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.state = RAGIntegrationState()
    
    @pytest.mark.asyncio
    async def test_rag_initialization(self):
        """Test RAG system connection initialization."""
        # Mock successful connection
        with patch.object(self.state, '_connect_to_weaviate'), \
             patch.object(self.state, '_connect_to_neo4j'), \
             patch.object(self.state, '_load_corpus_metadata'):
            
            await self.state.initialize_rag_connection()
            assert self.state.rag_connected is True
            assert self.state.rag_error == ""
    
    @pytest.mark.asyncio
    async def test_corpus_loading(self):
        """Test corpus metadata loading."""
        corpus_docs = await self.state._fetch_corpus_documents()
        assert len(corpus_docs) > 0
        assert all("id" in doc for doc in corpus_docs)
        assert all("title" in doc for doc in corpus_docs)
    
    @pytest.mark.asyncio
    async def test_semantic_search(self):
        """Test semantic search functionality."""
        results = await self.state.search_corpus_semantically("wisdom", 5)
        assert len(results) <= 5
        assert all("similarity" in result for result in results)
        assert all("text" in result for result in results)
    
    @pytest.mark.asyncio
    async def test_entity_search(self):
        """Test knowledge graph entity search."""
        entities = await self.state.find_related_entities("Socrates")
        assert len(entities) > 0
        assert all("entity_id" in entity for entity in entities)
        assert all("relation" in entity for entity in entities)
    
    def test_citation_highlighting(self):
        """Test citation highlighting for queries."""
        # Setup mock search results
        self.state.semantic_search_results = [
            {
                "chunk_id": "test_chunk",
                "text": "wisdom and knowledge are important",
                "similarity": 0.9
            }
        ]
        
        # Test highlighting
        self.state.highlight_citations_for_query("wisdom")
        assert len(self.state.active_citations) > 0
        
        # Test clearing
        self.state.clear_citation_highlighting()
        assert len(self.state.active_citations) == 0
    
    def test_citation_parsing(self):
        """Test paragraph citation parsing."""
        citations = [
            Citation(
                id="test_cite",
                text="wisdom",
                preview_text="Preview",
                full_text="Full text",
                author="Plato",
                work="Test",
                section="1a",
                page="1",
                position=0
            )
        ]
        
        content = self.state._parse_paragraph_with_citations(
            "The pursuit of wisdom is important.",
            ["test_cite"],
            citations
        )
        
        # Should have 3 parts: text before, citation, text after
        assert len(content) == 3
        assert content[0].type == "text"
        assert content[1].type == "citation"
        assert content[2].type == "text"


class TestDocumentViewerIntegration:
    """Test integration between components."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.doc_state = DocumentState()
        self.ui_state = UIState()
        self.rag_state = RAGIntegrationState()
    
    def test_state_coordination(self):
        """Test coordination between different states."""
        # Test that UI theme changes don't affect document state
        self.ui_state.toggle_dark_mode()
        assert self.doc_state.current_document.id == ""  # Unchanged
        
        # Test that document loading doesn't affect UI state
        self.doc_state.load_document("plato_apology")
        assert self.ui_state.current_page == "chat"  # Unchanged
    
    def test_responsive_behavior(self):
        """Test responsive design behavior."""
        # Test mobile vs desktop behavior
        self.ui_state.mobile_menu_open = True
        self.ui_state.set_current_page("documents")
        
        # Mobile menu should close on navigation
        assert self.ui_state.mobile_menu_open is False
    
    def test_accessibility_integration(self):
        """Test accessibility features across components."""
        # Test high contrast mode affects document viewer
        self.ui_state.toggle_high_contrast()
        theme_class = self.ui_state.theme_class
        assert "high-contrast" in theme_class
        
        # Test reduced motion affects UI animations
        self.ui_state.toggle_reduce_motion()
        assert "reduce-motion" in self.ui_state.theme_class


if __name__ == "__main__":
    pytest.main([__file__])