"""
Document Viewer UI Components for Arete.

This module provides Streamlit components for viewing and interacting with philosophical documents,
including citation highlighting, search functionality, and split-view layout capabilities.
"""

import streamlit as st
import re
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import uuid


@dataclass
class DocumentContent:
    """Represents a document with its content and metadata."""
    
    doc_id: str
    title: str
    content: str
    author: str
    metadata: Dict[str, Any]
    created_date: Optional[datetime] = None
    source: Optional[str] = None
    document_type: str = "philosophical_text"


@dataclass
class Citation:
    """Represents a citation with position information."""
    
    citation_id: str
    document_id: str
    start_pos: int
    end_pos: int
    text: str
    reference: str
    confidence: float = 1.0


@dataclass
class SearchResult:
    """Represents a search result in document text."""
    
    position: int
    text: str
    context_before: str
    context_after: str
    line_number: int


class DocumentRenderer:
    """Handles rendering of document content with highlighting and navigation."""
    
    def __init__(self):
        """Initialize the document renderer."""
        self.current_document: Optional[DocumentContent] = None
        self.citations: List[Citation] = []
        self.search_results: List[SearchResult] = []
        self.current_search_index: int = 0
        
    def set_document(self, document: DocumentContent):
        """Set the current document to display."""
        self.current_document = document
        
    def set_citations(self, citations: List[Citation]):
        """Set citations for the current document."""
        self.citations = citations
        
    def render_document_header(self):
        """Render document header with metadata."""
        if not self.current_document:
            return
            
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"### 📜 {self.current_document.title}")
            if self.current_document.author:
                st.markdown(f"**Author:** {self.current_document.author}")
        
        with col2:
            if st.button("📋 Document Info", key="doc_info"):
                self._show_document_metadata()
                
    def _show_document_metadata(self):
        """Show document metadata in an expander."""
        with st.expander("📊 Document Metadata", expanded=True):
            if self.current_document:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.caption(f"**Document ID:** {self.current_document.doc_id}")
                    st.caption(f"**Type:** {self.current_document.document_type}")
                    if self.current_document.source:
                        st.caption(f"**Source:** {self.current_document.source}")
                
                with col2:
                    if self.current_document.created_date:
                        st.caption(f"**Created:** {self.current_document.created_date.strftime('%Y-%m-%d')}")
                    st.caption(f"**Citations:** {len(self.citations)}")
                    st.caption(f"**Length:** {len(self.current_document.content)} characters")
                    
    def render_search_controls(self):
        """Render search controls for the document."""
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            search_query = st.text_input(
                "Search in document",
                placeholder="Enter search terms...",
                key="doc_search_query"
            )
            
        with col2:
            if st.button("🔍 Search", key="doc_search_btn"):
                if search_query:
                    self._perform_search(search_query)
        
        with col3:
            if st.button("❌ Clear", key="doc_search_clear"):
                self.search_results = []
                self.current_search_index = 0
                st.rerun()
                
        # Search navigation controls
        if self.search_results:
            self._render_search_navigation()
            
    def _perform_search(self, query: str):
        """Perform search in current document content."""
        if not self.current_document or not query:
            return
            
        content = self.current_document.content
        self.search_results = []
        
        # Case-insensitive search
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        
        for match in pattern.finditer(content):
            start_pos = match.start()
            end_pos = match.end()
            
            # Get context around the match
            context_start = max(0, start_pos - 50)
            context_end = min(len(content), end_pos + 50)
            
            context_before = content[context_start:start_pos]
            context_after = content[end_pos:context_end]
            
            # Calculate approximate line number
            line_number = content[:start_pos].count('\n') + 1
            
            result = SearchResult(
                position=start_pos,
                text=match.group(),
                context_before=context_before,
                context_after=context_after,
                line_number=line_number
            )
            
            self.search_results.append(result)
        
        self.current_search_index = 0
        st.success(f"Found {len(self.search_results)} matches")
        
    def _render_search_navigation(self):
        """Render search result navigation controls."""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("⬆️ Previous", key="search_prev"):
                if self.current_search_index > 0:
                    self.current_search_index -= 1
                    st.rerun()
        
        with col2:
            st.write(f"Result {self.current_search_index + 1} of {len(self.search_results)}")
        
        with col3:
            if st.button("⬇️ Next", key="search_next"):
                if self.current_search_index < len(self.search_results) - 1:
                    self.current_search_index += 1
                    st.rerun()
                    
        # Show current search result context
        if self.search_results:
            current_result = self.search_results[self.current_search_index]
            st.info(f"**Line {current_result.line_number}:** ...{current_result.context_before}**{current_result.text}**{current_result.context_after}...")
            
    def render_document_content(self, highlight_citations: bool = True, highlight_search: bool = True):
        """Render the main document content with highlighting."""
        if not self.current_document:
            st.warning("No document loaded")
            return
            
        content = self.current_document.content
        
        # Apply highlighting
        if highlight_citations and self.citations:
            content = self._apply_citation_highlighting(content)
            
        if highlight_search and self.search_results:
            content = self._apply_search_highlighting(content)
            
        # Render content in a scrollable container
        st.markdown(
            f"""
            <div style="height: 400px; overflow-y: auto; padding: 1rem; 
                        border: 1px solid #ddd; border-radius: 0.5rem; 
                        background-color: #fafafa; line-height: 1.6;">
                {content}
            </div>
            """,
            unsafe_allow_html=True
        )
        
    def _apply_citation_highlighting(self, content: str) -> str:
        """Apply citation highlighting to document content."""
        if not self.citations:
            return content
            
        # Sort citations by start position in reverse order to avoid position shifts
        sorted_citations = sorted(self.citations, key=lambda c: c.start_pos, reverse=True)
        
        for citation in sorted_citations:
            if citation.start_pos >= 0 and citation.end_pos <= len(content):
                before = content[:citation.start_pos]
                cited_text = content[citation.start_pos:citation.end_pos]
                after = content[citation.end_pos:]
                
                # Create clickable citation with highlighting and session state interaction
                citation_key = f"citation_clicked_{citation.citation_id}"
                
                # Create clickable citation with highlighting
                highlighted = f"""<span class="citation-highlight" 
                                      id="{citation.citation_id}"
                                      title="Citation: {citation.reference} (Click for details)"
                                      style="background-color: #fff3cd; border-left: 3px solid #856404; 
                                             padding: 2px 4px; cursor: pointer; 
                                             border-radius: 3px; position: relative;
                                             transition: background-color 0.3s ease;">
                                  {cited_text}
                                  <sup style="color: #856404; font-size: 0.8em;">🔗</sup>
                              </span>"""
                
                content = before + highlighted + after
                
        return content
        
    def handle_citation_click(self, citation_id: str):
        """Handle citation click events."""
        # Find the clicked citation
        clicked_citation = next((c for c in self.citations if c.citation_id == citation_id), None)
        
        if clicked_citation:
            # Store in session state for other components to access
            st.session_state[f"selected_citation"] = clicked_citation
            st.session_state[f"citation_details_expanded"] = True
            return clicked_citation
        
        return None
        
    def _apply_search_highlighting(self, content: str) -> str:
        """Apply search result highlighting to document content."""
        if not self.search_results:
            return content
            
        # Get current search result
        current_result = self.search_results[self.current_search_index]
        query = current_result.text
        
        # Highlight current search result differently
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        highlighted_content = pattern.sub(
            lambda m: f'<mark style="background-color: #ffeb3b; font-weight: bold;">{m.group()}</mark>'
            if m.start() == current_result.position
            else f'<mark style="background-color: #e3f2fd;">{m.group()}</mark>',
            content
        )
        
        return highlighted_content


class CitationNavigator:
    """Handles citation linking and navigation functionality."""
    
    def __init__(self):
        """Initialize citation navigator."""
        self.citations: List[Citation] = []
        self.current_citation_index: int = 0
        
    def set_citations(self, citations: List[Citation]):
        """Set citations for navigation."""
        self.citations = citations
        self.current_citation_index = 0
        
    def render_citation_panel(self):
        """Render citation navigation panel."""
        if not self.citations:
            st.info("No citations available for this document")
            return
            
        st.markdown("### 📖 Citations")
        
        # Citation navigation controls
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.button("⬅️ Prev", key="cite_prev"):
                if self.current_citation_index > 0:
                    self.current_citation_index -= 1
                    st.rerun()
        
        with col2:
            st.write(f"Citation {self.current_citation_index + 1} of {len(self.citations)}")
        
        with col3:
            if st.button("➡️ Next", key="cite_next"):
                if self.current_citation_index < len(self.citations) - 1:
                    self.current_citation_index += 1
                    st.rerun()
                    
        # Current citation details
        if self.citations:
            current_citation = self.citations[self.current_citation_index]
            self._render_citation_details(current_citation)
            
        # Citation list
        with st.expander("📋 All Citations", expanded=False):
            for i, citation in enumerate(self.citations):
                if st.button(f"📖 {citation.reference}", key=f"goto_cite_{i}"):
                    self.current_citation_index = i
                    st.rerun()
                    
    def _render_citation_details(self, citation: Citation):
        """Render details for a specific citation."""
        st.markdown(f"**Reference:** {citation.reference}")
        st.markdown(f"**Text:** _{citation.text}_")
        
        if citation.confidence < 1.0:
            st.caption(f"Confidence: {citation.confidence:.2f}")
            
        # Action buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🎯 Jump to Text", key=f"jump_{citation.citation_id}"):
                # This would scroll to the citation in the document
                st.session_state[f"scroll_to_{citation.citation_id}"] = True
                
        with col2:
            if st.button("🔗 Copy Reference", key=f"copy_{citation.citation_id}"):
                # This would copy the citation reference to clipboard
                st.success("Reference copied!")


class SplitViewLayout:
    """Handles split-view layout with chat and document panels."""
    
    def __init__(self):
        """Initialize split view layout."""
        self.document_renderer = DocumentRenderer()
        self.citation_navigator = CitationNavigator()
        
    def render_split_view(self, chat_interface, document: Optional[DocumentContent] = None):
        """Render split view with chat and document panels."""
        # Layout controls
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            layout_mode = st.selectbox(
                "Layout",
                ["Split View", "Chat Only", "Document Only"],
                key="layout_mode"
            )
        
        with col2:
            if layout_mode == "Split View":
                split_ratio = st.slider(
                    "Chat/Document Split",
                    min_value=20,
                    max_value=80,
                    value=50,
                    key="split_ratio"
                )
            else:
                split_ratio = 50
        
        with col3:
            if st.button("🔄 Refresh", key="refresh_split_view"):
                st.rerun()
                
        st.divider()
        
        # Render based on layout mode
        if layout_mode == "Chat Only":
            self._render_chat_only(chat_interface)
        elif layout_mode == "Document Only":
            self._render_document_only(document)
        else:  # Split View
            self._render_split_layout(chat_interface, document, split_ratio)
            
    def _render_chat_only(self, chat_interface):
        """Render chat interface only."""
        chat_interface.render_chat_interface()
        
    def _render_document_only(self, document: Optional[DocumentContent]):
        """Render document viewer only."""
        if document:
            self.document_renderer.set_document(document)
            self.document_renderer.render_document_header()
            self.document_renderer.render_search_controls()
            self.document_renderer.render_document_content()
            
            # Side panel for citations
            with st.sidebar:
                self.citation_navigator.render_citation_panel()
        else:
            st.info("No document selected")
            
    def _render_split_layout(self, chat_interface, document: Optional[DocumentContent], split_ratio: int):
        """Render split layout with both chat and document."""
        left_width = split_ratio / 100 * 10
        right_width = 10 - left_width
        
        col_left, col_right = st.columns([left_width, right_width])
        
        with col_left:
            st.markdown("### 💬 Chat")
            with st.container():
                chat_interface.render_chat_interface()
                
        with col_right:
            st.markdown("### 📄 Document")
            with st.container():
                if document:
                    self.document_renderer.set_document(document)
                    self.document_renderer.render_document_header()
                    self.document_renderer.render_search_controls()
                    self.document_renderer.render_document_content()
                else:
                    st.info("No document selected")
                    
        # Citation panel in sidebar for split view
        with st.sidebar:
            st.markdown("### 📚 Document Tools")
            if document:
                self.citation_navigator.render_citation_panel()


class DocumentSearchInterface:
    """Interface for searching and selecting documents."""
    
    def __init__(self):
        """Initialize document search interface."""
        self.available_documents: List[DocumentContent] = []
        
    def set_available_documents(self, documents: List[DocumentContent]):
        """Set available documents for selection."""
        self.available_documents = documents
        
    def render_document_selector(self) -> Optional[DocumentContent]:
        """Render document selection interface."""
        st.markdown("### 📚 Document Library")
        
        if not self.available_documents:
            st.info("No documents available. Please add documents to the library.")
            return None
            
        # Search/filter controls
        col1, col2 = st.columns([2, 1])
        
        with col1:
            search_term = st.text_input(
                "Search documents",
                placeholder="Search by title, author, or content...",
                key="doc_library_search"
            )
            
        with col2:
            author_filter = st.selectbox(
                "Filter by Author",
                ["All"] + list(set(doc.author for doc in self.available_documents if doc.author)),
                key="author_filter"
            )
            
        # Filter documents
        filtered_docs = self._filter_documents(search_term, author_filter)
        
        if not filtered_docs:
            st.warning("No documents match your search criteria.")
            return None
            
        # Document selection
        selected_doc_title = st.selectbox(
            "Select Document",
            [f"{doc.title} - {doc.author}" for doc in filtered_docs],
            key="selected_document"
        )
        
        if selected_doc_title:
            # Find the selected document
            selected_doc = next(
                (doc for doc in filtered_docs 
                 if f"{doc.title} - {doc.author}" == selected_doc_title),
                None
            )
            
            if selected_doc:
                # Show document preview
                with st.expander("📖 Document Preview", expanded=False):
                    st.markdown(f"**Title:** {selected_doc.title}")
                    st.markdown(f"**Author:** {selected_doc.author}")
                    preview_text = selected_doc.content[:500] + "..." if len(selected_doc.content) > 500 else selected_doc.content
                    st.markdown(f"**Preview:** {preview_text}")
                    
                return selected_doc
                
        return None
        
    def _filter_documents(self, search_term: str, author_filter: str) -> List[DocumentContent]:
        """Filter documents based on search criteria."""
        filtered = self.available_documents
        
        # Filter by author
        if author_filter != "All":
            filtered = [doc for doc in filtered if doc.author == author_filter]
            
        # Filter by search term
        if search_term:
            search_lower = search_term.lower()
            filtered = [
                doc for doc in filtered
                if (search_lower in doc.title.lower() or
                    search_lower in doc.author.lower() or
                    search_lower in doc.content.lower())
            ]
            
        return filtered


def create_sample_documents() -> List[DocumentContent]:
    """Create sample documents for testing."""
    return [
        DocumentContent(
            doc_id="plato_republic",
            title="The Republic",
            author="Plato",
            content="Now, I said, make another image to show how far our nature is enlightened or unenlightened. Imagine human beings living in an underground cave...",
            metadata={"period": "ancient", "topic": "political_philosophy"}
        ),
        DocumentContent(
            doc_id="aristotle_ethics",
            title="Nicomachean Ethics",
            author="Aristotle",
            content="Every art and every inquiry, and similarly every action and pursuit, is thought to aim at some good...",
            metadata={"period": "ancient", "topic": "ethics"}
        )
    ]


def create_sample_citations() -> List[Citation]:
    """Create sample citations for testing."""
    return [
        Citation(
            citation_id="cave_allegory",
            document_id="plato_republic",
            start_pos=50,
            end_pos=150,
            text="Imagine human beings living in an underground cave",
            reference="Republic 514a"
        ),
        Citation(
            citation_id="good_definition",
            document_id="aristotle_ethics",
            start_pos=0,
            end_pos=80,
            text="Every art and every inquiry, and similarly every action and pursuit, is thought to aim at some good",
            reference="Ethics 1094a"
        )
    ]