"""
Heading-Aware Chunking Strategy for Philosophical Texts

This chunker respects document structure by:
1. Never breaking within logical sections defined by headings
2. Maintaining hierarchical relationships between sections
3. Preserving philosophical argument boundaries 
4. Keeping related content together for better RAG performance
"""

import re
from typing import List, Dict, Optional, Tuple
from uuid import UUID
from dataclasses import dataclass

from ..models.chunk import Chunk, ChunkType


@dataclass
class HeadingInfo:
    """Information about a heading in the document."""
    
    level: int              # Heading level (1-6)
    title: str             # Heading text
    start_pos: int         # Character position where heading starts
    end_pos: int           # Character position where heading ends
    content_start: int     # Where content after heading starts
    content_end: int       # Where content before next heading ends
    parent_heading: Optional['HeadingInfo'] = None
    children: List['HeadingInfo'] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []


class HeadingAwareChunker:
    """
    Chunks text while respecting document structure and headings.
    
    This is especially valuable for philosophical texts where:
    - Arguments span multiple paragraphs
    - Sections build on each other logically  
    - Citations and cross-references need context
    - Hierarchical structure conveys meaning
    """
    
    def __init__(
        self, 
        max_chunk_size: int = 2000,
        min_chunk_size: int = 100,
        overlap_headings: bool = True,
        preserve_hierarchy: bool = True
    ):
        """
        Initialize heading-aware chunker.
        
        Args:
            max_chunk_size: Maximum characters per chunk
            min_chunk_size: Minimum characters per chunk (prevents tiny chunks)
            overlap_headings: Include parent heading context in child chunks
            preserve_hierarchy: Maintain hierarchical relationships in metadata
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.overlap_headings = overlap_headings
        self.preserve_hierarchy = preserve_hierarchy
        
        # Markdown heading pattern
        self.heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    
    def chunk_text(self, text: str, document_id: UUID) -> List[Chunk]:
        """
        Chunk text while respecting heading boundaries.
        
        Args:
            text: Text to be chunked (preferably markdown with headings)
            document_id: ID of the source document
            
        Returns:
            List of Chunk objects with structural metadata
        """
        
        # Extract heading structure
        headings = self._extract_headings(text)
        
        if not headings:
            # No headings found, fall back to paragraph chunking
            return self._fallback_paragraph_chunking(text, document_id)
        
        # Build hierarchical structure
        heading_tree = self._build_heading_hierarchy(headings)
        
        # Create chunks respecting heading boundaries
        chunks = self._create_heading_aware_chunks(text, heading_tree, document_id)
        
        return chunks
    
    def _extract_headings(self, text: str) -> List[HeadingInfo]:
        """Extract all headings with their positions and content boundaries."""
        
        headings = []
        matches = list(self.heading_pattern.finditer(text))
        
        for i, match in enumerate(matches):
            level = len(match.group(1))  # Number of # characters
            title = match.group(2).strip()
            start_pos = match.start()
            end_pos = match.end()
            content_start = end_pos + 1  # Content starts after heading line
            
            # Find where this heading's content ends (next heading or end of text)
            if i + 1 < len(matches):
                content_end = matches[i + 1].start()
            else:
                content_end = len(text)
            
            heading = HeadingInfo(
                level=level,
                title=title,
                start_pos=start_pos,
                end_pos=end_pos,
                content_start=content_start,
                content_end=content_end
            )
            headings.append(heading)
        
        return headings
    
    def _build_heading_hierarchy(self, headings: List[HeadingInfo]) -> List[HeadingInfo]:
        """Build hierarchical structure from flat heading list."""
        
        if not headings:
            return []
        
        # Stack to track parent headings at each level
        parent_stack = []
        root_headings = []
        
        for heading in headings:
            # Pop stack until we find appropriate parent level
            while parent_stack and parent_stack[-1].level >= heading.level:
                parent_stack.pop()
            
            # Set parent relationship
            if parent_stack:
                parent = parent_stack[-1]
                heading.parent_heading = parent
                parent.children.append(heading)
            else:
                # This is a root-level heading
                root_headings.append(heading)
            
            # Add to stack for future children
            parent_stack.append(heading)
        
        return root_headings
    
    def _create_heading_aware_chunks(
        self, 
        text: str, 
        heading_tree: List[HeadingInfo], 
        document_id: UUID
    ) -> List[Chunk]:
        """Create chunks that respect heading boundaries and hierarchy."""
        
        chunks = []
        
        # Process each top-level heading and its hierarchy
        for root_heading in heading_tree:
            chunks.extend(self._process_heading_section(text, root_heading, document_id))
        
        return chunks
    
    def _process_heading_section(
        self, 
        text: str, 
        heading: HeadingInfo, 
        document_id: UUID,
        parent_context: str = ""
    ) -> List[Chunk]:
        """Process a heading section and all its children."""
        
        chunks = []
        
        # Extract this section's content (without children)
        if heading.children:
            # Content ends where first child begins
            section_end = heading.children[0].start_pos
        else:
            # Content extends to the end of this section
            section_end = heading.content_end
        
        section_text = text[heading.content_start:section_end].strip()
        
        # Build context if overlapping with parent headings
        full_context = ""
        if self.overlap_headings and parent_context:
            full_context = f"{parent_context}\n\n"
        
        # Add this heading to context
        heading_text = f"{'#' * heading.level} {heading.title}"
        full_context += f"{heading_text}\n\n{section_text}"
        
        # Create chunk(s) for this section
        if len(full_context) <= self.max_chunk_size:
            # Single chunk for this section
            chunk = self._create_structural_chunk(
                text=full_context,
                document_id=document_id,
                heading=heading,
                position=len(chunks),
                start_char=heading.start_pos,
                end_char=section_end
            )
            chunks.append(chunk)
        
        else:
            # Section too large, split while preserving paragraphs
            section_chunks = self._split_large_section(
                full_context, heading, document_id, heading.start_pos, section_end
            )
            chunks.extend(section_chunks)
        
        # Process child headings recursively
        child_context = f"{heading_text}" if self.overlap_headings else ""
        
        for child in heading.children:
            child_chunks = self._process_heading_section(
                text, child, document_id, child_context
            )
            chunks.extend(child_chunks)
        
        return chunks
    
    def _split_large_section(
        self, 
        section_text: str, 
        heading: HeadingInfo, 
        document_id: UUID,
        start_char: int,
        end_char: int
    ) -> List[Chunk]:
        """Split a large section while respecting paragraph boundaries."""
        
        chunks = []
        
        # Split by paragraphs
        paragraphs = re.split(r'\n\s*\n', section_text)
        
        current_chunk = ""
        current_start = start_char
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # Check if adding this paragraph exceeds max size
            test_chunk = f"{current_chunk}\n\n{paragraph}" if current_chunk else paragraph
            
            if len(test_chunk) > self.max_chunk_size and current_chunk:
                # Create chunk from current content
                if len(current_chunk) >= self.min_chunk_size:
                    chunk = self._create_structural_chunk(
                        text=current_chunk,
                        document_id=document_id,
                        heading=heading,
                        position=len(chunks),
                        start_char=current_start,
                        end_char=current_start + len(current_chunk)
                    )
                    chunks.append(chunk)
                
                # Start new chunk with current paragraph
                current_chunk = paragraph
                current_start = current_start + len(current_chunk) + 2  # +2 for \n\n
            
            else:
                # Add paragraph to current chunk
                current_chunk = test_chunk
        
        # Handle remaining content
        if current_chunk and len(current_chunk) >= self.min_chunk_size:
            chunk = self._create_structural_chunk(
                text=current_chunk,
                document_id=document_id,
                heading=heading,
                position=len(chunks),
                start_char=current_start,
                end_char=end_char
            )
            chunks.append(chunk)
        
        return chunks
    
    def _create_structural_chunk(
        self,
        text: str,
        document_id: UUID,
        heading: HeadingInfo,
        position: int,
        start_char: int,
        end_char: int
    ) -> Chunk:
        """Create a chunk with rich structural metadata."""
        
        # Build hierarchical path (e.g., "Chapter 1 > Section 2 > Subsection A")
        hierarchy_path = self._build_hierarchy_path(heading)
        
        # Extract philosophical markers if present
        philosophical_role = self._detect_philosophical_role(heading.title)
        
        metadata = {
            'heading_title': heading.title,
            'heading_level': heading.level,
            'hierarchy_path': hierarchy_path,
            'structural_type': 'heading_aware',
            'philosophical_role': philosophical_role,
            'has_parent': heading.parent_heading is not None,
            'has_children': len(heading.children) > 0,
            'parent_title': heading.parent_heading.title if heading.parent_heading else None,
            'children_count': len(heading.children)
        }
        
        return Chunk(
            text=text,
            document_id=document_id,
            position=position,
            start_char=start_char,
            end_char=end_char,
            chunk_type=ChunkType.HEADING_AWARE,
            metadata=metadata
        )
    
    def _build_hierarchy_path(self, heading: HeadingInfo) -> str:
        """Build hierarchical path string for this heading."""
        
        path_parts = []
        current = heading
        
        # Walk up the hierarchy
        while current:
            path_parts.append(current.title)
            current = current.parent_heading
        
        # Reverse to get top-down path
        path_parts.reverse()
        return " > ".join(path_parts)
    
    def _detect_philosophical_role(self, title: str) -> Optional[str]:
        """Detect the philosophical role of a section from its title."""
        
        title_lower = title.lower()
        
        role_patterns = {
            'argument': ['argument', 'proof', 'demonstration', 'reasoning', 'case for'],
            'objection': ['objection', 'counter', 'criticism', 'refutation', 'against'],
            'response': ['response', 'reply', 'answer', 'solution', 'rebuttal'],
            'definition': ['definition', 'meaning', 'what is', 'essence', 'nature of'],
            'example': ['example', 'illustration', 'case', 'instance', 'analogy'],
            'conclusion': ['conclusion', 'therefore', 'thus', 'hence', 'summary'],
            'introduction': ['introduction', 'preface', 'overview', 'preliminary'],
            'analysis': ['analysis', 'examination', 'investigation', 'study'],
            'comparison': ['comparison', 'contrast', 'versus', 'compared to']
        }
        
        for role, keywords in role_patterns.items():
            if any(keyword in title_lower for keyword in keywords):
                return role
        
        return None
    
    def _fallback_paragraph_chunking(self, text: str, document_id: UUID) -> List[Chunk]:
        """Fallback to paragraph-based chunking when no headings are found."""
        
        # Simple paragraph chunking as fallback
        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        current_pos = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph or len(paragraph) < self.min_chunk_size:
                continue
            
            # Find actual position in text
            start_char = text.find(paragraph, current_pos)
            if start_char == -1:
                start_char = current_pos
            
            end_char = start_char + len(paragraph)
            
            chunk = Chunk(
                text=paragraph,
                document_id=document_id,
                position=len(chunks),
                start_char=start_char,
                end_char=end_char,
                chunk_type=ChunkType.PARAGRAPH,  # Fallback type
                metadata={'structural_type': 'fallback_paragraph'}
            )
            chunks.append(chunk)
            current_pos = end_char
        
        return chunks


# Integration with existing chunking system
class HeadingAwareChunkingStrategy(HeadingAwareChunker):
    """Adapter to integrate HeadingAwareChunker with existing ChunkingStrategy interface."""
    
    def chunk_text(self, text: str, document_id: UUID) -> List[Chunk]:
        """Implement ChunkingStrategy interface."""
        return super().chunk_text(text, document_id)