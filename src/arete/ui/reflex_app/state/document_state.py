"""Document state management with split-view integration."""

import reflex as rx
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime


class DocumentSection(rx.Base):
    """Document section model."""
    id: str
    title: str
    content: str
    level: int  # Heading level (1-6)
    position: float  # Position in document (0.0 - 1.0)
    word_count: int


class DocumentAnnotation(rx.Base):
    """Document annotation model."""
    id: str
    type: str  # "highlight", "note", "citation"
    start_position: int
    end_position: int
    text: str
    note: str = ""
    timestamp: datetime
    color: str = "yellow"


class DocumentSearchResult(rx.Base):
    """Document search result model."""
    id: str
    text: str
    position: float
    context: str
    relevance_score: float


class DocumentState(rx.State):
    """State management for document viewer with split-view coordination."""
    
    # Document content
    document_id: Optional[str] = None
    document_title: str = ""
    document_content: str = ""
    document_url: str = ""
    
    # Document structure
    sections: List[DocumentSection] = []
    table_of_contents: List[Dict[str, Any]] = []
    
    # Navigation
    current_position: float = 0.0  # 0.0 to 1.0
    current_section_id: Optional[str] = None
    scroll_position: int = 0
    
    # Search functionality
    search_query: str = ""
    search_results: List[DocumentSearchResult] = []
    current_search_index: int = 0
    search_highlights: List[Dict[str, Any]] = []
    
    # Citation system
    citations: List[Dict[str, Any]] = []
    active_citations: List[str] = []
    citation_highlights: Dict[str, str] = {}  # citation_id -> color
    
    # Annotations
    annotations: List[DocumentAnnotation] = []
    selected_text: str = ""
    selection_range: Tuple[int, int] = (0, 0)
    
    # Compact mode for split view
    compact_mode: bool = False
    sidebar_visible: bool = True
    
    # Loading state
    is_loading: bool = False
    error_message: str = ""
    
    # Performance optimization
    render_chunk_size: int = 1000  # Characters to render at once
    lazy_loading_enabled: bool = True
    
    def load_document(self, document_id: str, url: str):
        """Load document content."""
        self.is_loading = True
        self.error_message = ""
        
        try:
            # Simulate document loading (would integrate with actual document service)
            self.document_id = document_id
            self.document_url = url
            self._load_document_async(document_id, url)
        except Exception as e:
            self.error_message = f"Failed to load document: {str(e)}"
            self.is_loading = False
    
    def _load_document_async(self, document_id: str, url: str):
        """Load document content asynchronously."""
        # Mock document loading
        import time
        time.sleep(0.5)  # Simulate loading time
        
        # Mock document content
        self.document_title = "Plato's Apology"
        self.document_content = """
        The Apology of Socrates, written by Plato, is a Socratic dialogue of the speech 
        of legal self-defence which Socrates spoke at his trial for impiety and corruption 
        in 399 BCE. Specifically, the Apology of Socrates is a defence against the charges 
        of "corrupting the young, and by not believing in the gods in whom the city believes, 
        but in other daimonia that are novel" (24b).
        
        In this dialogue, Socrates explains who he is and what kind of life he has lived. 
        The text is divided into three main parts: the main speech, the counter-assessment, 
        and the final speech.
        """
        
        # Generate sections
        self.sections = [
            DocumentSection(
                id="section_1",
                title="Introduction",
                content="The Apology of Socrates, written by Plato...",
                level=1,
                position=0.0,
                word_count=50
            ),
            DocumentSection(
                id="section_2", 
                title="Main Speech",
                content="In this dialogue, Socrates explains...",
                level=1,
                position=0.4,
                word_count=75
            ),
            DocumentSection(
                id="section_3",
                title="Final Words",
                content="The text is divided into three main parts...",
                level=1,
                position=0.8,
                word_count=25
            )
        ]
        
        # Generate table of contents
        self._generate_table_of_contents()
        
        # Load citations
        self._load_citations()
        
        self.is_loading = False
    
    def load_document_by_citation(self, citation_id: str):
        """Load document based on citation reference."""
        # Mock citation-based loading
        citation_data = self._get_citation_data(citation_id)
        if citation_data:
            self.load_document(citation_data["document_id"], citation_data["url"])
    
    def _get_citation_data(self, citation_id: str) -> Optional[Dict[str, Any]]:
        """Get citation data by ID."""
        # Mock citation lookup
        return {
            "document_id": "doc_plato_apology",
            "url": "/documents/plato_apology.pdf",
            "title": "Plato's Apology"
        }
    
    def _generate_table_of_contents(self):
        """Generate table of contents from sections."""
        self.table_of_contents = [
            {
                "id": section.id,
                "title": section.title,
                "level": section.level,
                "position": section.position
            }
            for section in self.sections
        ]
    
    def _load_citations(self):
        """Load citation data for document."""
        self.citations = [
            {
                "id": "cite_1",
                "text": "corrupting the young, and by not believing in the gods",
                "position": 0.25,
                "section_id": "section_1",
                "relevance_score": 0.9
            },
            {
                "id": "cite_2",
                "text": "what kind of life he has lived",
                "position": 0.6,
                "section_id": "section_2",
                "relevance_score": 0.8
            }
        ]
    
    def perform_search(self, query: str):
        """Perform document search."""
        self.search_query = query
        self.current_search_index = 0
        
        if not query.strip():
            self.search_results.clear()
            self.search_highlights.clear()
            return
        
        # Mock search implementation
        self.search_results = [
            DocumentSearchResult(
                id="result_1",
                text="corrupting the young",
                position=0.25,
                context="...charges of corrupting the young, and by not believing...",
                relevance_score=0.95
            ),
            DocumentSearchResult(
                id="result_2", 
                text="Socrates explains",
                position=0.6,
                context="...In this dialogue, Socrates explains who he is...",
                relevance_score=0.8
            )
        ]
        
        # Generate search highlights
        self._generate_search_highlights()
    
    def _generate_search_highlights(self):
        """Generate search highlights from results."""
        self.search_highlights = [
            {
                "id": result.id,
                "start": int(result.position * len(self.document_content)),
                "end": int(result.position * len(self.document_content)) + len(result.text),
                "color": "bg-yellow-200 dark:bg-yellow-800"
            }
            for result in self.search_results
        ]
    
    def navigate_to_search_result(self, index: int):
        """Navigate to specific search result."""
        if 0 <= index < len(self.search_results):
            self.current_search_index = index
            result = self.search_results[index]
            self.scroll_to_position(result.position)
    
    def next_search_result(self):
        """Navigate to next search result."""
        if self.search_results:
            next_index = (self.current_search_index + 1) % len(self.search_results)
            self.navigate_to_search_result(next_index)
    
    def previous_search_result(self):
        """Navigate to previous search result."""
        if self.search_results:
            prev_index = (self.current_search_index - 1) % len(self.search_results)
            self.navigate_to_search_result(prev_index)
    
    def scroll_to_position(self, position: float):
        """Scroll to specific position in document."""
        self.current_position = max(0.0, min(1.0, position))
        
        # Update current section
        for section in self.sections:
            if section.position <= position:
                self.current_section_id = section.id
    
    def scroll_to_citation(self, citation_id: str):
        """Scroll to specific citation."""
        citation = next(
            (cite for cite in self.citations if cite["id"] == citation_id),
            None
        )
        
        if citation:
            self.scroll_to_position(citation["position"])
            self.highlight_citation(citation_id)
    
    def highlight_citation(self, citation_id: str, color: str = "bg-blue-200 dark:bg-blue-800"):
        """Highlight specific citation."""
        if citation_id not in self.active_citations:
            self.active_citations.append(citation_id)
        
        self.citation_highlights[citation_id] = color
    
    def remove_citation_highlight(self, citation_id: str):
        """Remove citation highlight."""
        if citation_id in self.active_citations:
            self.active_citations.remove(citation_id)
        
        if citation_id in self.citation_highlights:
            del self.citation_highlights[citation_id]
    
    def clear_citation_highlights(self):
        """Clear all citation highlights."""
        self.active_citations.clear()
        self.citation_highlights.clear()
    
    def add_annotation(self, annotation_type: str, note: str = "", color: str = "yellow"):
        """Add annotation to selected text."""
        if not self.selected_text or self.selection_range == (0, 0):
            return
        
        annotation = DocumentAnnotation(
            id=f"annotation_{len(self.annotations)}_{datetime.now().timestamp()}",
            type=annotation_type,
            start_position=self.selection_range[0],
            end_position=self.selection_range[1],
            text=self.selected_text,
            note=note,
            timestamp=datetime.now(),
            color=color
        )
        
        self.annotations.append(annotation)
        self.clear_selection()
    
    def remove_annotation(self, annotation_id: str):
        """Remove annotation."""
        self.annotations = [
            ann for ann in self.annotations 
            if ann.id != annotation_id
        ]
    
    def set_text_selection(self, text: str, start: int, end: int):
        """Set selected text range."""
        self.selected_text = text
        self.selection_range = (start, end)
    
    def clear_selection(self):
        """Clear text selection."""
        self.selected_text = ""
        self.selection_range = (0, 0)
    
    def toggle_sidebar(self):
        """Toggle sidebar visibility."""
        self.sidebar_visible = not self.sidebar_visible
    
    def set_compact_mode(self, compact: bool):
        """Set compact mode state."""
        self.compact_mode = compact
    
    def jump_to_section(self, section_id: str):
        """Jump to specific document section."""
        section = next(
            (sec for sec in self.sections if sec.id == section_id),
            None
        )
        
        if section:
            self.scroll_to_position(section.position)
    
    def export_annotations(self) -> str:
        """Export annotations as formatted text."""
        if not self.annotations:
            return "No annotations found."
        
        export_lines = [f"# Annotations for {self.document_title}", ""]
        
        for annotation in sorted(self.annotations, key=lambda a: a.start_position):
            export_lines.extend([
                f"**{annotation.type.title()}:** {annotation.text}",
                f"**Note:** {annotation.note}" if annotation.note else "",
                f"**Date:** {annotation.timestamp.strftime('%Y-%m-%d %H:%M')}",
                ""
            ])
        
        return "\n".join(export_lines)
    
    # Computed properties
    
    @rx.var
    def has_document(self) -> bool:
        """Check if document is loaded."""
        return self.document_id is not None and bool(self.document_content)
    
    @rx.var
    def search_result_count(self) -> int:
        """Get search result count."""
        return len(self.search_results)
    
    @rx.var
    def current_search_result(self) -> Optional[DocumentSearchResult]:
        """Get current search result."""
        if (self.search_results and 
            0 <= self.current_search_index < len(self.search_results)):
            return self.search_results[self.current_search_index]
        return None
    
    @rx.var
    def annotation_count(self) -> int:
        """Get annotation count."""
        return len(self.annotations)
    
    @rx.var
    def citation_count(self) -> int:
        """Get citation count."""
        return len(self.citations)
    
    @rx.var
    def active_citation_count(self) -> int:
        """Get active citation count."""
        return len(self.active_citations)
    
    @rx.var
    def current_section(self) -> Optional[DocumentSection]:
        """Get current document section."""
        if self.current_section_id:
            return next(
                (sec for sec in self.sections if sec.id == self.current_section_id),
                None
            )
        return None
    
    @rx.var
    def progress_percentage(self) -> int:
        """Get reading progress as percentage."""
        return int(self.current_position * 100)