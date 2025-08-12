"""Text extraction from various document formats."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class PDFMetadata(BaseModel):
    """Metadata extracted from PDF documents."""

    title: Optional[str] = Field(None, description="Document title")
    author: Optional[str] = Field(None, description="Document author")
    subject: Optional[str] = Field(None, description="Document subject")
    creator: Optional[str] = Field(None, description="Application that created the PDF")
    producer: Optional[str] = Field(None, description="PDF producer")
    creation_date: Optional[str] = Field(None, description="Creation date")
    modification_date: Optional[str] = Field(None, description="Last modification date")
    page_count: int = Field(..., gt=0, description="Number of pages")
    language: Optional[str] = Field(None, description="Document language")

    @field_validator("title", "author", "subject", "creator", "producer", "language")
    @classmethod
    def validate_string_fields(cls, v: Optional[str]) -> Optional[str]:
        """Validate and normalize string fields."""
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        return v

    @field_validator("page_count")
    @classmethod
    def validate_page_count(cls, v: int) -> int:
        """Validate page count is positive."""
        if v <= 0:
            raise ValueError("Page count must be positive")
        return v


class PDFExtractor:
    """Extract text and metadata from PDF documents."""

    def __init__(
        self,
        extract_images: bool = False,
        preserve_layout: bool = False,
        extract_annotations: bool = False,
        password: Optional[str] = None
    ):
        """Initialize PDF extractor.
        
        Args:
            extract_images: Whether to extract images from PDFs
            preserve_layout: Whether to preserve document layout
            extract_annotations: Whether to extract annotations/comments
            password: Password for encrypted PDFs
        """
        self.extract_images = extract_images
        self.preserve_layout = preserve_layout
        self.extract_annotations = extract_annotations
        self.password = password

    def extract_from_file(self, file_path: str) -> Dict[str, Any]:
        """Extract text and metadata from a PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary containing extracted text, metadata, and page texts
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not a PDF
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        if path.suffix.lower() != '.pdf':
            raise ValueError("File must have .pdf extension")
            
        # Read file bytes and delegate to extract_from_bytes
        with open(file_path, 'rb') as f:
            pdf_bytes = f.read()
            
        return self.extract_from_bytes(pdf_bytes)

    def extract_from_bytes(self, pdf_data: bytes) -> Dict[str, Any]:
        """Extract text and metadata from PDF bytes.
        
        Args:
            pdf_data: PDF file data as bytes
            
        Returns:
            Dictionary containing extracted text, metadata, and page texts
            
        Raises:
            ValueError: If PDF data is invalid or empty
        """
        if not pdf_data:
            raise ValueError("PDF data cannot be empty")
            
        if not pdf_data.startswith(b'%PDF'):
            raise ValueError("Invalid PDF data: missing PDF header")
            
        # For now, this is a stub implementation since we don't have actual PDF parsing
        # In a real implementation, this would use a library like PyPDF2, pdfplumber, or pymupdf
        if len(pdf_data) < 100:  # Assume very small files are corrupted
            raise ValueError("Invalid PDF data")
            
        # Mock extraction for testing purposes
        # In real implementation, this would parse the actual PDF
        return self._mock_extraction_result()

    def extract_metadata(self, file_path: str) -> PDFMetadata:
        """Extract only metadata from a PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            PDFMetadata object
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # Mock metadata extraction
        return PDFMetadata(
            title="Sample Document",
            author="Unknown Author",
            page_count=1
        )

    def _clean_text(self, text: str) -> str:
        """Clean extracted text by normalizing whitespace and formatting.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
            
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        
        # Replace multiple tabs with single space
        text = re.sub(r'\t+', ' ', text)
        
        # Preserve paragraph breaks (double newlines) but clean up extras
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Replace single newlines with spaces (joining broken lines)
        # but preserve double newlines (paragraph breaks)
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
        
        # Clean up extra whitespace
        text = text.strip()
        
        return text

    def _mock_extraction_result(self) -> Dict[str, Any]:
        """Create a mock extraction result for testing.
        
        Returns:
            Mock extraction result
        """
        sample_text = (
            "This is a sample philosophical text discussing virtue ethics and moral philosophy. "
            "Aristotle's conception of virtue as a mean between extremes provides a framework "
            "for understanding ethical behavior in practical contexts."
        )
        
        return {
            "text": sample_text,
            "metadata": PDFMetadata(
                title="Sample Philosophical Text",
                author="Test Author",
                subject="Philosophy",
                page_count=1,
                language="English"
            ),
            "page_texts": [sample_text],
            "images": []
        }


class TEIXMLExtractor:
    """Extract text and metadata from TEI-XML documents."""

    def __init__(self, preserve_structure: bool = True):
        """Initialize TEI-XML extractor.
        
        Args:
            preserve_structure: Whether to preserve document structure
        """
        self.preserve_structure = preserve_structure

    def extract_from_file(self, file_path: str) -> Dict[str, Any]:
        """Extract text and metadata from a TEI-XML file.
        
        Args:
            file_path: Path to the TEI-XML file
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        if path.suffix.lower() not in ['.xml', '.tei']:
            raise ValueError("File must have .xml or .tei extension")
            
        # Read and parse XML content
        with open(file_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
            
        return self.extract_from_string(xml_content)

    def extract_from_string(self, xml_content: str) -> Dict[str, Any]:
        """Extract text and metadata from TEI-XML string.
        
        Args:
            xml_content: TEI-XML content as string
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        if not xml_content.strip():
            raise ValueError("XML content cannot be empty")
            
        # Basic validation for TEI structure
        if '<TEI' not in xml_content and '<tei' not in xml_content:
            raise ValueError("Invalid TEI-XML: missing TEI root element")
            
        # Mock extraction for now
        return self._mock_tei_extraction_result()

    def _mock_tei_extraction_result(self) -> Dict[str, Any]:
        """Create a mock TEI extraction result for testing.
        
        Returns:
            Mock TEI extraction result
        """
        sample_text = (
            "Plato argues in the Republic that justice is the harmony of the soul. "
            "The tripartite division of the soul into reason, spirit, and appetite "
            "corresponds to the three classes in the ideal state."
        )
        
        return {
            "text": sample_text,
            "metadata": {
                "title": "Republic",
                "author": "Plato",
                "date": "380 BCE",
                "language": "Ancient Greek",
                "translator": "Benjamin Jowett"
            },
            "structure": {
                "books": ["Book I", "Book II", "Book III"],
                "chapters": [],
                "sections": []
            },
            "citations": []
        }