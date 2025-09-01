"""
RestructuredText Ingestion Pipeline

Processes .rst files, extracts structured content, creates knowledge graph entities,
and generates embeddings for the Arete philosophical tutoring system.

This module handles:
- RST file parsing and content extraction
- Metadata extraction and validation
- Entity identification and relationship mapping
- Chunk generation with proper positioning
- Citation extraction and validation
- Knowledge graph storage (Neo4j) and vector storage (Weaviate)
"""

import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime
from dataclasses import dataclass

# Pydantic imports
from pydantic import ValidationError

# Arete core imports
from arete.config.config_manager import ConfigManager
from arete.data.models.document import Document
from arete.data.models.entity import Entity
from arete.data.models.chunk import Chunk
from arete.data.models.citation import Citation
from arete.data.clients.neo4j_client import Neo4jClient
from arete.data.clients.weaviate_client import WeaviateClient
from arete.text_processing.chunking.chunking_service import ChunkingService
from arete.text_processing.embedding.embedding_service_factory import EmbeddingServiceFactory
from arete.text_processing.citation.citation_extractor import CitationExtractor

# Setup logging
logger = logging.getLogger(__name__)


@dataclass
class RSTSection:
    """Represents a section from RST document with hierarchy information."""
    title: str
    content: str
    level: int
    start_char: int
    end_char: int
    parent_section: Optional[str] = None
    subsections: List[str] = None

    def __post_init__(self):
        if self.subsections is None:
            self.subsections = []


@dataclass
class RSTMetadata:
    """Metadata extracted from RST document."""
    title: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = None
    language: str = "en"

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class RSTProcessor:
    """Processes RestructuredText files for the Arete system."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """Initialize RST processor with configuration."""
        self.config_manager = config_manager or ConfigManager()
        self.neo4j_client = Neo4jClient(self.config_manager)
        self.weaviate_client = WeaviateClient(self.config_manager)
        self.chunking_service = ChunkingService()
        self.embedding_service = EmbeddingServiceFactory.create_service()
        self.citation_extractor = CitationExtractor()

        # RST parsing patterns
        self.title_patterns = [
            (re.compile(r'^(.+)\n[=#\-\^"~`:\'._*+<>!?/\\|@$%&()[\]{}]+\s*$', re.MULTILINE), 1),
            (re.compile(r'^[=#\-\^"~`:\'._*+<>!?/\\|@$%&()[\]{}]+\s*\n(.+)\n[=#\-\^"~`:\'._*+<>!?/\\|@$%&()[\]{}]+\s*$', re.MULTILINE), 2)
        ]
        
        self.metadata_pattern = re.compile(r'^:([^:]+):\s*(.+)$', re.MULTILINE)
        self.directive_pattern = re.compile(r'^\.\. ([^:]+)::\s*(.*?)(?=^\.\. |\Z)', re.MULTILINE | re.DOTALL)
        
        # Section hierarchy markers (most common first)
        self.section_markers = ['#', '*', '=', '-', '^', '"']

    def process_rst_file(self, file_path: str) -> Document:
        """
        Process a single RST file and return a Document object.
        
        Args:
            file_path: Path to the RST file
            
        Returns:
            Document object with processed content
        """
        logger.info(f"Processing RST file: {file_path}")
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata
            metadata = self._extract_metadata(content)
            
            # Parse document structure
            sections = self._parse_sections(content)
            
            # Create document object
            document = self._create_document(file_path, content, metadata, sections)
            
            # Process entities and relationships
            self._extract_entities(document, sections)
            
            # Generate chunks with proper positioning
            self._create_chunks(document, sections, content)
            
            # Extract citations
            self._extract_citations(document, content)
            
            logger.info(f"Successfully processed RST file: {file_path}")
            return document
            
        except Exception as e:
            logger.error(f"Error processing RST file {file_path}: {e}")
            raise

    def _extract_metadata(self, content: str) -> RSTMetadata:
        """Extract metadata from RST content."""
        metadata = RSTMetadata()
        
        # Extract field list metadata (e.g., :author: John Doe)
        for match in self.metadata_pattern.finditer(content):
            field = match.group(1).lower().strip()
            value = match.group(2).strip()
            
            if field == 'title':
                metadata.title = value
            elif field == 'author':
                metadata.author = value
            elif field == 'date':
                metadata.date = value
            elif field == 'version':
                metadata.version = value
            elif field in ['description', 'summary']:
                metadata.description = value
            elif field in ['tags', 'keywords']:
                metadata.tags = [tag.strip() for tag in value.split(',')]
            elif field in ['language', 'lang']:
                metadata.language = value
        
        # If no title found in metadata, try to extract from first heading
        if not metadata.title:
            for pattern, group in self.title_patterns:
                match = pattern.search(content)
                if match:
                    metadata.title = match.group(group).strip()
                    break
        
        return metadata

    def _parse_sections(self, content: str) -> List[RSTSection]:
        """Parse RST content into structured sections."""
        sections = []
        lines = content.split('\n')
        current_position = 0
        
        i = 0
        section_stack = []  # Stack to track section hierarchy
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                current_position += len(lines[i]) + 1  # +1 for newline
                i += 1
                continue
            
            # Check if this might be a section title
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and len(set(next_line)) == 1 and next_line[0] in self.section_markers:
                    # This is a section title
                    title = line
                    marker = next_line[0]
                    level = self._get_section_level(marker, section_stack)
                    
                    # Find section content
                    section_start = current_position
                    content_start = i + 2
                    
                    # Find end of section (next section or end of document)
                    section_end_line = len(lines)
                    for j in range(i + 2, len(lines)):
                        if j + 1 < len(lines):
                            potential_title = lines[j].strip()
                            potential_marker_line = lines[j + 1].strip()
                            if (potential_title and potential_marker_line and 
                                len(set(potential_marker_line)) == 1 and 
                                potential_marker_line[0] in self.section_markers):
                                section_end_line = j
                                break
                    
                    # Calculate character positions
                    section_content_lines = lines[content_start:section_end_line]
                    section_content = '\n'.join(section_content_lines)
                    
                    # Calculate start and end character positions
                    start_char = sum(len(lines[k]) + 1 for k in range(content_start))
                    end_char = start_char + len(section_content)
                    
                    # Update section stack based on level
                    section_stack = [s for s in section_stack if s[1] < level]
                    parent_section = section_stack[-1][0] if section_stack else None
                    section_stack.append((title, level))
                    
                    section = RSTSection(
                        title=title,
                        content=section_content,
                        level=level,
                        start_char=start_char,
                        end_char=end_char,
                        parent_section=parent_section
                    )
                    sections.append(section)
                    
                    # Skip to end of this section
                    i = section_end_line
                    current_position = end_char
                    continue
            
            # Regular content line
            current_position += len(lines[i]) + 1
            i += 1
        
        return sections

    def _get_section_level(self, marker: str, section_stack: List[Tuple[str, int]]) -> int:
        """Determine section level based on marker and current stack."""
        # Check if we've seen this marker before
        for _, level in section_stack:
            if marker == self.section_markers[min(level, len(self.section_markers) - 1)]:
                return level
        
        # New marker, assign next level
        return len(section_stack)

    def _create_document(self, file_path: str, content: str, metadata: RSTMetadata, sections: List[RSTSection]) -> Document:
        """Create Document object from RST content and metadata."""
        file_name = Path(file_path).name
        
        # Create document with comprehensive metadata
        document_data = {
            'title': metadata.title or file_name,
            'content': content,
            'file_path': file_path,
            'file_name': file_name,
            'file_type': 'rst',
            'file_size': len(content.encode('utf-8')),
            'language': metadata.language,
            'created_at': datetime.now(),
            'processed_at': datetime.now(),
            'metadata': {
                'author': metadata.author,
                'date': metadata.date,
                'version': metadata.version,
                'description': metadata.description,
                'tags': metadata.tags,
                'section_count': len(sections),
                'character_count': len(content),
                'word_count': len(content.split())
            }
        }
        
        return Document(**document_data)

    def _extract_entities(self, document: Document, sections: List[RSTSection]) -> None:
        """Extract philosophical entities from RST sections."""
        entities = []
        
        for section in sections:
            # Extract entities from section title and content
            section_text = f"{section.title}\n{section.content}"
            
            # Simple entity extraction (can be enhanced with NLP)
            # Look for philosophical terms, concepts, and references
            entity_patterns = [
                (r'\b(Plato|Aristotle|Socrates|Augustine|Aquinas|Kant|Hegel|Nietzsche)\b', 'Person'),
                (r'\b(Republic|Ethics|Meditations|Critique|Phenomenology)\b', 'Work'),
                (r'\b(justice|virtue|truth|beauty|good|being|existence|knowledge|wisdom)\b', 'Concept'),
                (r'\b(dialectic|syllogism|categorical imperative|forms|ideas)\b', 'Method')
            ]
            
            for pattern, entity_type in entity_patterns:
                matches = re.finditer(pattern, section_text, re.IGNORECASE)
                for match in matches:
                    entity_name = match.group(1)
                    
                    # Create entity if not already exists
                    entity = Entity(
                        name=entity_name,
                        entity_type=entity_type,
                        description=f"{entity_type} mentioned in {section.title}",
                        confidence=0.8,
                        source_document=document.title,
                        context=section.title,
                        metadata={
                            'section': section.title,
                            'level': section.level,
                            'extraction_method': 'pattern_matching'
                        }
                    )
                    entities.append(entity)
        
        document.metadata['entities'] = len(entities)
        # Store entities (implementation depends on your storage strategy)

    def _create_chunks(self, document: Document, sections: List[RSTSection], full_content: str) -> None:
        """Create chunks from document sections with proper character positioning."""
        chunks = []
        chunk_position = 0
        
        for section in sections:
            # Create semantic chunks from section content
            section_chunks = self.create_semantic_chunks(
                text=section.content,
                document_id=document.title,  # Using title as ID for now
                section_title=section.title,
                section_start_char=section.start_char,
                chunk_position_offset=chunk_position,
                full_content=full_content
            )
            
            chunks.extend(section_chunks)
            chunk_position += len(section_chunks)
        
        # Generate embeddings for chunks
        for chunk in chunks:
            try:
                embedding = self.embedding_service.generate_embedding(chunk.content)
                chunk.embedding_vector = embedding
            except Exception as e:
                logger.warning(f"Failed to generate embedding for chunk: {e}")
        
        document.metadata['chunk_count'] = len(chunks)
        # Store chunks (implementation depends on your storage strategy)

    def create_semantic_chunks(self, 
                             text: str, 
                             document_id: str, 
                             section_title: str,
                             section_start_char: int,
                             chunk_position_offset: int,
                             full_content: str) -> List[Chunk]:
        """Create semantic chunks from text with proper positioning."""
        chunks = []
        
        # Use chunking service to split text
        raw_chunks = self.chunking_service.chunk_text(text, strategy='semantic', max_chunk_size=500)
        
        current_char_position = 0
        
        for i, chunk_text in enumerate(raw_chunks):
            # Calculate character positions within the section
            start_char_in_section = current_char_position
            end_char_in_section = start_char_in_section + len(chunk_text)
            
            # Calculate absolute positions in the full document
            absolute_start_char = section_start_char + start_char_in_section
            absolute_end_char = section_start_char + end_char_in_section
            
            # Create chunk with proper field mapping
            chunk = self._create_chunk(
                chunk_text=chunk_text,
                document_id=document_id,
                position=chunk_position_offset + i,  # position (sequence number)
                start_char=absolute_start_char,      # start_char (not start_position)
                end_char=absolute_end_char,          # end_char (not end_position)
                section_title=section_title,
                full_content=full_content
            )
            
            chunks.append(chunk)
            current_char_position = end_char_in_section
        
        return chunks

    def _create_chunk(self, 
                     chunk_text: str, 
                     document_id: str, 
                     position: int,
                     start_char: int, 
                     end_char: int,
                     section_title: str,
                     full_content: str) -> Chunk:
        """Create a Chunk object with proper field mapping and validation."""
        
        try:
            # Calculate additional metadata
            word_count = len(chunk_text.split())
            char_count = len(chunk_text)
            
            # Create chunk with correct field names
            chunk_data = {
                'content': chunk_text,
                'document_id': document_id,
                'position': position,           # Correct field name (not sequence_number)
                'start_char': start_char,       # Correct field name (not start_position)  
                'end_char': end_char,           # Correct field name (not end_position)
                'chunk_type': 'semantic',
                'word_count': word_count,
                'char_count': char_count,
                'metadata': {
                    'section_title': section_title,
                    'extraction_method': 'rst_section',
                    'content_preview': chunk_text[:100] + '...' if len(chunk_text) > 100 else chunk_text
                }
            }
            
            # Validate chunk data by creating the object
            chunk = Chunk(**chunk_data)
            logger.debug(f"Created chunk {position} with {word_count} words, chars {start_char}-{end_char}")
            
            return chunk
            
        except ValidationError as e:
            logger.error(f"Chunk validation error for position {position}: {e}")
            logger.error(f"Chunk data: {chunk_data}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating chunk at position {position}: {e}")
            raise

    def _extract_citations(self, document: Document, content: str) -> None:
        """Extract citations from RST content."""
        citations = []
        
        # RST citation patterns
        citation_patterns = [
            # .. [Author2000] Author, A. (2000). Title. Publisher.
            re.compile(r'\.\.\s+\[([^\]]+)\]\s+(.+)'),
            # :cite:`Author2000`
            re.compile(r':cite:`([^`]+)`'),
            # [#]_ footnote style
            re.compile(r'\[#\]\s+(.+)'),
            # .. _reference: URL
            re.compile(r'\.\.\s+_([^:]+):\s+(.+)')
        ]
        
        for pattern in citation_patterns:
            matches = pattern.finditer(content)
            for match in matches:
                if len(match.groups()) >= 2:
                    citation_key = match.group(1)
                    citation_text = match.group(2)
                    
                    try:
                        citation = Citation(
                            citation_text=citation_text,
                            citation_type='reference',
                            confidence=0.9,
                            start_char=match.start(),
                            end_char=match.end(),
                            document_source=document.title,
                            context='rst_extraction',
                            metadata={
                                'citation_key': citation_key,
                                'extraction_pattern': 'rst_citation',
                                'full_match': match.group(0)
                            }
                        )
                        citations.append(citation)
                    except ValidationError as e:
                        logger.warning(f"Invalid citation data: {e}")
        
        document.metadata['citation_count'] = len(citations)
        # Store citations (implementation depends on your storage strategy)

    def process_directory(self, directory_path: str) -> List[Document]:
        """Process all RST files in a directory."""
        documents = []
        rst_files = list(Path(directory_path).glob('**/*.rst'))
        
        logger.info(f"Found {len(rst_files)} RST files in {directory_path}")
        
        for rst_file in rst_files:
            try:
                document = self.process_rst_file(str(rst_file))
                documents.append(document)
            except Exception as e:
                logger.error(f"Failed to process {rst_file}: {e}")
                continue
        
        logger.info(f"Successfully processed {len(documents)} RST documents")
        return documents

    def store_documents(self, documents: List[Document]) -> None:
        """Store processed documents in Neo4j and Weaviate."""
        logger.info(f"Storing {len(documents)} documents...")
        
        try:
            with self.neo4j_client as neo4j:
                with self.weaviate_client as weaviate:
                    for document in documents:
                        # Store in Neo4j
                        neo4j_data = document.to_neo4j_dict()
                        neo4j.create_document(neo4j_data)
                        
                        # Store in Weaviate
                        weaviate_data = document.to_weaviate_dict()
                        weaviate.create_document(weaviate_data)
            
            logger.info("Successfully stored all documents")
            
        except Exception as e:
            logger.error(f"Error storing documents: {e}")
            raise


def main():
    """Main function for RST ingestion processing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Process RestructuredText files for Arete")
    parser.add_argument('input_path', help='Path to RST file or directory')
    parser.add_argument('--store', action='store_true', help='Store processed documents in databases')
    parser.add_argument('--log-level', default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        processor = RSTProcessor()
        
        input_path = Path(args.input_path)
        
        if input_path.is_file():
            # Process single file
            document = processor.process_rst_file(str(input_path))
            documents = [document]
        elif input_path.is_dir():
            # Process directory
            documents = processor.process_directory(str(input_path))
        else:
            logger.error(f"Input path does not exist: {input_path}")
            return
        
        logger.info(f"Processed {len(documents)} documents")
        
        if args.store:
            processor.store_documents(documents)
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise


if __name__ == '__main__':
    main()