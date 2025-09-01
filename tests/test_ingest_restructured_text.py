"""
Comprehensive tests for ingest_restructured_text.py chunk validation and character positioning.

This test suite focuses on validating the fixed Chunk model validation,
character position calculations, semantic chunking, and error handling.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from arete.ingestion.ingest_restructured_text import (
    RestructuredTextIngestionService,
    parse_restructured_text_file,
    _create_chunk,
    _calculate_semantic_positions
)
from arete.models.chunk import Chunk, ChunkType
from arete.models.document import Document
from arete.core.exceptions import ValidationError, ProcessingError


class TestChunkCreation:
    """Test the _create_chunk method with correct field mapping."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_document = Mock(spec=Document)
        self.mock_document.id = "test_doc_123"
        self.mock_document.title = "Test Document"
        
    def test_create_chunk_with_all_required_fields(self):
        """Test _create_chunk with all required Chunk fields."""
        # Given
        text = "This is a test chunk with meaningful content for validation."
        start_char = 100
        end_char = 165
        position = 5
        chunk_type = ChunkType.SEMANTIC
        
        # When
        chunk = _create_chunk(
            document=self.mock_document,
            text=text,
            start_char=start_char,
            end_char=end_char,
            position=position,
            chunk_type=chunk_type
        )
        
        # Then
        assert chunk.document_id == "test_doc_123"
        assert chunk.text == text
        assert chunk.start_char == start_char
        assert chunk.end_char == end_char
        assert chunk.position == position
        assert chunk.chunk_type == chunk_type
        assert chunk.chunk_size == len(text)
        assert len(chunk.text) > 0
        
    def test_create_chunk_character_count_validation(self):
        """Test that chunk size matches text length."""
        # Given
        text = "Short text"
        expected_size = len(text)
        
        # When
        chunk = _create_chunk(
            document=self.mock_document,
            text=text,
            start_char=0,
            end_char=expected_size,
            position=1,
            chunk_type=ChunkType.PARAGRAPH
        )
        
        # Then
        assert chunk.chunk_size == expected_size
        assert chunk.end_char - chunk.start_char == expected_size
        
    def test_create_chunk_with_empty_text_raises_error(self):
        """Test that empty text raises ValidationError."""
        # When/Then
        with pytest.raises(ValidationError, match="Chunk text cannot be empty"):
            _create_chunk(
                document=self.mock_document,
                text="",
                start_char=0,
                end_char=0,
                position=1,
                chunk_type=ChunkType.PARAGRAPH
            )
            
    def test_create_chunk_with_invalid_position_raises_error(self):
        """Test that negative position raises ValidationError."""
        # When/Then
        with pytest.raises(ValidationError, match="Position must be non-negative"):
            _create_chunk(
                document=self.mock_document,
                text="Valid text",
                start_char=0,
                end_char=10,
                position=-1,
                chunk_type=ChunkType.PARAGRAPH
            )
            
    def test_create_chunk_with_invalid_char_range_raises_error(self):
        """Test that invalid character range raises ValidationError."""
        # When/Then
        with pytest.raises(ValidationError, match="Invalid character range"):
            _create_chunk(
                document=self.mock_document,
                text="Valid text",
                start_char=20,
                end_char=10,  # end < start
                position=1,
                chunk_type=ChunkType.PARAGRAPH
            )


class TestCharacterPositionCalculations:
    """Test character position calculations in text processing."""
    
    def test_calculate_semantic_positions_single_chunk(self):
        """Test character position calculation for single semantic chunk."""
        # Given
        full_text = "This is the beginning of the document. This is a semantic chunk that should be positioned correctly."
        chunk_text = "This is a semantic chunk that should be positioned correctly."
        start_offset = 39  # Position in full_text
        
        # When
        positions = _calculate_semantic_positions(full_text, [chunk_text], start_offset)
        
        # Then
        assert len(positions) == 1
        start_char, end_char = positions[0]
        assert start_char == start_offset
        assert end_char == start_offset + len(chunk_text)
        assert full_text[start_char:end_char] == chunk_text
        
    def test_calculate_semantic_positions_multiple_chunks(self):
        """Test character position calculation for multiple semantic chunks."""
        # Given
        full_text = "Chapter 1: Introduction\n\nThis is the first paragraph of meaningful content.\n\nThis is the second paragraph with different ideas."
        chunk_texts = [
            "This is the first paragraph of meaningful content.",
            "This is the second paragraph with different ideas."
        ]
        start_offset = 25
        
        # When
        positions = _calculate_semantic_positions(full_text, chunk_texts, start_offset)
        
        # Then
        assert len(positions) == 2
        
        # Verify first chunk position
        start_char_1, end_char_1 = positions[0]
        assert full_text[start_char_1:end_char_1] == chunk_texts[0]
        
        # Verify second chunk position
        start_char_2, end_char_2 = positions[1]
        assert full_text[start_char_2:end_char_2] == chunk_texts[1]
        
        # Verify chunks don't overlap
        assert end_char_1 <= start_char_2
        
    def test_calculate_semantic_positions_with_whitespace(self):
        """Test position calculation handles whitespace correctly."""
        # Given
        full_text = "First chunk.\n\n   \n\nSecond chunk with spacing."
        chunk_texts = ["First chunk.", "Second chunk with spacing."]
        
        # When
        positions = _calculate_semantic_positions(full_text, chunk_texts, 0)
        
        # Then
        start_char_1, end_char_1 = positions[0]
        start_char_2, end_char_2 = positions[1]
        
        assert full_text[start_char_1:end_char_1] == chunk_texts[0]
        assert full_text[start_char_2:end_char_2] == chunk_texts[1]
        
    def test_calculate_semantic_positions_chunk_not_found_raises_error(self):
        """Test that missing chunk text raises ProcessingError."""
        # Given
        full_text = "This text does not contain the chunk."
        chunk_texts = ["Missing chunk text"]
        
        # When/Then
        with pytest.raises(ProcessingError, match="Chunk text not found in document"):
            _calculate_semantic_positions(full_text, chunk_texts, 0)


class TestSemanticChunkCreation:
    """Test semantic chunk creation with proper positioning."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_document = Mock(spec=Document)
        self.mock_document.id = "semantic_doc_456"
        self.mock_document.title = "Semantic Test Document"
        
    @patch('arete.ingestion.ingest_restructured_text.SimpleLLMService')
    def test_semantic_chunking_with_ai_structured_content(self, mock_llm_service):
        """Test semantic chunking with AI-structured content and positioning."""
        # Given
        full_text = """Introduction to Philosophy

Philosophy is the study of fundamental questions about existence, knowledge, values, reason, mind, and language.

The word "philosophy" comes from the Greek philosophia, which literally means "love of wisdom."

Ancient philosophers like Plato and Aristotle laid the groundwork for many philosophical traditions that continue today."""
        
        # Mock LLM response with structured chunks
        mock_llm_service.return_value.generate_response.return_value = {
            "choices": [{
                "message": {
                    "content": """[
                        "Philosophy is the study of fundamental questions about existence, knowledge, values, reason, mind, and language.",
                        "The word \\"philosophy\\" comes from the Greek philosophia, which literally means \\"love of wisdom.\\"",
                        "Ancient philosophers like Plato and Aristotle laid the groundwork for many philosophical traditions that continue today."
                    ]"""
                }
            }]
        }
        
        # When
        service = RestructuredTextIngestionService()
        chunks = service._create_semantic_chunks(self.mock_document, full_text)
        
        # Then
        assert len(chunks) == 3
        
        # Verify first chunk
        chunk1 = chunks[0]
        assert chunk1.document_id == "semantic_doc_456"
        assert chunk1.chunk_type == ChunkType.SEMANTIC
        assert chunk1.position == 0
        assert "fundamental questions" in chunk1.text
        
        # Verify character positions are sequential and non-overlapping
        for i in range(len(chunks) - 1):
            assert chunks[i].end_char <= chunks[i + 1].start_char
            
        # Verify each chunk text exists in the full text
        for chunk in chunks:
            assert chunk.text in full_text
            assert full_text[chunk.start_char:chunk.end_char] == chunk.text
            
    @patch('arete.ingestion.ingest_restructured_text.SimpleLLMService')
    def test_semantic_chunking_llm_failure_handling(self, mock_llm_service):
        """Test error handling when LLM fails during semantic chunking."""
        # Given
        full_text = "Sample text for chunking"
        mock_llm_service.return_value.generate_response.side_effect = Exception("LLM service unavailable")
        
        # When
        service = RestructuredTextIngestionService()
        
        # Then
        with pytest.raises(ProcessingError, match="Failed to create semantic chunks"):
            service._create_semantic_chunks(self.mock_document, full_text)


class TestSectionParsingWithCharacterTracking:
    """Test section parsing with accurate character position tracking."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_document = Mock(spec=Document)
        self.mock_document.id = "section_doc_789"
        
    def test_parse_sections_with_character_tracking(self):
        """Test that section parsing maintains accurate character positions."""
        # Given
        restructured_text = """Chapter 1: The Beginning
=======================

This is the first paragraph of chapter 1.

This is the second paragraph.

Chapter 2: The Middle
====================

This is the first paragraph of chapter 2.

This contains important philosophical concepts.
"""
        
        # When
        service = RestructuredTextIngestionService()
        sections = service._parse_sections(restructured_text)
        
        # Then
        assert len(sections) >= 2
        
        # Verify sections have proper character tracking
        total_chars_covered = 0
        for section in sections:
            assert section['start_char'] >= total_chars_covered
            assert section['end_char'] > section['start_char']
            assert len(section['content']) > 0
            
            # Verify content matches extracted text
            extracted_content = restructured_text[section['start_char']:section['end_char']]
            assert section['content'] in extracted_content
            
            total_chars_covered = section['end_char']
            
    def test_parse_sections_empty_document_handling(self):
        """Test section parsing with empty document."""
        # Given
        empty_text = ""
        
        # When
        service = RestructuredTextIngestionService()
        sections = service._parse_sections(empty_text)
        
        # Then
        assert len(sections) == 0
        
    def test_parse_sections_single_paragraph_no_headers(self):
        """Test section parsing with single paragraph and no headers."""
        # Given
        simple_text = "This is a simple paragraph with no section headers or special formatting."
        
        # When
        service = RestructuredTextIngestionService()
        sections = service._parse_sections(simple_text)
        
        # Then
        assert len(sections) == 1
        section = sections[0]
        assert section['start_char'] == 0
        assert section['end_char'] == len(simple_text)
        assert section['content'] == simple_text


class TestValidationErrorHandling:
    """Test validation error handling for malformed chunk data."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_document = Mock(spec=Document)
        self.mock_document.id = "validation_doc_101"
        
    def test_validation_missing_required_fields(self):
        """Test validation error for missing required Chunk fields."""
        # When/Then - Missing document
        with pytest.raises(ValidationError, match="Document is required"):
            _create_chunk(
                document=None,
                text="Valid text",
                start_char=0,
                end_char=10,
                position=1,
                chunk_type=ChunkType.PARAGRAPH
            )
            
    def test_validation_invalid_chunk_type(self):
        """Test validation error for invalid chunk type."""
        # When/Then
        with pytest.raises(ValidationError, match="Invalid chunk type"):
            _create_chunk(
                document=self.mock_document,
                text="Valid text",
                start_char=0,
                end_char=10,
                position=1,
                chunk_type="INVALID_TYPE"  # Invalid type
            )
            
    def test_validation_character_range_consistency(self):
        """Test validation of character range consistency with text length."""
        # Given
        text = "This text has exactly thirty characters!"
        text_length = len(text)  # Should be 41
        
        # When/Then - Character range doesn't match text length
        with pytest.raises(ValidationError, match="Character range inconsistent with text length"):
            _create_chunk(
                document=self.mock_document,
                text=text,
                start_char=0,
                end_char=text_length + 10,  # Inconsistent range
                position=1,
                chunk_type=ChunkType.PARAGRAPH
            )
            
    def test_validation_whitespace_only_text(self):
        """Test validation error for whitespace-only text."""
        # When/Then
        with pytest.raises(ValidationError, match="Chunk text cannot contain only whitespace"):
            _create_chunk(
                document=self.mock_document,
                text="   \n\t   ",  # Only whitespace
                start_char=0,
                end_char=8,
                position=1,
                chunk_type=ChunkType.PARAGRAPH
            )


class TestRestructuredTextIngestionService:
    """Integration tests for the complete ingestion service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = RestructuredTextIngestionService()
        self.mock_document = Mock(spec=Document)
        self.mock_document.id = "integration_doc_202"
        self.mock_document.title = "Integration Test Document"
        
    @patch('arete.ingestion.ingest_restructured_text.SimpleLLMService')
    def test_full_ingestion_pipeline_with_validation(self, mock_llm_service):
        """Test complete ingestion pipeline with chunk validation."""
        # Given
        restructured_content = """Philosophical Concepts
=====================

The Nature of Reality
---------------------

Reality consists of both material and immaterial aspects that interact in complex ways.

The material world is what we perceive through our senses.

Knowledge and Truth
------------------

Truth is the correspondence between our beliefs and reality.

Knowledge requires both true belief and proper justification.
"""
        
        # Mock LLM for semantic chunking
        mock_llm_service.return_value.generate_response.return_value = {
            "choices": [{
                "message": {
                    "content": """[
                        "Reality consists of both material and immaterial aspects that interact in complex ways.",
                        "The material world is what we perceive through our senses.",
                        "Truth is the correspondence between our beliefs and reality.",
                        "Knowledge requires both true belief and proper justification."
                    ]"""
                }
            }]
        }
        
        # When
        chunks = self.service.process_text(self.mock_document, restructured_content)
        
        # Then
        assert len(chunks) > 0
        
        # Verify all chunks have required fields
        for i, chunk in enumerate(chunks):
            assert chunk.document_id == "integration_doc_202"
            assert chunk.position == i
            assert chunk.start_char >= 0
            assert chunk.end_char > chunk.start_char
            assert len(chunk.text.strip()) > 0
            assert chunk.chunk_size == len(chunk.text)
            assert chunk.chunk_type in [ChunkType.SEMANTIC, ChunkType.SECTION, ChunkType.PARAGRAPH]
            
        # Verify chunks are properly ordered and non-overlapping
        for i in range(len(chunks) - 1):
            assert chunks[i].position < chunks[i + 1].position
            # Allow for gaps but no overlaps
            assert chunks[i].end_char <= chunks[i + 1].start_char
            
    def test_ingestion_service_error_recovery(self):
        """Test ingestion service error recovery mechanisms."""
        # Given - Malformed content that should trigger error handling
        malformed_content = None
        
        # When/Then
        with pytest.raises(ProcessingError, match="Invalid content provided"):
            self.service.process_text(self.mock_document, malformed_content)


class TestFileParsingIntegration:
    """Test file parsing integration with chunk validation."""
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_parse_restructured_text_file_success(self, mock_read_text, mock_exists):
        """Test successful file parsing with proper chunk creation."""
        # Given
        mock_exists.return_value = True
        mock_read_text.return_value = """Test Document
=============

This is a test paragraph for file parsing validation.

Another paragraph to ensure proper chunking.
"""
        
        file_path = Path("/test/document.rst")
        
        # When
        with patch('arete.ingestion.ingest_restructured_text.RestructuredTextIngestionService') as mock_service:
            mock_service.return_value.process_text.return_value = [
                Mock(spec=Chunk, document_id="test", position=0, text="Test content")
            ]
            
            result = parse_restructured_text_file(file_path)
            
        # Then
        assert result is not None
        mock_service.return_value.process_text.assert_called_once()
        
    @patch('pathlib.Path.exists')
    def test_parse_restructured_text_file_not_found(self, mock_exists):
        """Test file parsing with missing file."""
        # Given
        mock_exists.return_value = False
        file_path = Path("/test/missing.rst")
        
        # When/Then
        with pytest.raises(FileNotFoundError, match="File not found"):
            parse_restructured_text_file(file_path)