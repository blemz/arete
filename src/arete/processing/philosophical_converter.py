"""
Philosophical Text Conversion and Cleaning Module

This module provides enhanced PDF → Markdown → Cleaned Text pipeline specifically
optimized for classical philosophical texts with:
1. PyMuPDF4LLM for superior PDF → Markdown conversion
2. YAML front-matter for rich metadata
3. Heading-aware chunking strategies  
4. Structural GraphRAG (headings → nodes, links → edges)
5. Human-in-the-loop quality enhancement
"""

import re
import time
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

import pymupdf4llm

from ..models.document import Document, ProcessingStatus
from ..models.chunk import Chunk
from ..config import get_settings


class PhilosophicalPeriod(Enum):
    """Classical philosophical periods for metadata."""
    ANCIENT = "ancient"           # Pre-Socratic to Late Antiquity
    MEDIEVAL = "medieval"         # Augustine to Aquinas 
    RENAISSANCE = "renaissance"   # Humanism to early modern
    MODERN = "modern"            # Descartes to Kant
    CONTEMPORARY = "contemporary" # 19th century onwards


class TextType(Enum):
    """Types of philosophical texts."""
    DIALOGUE = "dialogue"         # Platonic dialogues
    TREATISE = "treatise"         # Systematic works (Ethics, Summa)
    COMMENTARY = "commentary"     # Commentary on other works
    LETTER = "letter"            # Correspondence  
    FRAGMENT = "fragment"        # Fragmentary works
    TRANSLATION = "translation"  # Modern translations


@dataclass
class PhilosophicalMetadata:
    """Rich metadata for philosophical texts with YAML front-matter support."""
    
    # Core bibliographic data
    title: str
    author: str
    translator: Optional[str] = None
    editor: Optional[str] = None
    original_language: str = "Ancient Greek"
    translation_language: str = "English"
    publication_year: Optional[int] = None
    publisher: Optional[str] = None
    isbn: Optional[str] = None
    
    # Philosophical categorization
    philosophical_period: PhilosophicalPeriod = PhilosophicalPeriod.ANCIENT
    text_type: TextType = TextType.TREATISE
    philosophical_school: Optional[str] = None  # Platonism, Aristotelianism, Stoicism
    
    # Content structure
    major_themes: List[str] = None
    key_concepts: List[str] = None
    related_works: List[str] = None
    cross_references: List[str] = None
    
    # Citation and reference format
    citation_style: str = "classical"  # "classical", "modern", "mixed"
    standard_abbreviations: Dict[str, str] = None  # "Rep." -> "Republic"
    
    # Processing metadata
    processing_date: str = None
    source_quality: str = "high"  # "high", "medium", "low"
    ocr_confidence: Optional[float] = None
    human_reviewed: bool = False
    
    def __post_init__(self):
        """Initialize default values."""
        if self.major_themes is None:
            self.major_themes = []
        if self.key_concepts is None:
            self.key_concepts = []
        if self.related_works is None:
            self.related_works = []
        if self.cross_references is None:
            self.cross_references = []
        if self.standard_abbreviations is None:
            self.standard_abbreviations = {}
        if self.processing_date is None:
            self.processing_date = datetime.now().isoformat()
    
    def to_yaml_frontmatter(self) -> str:
        """Convert to YAML front-matter format."""
        # Convert enums to strings for YAML serialization
        data = asdict(self)
        data['philosophical_period'] = self.philosophical_period.value
        data['text_type'] = self.text_type.value
        
        yaml_content = yaml.dump(data, default_flow_style=False, sort_keys=False)
        return f"---\n{yaml_content}---\n\n"
    
    @classmethod
    def from_yaml_frontmatter(cls, yaml_content: str) -> 'PhilosophicalMetadata':
        """Create from YAML front-matter."""
        data = yaml.safe_load(yaml_content)
        
        # Convert string enums back to enum objects
        if 'philosophical_period' in data:
            data['philosophical_period'] = PhilosophicalPeriod(data['philosophical_period'])
        if 'text_type' in data:
            data['text_type'] = TextType(data['text_type'])
        
        return cls(**data)


@dataclass 
class StructuralElement:
    """Represents a structural element (heading, section) for GraphRAG."""
    
    element_id: str
    element_type: str  # "book", "chapter", "section", "argument", "definition"
    title: str
    level: int  # Heading depth (1-6)
    content: str
    parent_id: Optional[str] = None
    children: List[str] = None
    cross_references: List[str] = None
    philosophical_role: Optional[str] = None  # "premise", "conclusion", "objection", "response"
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
        if self.cross_references is None:
            self.cross_references = []


class PhilosophicalConverter:
    """
    Advanced converter for philosophical texts with PyMuPDF4LLM and structural analysis.
    
    Features:
    - Superior PDF → Markdown conversion with PyMuPDF4LLM
    - Rich YAML front-matter metadata
    - Heading-aware chunking strategies
    - Structural GraphRAG preparation
    - Human review integration points
    """
    
    def __init__(self, config=None):
        self.config = config or get_settings()
        self.structural_elements: List[StructuralElement] = []
        self.cross_references: Dict[str, List[str]] = {}
    
    async def convert_pdf_to_enhanced_markdown(
        self, 
        pdf_path: str, 
        output_dir: str = "enhanced_texts",
        metadata: Optional[PhilosophicalMetadata] = None
    ) -> Tuple[str, PhilosophicalMetadata]:
        """
        Convert PDF to enhanced markdown with YAML front-matter and structural analysis.
        
        Returns:
            Tuple of (markdown_file_path, metadata)
        """
        
        print("🏛️ Enhanced Philosophical Text Conversion Pipeline")
        print("=" * 80)
        
        pdf_name = Path(pdf_path).stem
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Stage 1: PyMuPDF4LLM conversion with enhanced settings
        print(f"\n=== Stage 1: PyMuPDF4LLM PDF → Markdown Conversion ===")
        print(f"Input: {pdf_path}")
        
        try:
            # Use PyMuPDF4LLM for superior conversion
            markdown_text = pymupdf4llm.to_markdown(
                pdf_path,
                page_chunks=False,      # Get full document as single markdown
                write_images=True,      # Extract images for diagrams
                # Additional parameters for philosophical texts
                margins=0,              # Don't ignore margins (footnotes, marginalia)
                dpi=300,               # High resolution for Greek text/symbols
                extract_words=False,   # We'll do our own tokenization
                ignore_code=False,     # Preserve formatting for citations
                table_strategy="advanced"  # Better table detection for structured arguments
            )
            
            print(f"✅ Converted to markdown: {len(markdown_text):,} characters")
            
        except Exception as e:
            print(f"❌ PyMuPDF4LLM conversion failed: {e}")
            # Fallback to basic extraction if needed
            raise
        
        # Stage 2: Extract or create metadata
        if metadata is None:
            print(f"\n=== Stage 2: Generating Philosophical Metadata ===")
            metadata = self._extract_metadata_from_text(markdown_text, pdf_name)
        
        # Stage 3: Structural analysis
        print(f"\n=== Stage 3: Structural Analysis for GraphRAG ===")
        enhanced_markdown = self._perform_structural_analysis(markdown_text, metadata)
        
        # Stage 4: Generate enhanced markdown with front-matter
        print(f"\n=== Stage 4: Creating Enhanced Markdown ===")
        final_markdown = self._create_enhanced_markdown(enhanced_markdown, metadata)
        
        # Save enhanced markdown
        output_file = output_path / f"{pdf_name}_enhanced.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_markdown)
        
        print(f"✅ Enhanced markdown created: {output_file}")
        print(f"   Size: {len(final_markdown):,} characters")
        print(f"   Structural elements: {len(self.structural_elements)}")
        print(f"   Cross-references: {len(self.cross_references)}")
        
        return str(output_file), metadata
    
    def _extract_metadata_from_text(self, text: str, filename: str) -> PhilosophicalMetadata:
        """Extract metadata from text using heuristics and patterns."""
        
        # Try to extract title (first major heading)
        title_match = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
        title = title_match.group(1) if title_match else filename
        
        # Try to extract author from common patterns
        author_patterns = [
            r'[Bb]y\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'Author:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'^([A-Z][A-Z\s]+)$'  # ALL CAPS author names
        ]
        
        author = "Classical Philosopher"
        for pattern in author_patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                author = match.group(1).strip()
                break
        
        # Detect philosophical period based on content
        period = PhilosophicalPeriod.ANCIENT
        if any(name in text for name in ['Plato', 'Aristotle', 'Socrates']):
            period = PhilosophicalPeriod.ANCIENT
        elif any(name in text for name in ['Augustine', 'Aquinas', 'Maimonides']):
            period = PhilosophicalPeriod.MEDIEVAL
        elif any(name in text for name in ['Descartes', 'Spinoza', 'Leibniz']):
            period = PhilosophicalPeriod.MODERN
        
        # Extract key concepts from philosophical terms
        philosophical_terms = [
            'justice', 'virtue', 'soul', 'form', 'idea', 'good', 'truth', 'beauty',
            'being', 'essence', 'existence', 'substance', 'causation', 'knowledge',
            'wisdom', 'courage', 'temperance', 'piety', 'love', 'friendship'
        ]
        
        key_concepts = [term for term in philosophical_terms 
                       if re.search(rf'\\b{term}\\b', text, re.IGNORECASE)]
        
        return PhilosophicalMetadata(
            title=title,
            author=author,
            philosophical_period=period,
            key_concepts=key_concepts[:10],  # Limit to top 10
            source_quality="high"  # PyMuPDF4LLM produces high quality
        )
    
    def _perform_structural_analysis(self, text: str, metadata: PhilosophicalMetadata) -> str:
        """
        Analyze document structure for GraphRAG preparation.
        
        This creates structural elements that become nodes in the knowledge graph:
        - Headings become hierarchical nodes
        - Cross-references become edges  
        - Arguments become specialized philosophical nodes
        """
        
        print("Analyzing document structure for GraphRAG...")
        
        # Reset structural analysis
        self.structural_elements = []
        self.cross_references = {}
        
        # Parse heading structure
        heading_pattern = r'^(#{1,6})\\s+(.+)$'
        headings = re.findall(heading_pattern, text, re.MULTILINE)
        
        current_hierarchy = {}  # level -> element_id
        
        for i, (hashes, title) in enumerate(headings):
            level = len(hashes)
            element_id = f"struct_{i:04d}"
            
            # Determine parent
            parent_id = None
            for parent_level in range(level - 1, 0, -1):
                if parent_level in current_hierarchy:
                    parent_id = current_hierarchy[parent_level]
                    break
            
            # Classify philosophical role
            philosophical_role = self._classify_philosophical_role(title.lower())
            
            # Determine element type based on level and content
            element_type = self._classify_element_type(level, title, metadata)
            
            # Extract content for this section (simplified)
            content = self._extract_section_content(text, title)
            
            element = StructuralElement(
                element_id=element_id,
                element_type=element_type,
                title=title,
                level=level,
                content=content[:500],  # Preview
                parent_id=parent_id,
                philosophical_role=philosophical_role
            )
            
            self.structural_elements.append(element)
            current_hierarchy[level] = element_id
            
            # Update parent's children
            if parent_id:
                parent = next((e for e in self.structural_elements if e.element_id == parent_id), None)
                if parent:
                    parent.children.append(element_id)
        
        # Extract cross-references
        self._extract_cross_references(text)
        
        print(f"   Structural elements identified: {len(self.structural_elements)}")
        return text
    
    def _classify_philosophical_role(self, title_lower: str) -> Optional[str]:
        """Classify the philosophical role of a section."""
        
        role_patterns = {
            'argument': ['argument', 'proof', 'demonstration', 'reasoning'],
            'objection': ['objection', 'counter', 'criticism', 'refutation'],
            'response': ['response', 'reply', 'answer', 'solution'],
            'definition': ['definition', 'meaning', 'concept', 'essence'],
            'example': ['example', 'illustration', 'case', 'instance'],
            'conclusion': ['conclusion', 'therefore', 'thus', 'hence']
        }
        
        for role, keywords in role_patterns.items():
            if any(keyword in title_lower for keyword in keywords):
                return role
        
        return None
    
    def _classify_element_type(self, level: int, title: str, metadata: PhilosophicalMetadata) -> str:
        """Classify structural element type based on level and content."""
        
        # Classical text patterns
        if level == 1:
            return "work"  # Whole work (Republic, Ethics)
        elif level == 2:
            if any(word in title.lower() for word in ['book', 'part', 'section']):
                return "book"
            return "major_division"
        elif level == 3:
            if any(word in title.lower() for word in ['chapter', 'discourse']):
                return "chapter"
            return "section"
        elif level == 4:
            return "subsection"
        else:
            return "paragraph"
    
    def _extract_section_content(self, text: str, heading_title: str) -> str:
        """Extract content for a specific section (simplified implementation)."""
        
        # Find the heading in text
        heading_pattern = rf'^#+\\s+{re.escape(heading_title)}$'
        match = re.search(heading_pattern, text, re.MULTILINE)
        
        if not match:
            return ""
        
        # Extract content until next heading of same or higher level
        start_pos = match.end()
        next_heading = re.search(r'^#+\\s+', text[start_pos:], re.MULTILINE)
        
        if next_heading:
            content = text[start_pos:start_pos + next_heading.start()]
        else:
            content = text[start_pos:]
        
        return content.strip()
    
    def _extract_cross_references(self, text: str):
        """Extract cross-references for graph edges."""
        
        # Classical reference patterns
        reference_patterns = [
            r'Republic\\s+(\\d+[a-z]?)',      # Republic 514a
            r'Ethics\\s+(\\d+[a-z]?)',       # Ethics 1103a
            r'Book\\s+(\\w+)',                # Book II
            r'Chapter\\s+(\\w+)',             # Chapter 5
            r'see\\s+([^,.]+)',               # see Book II
            r'cf\\.\\s+([^,.]+)',             # cf. Republic 514a
            r'compare\\s+([^,.]+)'            # compare Ethics 1103a
        ]
        
        for pattern in reference_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                ref_key = f"ref_{len(self.cross_references)}"
                if ref_key not in self.cross_references:
                    self.cross_references[ref_key] = []
                self.cross_references[ref_key].append(match)
        
        print(f"   Cross-references found: {len(self.cross_references)}")
    
    def _create_enhanced_markdown(self, text: str, metadata: PhilosophicalMetadata) -> str:
        """Create final enhanced markdown with front-matter and structural markup."""
        
        # Add YAML front-matter
        frontmatter = metadata.to_yaml_frontmatter()
        
        # Add structural analysis section
        structural_section = self._generate_structural_section()
        
        # Add graph preparation section
        graph_section = self._generate_graph_preparation_section()
        
        enhanced_content = f"""{frontmatter}
# {metadata.title}

**Author:** {metadata.author}  
**Period:** {metadata.philosophical_period.value.title()}  
**Processing Date:** {metadata.processing_date}  

---

## Document Structure (for GraphRAG)

This document has been analyzed for structural elements that will become nodes in the knowledge graph.
See the structural analysis below for the hierarchical organization.

---

{text}

---

{structural_section}

---

{graph_section}

---

## Processing Notes

This text has been processed using PyMuPDF4LLM for superior PDF conversion and enhanced with:
- YAML front-matter metadata
- Structural analysis for GraphRAG
- Cross-reference extraction
- Philosophical role classification

Ready for heading-aware chunking and knowledge graph construction.
"""
        
        return enhanced_content
    
    def _generate_structural_section(self) -> str:
        """Generate markdown section describing document structure."""
        
        if not self.structural_elements:
            return "## Structural Analysis\\n\\nNo structural elements identified."
        
        section = "## Structural Analysis\\n\\n"
        section += "The following structural elements have been identified for GraphRAG:\\n\\n"
        
        for element in self.structural_elements:
            indent = "  " * (element.level - 1)
            role_info = f" `[{element.philosophical_role}]`" if element.philosophical_role else ""
            section += f"{indent}- **{element.element_type.replace('_', ' ').title()}:** {element.title}{role_info}\\n"
            section += f"{indent}  - ID: `{element.element_id}`\\n"
            if element.parent_id:
                section += f"{indent}  - Parent: `{element.parent_id}`\\n"
            if element.children:
                section += f"{indent}  - Children: {', '.join([f'`{c}`' for c in element.children])}\\n"
            section += "\\n"
        
        return section
    
    def _generate_graph_preparation_section(self) -> str:
        """Generate section for graph preparation instructions."""
        
        section = """## GraphRAG Preparation

### Nodes (from Structure)
Each structural element becomes a node:
- **Work/Book nodes:** Top-level divisions
- **Chapter/Section nodes:** Mid-level organization  
- **Argument/Definition nodes:** Content-specific nodes

### Edges (from References)
Cross-references become edges:
- **PART_OF:** Hierarchical relationships
- **REFERENCES:** Cross-references within text
- **SUPPORTS/CONTRADICTS:** Argumentative relationships

### Node Properties
Each node includes:
- `element_type`: Type of structural element
- `philosophical_role`: Role in philosophical argument
- `content_preview`: First 500 characters
- `level`: Heading depth (1-6)

### Usage for Chunking
Use structural elements as chunk boundaries:
"""
        
        if self.structural_elements:
            section += "\\n```python\\n"
            section += "# Heading-aware chunking strategy\\n"
            section += "chunk_boundaries = [\\n"
            for element in self.structural_elements[:5]:  # Show first 5 as example
                section += f"    '{element.element_id}': '{element.title}',\\n"
            if len(self.structural_elements) > 5:
                section += f"    # ... {len(self.structural_elements) - 5} more elements\\n"
            section += "]\\n```\\n"
        
        return section
    
    def get_structural_elements(self) -> List[StructuralElement]:
        """Get extracted structural elements for GraphRAG."""
        return self.structural_elements
    
    def get_cross_references(self) -> Dict[str, List[str]]:
        """Get extracted cross-references for graph edges."""
        return self.cross_references
    
    def create_heading_aware_chunks(
        self, 
        text: str, 
        max_chunk_size: int = 2000,
        min_chunk_size: int = 100
    ) -> List[Chunk]:
        """
        Create chunks that respect heading boundaries for better philosophical coherence.
        
        This strategy:
        1. Never breaks in the middle of an argument
        2. Keeps related philosophical content together
        3. Maintains citation context
        4. Preserves hierarchical relationships
        """
        
        chunks = []
        
        # Use structural elements as natural chunk boundaries
        for element in self.structural_elements:
            content = element.content
            
            # If element content is small enough, make it one chunk
            if len(content) <= max_chunk_size:
                chunk = Chunk(
                    text=content,
                    metadata={
                        'structural_element_id': element.element_id,
                        'element_type': element.element_type,
                        'title': element.title,
                        'level': element.level,
                        'philosophical_role': element.philosophical_role,
                        'parent_id': element.parent_id,
                        'heading_aware': True
                    },
                    chunk_type='structural'
                )
                chunks.append(chunk)
            
            else:
                # Split large sections while respecting paragraph boundaries
                paragraphs = content.split('\\n\\n')
                current_chunk = ""
                current_metadata = {
                    'structural_element_id': element.element_id,
                    'element_type': element.element_type,
                    'title': element.title,
                    'level': element.level,
                    'philosophical_role': element.philosophical_role,
                    'parent_id': element.parent_id,
                    'heading_aware': True
                }
                
                for paragraph in paragraphs:
                    if len(current_chunk) + len(paragraph) > max_chunk_size and current_chunk:
                        # Create chunk and start new one
                        if len(current_chunk) >= min_chunk_size:
                            chunk = Chunk(
                                text=current_chunk.strip(),
                                metadata=current_metadata.copy(),
                                chunk_type='structural'
                            )
                            chunks.append(chunk)
                        current_chunk = paragraph
                    else:
                        current_chunk += ("\\n\\n" if current_chunk else "") + paragraph
                
                # Add final chunk if any content remains
                if current_chunk.strip() and len(current_chunk) >= min_chunk_size:
                    chunk = Chunk(
                        text=current_chunk.strip(),
                        metadata=current_metadata,
                        chunk_type='structural'
                    )
                    chunks.append(chunk)
        
        print(f"Created {len(chunks)} heading-aware chunks")
        return chunks


async def convert_philosophical_text(
    pdf_path: str,
    output_dir: str = "enhanced_texts",
    metadata: Optional[PhilosophicalMetadata] = None
) -> Tuple[str, PhilosophicalMetadata, List[StructuralElement]]:
    """
    Convenience function to convert a philosophical PDF to enhanced markdown.
    
    Returns:
        Tuple of (markdown_file_path, metadata, structural_elements)
    """
    
    converter = PhilosophicalConverter()
    markdown_file, final_metadata = await converter.convert_pdf_to_enhanced_markdown(
        pdf_path, output_dir, metadata
    )
    
    structural_elements = converter.get_structural_elements()
    
    return markdown_file, final_metadata, structural_elements


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def test_conversion():
        # Example with Republic
        metadata = PhilosophicalMetadata(
            title="The Republic",
            author="Plato",
            translator="Benjamin Jowett",
            philosophical_period=PhilosophicalPeriod.ANCIENT,
            text_type=TextType.DIALOGUE,
            philosophical_school="Platonism",
            major_themes=["justice", "ideal state", "philosopher king", "forms"],
            key_concepts=["justice", "virtue", "soul", "form", "good"],
            related_works=["Laws", "Phaedo", "Phaedrus"],
            citation_style="classical"
        )
        
        # This would be the actual conversion call
        print("🧪 Testing Philosophical Converter")
        print("Note: Replace with actual PDF path for testing")
        # markdown_file, metadata, elements = await convert_philosophical_text(
        #     "path/to/republic.pdf",
        #     metadata=metadata
        # )
    
    # asyncio.run(test_conversion())
    print("✅ Philosophical Converter module ready")
    print("   Features: PyMuPDF4LLM, YAML front-matter, structural analysis, GraphRAG prep")