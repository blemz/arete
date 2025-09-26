"""Document state management for the document viewer component."""

import reflex as rx
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Citation:
    """Citation data model."""
    id: str
    text: str
    preview_text: str
    full_text: str
    author: str
    work: str
    section: str
    page: str
    position: int
    type: str = "citation"


@dataclass  
class DocumentSection:
    """Document section for table of contents."""
    id: str
    title: str
    level: int
    position: int


@dataclass
class DocumentContent:
    """Document content element (text or citation)."""
    text: str
    type: str  # "text" or "citation"
    highlighted: bool = False
    citation_data: Optional[Citation] = None


@dataclass
class DocumentParagraph:
    """Document paragraph with mixed content."""
    id: str
    content: List[DocumentContent]
    position: int


@dataclass
class Bookmark:
    """Document bookmark."""
    id: str
    title: str
    preview: str
    position: int
    created_at: datetime


@dataclass
class SearchResult:
    """Search result with position and context."""
    position: int
    text: str
    context: str
    paragraph_id: str


@dataclass
class DocumentMetadata:
    """Document metadata model."""
    id: str
    title: str
    author: str
    date: str
    word_count: int
    type: str
    description: str
    sections: List[DocumentSection]
    paragraphs: List[DocumentParagraph]
    citations: List[Citation]


class DocumentState(rx.State):
    """State management for document viewer functionality."""
    
    # Current document
    current_document: DocumentMetadata = DocumentMetadata(
        id="", title="", author="", date="", word_count=0, type="",
        description="", sections=[], paragraphs=[], citations=[]
    )
    
    # Document library
    documents: List[DocumentMetadata] = []
    library_search: str = ""
    filtered_documents: List[DocumentMetadata] = []
    
    # Search functionality
    show_search: bool = False
    search_query: str = ""
    search_results: List[SearchResult] = []
    current_search_index: int = 0
    
    # Citation system
    show_citation_modal: bool = False
    selected_citation: Citation = Citation(
        id="", text="", preview_text="", full_text="", 
        author="", work="", section="", page="", position=0
    )
    
    # Navigation and progress
    reading_progress: int = 0
    current_position: int = 0
    
    # Bookmarks
    show_bookmarks: bool = False
    bookmarks: List[Bookmark] = []
    
    # Export functionality
    show_export_menu: bool = False
    
    def __init__(self):
        super().__init__()
        self.load_document_library()
    
    def load_document_library(self):
        """Load available documents from the RAG system."""
        # Mock data - in production this would connect to the actual document corpus
        self.documents = [
            DocumentMetadata(
                id="plato_apology",
                title="Apology",
                author="Plato",
                date="399 BCE", 
                word_count=12500,
                type="Dialogue",
                description="Socrates' defense speech at his trial for impiety and corrupting youth.",
                sections=[
                    DocumentSection("intro", "Introduction", 1, 0),
                    DocumentSection("charges", "The Charges", 1, 100),
                    DocumentSection("defense", "Socrates' Defense", 1, 500),
                    DocumentSection("penalty", "The Penalty", 1, 900)
                ],
                paragraphs=[],
                citations=[]
            ),
            DocumentMetadata(
                id="plato_charmides", 
                title="Charmides",
                author="Plato",
                date="390 BCE",
                word_count=8900,
                type="Dialogue",
                description="An exploration of temperance and self-knowledge through dialogue.",
                sections=[
                    DocumentSection("opening", "Opening Scene", 1, 0),
                    DocumentSection("temperance", "On Temperance", 1, 200),
                    DocumentSection("knowledge", "Self-Knowledge", 1, 600)
                ],
                paragraphs=[],
                citations=[]
            ),
            DocumentMetadata(
                id="aristotle_ethics",
                title="Nicomachean Ethics",
                author="Aristotle", 
                date="350 BCE",
                word_count=95000,
                type="Treatise",
                description="Aristotle's comprehensive work on ethics and the good life.",
                sections=[
                    DocumentSection("book1", "Book I: The Good", 1, 0),
                    DocumentSection("book2", "Book II: Virtue", 1, 1000),
                    DocumentSection("book3", "Book III: Voluntary Action", 1, 2000),
                    DocumentSection("book10", "Book X: Happiness", 1, 9000)
                ],
                paragraphs=[],
                citations=[]
            )
        ]
        self.filtered_documents = self.documents.copy()
    
    def set_library_search(self, query: str):
        """Filter document library by search query."""
        self.library_search = query
        if not query:
            self.filtered_documents = self.documents.copy()
        else:
            self.filtered_documents = [
                doc for doc in self.documents
                if query.lower() in doc.title.lower() 
                or query.lower() in doc.author.lower()
                or query.lower() in doc.description.lower()
            ]
    
    def load_document(self, document_id: str):
        """Load a specific document for viewing."""
        doc = next((d for d in self.documents if d.id == document_id), None)
        if doc:
            # In production, this would load the full document content from the RAG system
            self.current_document = self._load_full_document_content(doc)
            self.reading_progress = 0
            self.current_position = 0
    
    def _load_full_document_content(self, doc: DocumentMetadata) -> DocumentMetadata:
        """Load full document content including paragraphs and citations."""
        # Mock implementation - in production this would query the actual document corpus
        sample_citations = [
            Citation(
                id="cite_1",
                text="examined life",
                preview_text="The unexamined life is not worth living for a human being.",
                full_text="The unexamined life is not worth living for a human being. This is what I have learned from the god, and I believe it to be true.",
                author="Plato",
                work="Apology",
                section="38a",
                page="42",
                position=850
            ),
            Citation(
                id="cite_2", 
                text="wisdom",
                preview_text="Human wisdom is of little or no value compared to divine wisdom.",
                full_text="When I heard this, I thought to myself: What can the god mean? What is the riddle? I am conscious that I am not wise either much or little.",
                author="Plato",
                work="Apology", 
                section="21b",
                page="28",
                position=200
            )
        ]
        
        sample_content = [
            DocumentContent("When I heard this oracle, I thought to myself: What can the god mean? For I am conscious that I am not ", "text"),
            DocumentContent("wise", "citation", citation_data=sample_citations[1]),
            DocumentContent(" either much or little. What then does he mean by saying that I am the wisest? For he certainly does not lie; that is not his way.", "text")
        ]
        
        sample_paragraphs = [
            DocumentParagraph(
                id="para_1",
                content=sample_content,
                position=1
            ),
            DocumentParagraph(
                id="para_2", 
                content=[
                    DocumentContent("The ", "text"),
                    DocumentContent("examined life", "citation", citation_data=sample_citations[0]),
                    DocumentContent(" is the only life worth living, according to Socrates in his final speech.", "text")
                ],
                position=2
            )
        ]
        
        doc.paragraphs = sample_paragraphs
        doc.citations = sample_citations
        return doc
    
    def toggle_search(self):
        """Toggle search panel visibility."""
        self.show_search = not self.show_search
        if not self.show_search:
            self.clear_search()
    
    def set_search_query(self, query: str):
        """Set search query."""
        self.search_query = query
    
    def handle_search_keydown(self, key: str):
        """Handle search input keydown events."""
        if key == "Enter":
            self.search_document()
    
    def search_document(self):
        """Search current document content."""
        if not self.search_query or not self.current_document.paragraphs:
            return
            
        results = []
        for para in self.current_document.paragraphs:
            full_text = "".join([content.text for content in para.content])
            if self.search_query.lower() in full_text.lower():
                # Find position of match
                match_pos = full_text.lower().find(self.search_query.lower())
                context_start = max(0, match_pos - 50)
                context_end = min(len(full_text), match_pos + len(self.search_query) + 50)
                context = full_text[context_start:context_end]
                
                results.append(SearchResult(
                    position=para.position,
                    text=self.search_query,
                    context=context,
                    paragraph_id=para.id
                ))
        
        self.search_results = results
        self.current_search_index = 0
        if results:
            self.jump_to_search_result(0)
    
    def clear_search(self):
        """Clear search results and highlighting."""
        self.search_query = ""
        self.search_results = []
        self.current_search_index = 0
        self._clear_highlighting()
    
    def previous_search_result(self):
        """Navigate to previous search result."""
        if self.current_search_index > 0:
            self.current_search_index -= 1
            self.jump_to_search_result(self.current_search_index)
    
    def next_search_result(self):
        """Navigate to next search result."""
        if self.current_search_index < len(self.search_results) - 1:
            self.current_search_index += 1
            self.jump_to_search_result(self.current_search_index)
    
    def jump_to_search_result(self, index: int):
        """Jump to specific search result and highlight."""
        if 0 <= index < len(self.search_results):
            result = self.search_results[index]
            self.current_position = result.position
            self._highlight_search_term(result.paragraph_id, self.search_query)
    
    def _highlight_search_term(self, paragraph_id: str, term: str):
        """Highlight search term in specified paragraph."""
        # Implementation would update highlighting state
        pass
    
    def _clear_highlighting(self):
        """Clear all text highlighting."""
        # Implementation would clear highlighting state
        pass
    
    def jump_to_section(self, section_id: str):
        """Jump to document section."""
        section = next((s for s in self.current_document.sections if s.id == section_id), None)
        if section:
            self.current_position = section.position
            self._calculate_reading_progress()
    
    def _calculate_reading_progress(self):
        """Calculate reading progress percentage."""
        if self.current_document.paragraphs:
            total_paragraphs = len(self.current_document.paragraphs)
            current_para = min(self.current_position, total_paragraphs)
            self.reading_progress = int((current_para / total_paragraphs) * 100)
    
    def open_citation_modal(self, citation_id: str):
        """Open citation detail modal."""
        citation = next((c for c in self.current_document.citations if c.id == citation_id), None)
        if citation:
            self.selected_citation = citation
            self.show_citation_modal = True
    
    def close_citation_modal(self):
        """Close citation modal."""
        self.show_citation_modal = False
    
    def previous_citation(self):
        """Navigate to previous citation."""
        current_index = next((i for i, c in enumerate(self.current_document.citations) if c.id == self.selected_citation.id), -1)
        if current_index > 0:
            self.selected_citation = self.current_document.citations[current_index - 1]
    
    def next_citation(self):
        """Navigate to next citation."""
        current_index = next((i for i, c in enumerate(self.current_document.citations) if c.id == self.selected_citation.id), -1)
        if current_index < len(self.current_document.citations) - 1:
            self.selected_citation = self.current_document.citations[current_index + 1]
    
    @rx.var
    def has_previous_citation(self) -> bool:
        """Check if there is a previous citation."""
        current_index = next((i for i, c in enumerate(self.current_document.citations) if c.id == self.selected_citation.id), -1)
        return current_index > 0
    
    @rx.var
    def has_next_citation(self) -> bool:
        """Check if there is a next citation."""
        current_index = next((i for i, c in enumerate(self.current_document.citations) if c.id == self.selected_citation.id), -1)
        return current_index < len(self.current_document.citations) - 1
    
    def copy_citation(self):
        """Copy citation to clipboard."""
        # Implementation would copy citation text to clipboard
        pass
    
    def share_citation(self):
        """Share citation."""
        # Implementation would provide sharing options
        pass
    
    def toggle_bookmarks(self):
        """Toggle bookmarks panel."""
        self.show_bookmarks = not self.show_bookmarks
    
    def close_bookmarks(self):
        """Close bookmarks panel."""
        self.show_bookmarks = False
    
    def add_bookmark(self, title: str, preview: str, position: int):
        """Add bookmark at current position."""
        bookmark = Bookmark(
            id=f"bookmark_{len(self.bookmarks)}",
            title=title,
            preview=preview,
            position=position,
            created_at=datetime.now()
        )
        self.bookmarks.append(bookmark)
    
    def remove_bookmark(self, bookmark_id: str):
        """Remove bookmark."""
        self.bookmarks = [b for b in self.bookmarks if b.id != bookmark_id]
    
    def jump_to_bookmark(self, bookmark_id: str):
        """Jump to bookmark position."""
        bookmark = next((b for b in self.bookmarks if b.id == bookmark_id), None)
        if bookmark:
            self.current_position = bookmark.position
            self._calculate_reading_progress()
            self.close_bookmarks()
    
    def toggle_export_menu(self):
        """Toggle export menu."""
        self.show_export_menu = not self.show_export_menu
    
    def export_document(self, format: str):
        """Export document in specified format."""
        # Implementation would handle document export
        self.show_export_menu = False
        # Add success notification
        pass