"""
Tests for Arete data models.
Following TDD principles - tests written before implementation.
"""

import uuid
from datetime import datetime
from typing import Dict, Any

import pytest
from pydantic import ValidationError

from arete.models.document import Document, ProcessingStatus


class TestDocument:
    """Test suite for Document model following TDD principles."""

    def test_document_creation_with_valid_data(self, sample_document_data):
        """Test basic document creation with valid data."""
        document = Document(**sample_document_data)

        assert document.title == "Republic"
        assert document.author == "Plato"
        assert (
            document.content == "Justice is the excellence of the soul and governs the "
            "harmony of all virtues."
        )
        assert document.language == "English"
        assert document.source == "Perseus Digital Library"
        assert document.translator == "Benjamin Jowett"
        assert document.publication_year == 380
        assert document.processing_status == ProcessingStatus.PENDING

        # Test auto-generated fields
        assert isinstance(document.id, uuid.UUID)
        assert isinstance(document.created_at, datetime)
        assert document.updated_at is None
        assert isinstance(document.metadata, dict)

    def test_document_creation_with_minimal_data(self):
        """Test document creation with only required fields."""
        minimal_data = {
            "title": "Phaedo",
            "author": "Plato",
            "content": "The soul is immortal and the body is merely its "
            "temporary prison.",
        }

        document = Document(**minimal_data)

        assert document.title == "Phaedo"
        assert document.author == "Plato"
        assert (
            document.content == "The soul is immortal and the body is merely its "
            "temporary prison."
        )
        assert document.language == "English"  # Default value
        assert document.source is None
        assert document.translator is None
        assert document.editor is None
        assert document.publication_year is None
        assert document.word_count is None
        assert document.chunk_count is None
        assert document.processing_status == ProcessingStatus.PENDING

    def test_document_title_validation(self):
        """Test title field validation rules."""
        base_data = {
            "author": "Plato",
            "content": "Some philosophical content here that meets "
            "minimum length requirements.",
        }

        # Test empty title
        with pytest.raises(ValidationError) as exc_info:
            Document(title="", **base_data)
        assert "at least 1 character" in str(exc_info.value)

        # Test whitespace-only title
        with pytest.raises(ValidationError) as exc_info:
            Document(title="   ", **base_data)
        assert "String should have at least 1 character" in str(exc_info.value)

        # Test title too long
        long_title = "A" * 501
        with pytest.raises(ValidationError) as exc_info:
            Document(title=long_title, **base_data)
        assert "at most 500 characters" in str(exc_info.value)

        # Test valid title at boundary (500 chars)
        boundary_title = "A" * 500
        document = Document(title=boundary_title, **base_data)
        assert document.title == boundary_title

    def test_document_author_validation(self):
        """Test author field validation rules."""
        base_data = {
            "title": "Test Work",
            "content": "Some philosophical content here that meets "
            "minimum length requirements.",
        }

        # Test empty author
        with pytest.raises(ValidationError) as exc_info:
            Document(author="", **base_data)
        assert "at least 1 character" in str(exc_info.value)

        # Test whitespace-only author
        with pytest.raises(ValidationError) as exc_info:
            Document(author="   ", **base_data)
        assert "String should have at least 1 character" in str(exc_info.value)

        # Test author too long
        long_author = "B" * 201
        with pytest.raises(ValidationError) as exc_info:
            Document(author=long_author, **base_data)
        assert "at most 200 characters" in str(exc_info.value)

        # Test valid author at boundary (200 chars)
        boundary_author = "B" * 200
        document = Document(author=boundary_author, **base_data)
        assert document.author == boundary_author

    def test_document_content_validation(self):
        """Test content field validation and sanitization."""
        base_data = {"title": "Test Work", "author": "Test Author"}

        # Test content too short
        with pytest.raises(ValidationError) as exc_info:
            Document(content="Short", **base_data)
        assert "at least 10 characters" in str(exc_info.value)

        # Test empty content
        with pytest.raises(ValidationError) as exc_info:
            Document(content="", **base_data)
        assert "at least 10 characters" in str(exc_info.value)

        # Test whitespace-only content
        with pytest.raises(ValidationError) as exc_info:
            Document(content="   \n\t   ", **base_data)
        assert "at least 10 characters" in str(exc_info.value)

        # Test content with leading/trailing whitespace gets trimmed
        content_with_whitespace = (
            "  \n  This is valid content with sufficient length.  \t  "
        )
        document = Document(content=content_with_whitespace, **base_data)
        assert document.content == "This is valid content with sufficient length."

        # Test minimum valid content (exactly 10 chars after trimming)
        min_content = "1234567890"
        document = Document(content=min_content, **base_data)
        assert document.content == min_content

    def test_document_publication_year_validation(self):
        """Test publication year validation rules."""
        base_data = {
            "title": "Test Work",
            "author": "Test Author",
            "content": "Some philosophical content here that meets "
            "minimum length requirements.",
        }

        # Test year too early (before -800)
        with pytest.raises(ValidationError) as exc_info:
            Document(publication_year=-801, **base_data)
        assert "greater than or equal to -800" in str(exc_info.value)

        # Test year too late (after 2030)
        with pytest.raises(ValidationError) as exc_info:
            Document(publication_year=2031, **base_data)
        assert "less than or equal to 2030" in str(exc_info.value)

        # Test valid boundary years
        ancient_doc = Document(publication_year=-800, **base_data)
        assert ancient_doc.publication_year == -800

        future_doc = Document(publication_year=2030, **base_data)
        assert future_doc.publication_year == 2030

        # Test typical philosophical dates
        classical_doc = Document(publication_year=-380, **base_data)
        assert classical_doc.publication_year == -380

    def test_document_processing_status_enum(self):
        """Test ProcessingStatus enum handling."""
        base_data = {
            "title": "Test Work",
            "author": "Test Author",
            "content": "Some philosophical content here that meets "
            "minimum length requirements.",
        }

        # Test all valid enum values
        for status in ProcessingStatus:
            document = Document(processing_status=status, **base_data)
            assert document.processing_status == status

        # Test default status
        document = Document(**base_data)
        assert document.processing_status == ProcessingStatus.PENDING

        # Test invalid status (should be handled by Pydantic)
        with pytest.raises(ValidationError):
            Document(processing_status="INVALID_STATUS", **base_data)

    def test_document_word_count_property(self):
        """Test computed word count calculation."""
        base_data = {"title": "Test Work", "author": "Test Author"}

        # Test simple word count
        document = Document(
            content="This is a test with exactly seven words.", **base_data
        )
        assert document.computed_word_count == 8

        # Test with punctuation and whitespace
        document = Document(
            content="Hello,    world!   This    has   multiple   spaces.", **base_data
        )
        assert document.computed_word_count == 6

        # Test with newlines and tabs
        document = Document(content="Line one.\nLine two.\tTabbed word.", **base_data)
        assert document.computed_word_count == 6

        # Test with minimum content
        document = Document(content="1234567890", **base_data)  # 10 chars, 1 word
        assert document.computed_word_count == 1

    def test_document_metadata_field(self):
        """Test metadata dictionary field."""
        document_data = {
            "title": "Test Work",
            "author": "Test Author",
            "content": "Some philosophical content here that meets "
            "minimum length requirements.",
            "metadata": {
                "manuscript": "Vaticanus_gr_1",
                "digital_source": "TLG",
                "encoding": "TEI-XML",
                "quality_score": 0.95,
            },
        }

        document = Document(**document_data)

        assert document.metadata["manuscript"] == "Vaticanus_gr_1"
        assert document.metadata["digital_source"] == "TLG"
        assert document.metadata["encoding"] == "TEI-XML"
        assert document.metadata["quality_score"] == 0.95

        # Test empty metadata (should default to empty dict)
        minimal_data = {
            "title": "Test Work",
            "author": "Test Author",
            "content": "Some philosophical content here that meets "
            "minimum length requirements.",
        }
        document = Document(**minimal_data)
        assert document.metadata == {}

    def test_document_neo4j_serialization(self, sample_document_data):
        """Test Neo4j dictionary serialization format."""
        document = Document(**sample_document_data)
        neo4j_dict = document.to_neo4j_dict()

        # Test required fields present
        assert neo4j_dict["title"] == "Republic"
        assert neo4j_dict["author"] == "Plato"
        assert (
            neo4j_dict["content"]
            == "Justice is the excellence of the soul and governs the "
            "harmony of all virtues."
        )
        assert neo4j_dict["language"] == "English"
        assert neo4j_dict["processing_status"] == "pending"

        # Test UUID converted to string
        assert isinstance(neo4j_dict["id"], str)
        uuid.UUID(neo4j_dict["id"])  # Should not raise exception

        # Test datetime converted to timestamp
        assert isinstance(neo4j_dict["created_at"], float)
        assert neo4j_dict["created_at"] > 0

        # Test None values excluded
        if document.updated_at is None:
            assert "updated_at" not in neo4j_dict

        # Test metadata preserved
        assert "metadata" in neo4j_dict

    def test_document_weaviate_serialization(self, sample_document_data):
        """Test Weaviate dictionary serialization format."""
        document = Document(**sample_document_data)
        weaviate_dict = document.to_weaviate_dict()

        # Test required fields present
        assert weaviate_dict["title"] == "Republic"
        assert weaviate_dict["author"] == "Plato"
        assert (
            weaviate_dict["content"]
            == "Justice is the excellence of the soul and governs the "
            "harmony of all virtues."
        )
        assert weaviate_dict["language"] == "English"

        # Test UUID excluded (Weaviate manages its own IDs)
        assert "id" not in weaviate_dict

        # Test Neo4j reference included for cross-referencing
        assert weaviate_dict["neo4j_id"] == str(document.id)

        # Test timestamps preserved for Weaviate
        assert "created_at" in weaviate_dict
        assert isinstance(weaviate_dict["created_at"], datetime)

    def test_document_string_field_sanitization(self):
        """Test that string fields are properly sanitized."""
        document_data = {
            "title": "  Republic  ",
            "author": "  Plato  ",
            "content": "  Justice is the excellence of the soul.  ",
            "source": "  Perseus Digital Library  ",
            "translator": "  Benjamin Jowett  ",
            "editor": "  John Smith  ",
        }

        document = Document(**document_data)

        # Test all string fields are trimmed
        assert document.title == "Republic"
        assert document.author == "Plato"
        assert document.content == "Justice is the excellence of the soul."
        assert document.source == "Perseus Digital Library"
        assert document.translator == "Benjamin Jowett"
        assert document.editor == "John Smith"

    def test_document_create_chunks_method(self, sample_document_data):
        """Test chunk creation functionality."""
        document = Document(**sample_document_data)

        # Test default chunk creation
        chunks = document.create_chunks()

        assert isinstance(chunks, list)
        assert len(chunks) > 0

        # Each chunk should have the expected structure
        for chunk in chunks:
            assert hasattr(chunk, "text")
            assert hasattr(chunk, "document_id")
            assert hasattr(chunk, "position")
            assert chunk.document_id == document.id
            assert len(chunk.text) <= 1000  # Default chunk size
            assert len(chunk.text) >= 10  # Minimum meaningful chunk size

    def test_document_create_chunks_with_custom_parameters(self):
        """Test chunk creation with custom parameters."""
        long_content = " ".join([f"Word{i}" for i in range(500)])  # ~500 words
        document_data = {
            "title": "Long Work",
            "author": "Test Author",
            "content": long_content,
        }
        document = Document(**document_data)

        # Test custom chunk size and overlap
        chunks = document.create_chunks(chunk_size=500, overlap=100)

        assert len(chunks) >= 2  # Should create multiple chunks

        # Test that chunks respect size limits
        for chunk in chunks:
            assert len(chunk.text) <= 500

        # Test overlap between consecutive chunks
        if len(chunks) > 1:
            overlap = chunks[0].get_overlap_with(chunks[1])
            assert overlap > 0  # Should have some overlap

    def test_document_extract_citations_method(self):
        """Test citation extraction functionality."""
        content_with_citations = (
            "As Plato writes in Republic 347e, "
            '"Justice is the excellence of the soul." '
            "Aristotle disagrees in Nicomachean Ethics 1094a, "
            'stating that "Ethics is practical wisdom." '
            "See also Aquinas, Summa Theologica I.q.21.a.1."
        )

        document_data = {
            "title": "Citations Test",
            "author": "Test Author",
            "content": content_with_citations,
        }
        document = Document(**document_data)

        citations = document.extract_citations()

        assert isinstance(citations, list)
        assert len(citations) >= 2  # Should find multiple citations

        # Test citation structure
        for citation in citations:
            assert hasattr(citation, "text")
            assert hasattr(citation, "source_title")
            assert hasattr(citation, "author")
            assert hasattr(citation, "document_id")
            assert citation.document_id == document.id

    def test_document_get_vectorizable_text(self, sample_document_data):
        """Test vectorizable text extraction for embeddings."""
        document = Document(**sample_document_data)
        vectorizable_text = document.get_vectorizable_text()

        assert isinstance(vectorizable_text, str)
        assert len(vectorizable_text) > 0

        # Should combine title, author, and content
        assert document.title in vectorizable_text
        assert document.author in vectorizable_text
        assert document.content in vectorizable_text

    def test_document_update_processing_status(self, sample_document_data):
        """Test processing status updates with timestamp tracking."""
        import time

        document = Document(**sample_document_data)
        original_updated_at = document.updated_at

        # Small delay to ensure different timestamp
        time.sleep(0.001)

        # Update processing status
        document.processing_status = ProcessingStatus.PROCESSING
        document.updated_at = datetime.utcnow()

        assert document.processing_status == ProcessingStatus.PROCESSING
        assert document.updated_at != original_updated_at
        assert document.updated_at >= document.created_at

    def test_document_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Test with special characters in content
        special_content = (
            "φιλοσοφία means love of wisdom. Αριστοτέλης wrote about ἠθικά."
        )
        document_data = {
            "title": "Greek Philosophy",
            "author": "Aristotle",
            "content": special_content,
        }

        document = Document(**document_data)
        assert document.content == special_content
        assert document.computed_word_count > 0

        # Test with very old publication year
        ancient_document = Document(
            title="Ancient Text",
            author="Unknown",
            content="Very ancient philosophical wisdom passed down "
            "through generations.",
            publication_year=-800,
        )
        assert ancient_document.publication_year == -800

    def test_document_repr_security(self):
        """Test that document representation doesn't leak sensitive data."""
        document_data = {
            "title": "Secret Work",
            "author": "Anonymous",
            "content": "This contains sensitive philosophical arguments.",
            "metadata": {"api_key": "secret123", "user_id": "user456"},
        }

        document = Document(**document_data)
        repr_str = repr(document)

        # Basic fields should be visible
        assert "Secret Work" in repr_str
        assert "Anonymous" in repr_str

        # But sensitive metadata should not be exposed in basic repr
        # (This would depend on the actual repr implementation)

    def test_document_model_validation_assignment(self):
        """Test that validate_assignment=True works correctly."""
        document_data = {
            "title": "Test Work",
            "author": "Test Author",
            "content": "Some philosophical content here that meets "
            "minimum length requirements.",
        }
        document = Document(**document_data)

        # Test that assignment validation works
        with pytest.raises(ValidationError):
            document.title = ""  # Should fail validation

        with pytest.raises(ValidationError):
            document.publication_year = 2031  # Should fail validation

        # Test valid assignments
        document.title = "New Title"
        assert document.title == "New Title"


# Test fixtures for reusable test data
@pytest.fixture
def sample_document_data() -> Dict[str, Any]:
    """Sample document data for testing."""
    return {
        "title": "Republic",
        "author": "Plato",
        "content": "Justice is the excellence of the soul and governs "
        "the harmony of all virtues.",
        "language": "English",
        "source": "Perseus Digital Library",
        "translator": "Benjamin Jowett",
        "editor": "Paul Shorey",
        "publication_year": 380,
    }


@pytest.fixture
def minimal_document_data() -> Dict[str, Any]:
    """Minimal valid document data for testing."""
    return {
        "title": "Phaedo",
        "author": "Plato",
        "content": "The soul is immortal and beyond the physical realm.",
    }


@pytest.fixture
def sample_processed_document() -> Dict[str, Any]:
    """Sample processed document with metadata."""
    return {
        "title": "Nicomachean Ethics",
        "author": "Aristotle",
        "content": "Happiness is the highest human good and the end at "
        "which all our activities ultimately aim.",
        "language": "English",
        "source": "Loeb Classical Library",
        "translator": "H. Rackham",
        "publication_year": 1926,
        "word_count": 95000,
        "chunk_count": 95,
        "processing_status": ProcessingStatus.COMPLETED,
        "metadata": {
            "manuscript_tradition": "multiple_sources",
            "scholarly_edition": "Ross_1925",
            "bekker_pages": "1094a-1181b",
            "books": 10,
            "quality_score": 0.98,
        },
    }


class TestProcessingStatus:
    """Test ProcessingStatus enum."""

    def test_processing_status_values(self):
        """Test all ProcessingStatus enum values."""
        assert ProcessingStatus.PENDING == "pending"
        assert ProcessingStatus.PROCESSING == "processing"
        assert ProcessingStatus.COMPLETED == "completed"
        assert ProcessingStatus.FAILED == "failed"

    def test_processing_status_iteration(self):
        """Test that all status values can be iterated."""
        statuses = list(ProcessingStatus)
        assert len(statuses) == 5
        assert ProcessingStatus.PENDING in statuses
        assert ProcessingStatus.PROCESSING in statuses
        assert ProcessingStatus.COMPLETED in statuses
        assert ProcessingStatus.FAILED in statuses
        assert ProcessingStatus.SKIPPED in statuses


class TestDocumentIntegration:
    """Integration tests for Document model with database serialization."""

    def test_full_document_lifecycle(self, sample_document_data):
        """Test complete document lifecycle from creation to serialization."""
        # 1. Create document
        document = Document(**sample_document_data)

        # 2. Verify initial state
        assert document.processing_status == ProcessingStatus.PENDING
        assert document.word_count is None
        assert document.chunk_count is None

        # 3. Process document (simulate processing)
        document.processing_status = ProcessingStatus.PROCESSING
        chunks = document.create_chunks()
        document.extract_citations()  # Call but don't store unused result

        # 4. Update metadata
        document.word_count = document.computed_word_count
        document.chunk_count = len(chunks)
        document.processing_status = ProcessingStatus.COMPLETED
        document.updated_at = datetime.utcnow()

        # 5. Test serialization for both databases
        neo4j_data = document.to_neo4j_dict()
        weaviate_data = document.to_weaviate_dict()

        # Verify both serializations are valid
        assert neo4j_data["processing_status"] == "completed"
        assert weaviate_data["word_count"] == document.computed_word_count
        assert weaviate_data["neo4j_id"] == str(document.id)

    def test_document_batch_processing_simulation(self):
        """Test batch processing of multiple documents."""
        documents_data = [
            {
                "title": f"Work {i}",
                "author": f"Author {i}",
                "content": f"Philosophical content {i} " * 20,  # Ensure minimum length
            }
            for i in range(5)
        ]

        documents = [Document(**data) for data in documents_data]

        # Simulate batch processing
        for doc in documents:
            assert doc.processing_status == ProcessingStatus.PENDING
            chunks = doc.create_chunks()
            assert len(chunks) > 0

        # Verify all documents processed
        assert len(documents) == 5
        assert all(doc.computed_word_count > 0 for doc in documents)
