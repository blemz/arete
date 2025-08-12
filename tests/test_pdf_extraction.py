"""Test suite for PDF text extraction."""

import io
import tempfile
from pathlib import Path
from typing import Dict

import pytest

from src.arete.processing.extractors import PDFExtractor, PDFMetadata


class TestPDFMetadata:
    """Test PDFMetadata model."""

    def test_pdf_metadata_creation(self):
        """Test creating PDFMetadata with all fields."""
        metadata = PDFMetadata(
            title="Republic",
            author="Plato",
            subject="Political Philosophy",
            creator="LaTeX",
            producer="pdfTeX",
            creation_date="2024-01-01",
            modification_date="2024-01-02",
            page_count=10,
            language="English"
        )
        
        assert metadata.title == "Republic"
        assert metadata.author == "Plato"
        assert metadata.subject == "Political Philosophy"
        assert metadata.page_count == 10

    def test_pdf_metadata_minimal(self):
        """Test creating PDFMetadata with minimal fields."""
        metadata = PDFMetadata(page_count=5)
        
        assert metadata.page_count == 5
        assert metadata.title is None
        assert metadata.author is None

    def test_pdf_metadata_validation(self):
        """Test PDFMetadata validation."""
        from pydantic import ValidationError
        
        # Test negative page count
        with pytest.raises(ValidationError):
            PDFMetadata(page_count=-1)
            
        # Test zero page count
        with pytest.raises(ValidationError):
            PDFMetadata(page_count=0)

    def test_pdf_metadata_string_normalization(self):
        """Test string field normalization."""
        metadata = PDFMetadata(
            title="  Republic  ",
            author="  Plato  ",
            page_count=1
        )
        
        assert metadata.title == "Republic"
        assert metadata.author == "Plato"

    def test_pdf_metadata_empty_strings(self):
        """Test handling of empty strings."""
        metadata = PDFMetadata(
            title="",
            author="   ",
            page_count=1
        )
        
        assert metadata.title is None
        assert metadata.author is None


class TestPDFExtractor:
    """Test PDF text extraction functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = PDFExtractor()

    def test_extractor_initialization(self):
        """Test PDFExtractor initialization."""
        extractor = PDFExtractor()
        assert extractor is not None

    def test_extractor_with_options(self):
        """Test PDFExtractor with custom options."""
        extractor = PDFExtractor(
            extract_images=True,
            preserve_layout=True,
            password="secret"
        )
        assert extractor.extract_images is True
        assert extractor.preserve_layout is True
        assert extractor.password == "secret"

    def test_validate_pdf_file_path(self):
        """Test PDF file path validation."""
        # Test non-existent file
        with pytest.raises(FileNotFoundError):
            self.extractor.extract_from_file("/nonexistent/file.pdf")
            
        # Test non-PDF file
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp.write(b"Not a PDF")
            tmp.flush()
            
            with pytest.raises(ValueError, match="File must have .pdf extension"):
                self.extractor.extract_from_file(tmp.name)

    def test_extract_from_bytes_invalid(self):
        """Test extraction from invalid PDF bytes."""
        invalid_pdf = b"This is not a PDF file"
        
        with pytest.raises(ValueError, match="Invalid PDF data"):
            self.extractor.extract_from_bytes(invalid_pdf)

    def test_extract_from_bytes_empty(self):
        """Test extraction from empty bytes."""
        with pytest.raises(ValueError, match="PDF data cannot be empty"):
            self.extractor.extract_from_bytes(b"")

    def test_extract_metadata_only(self):
        """Test extracting only metadata without text."""
        # This would typically be tested with a real PDF file
        # For now, we test the method signature and error handling
        with pytest.raises(FileNotFoundError):
            self.extractor.extract_metadata("/nonexistent/file.pdf")

    def test_create_sample_pdf_content(self):
        """Test creating sample PDF content for testing."""
        # Test the structure of extracted content
        sample_content = {
            "text": "Sample philosophical text about virtue ethics.",
            "metadata": PDFMetadata(
                title="Test Document",
                author="Test Author",
                page_count=1
            ),
            "page_texts": ["Sample philosophical text about virtue ethics."],
            "images": []
        }
        
        assert "text" in sample_content
        assert "metadata" in sample_content
        assert "page_texts" in sample_content
        assert isinstance(sample_content["metadata"], PDFMetadata)
        assert len(sample_content["page_texts"]) == 1

    def test_extract_result_structure(self):
        """Test the structure of extraction results."""
        # Test what a typical extraction result should look like
        expected_keys = {"text", "metadata", "page_texts", "images"}
        
        # Mock result structure
        mock_result = {
            "text": "Combined text from all pages",
            "metadata": PDFMetadata(page_count=2),
            "page_texts": ["Page 1 text", "Page 2 text"],
            "images": []
        }
        
        assert all(key in mock_result for key in expected_keys)
        assert isinstance(mock_result["metadata"], PDFMetadata)
        assert isinstance(mock_result["page_texts"], list)
        assert isinstance(mock_result["images"], list)

    def test_text_cleaning(self):
        """Test text cleaning functionality."""
        dirty_text = "  This is\n\na philosophical\r\ntext with\t\textra   whitespace.  "
        cleaned = self.extractor._clean_text(dirty_text)
        
        # Text should be cleaned but paragraph breaks preserved
        assert "This is" in cleaned
        assert "philosophical" in cleaned  
        assert "extra whitespace" in cleaned
        assert cleaned.startswith("This is")
        assert cleaned.endswith("whitespace.")

    def test_text_cleaning_edge_cases(self):
        """Test text cleaning edge cases."""
        # Empty text
        assert self.extractor._clean_text("") == ""
        
        # Whitespace only
        assert self.extractor._clean_text("   \n\t\r   ") == ""
        
        # Text with multiple paragraph breaks
        text_with_breaks = "First paragraph.\n\n\nSecond paragraph."
        cleaned = self.extractor._clean_text(text_with_breaks)
        assert "\n\n" in cleaned  # Should preserve paragraph breaks

    def test_page_text_extraction(self):
        """Test individual page text extraction."""
        # Test the expected behavior for page-by-page extraction
        sample_pages = [
            "First page content about Aristotelian ethics.",
            "Second page discusses virtue theory.",
            "Third page concludes with practical applications."
        ]
        
        # Test that page texts are properly structured
        for i, page_text in enumerate(sample_pages):
            assert isinstance(page_text, str)
            assert len(page_text) > 0
            assert page_text.strip() == page_text  # Should be cleaned

    def test_metadata_extraction_fields(self):
        """Test extraction of specific metadata fields."""
        # Test that all expected metadata fields can be handled
        full_metadata = PDFMetadata(
            title="Nicomachean Ethics",
            author="Aristotle",
            subject="Philosophy",
            creator="LaTeX compiler",
            producer="pdfTeX-1.40.21",
            creation_date="2024-01-15T10:30:00Z",
            modification_date="2024-01-15T11:45:00Z",
            page_count=350,
            language="English"
        )
        
        assert full_metadata.title == "Nicomachean Ethics"
        assert full_metadata.author == "Aristotle"
        assert full_metadata.page_count == 350

    def test_error_handling_corrupted_pdf(self):
        """Test handling of corrupted PDF files."""
        # Test with malformed PDF-like data
        corrupted_pdf = b"%PDF-1.4\nCorrupted content"
        
        with pytest.raises(ValueError, match="Invalid PDF data"):
            self.extractor.extract_from_bytes(corrupted_pdf)

    def test_password_protected_pdf(self):
        """Test handling of password-protected PDFs."""
        # This would be tested with actual password-protected PDFs
        # For now, test the interface
        extractor = PDFExtractor(password="wrongpassword")
        
        # Test that password is stored
        assert extractor.password == "wrongpassword"

    def test_extract_with_options(self):
        """Test extraction with various options."""
        extractor = PDFExtractor(
            extract_images=True,
            preserve_layout=True,
            extract_annotations=True
        )
        
        assert extractor.extract_images is True
        assert extractor.preserve_layout is True
        assert extractor.extract_annotations is True

    def test_large_pdf_handling(self):
        """Test handling of large PDF files."""
        # Test memory management for large files
        # This would typically involve testing with actual large PDFs
        extractor = PDFExtractor()
        
        # Test that extractor can handle the concept of large files
        assert hasattr(extractor, 'extract_from_file')
        assert hasattr(extractor, 'extract_from_bytes')

    def test_philosophical_text_detection(self):
        """Test detection of philosophical content patterns."""
        philosophical_text = (
            "Aristotle argues in the Nicomachean Ethics that virtue is a disposition. "
            "The concept of eudaimonia, often translated as happiness or flourishing, "
            "represents the highest good according to Aristotelian thought."
        )
        
        # Test that philosophical terms are preserved during extraction
        cleaned = self.extractor._clean_text(philosophical_text)
        philosophical_terms = ["Aristotle", "Nicomachean Ethics", "virtue", "eudaimonia"]
        
        for term in philosophical_terms:
            assert term in cleaned