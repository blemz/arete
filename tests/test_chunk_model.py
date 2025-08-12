"""Test suite for Chunk model."""

import uuid
from typing import Dict, List
from uuid import UUID

import pytest
from pydantic import ValidationError

from src.arete.models.chunk import Chunk, ChunkType, OverlapData
from src.arete.models.base import ProcessingStatus


class TestChunkType:
    """Test ChunkType enum."""

    def test_chunk_type_values(self):
        """Test that ChunkType has expected values."""
        assert ChunkType.PARAGRAPH == "paragraph"
        assert ChunkType.SENTENCE == "sentence"
        assert ChunkType.SEMANTIC == "semantic"
        assert ChunkType.SLIDING_WINDOW == "sliding_window"

    def test_chunk_type_case_insensitive_creation(self):
        """Test case-insensitive enum creation."""
        assert ChunkType._missing_("PARAGRAPH") == ChunkType.PARAGRAPH
        assert ChunkType._missing_("paragraph") == ChunkType.PARAGRAPH
        assert ChunkType._missing_("Paragraph") == ChunkType.PARAGRAPH

    def test_chunk_type_invalid_value(self):
        """Test that invalid values return None."""
        assert ChunkType._missing_("invalid") is None


class TestOverlapData:
    """Test OverlapData model."""

    def test_overlap_data_creation(self):
        """Test creating valid OverlapData."""
        other_chunk_id = uuid.uuid4()
        overlap = OverlapData(
            other_chunk_id=other_chunk_id,
            overlap_characters=50,
            overlap_ratio=0.25
        )
        
        assert overlap.other_chunk_id == other_chunk_id
        assert overlap.overlap_characters == 50
        assert overlap.overlap_ratio == 0.25

    def test_overlap_data_validation(self):
        """Test OverlapData validation."""
        other_chunk_id = uuid.uuid4()
        
        # Test negative overlap_characters
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            OverlapData(
                other_chunk_id=other_chunk_id,
                overlap_characters=-1,
                overlap_ratio=0.25
            )
            
        # Test overlap_ratio out of range
        with pytest.raises(ValidationError, match="less than or equal to 1"):
            OverlapData(
                other_chunk_id=other_chunk_id,
                overlap_characters=50,
                overlap_ratio=1.5
            )
            
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            OverlapData(
                other_chunk_id=other_chunk_id,
                overlap_characters=50,
                overlap_ratio=-0.1
            )


class TestChunk:
    """Test Chunk model."""

    def setup_method(self):
        """Set up test fixtures."""
        self.document_id = uuid.uuid4()
        self.chunk_id = uuid.uuid4()
        
        self.sample_chunk_data = {
            "id": self.chunk_id,
            "text": "This is a sample chunk of philosophical text discussing virtue ethics.",
            "document_id": self.document_id,
            "position": 0,
            "start_char": 0,
            "end_char": 72,
            "chunk_type": ChunkType.PARAGRAPH
        }

    def test_chunk_creation_minimal(self):
        """Test creating chunk with minimal required fields."""
        chunk = Chunk(**self.sample_chunk_data)
        
        assert chunk.id == self.chunk_id
        assert chunk.text == "This is a sample chunk of philosophical text discussing virtue ethics."
        assert chunk.document_id == self.document_id
        assert chunk.position == 0
        assert chunk.start_char == 0
        assert chunk.end_char == 72
        assert chunk.chunk_type == ChunkType.PARAGRAPH
        assert chunk.processing_status == ProcessingStatus.PENDING
        assert chunk.overlaps == []
        assert chunk.metadata == {}

    def test_chunk_creation_full(self):
        """Test creating chunk with all fields."""
        overlap_data = OverlapData(
            other_chunk_id=uuid.uuid4(),
            overlap_characters=20,
            overlap_ratio=0.2
        )
        
        full_data = {
            **self.sample_chunk_data,
            "word_count": 12,
            "processing_status": ProcessingStatus.COMPLETED,
            "overlaps": [overlap_data],
            "metadata": {"topic": "virtue ethics", "complexity": "medium"}
        }
        
        chunk = Chunk(**full_data)
        
        assert chunk.word_count == 12
        assert chunk.processing_status == ProcessingStatus.COMPLETED
        assert len(chunk.overlaps) == 1
        assert chunk.overlaps[0].other_chunk_id == overlap_data.other_chunk_id
        assert chunk.metadata["topic"] == "virtue ethics"

    def test_chunk_validation_text_required(self):
        """Test that text field is required and validated."""
        # Test missing text
        data = {**self.sample_chunk_data}
        del data["text"]
        with pytest.raises(ValidationError, match="Field required"):
            Chunk(**data)
            
        # Test empty text
        data = {**self.sample_chunk_data, "text": ""}
        with pytest.raises(ValidationError, match="at least 1 character"):
            Chunk(**data)
            
        # Test whitespace-only text
        data = {**self.sample_chunk_data, "text": "   "}
        with pytest.raises(ValidationError, match="at least 1 character"):
            Chunk(**data)

    def test_chunk_validation_positions(self):
        """Test position and character validation."""
        # Test negative position
        data = {**self.sample_chunk_data, "position": -1}
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            Chunk(**data)
            
        # Test negative start_char
        data = {**self.sample_chunk_data, "start_char": -1}
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            Chunk(**data)
            
        # Test end_char <= start_char
        data = {**self.sample_chunk_data, "start_char": 50, "end_char": 50}
        with pytest.raises(ValidationError, match="end_char must be greater than start_char"):
            Chunk(**data)
            
        data = {**self.sample_chunk_data, "start_char": 50, "end_char": 40}
        with pytest.raises(ValidationError, match="end_char must be greater than start_char"):
            Chunk(**data)

    def test_chunk_computed_properties(self):
        """Test computed properties."""
        chunk = Chunk(**self.sample_chunk_data)
        
        # Test computed_word_count
        expected_words = len(chunk.text.split())
        assert chunk.computed_word_count == expected_words
        
        # Test character_count
        assert chunk.character_count == len(chunk.text)
        
        # Test character_span
        assert chunk.character_span == chunk.end_char - chunk.start_char

    def test_chunk_get_overlap_with(self):
        """Test overlap calculation with other chunks."""
        chunk1 = Chunk(
            text="First chunk",
            document_id=self.document_id,
            position=0,
            start_char=0,
            end_char=50,
            chunk_type=ChunkType.SLIDING_WINDOW
        )
        
        # Overlapping chunk
        chunk2 = Chunk(
            text="Second chunk",
            document_id=self.document_id,
            position=1,
            start_char=30,
            end_char=80,
            chunk_type=ChunkType.SLIDING_WINDOW
        )
        
        # Non-overlapping chunk
        chunk3 = Chunk(
            text="Third chunk",
            document_id=self.document_id,
            position=2,
            start_char=100,
            end_char=150,
            chunk_type=ChunkType.SLIDING_WINDOW
        )
        
        # Test overlap calculation
        assert chunk1.get_overlap_with(chunk2) == 20  # 50 - 30 = 20
        assert chunk1.get_overlap_with(chunk3) == 0   # No overlap
        assert chunk2.get_overlap_with(chunk1) == 20  # Symmetric

    def test_chunk_add_overlap(self):
        """Test adding overlap data."""
        chunk = Chunk(**self.sample_chunk_data)
        other_chunk_id = uuid.uuid4()
        
        chunk.add_overlap(other_chunk_id, 25, 0.3)
        
        assert len(chunk.overlaps) == 1
        assert chunk.overlaps[0].other_chunk_id == other_chunk_id
        assert chunk.overlaps[0].overlap_characters == 25
        assert chunk.overlaps[0].overlap_ratio == 0.3
        
        # Test adding duplicate overlap (should not add)
        chunk.add_overlap(other_chunk_id, 25, 0.3)
        assert len(chunk.overlaps) == 1  # Still only one overlap

    def test_chunk_get_vectorizable_text(self):
        """Test vectorizable text generation."""
        chunk = Chunk(
            **self.sample_chunk_data,
            metadata={"topic": "virtue ethics", "author": "Aristotle"}
        )
        
        vectorizable = chunk.get_vectorizable_text()
        
        # Should include text and relevant metadata
        assert chunk.text in vectorizable
        assert "virtue ethics" in vectorizable
        assert "Aristotle" in vectorizable

    def test_chunk_to_neo4j_dict(self):
        """Test Neo4j dictionary conversion."""
        chunk = Chunk(**self.sample_chunk_data)
        neo4j_dict = chunk.to_neo4j_dict()
        
        # Check core fields
        assert neo4j_dict["text"] == chunk.text
        assert neo4j_dict["document_id"] == str(chunk.document_id)
        assert neo4j_dict["position"] == chunk.position
        assert neo4j_dict["start_char"] == chunk.start_char
        assert neo4j_dict["end_char"] == chunk.end_char
        chunk_type_str = chunk.chunk_type.value if hasattr(chunk.chunk_type, 'value') else str(chunk.chunk_type)
        assert neo4j_dict["chunk_type"] == chunk_type_str
        
        # Check computed fields
        assert neo4j_dict["computed_word_count"] == chunk.computed_word_count
        assert neo4j_dict["character_count"] == chunk.character_count
        assert neo4j_dict["character_span"] == chunk.character_span

    def test_chunk_to_weaviate_dict(self):
        """Test Weaviate dictionary conversion."""
        chunk = Chunk(**self.sample_chunk_data)
        weaviate_dict = chunk.to_weaviate_dict()
        
        # Check core fields
        assert weaviate_dict["text"] == chunk.text
        chunk_type_str = chunk.chunk_type.value if hasattr(chunk.chunk_type, 'value') else str(chunk.chunk_type)
        assert weaviate_dict["chunk_type"] == chunk_type_str
        
        # Check vectorizable text
        assert "vectorizable_text" in weaviate_dict
        assert chunk.text in weaviate_dict["vectorizable_text"]
        
        # Check computed fields
        assert weaviate_dict["computed_word_count"] == chunk.computed_word_count
        assert weaviate_dict["character_count"] == chunk.character_count

    def test_chunk_string_representation(self):
        """Test string representation."""
        chunk = Chunk(**self.sample_chunk_data)
        str_repr = str(chunk)
        
        assert str(chunk.id) in str_repr
        assert str(chunk.position) in str_repr
        chunk_type_str = chunk.chunk_type.value if hasattr(chunk.chunk_type, 'value') else str(chunk.chunk_type)
        assert chunk_type_str in str_repr

    def test_chunk_validation_word_count(self):
        """Test word count validation."""
        # Test negative word count
        data = {**self.sample_chunk_data, "word_count": -1}
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            Chunk(**data)

    def test_chunk_text_normalization(self):
        """Test text field normalization."""
        # Test text with leading/trailing whitespace
        data = {**self.sample_chunk_data, "text": "  Normalized text  "}
        chunk = Chunk(**data)
        assert chunk.text == "Normalized text"

    def test_chunk_different_chunk_types(self):
        """Test chunk creation with different chunk types."""
        for chunk_type in ChunkType:
            data = {**self.sample_chunk_data, "chunk_type": chunk_type}
            chunk = Chunk(**data)
            assert chunk.chunk_type == chunk_type

    def test_chunk_metadata_optional(self):
        """Test that metadata is optional and defaults to empty dict."""
        chunk = Chunk(**self.sample_chunk_data)
        assert chunk.metadata == {}
        
        # Test with custom metadata
        data = {**self.sample_chunk_data, "metadata": {"custom": "value"}}
        chunk = Chunk(**data)
        assert chunk.metadata["custom"] == "value"

    def test_chunk_overlaps_list_handling(self):
        """Test overlaps list handling."""
        # Test empty overlaps list
        chunk = Chunk(**self.sample_chunk_data)
        assert chunk.overlaps == []
        
        # Test with multiple overlaps
        overlap1 = OverlapData(
            other_chunk_id=uuid.uuid4(),
            overlap_characters=10,
            overlap_ratio=0.1
        )
        overlap2 = OverlapData(
            other_chunk_id=uuid.uuid4(),
            overlap_characters=20,
            overlap_ratio=0.2
        )
        
        data = {**self.sample_chunk_data, "overlaps": [overlap1, overlap2]}
        chunk = Chunk(**data)
        assert len(chunk.overlaps) == 2