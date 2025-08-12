"""Test suite for text chunking algorithms."""

import uuid
from typing import List

import pytest

from src.arete.models.chunk import Chunk, ChunkType
from src.arete.processing.chunker import (
    ChunkingStrategy,
    ParagraphChunker,
    SemanticChunker,
    SentenceChunker,
    SlidingWindowChunker,
)


class TestSlidingWindowChunker:
    """Test sliding window chunking strategy."""

    def setup_method(self):
        """Set up test fixtures."""
        self.chunker = SlidingWindowChunker(chunk_size=100, overlap=20)
        self.document_id = uuid.uuid4()
        self.short_text = "This is a short text that fits in one chunk."
        self.long_text = (
            "This is a longer text that will be split into multiple chunks. "
            "Each chunk will have a specific size with overlap between consecutive chunks. "
            "This helps maintain context between chunks for better semantic understanding. "
            "The sliding window approach is particularly useful for dense philosophical texts."
        )

    def test_chunker_initialization(self):
        """Test chunker initialization with parameters."""
        chunker = SlidingWindowChunker(chunk_size=200, overlap=50)
        assert chunker.chunk_size == 200
        assert chunker.overlap == 50

    def test_chunker_validation(self):
        """Test parameter validation."""
        # Test invalid chunk size
        with pytest.raises(ValueError, match="Chunk size must be positive"):
            SlidingWindowChunker(chunk_size=0, overlap=10)
            
        # Test negative overlap
        with pytest.raises(ValueError, match="Overlap cannot be negative"):
            SlidingWindowChunker(chunk_size=100, overlap=-5)
            
        # Test overlap >= chunk_size
        with pytest.raises(ValueError, match="Overlap must be less than chunk size"):
            SlidingWindowChunker(chunk_size=100, overlap=100)

    def test_chunk_short_text(self):
        """Test chunking text that fits in one chunk."""
        chunks = self.chunker.chunk_text(self.short_text, self.document_id)
        
        assert len(chunks) == 1
        assert chunks[0].text == self.short_text
        assert chunks[0].position == 0
        assert chunks[0].start_char == 0
        assert chunks[0].end_char == len(self.short_text)
        assert chunks[0].chunk_type == ChunkType.SLIDING_WINDOW

    def test_chunk_long_text(self):
        """Test chunking text that requires multiple chunks."""
        chunks = self.chunker.chunk_text(self.long_text, self.document_id)
        
        # Should create multiple chunks
        assert len(chunks) > 1
        
        # Check chunk properties
        for i, chunk in enumerate(chunks):
            assert chunk.position == i
            assert chunk.document_id == self.document_id
            assert chunk.chunk_type == ChunkType.SLIDING_WINDOW
            assert len(chunk.text) <= self.chunker.chunk_size
            
        # Check overlap between consecutive chunks
        for i in range(len(chunks) - 1):
            current_chunk = chunks[i]
            next_chunk = chunks[i + 1]
            overlap = current_chunk.get_overlap_with(next_chunk)
            assert overlap > 0  # Should have some overlap

    def test_chunk_boundaries(self):
        """Test that chunk boundaries are correct."""
        chunks = self.chunker.chunk_text(self.long_text, self.document_id)
        
        # First chunk should start at 0
        assert chunks[0].start_char == 0
        
        # Last chunk should end at text length
        assert chunks[-1].end_char == len(self.long_text)
        
        # Chunks should be sequential with proper overlap
        for i in range(len(chunks) - 1):
            current_end = chunks[i].end_char
            next_start = chunks[i + 1].start_char
            expected_next_start = current_end - self.chunker.overlap
            assert next_start == expected_next_start


class TestParagraphChunker:
    """Test paragraph-based chunking strategy."""

    def setup_method(self):
        """Set up test fixtures."""
        self.chunker = ParagraphChunker()
        self.document_id = uuid.uuid4()
        self.single_paragraph = "This is a single paragraph with no line breaks."
        self.multi_paragraph = (
            "This is the first paragraph.\n\n"
            "This is the second paragraph.\n\n"
            "This is the third paragraph."
        )

    def test_chunk_single_paragraph(self):
        """Test chunking single paragraph."""
        chunks = self.chunker.chunk_text(self.single_paragraph, self.document_id)
        
        assert len(chunks) == 1
        assert chunks[0].text.strip() == self.single_paragraph
        assert chunks[0].chunk_type == ChunkType.PARAGRAPH

    def test_chunk_multiple_paragraphs(self):
        """Test chunking multiple paragraphs."""
        chunks = self.chunker.chunk_text(self.multi_paragraph, self.document_id)
        
        assert len(chunks) == 3
        assert "first paragraph" in chunks[0].text
        assert "second paragraph" in chunks[1].text
        assert "third paragraph" in chunks[2].text
        
        for chunk in chunks:
            assert chunk.chunk_type == ChunkType.PARAGRAPH

    def test_empty_paragraphs_filtered(self):
        """Test that empty paragraphs are filtered out."""
        text_with_empty = "First paragraph.\n\n\n\nSecond paragraph."
        chunks = self.chunker.chunk_text(text_with_empty, self.document_id)
        
        assert len(chunks) == 2  # Empty paragraphs should be filtered


class TestSentenceChunker:
    """Test sentence-based chunking strategy."""

    def setup_method(self):
        """Set up test fixtures."""
        self.chunker = SentenceChunker()
        self.document_id = uuid.uuid4()
        self.single_sentence = "This is a single sentence."
        self.multi_sentence = (
            "This is the first sentence. This is the second sentence! "
            "This is the third sentence? And this is the fourth."
        )

    def test_chunk_single_sentence(self):
        """Test chunking single sentence."""
        chunks = self.chunker.chunk_text(self.single_sentence, self.document_id)
        
        assert len(chunks) == 1
        assert chunks[0].text.strip() == self.single_sentence
        assert chunks[0].chunk_type == ChunkType.SENTENCE

    def test_chunk_multiple_sentences(self):
        """Test chunking multiple sentences."""
        chunks = self.chunker.chunk_text(self.multi_sentence, self.document_id)
        
        assert len(chunks) == 4
        assert "first sentence" in chunks[0].text
        assert "second sentence" in chunks[1].text
        assert "third sentence" in chunks[2].text
        assert "fourth" in chunks[3].text
        
        for chunk in chunks:
            assert chunk.chunk_type == ChunkType.SENTENCE


class TestSemanticChunker:
    """Test semantic chunking strategy."""

    def setup_method(self):
        """Set up test fixtures."""
        self.chunker = SemanticChunker(max_chunk_size=200)
        self.document_id = uuid.uuid4()
        self.philosophical_text = (
            "Virtue ethics is a normative approach to ethics that emphasizes the character of the moral agent. "
            "Unlike deontological ethics which focuses on rules, or consequentialism which focuses on outcomes, "
            "virtue ethics asks what kind of person one should be. "
            "Aristotle is considered the founder of virtue ethics in his Nicomachean Ethics. "
            "He argued that virtues are acquired through practice and habituation. "
            "The doctrine of the mean suggests that virtue lies between extremes of excess and deficiency."
        )

    def test_semantic_chunking_initialization(self):
        """Test semantic chunker initialization."""
        chunker = SemanticChunker(max_chunk_size=150)
        assert chunker.max_chunk_size == 150

    def test_semantic_chunking_basic(self):
        """Test basic semantic chunking."""
        chunks = self.chunker.chunk_text(self.philosophical_text, self.document_id)
        
        assert len(chunks) > 1
        for chunk in chunks:
            assert chunk.chunk_type == ChunkType.SEMANTIC
            assert len(chunk.text) <= self.chunker.max_chunk_size

    def test_semantic_boundary_detection(self):
        """Test that semantic boundaries are respected."""
        chunks = self.chunker.chunk_text(self.philosophical_text, self.document_id)
        
        # Chunks should break at sentence boundaries when possible
        for chunk in chunks:
            # Most chunks should end with sentence-ending punctuation
            text = chunk.text.strip()
            if text and len(text) < self.chunker.max_chunk_size * 0.8:
                assert text[-1] in '.!?', f"Chunk should end with sentence punctuation: '{text[-20:]}'"


class TestChunkingStrategy:
    """Test the abstract base class and factory methods."""

    def test_chunking_strategy_interface(self):
        """Test that ChunkingStrategy defines the correct interface."""
        # Verify abstract methods exist
        assert hasattr(ChunkingStrategy, 'chunk_text')
        
        # Test that direct instantiation raises error
        with pytest.raises(TypeError):
            ChunkingStrategy()

    def test_get_chunker_factory(self):
        """Test factory method for getting chunkers."""
        # Test creating different chunker types
        sliding_chunker = ChunkingStrategy.get_chunker("sliding_window", chunk_size=100, overlap=20)
        assert isinstance(sliding_chunker, SlidingWindowChunker)
        
        paragraph_chunker = ChunkingStrategy.get_chunker("paragraph")
        assert isinstance(paragraph_chunker, ParagraphChunker)
        
        sentence_chunker = ChunkingStrategy.get_chunker("sentence")
        assert isinstance(sentence_chunker, SentenceChunker)
        
        semantic_chunker = ChunkingStrategy.get_chunker("semantic", max_chunk_size=200)
        assert isinstance(semantic_chunker, SemanticChunker)

    def test_get_chunker_invalid_type(self):
        """Test factory with invalid chunker type."""
        with pytest.raises(ValueError, match="Unknown chunking strategy"):
            ChunkingStrategy.get_chunker("invalid_type")


class TestIntegratedChunking:
    """Test integrated chunking workflows."""

    def setup_method(self):
        """Set up test fixtures."""
        self.document_id = uuid.uuid4()
        self.complex_text = (
            "Aristotle's concept of virtue ethics represents a fundamental approach to moral philosophy. "
            "In the Nicomachean Ethics, he argues that virtue is not merely following rules or calculating consequences. "
            "\n\n"
            "Instead, virtue is about developing good character traits through practice and habituation. "
            "The doctrine of the mean suggests that most virtues lie between extremes. "
            "For example, courage is the mean between cowardice (deficiency) and recklessness (excess). "
            "\n\n"
            "This approach has been influential in modern moral philosophy and psychology. "
            "Virtue ethics complements rather than replaces other ethical frameworks."
        )

    def test_chunking_comparison(self):
        """Test different chunking strategies on the same text."""
        strategies = [
            ("sliding_window", {"chunk_size": 150, "overlap": 30}),
            ("paragraph", {}),
            ("sentence", {}),
            ("semantic", {"max_chunk_size": 180})
        ]
        
        results = {}
        for strategy_name, params in strategies:
            chunker = ChunkingStrategy.get_chunker(strategy_name, **params)
            chunks = chunker.chunk_text(self.complex_text, self.document_id)
            results[strategy_name] = len(chunks)
        
        # Different strategies should produce different numbers of chunks
        assert len(set(results.values())) > 1, "Different strategies should produce different chunk counts"
        
        # Paragraph chunking should create fewer chunks than sentence chunking
        assert results["paragraph"] <= results["sentence"]

    def test_chunk_overlap_calculation(self):
        """Test overlap calculation between chunks."""
        chunker = SlidingWindowChunker(chunk_size=100, overlap=25)
        chunks = chunker.chunk_text(self.complex_text, self.document_id)
        
        if len(chunks) > 1:
            for i in range(len(chunks) - 1):
                overlap = chunks[i].get_overlap_with(chunks[i + 1])
                assert overlap > 0, "Adjacent chunks should have overlap"
                assert overlap <= 25, "Overlap should not exceed specified amount"

    def test_chunk_metadata_preservation(self):
        """Test that chunk metadata is properly set."""
        chunker = SemanticChunker(max_chunk_size=150)
        chunks = chunker.chunk_text(self.complex_text, self.document_id)
        
        for i, chunk in enumerate(chunks):
            assert chunk.document_id == self.document_id
            assert chunk.position == i
            assert chunk.start_char >= 0
            assert chunk.end_char > chunk.start_char
            assert chunk.computed_word_count > 0