"""Text chunking strategies for processing philosophical documents."""

import re
from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from ..models.chunk import Chunk, ChunkType
from .heading_aware import HeadingAwareChunkingStrategy


class ChunkingStrategy(ABC):
    """Abstract base class for text chunking strategies."""

    @abstractmethod
    def chunk_text(self, text: str, document_id: UUID) -> List[Chunk]:
        """Chunk text into a list of Chunk objects.
        
        Args:
            text: Text to be chunked
            document_id: ID of the source document
            
        Returns:
            List of Chunk objects
        """
        pass

    @staticmethod
    def get_chunker(strategy: str, **kwargs) -> "ChunkingStrategy":
        """Factory method to get a chunker by strategy name.
        
        Args:
            strategy: Name of the chunking strategy
            **kwargs: Additional parameters for the specific chunker
            
        Returns:
            ChunkingStrategy instance
            
        Raises:
            ValueError: If strategy is unknown
        """
        strategies = {
            "sliding_window": SlidingWindowChunker,
            "paragraph": ParagraphChunker,
            "sentence": SentenceChunker,
            "semantic": SemanticChunker,
            "heading_aware": HeadingAwareChunkingStrategy
        }
        
        if strategy not in strategies:
            raise ValueError(f"Unknown chunking strategy: {strategy}")
            
        return strategies[strategy](**kwargs)


class SlidingWindowChunker(ChunkingStrategy):
    """Sliding window chunking with configurable size and overlap."""

    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        """Initialize sliding window chunker.
        
        Args:
            chunk_size: Maximum characters per chunk
            overlap: Character overlap between chunks
            
        Raises:
            ValueError: If parameters are invalid
        """
        if chunk_size <= 0:
            raise ValueError("Chunk size must be positive")
        if overlap < 0:
            raise ValueError("Overlap cannot be negative")
        if overlap >= chunk_size:
            raise ValueError("Overlap must be less than chunk size")
            
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str, document_id: UUID) -> List[Chunk]:
        """Chunk text using sliding window approach.
        
        Args:
            text: Text to be chunked
            document_id: ID of the source document
            
        Returns:
            List of Chunk objects
        """
        if len(text) <= self.chunk_size:
            # Text fits in single chunk
            return [Chunk(
                text=text,
                document_id=document_id,
                position=0,
                start_char=0,
                end_char=len(text),
                chunk_type=ChunkType.SLIDING_WINDOW
            )]

        chunks = []
        start = 0
        position = 0

        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk_text = text[start:end]

            chunk = Chunk(
                text=chunk_text,
                document_id=document_id,
                position=position,
                start_char=start,
                end_char=end,
                chunk_type=ChunkType.SLIDING_WINDOW
            )
            chunks.append(chunk)

            # Move start position, accounting for overlap
            start = end - self.overlap
            position += 1

            # Prevent infinite loop if we're at the end
            if end == len(text):
                break

        return chunks


class ParagraphChunker(ChunkingStrategy):
    """Chunk text by paragraphs."""

    def chunk_text(self, text: str, document_id: UUID) -> List[Chunk]:
        """Chunk text by paragraphs.
        
        Args:
            text: Text to be chunked
            document_id: ID of the source document
            
        Returns:
            List of Chunk objects
        """
        # Split by double newlines (paragraph breaks)
        paragraphs = re.split(r'\n\s*\n', text)
        
        chunks = []
        current_pos = 0
        
        for i, paragraph in enumerate(paragraphs):
            paragraph = paragraph.strip()
            if not paragraph:
                # Skip empty paragraphs
                current_pos = text.find('\n\n', current_pos) + 2
                continue
                
            # Find the actual position in the original text
            start_char = text.find(paragraph, current_pos)
            if start_char == -1:
                # Fallback to current position if exact match not found
                start_char = current_pos
            
            end_char = start_char + len(paragraph)
            
            chunk = Chunk(
                text=paragraph,
                document_id=document_id,
                position=len(chunks),          # Fixed: use position (sequential position)
                start_char=start_char,         # Fixed: use start_char  
                end_char=end_char,            # Fixed: use end_char
                chunk_type=ChunkType.PARAGRAPH
            )
            chunks.append(chunk)
            
            current_pos = end_char

        return chunks


class SentenceChunker(ChunkingStrategy):
    """Chunk text by sentences."""

    def __init__(self):
        """Initialize sentence chunker."""
        # Pattern to split sentences on '.', '!', '?'
        self.sentence_pattern = re.compile(r'(?<=[.!?])\s+')

    def chunk_text(self, text: str, document_id: UUID) -> List[Chunk]:
        """Chunk text by sentences.
        
        Args:
            text: Text to be chunked
            document_id: ID of the source document
            
        Returns:
            List of Chunk objects
        """
        # Split into sentences
        sentences = self.sentence_pattern.split(text)
        
        chunks = []
        current_pos = 0
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Find the actual position in the original text
            start_char = text.find(sentence, current_pos)
            if start_char == -1:
                start_char = current_pos
            
            end_char = start_char + len(sentence)
            
            chunk = Chunk(
                text=sentence,
                document_id=document_id,
                position=len(chunks),
                start_char=start_char,
                end_char=end_char,
                chunk_type=ChunkType.SENTENCE
            )
            chunks.append(chunk)
            
            current_pos = end_char

        return chunks


class SemanticChunker(ChunkingStrategy):
    """Chunk text based on semantic boundaries with size constraints."""

    def __init__(self, max_chunk_size: int = 1000):
        """Initialize semantic chunker.
        
        Args:
            max_chunk_size: Maximum characters per chunk
        """
        self.max_chunk_size = max_chunk_size
        # Pattern to identify sentence boundaries
        self.sentence_pattern = re.compile(r'(?<=[.!?])\s+')

    def chunk_text(self, text: str, document_id: UUID) -> List[Chunk]:
        """Chunk text based on semantic boundaries.
        
        Args:
            text: Text to be chunked
            document_id: ID of the source document
            
        Returns:
            List of Chunk objects
        """
        # First split into sentences
        sentences = self.sentence_pattern.split(text)
        
        chunks = []
        current_chunk_sentences = []
        current_chunk_length = 0
        current_start_char = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            sentence_length = len(sentence)
            
            # Check if adding this sentence would exceed max chunk size
            if (current_chunk_length + sentence_length > self.max_chunk_size and 
                current_chunk_sentences):
                
                # Create chunk from current sentences
                chunk_text = ' '.join(current_chunk_sentences)
                
                # Find positions in original text
                start_char = text.find(current_chunk_sentences[0], current_start_char)
                if start_char == -1:
                    start_char = current_start_char
                end_char = start_char + len(chunk_text)
                
                chunk = Chunk(
                    text=chunk_text,
                    document_id=document_id,
                    position=len(chunks),
                    start_char=start_char,
                    end_char=end_char,
                    chunk_type=ChunkType.SEMANTIC
                )
                chunks.append(chunk)
                
                # Start new chunk
                current_chunk_sentences = [sentence]
                current_chunk_length = sentence_length
                current_start_char = end_char
            else:
                # Add sentence to current chunk
                current_chunk_sentences.append(sentence)
                current_chunk_length += sentence_length + 1  # +1 for space
        
        # Handle remaining sentences
        if current_chunk_sentences:
            chunk_text = ' '.join(current_chunk_sentences)
            
            start_char = text.find(current_chunk_sentences[0], current_start_char)
            if start_char == -1:
                start_char = current_start_char
            end_char = start_char + len(chunk_text)
            
            chunk = Chunk(
                text=chunk_text,
                document_id=document_id,
                position=len(chunks),
                start_char=start_char,
                end_char=end_char,
                chunk_type=ChunkType.SEMANTIC
            )
            chunks.append(chunk)

        return chunks