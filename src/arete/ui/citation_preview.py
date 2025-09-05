"""
Interactive Citation Preview Component.

Provides hover and click interactions for citations with expandable details,
supporting scholarly display of philosophical references.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import streamlit as st
from streamlit.components.v1 import html


@dataclass
class CitationDetails:
    """Extended citation information for preview display."""
    
    # Core citation data
    citation_id: str
    text: str
    source: str
    author: Optional[str] = None
    work: Optional[str] = None
    reference: Optional[str] = None  # e.g., "Republic 514a"
    
    # Additional context
    context: Optional[str] = None
    confidence: float = 1.0
    relevance_score: float = 0.0
    
    # Metadata
    chunk_id: Optional[str] = None
    position: Optional[int] = None
    document_id: Optional[str] = None
    
    # Display state
    is_expanded: bool = False
    preview_length: int = 200
    
    def get_preview(self) -> str:
        """Get truncated preview of citation text."""
        if len(self.text) <= self.preview_length:
            return self.text
        return f"{self.text[:self.preview_length]}..."
    
    def get_formatted_reference(self) -> str:
        """Get formatted classical reference."""
        if self.author and self.work and self.reference:
            return f"{self.author}, {self.work} {self.reference}"
        elif self.work and self.reference:
            return f"{self.work} {self.reference}"
        elif self.reference:
            return self.reference
        return self.source
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for export."""
        return {
            "citation_id": self.citation_id,
            "text": self.text,
            "source": self.source,
            "author": self.author,
            "work": self.work,
            "reference": self.reference,
            "context": self.context,
            "confidence": self.confidence,
            "relevance_score": self.relevance_score,
            "chunk_id": self.chunk_id,
            "position": self.position,
            "document_id": self.document_id
        }


class InteractiveCitationPreview:
    """
    Interactive citation preview component with hover and click interactions.
    
    Features:
    - Hover to show citation preview
    - Click to expand full citation
    - Contextual information display
    - Confidence and relevance indicators
    """
    
    def __init__(self):
        """Initialize the citation preview component."""
        if "expanded_citations" not in st.session_state:
            st.session_state.expanded_citations = set()
        if "hovered_citation" not in st.session_state:
            st.session_state.hovered_citation = None
    
    def render_citation_card(self, citation: CitationDetails, index: int) -> None:
        """
        Render an interactive citation card.
        
        Args:
            citation: Citation details to display
            index: Index for unique component identification
        """
        is_expanded = citation.citation_id in st.session_state.expanded_citations
        
        with st.container():
            # Citation header with click interaction
            col1, col2, col3 = st.columns([8, 1, 1])
            
            with col1:
                if st.button(
                    f"📚 {citation.get_formatted_reference()}",
                    key=f"cite_header_{index}",
                    use_container_width=True,
                    help="Click to expand/collapse"
                ):
                    if is_expanded:
                        st.session_state.expanded_citations.discard(citation.citation_id)
                    else:
                        st.session_state.expanded_citations.add(citation.citation_id)
                    st.rerun()
            
            with col2:
                # Confidence indicator
                confidence_color = self._get_confidence_color(citation.confidence)
                st.markdown(
                    f"<span style='color: {confidence_color}; font-weight: bold;'>"
                    f"{citation.confidence:.0%}</span>",
                    unsafe_allow_html=True
                )
            
            with col3:
                # Relevance indicator
                relevance_color = self._get_relevance_color(citation.relevance_score)
                st.markdown(
                    f"<span style='color: {relevance_color}; font-weight: bold;'>"
                    f"{citation.relevance_score:.0%}</span>",
                    unsafe_allow_html=True
                )
            
            # Citation content
            if is_expanded:
                self._render_expanded_citation(citation, index)
            else:
                self._render_preview_citation(citation, index)
    
    def _render_preview_citation(self, citation: CitationDetails, index: int) -> None:
        """Render citation preview (collapsed state)."""
        with st.container():
            # Apply hover effect with CSS
            hover_html = f"""
            <div class="citation-preview" id="cite-preview-{index}"
                 onmouseover="this.style.backgroundColor='#f8f9fa'; this.style.cursor='pointer';"
                 onmouseout="this.style.backgroundColor='transparent';"
                 style="padding: 10px; border-radius: 5px; transition: background-color 0.3s;">
                <p style="margin: 0; color: #495057; font-style: italic;">
                    "{citation.get_preview()}"
                </p>
                {f'<p style="margin: 5px 0 0 0; color: #6c757d; font-size: 0.9em;">— {citation.author}</p>' if citation.author else ''}
            </div>
            """
            st.markdown(hover_html, unsafe_allow_html=True)
    
    def _render_expanded_citation(self, citation: CitationDetails, index: int) -> None:
        """Render expanded citation with full details."""
        with st.expander("Citation Details", expanded=True):
            # Full text
            st.markdown("**Full Text:**")
            st.markdown(f"_{citation.text}_")
            
            # Metadata columns
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Source Information:**")
                if citation.author:
                    st.text(f"Author: {citation.author}")
                if citation.work:
                    st.text(f"Work: {citation.work}")
                if citation.reference:
                    st.text(f"Reference: {citation.reference}")
                st.text(f"Source: {citation.source}")
            
            with col2:
                st.markdown("**Quality Metrics:**")
                st.text(f"Confidence: {citation.confidence:.1%}")
                st.text(f"Relevance: {citation.relevance_score:.1%}")
                if citation.position:
                    st.text(f"Position: {citation.position}")
            
            # Context if available
            if citation.context:
                st.markdown("**Context:**")
                st.info(citation.context)
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📋 Copy", key=f"copy_{index}"):
                    self._copy_to_clipboard(citation)
            with col2:
                if st.button("🔗 Share", key=f"share_{index}"):
                    self._share_citation(citation)
            with col3:
                if st.button("📍 Go to Source", key=f"goto_{index}"):
                    self._navigate_to_source(citation)
    
    def render_citation_list(self, citations: List[CitationDetails]) -> None:
        """
        Render a list of interactive citations.
        
        Args:
            citations: List of citations to display
        """
        if not citations:
            st.info("No citations available")
            return
        
        # Add custom CSS for hover effects
        st.markdown("""
        <style>
        .citation-preview:hover {
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }
        .citation-card {
            border-left: 3px solid #007bff;
            padding-left: 15px;
            margin-bottom: 15px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Group citations by work/author for better organization
        grouped = self._group_citations(citations)
        
        for group_name, group_citations in grouped.items():
            with st.container():
                st.markdown(f"### {group_name}")
                for i, citation in enumerate(group_citations):
                    with st.container():
                        st.markdown('<div class="citation-card">', unsafe_allow_html=True)
                        self.render_citation_card(citation, f"{group_name}_{i}")
                        st.markdown('</div>', unsafe_allow_html=True)
    
    def _group_citations(self, citations: List[CitationDetails]) -> Dict[str, List[CitationDetails]]:
        """Group citations by work/author for organized display."""
        grouped = {}
        for citation in citations:
            if citation.work:
                key = f"{citation.author or 'Unknown'} - {citation.work}"
            elif citation.author:
                key = citation.author
            else:
                key = "Other Sources"
            
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(citation)
        
        return grouped
    
    def _get_confidence_color(self, confidence: float) -> str:
        """Get color based on confidence score."""
        if confidence >= 0.8:
            return "#28a745"  # Green
        elif confidence >= 0.6:
            return "#ffc107"  # Yellow
        else:
            return "#dc3545"  # Red
    
    def _get_relevance_color(self, relevance: float) -> str:
        """Get color based on relevance score."""
        if relevance >= 0.7:
            return "#007bff"  # Blue
        elif relevance >= 0.5:
            return "#17a2b8"  # Cyan
        else:
            return "#6c757d"  # Gray
    
    def _copy_to_clipboard(self, citation: CitationDetails) -> None:
        """Copy citation to clipboard."""
        formatted = citation.get_formatted_reference()
        if citation.text:
            formatted += f"\n\"{citation.text}\""
        
        # Note: Streamlit doesn't have direct clipboard access
        # This would need JavaScript component or user manual copy
        st.success("Citation ready to copy (select and Ctrl+C)")
        st.code(formatted)
    
    def _share_citation(self, citation: CitationDetails) -> None:
        """Share citation (placeholder for sharing functionality)."""
        st.info("Share functionality coming soon!")
    
    def _navigate_to_source(self, citation: CitationDetails) -> None:
        """Navigate to source document."""
        if citation.document_id:
            st.session_state.current_document = citation.document_id
            st.session_state.scroll_to_position = citation.position
            st.success(f"Navigating to source at position {citation.position}")
        else:
            st.warning("Source document not available")


def create_sample_citations() -> List[CitationDetails]:
    """Create sample citations for testing."""
    return [
        CitationDetails(
            citation_id="cite_1",
            text="The unexamined life is not worth living for a human being.",
            source="Apology 38a",
            author="Plato",
            work="Apology",
            reference="38a",
            context="Socrates' defense speech at his trial",
            confidence=0.95,
            relevance_score=0.88,
            position=1250
        ),
        CitationDetails(
            citation_id="cite_2",
            text="Virtue, then, is a state of character concerned with choice, lying in a mean relative to us, this being determined by reason and in the way in which the person of practical wisdom would determine it.",
            source="Nicomachean Ethics 1106b36",
            author="Aristotle",
            work="Nicomachean Ethics",
            reference="1106b36",
            context="Definition of moral virtue",
            confidence=0.92,
            relevance_score=0.75,
            position=3420
        ),
        CitationDetails(
            citation_id="cite_3",
            text="I think, therefore I am.",
            source="Discourse on Method",
            author="Descartes",
            work="Discourse on Method",
            reference="Part IV",
            context="Foundation of certain knowledge",
            confidence=0.99,
            relevance_score=0.65,
            position=890
        )
    ]