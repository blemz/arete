"""Text extraction from various document formats."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree as ET

from pydantic import BaseModel, Field, field_validator

try:
    import spacy
    from spacy.language import Language
    from spacy.pipeline import EntityRuler
except Exception:  # pragma: no cover - spaCy optional import handled at runtime
    spacy = None
    Language = None
    EntityRuler = None

from arete.models.entity import Entity, EntityType, MentionData


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
        # Define TEI namespaces
        self.namespaces = {
            'tei': 'http://www.tei-c.org/ns/1.0',
            '': 'http://www.tei-c.org/ns/1.0'
        }

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
            
        try:
            # Parse the XML
            root = ET.fromstring(xml_content)
            
            # Register TEI namespace if present
            if 'http://www.tei-c.org/ns/1.0' in xml_content:
                ET.register_namespace('tei', 'http://www.tei-c.org/ns/1.0')
            
            # Extract metadata from teiHeader
            metadata = self._extract_metadata(root)
            
            # Extract text content
            text = self._extract_text(root)
            
            # Extract structure if requested
            structure = self._extract_structure(root) if self.preserve_structure else {}
            
            # Extract citations and references
            citations = self._extract_citations(root)
            
            return {
                "text": text,
                "metadata": metadata,
                "structure": structure,
                "citations": citations
            }
            
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML format: {e}")

    def _extract_metadata(self, root: ET.Element) -> Dict[str, str]:
        """Extract metadata from TEI header.
        
        Args:
            root: Root element of TEI document
            
        Returns:
            Dictionary of metadata
        """
        metadata = {}
        
        # Handle both namespaced and non-namespaced TEI
        tei_header = None
        # Try with namespace first
        tei_header = root.find('.//{http://www.tei-c.org/ns/1.0}teiHeader')
        if tei_header is None:
            # Try without namespace
            tei_header = root.find('.//teiHeader')
                
        if tei_header is None:
            return metadata
            
        # Extract title
        title_elem = tei_header.find('.//{http://www.tei-c.org/ns/1.0}title')
        if title_elem is None:
            title_elem = tei_header.find('.//title')
        if title_elem is not None and title_elem.text:
            metadata['title'] = title_elem.text.strip()
                
        # Extract author
        author_elem = tei_header.find('.//{http://www.tei-c.org/ns/1.0}author')
        if author_elem is None:
            author_elem = tei_header.find('.//author')
        if author_elem is not None and author_elem.text:
            metadata['author'] = author_elem.text.strip()
                
        # Extract editor
        editor_elem = tei_header.find('.//{http://www.tei-c.org/ns/1.0}editor')
        if editor_elem is None:
            editor_elem = tei_header.find('.//editor')
        if editor_elem is not None and editor_elem.text:
            metadata['editor'] = editor_elem.text.strip()
                
        # Extract translator
        translator_elem = tei_header.find('.//{http://www.tei-c.org/ns/1.0}translator')
        if translator_elem is None:
            translator_elem = tei_header.find('.//translator')
        if translator_elem is not None and translator_elem.text:
            metadata['translator'] = translator_elem.text.strip()
                
        # Extract date
        date_elem = tei_header.find('.//{http://www.tei-c.org/ns/1.0}date')
        if date_elem is None:
            date_elem = tei_header.find('.//date')
        if date_elem is not None and date_elem.text:
            metadata['date'] = date_elem.text.strip()
                
        # Extract language
        lang_elem = tei_header.find('.//{http://www.tei-c.org/ns/1.0}language')
        if lang_elem is None:
            lang_elem = tei_header.find('.//language')
        if lang_elem is not None:
            if lang_elem.text:
                metadata['language'] = lang_elem.text.strip()
            elif 'ident' in lang_elem.attrib:
                lang_code = lang_elem.attrib['ident']
                lang_map = {
                    'en': 'English',
                    'grc': 'Ancient Greek', 
                    'la': 'Latin',
                    'de': 'German',
                    'fr': 'French'
                }
                metadata['language'] = lang_map.get(lang_code, lang_code)
        
        # Extract publisher
        pub_elem = tei_header.find('.//{http://www.tei-c.org/ns/1.0}publisher')
        if pub_elem is None:
            pub_elem = tei_header.find('.//publisher')
        if pub_elem is not None and pub_elem.text:
            metadata['publisher'] = pub_elem.text.strip()
        
        return metadata

    def _extract_text(self, root: ET.Element) -> str:
        """Extract text content from TEI document.
        
        Args:
            root: Root element of TEI document
            
        Returns:
            Extracted text content
        """
        # Find the text element
        text_elem = root.find('.//{http://www.tei-c.org/ns/1.0}text')
        if text_elem is None:
            text_elem = root.find('.//text')
                
        if text_elem is None:
            return ""
            
        # Extract all text content, preserving paragraph structure
        text_parts = []
        
        # Process all content, maintaining document order
        # We need to get all paragraphs and speeches, preserving their order
        
        # Get all body elements and process them in document order
        body = text_elem.find('.//{http://www.tei-c.org/ns/1.0}body')
        if body is None:
            body = text_elem.find('.//body')
            
        if body is not None:
            # Process all direct children and descendants that contain text
            self._extract_text_from_element(body, text_parts)
        else:
            # Fallback: process all paragraphs and speeches
            pass
            
        # If no paragraphs found, get all text
        if not text_parts:
            text_content = self._get_element_text(text_elem)
            if text_content.strip():
                text_parts.append(text_content.strip())
        
        # Join paragraphs with double newlines
        return '\n\n'.join(text_parts)

    def _get_element_text(self, element: ET.Element) -> str:
        """Get all text content from an element, including children.
        
        Args:
            element: XML element
            
        Returns:
            Combined text content
        """
        text_parts = []
        
        if element.text:
            text_parts.append(element.text)
            
        for child in element:
            # Get text from child elements
            child_text = self._get_element_text(child)
            if child_text.strip():
                text_parts.append(child_text)
                
            # Get tail text after child element
            if child.tail:
                text_parts.append(child.tail)
                
        return ' '.join(text_parts)

    def _extract_text_from_element(self, element: ET.Element, text_parts: List[str]) -> None:
        """Extract text from element in document order.
        
        Args:
            element: XML element to extract text from
            text_parts: List to append extracted text parts to
        """
        # Process direct paragraphs
        direct_paragraphs = []
        for child in element:
            if child.tag.endswith('}p') or child.tag == 'p':
                # Check if this paragraph is not inside a speech element
                is_in_speech = False
                parent = element
                while parent is not None:
                    if parent.tag.endswith('}sp') or parent.tag == 'sp':
                        is_in_speech = True
                        break
                    parent = parent.getparent() if hasattr(parent, 'getparent') else None
                    
                if not is_in_speech:
                    para_text = self._get_element_text(child)
                    if para_text.strip():
                        text_parts.append(para_text.strip())
                        
            elif child.tag.endswith('}sp') or child.tag == 'sp':
                # Handle speech elements
                speech_parts = []
                
                # Extract speaker name if present
                speaker = child.find('.//{http://www.tei-c.org/ns/1.0}speaker')
                if speaker is None:
                    speaker = child.find('.//speaker')
                if speaker is not None and speaker.text:
                    speech_parts.append(f"{speaker.text.strip()}:")
                
                # Extract paragraphs within this speech
                sp_paragraphs = child.findall('.//{http://www.tei-c.org/ns/1.0}p')
                if not sp_paragraphs:
                    sp_paragraphs = child.findall('.//p')
                    
                for p in sp_paragraphs:
                    para_text = self._get_element_text(p)
                    if para_text.strip():
                        speech_parts.append(para_text.strip())
                
                if speech_parts:
                    text_parts.append(' '.join(speech_parts))
            else:
                # Recursively process other elements that might contain text
                self._extract_text_from_element(child, text_parts)

    def _extract_structure(self, root: ET.Element) -> Dict[str, List[str]]:
        """Extract document structure information.
        
        Args:
            root: Root element of TEI document
            
        Returns:
            Dictionary with structure information
        """
        structure = {
            "books": [],
            "chapters": [],
            "sections": []
        }
        
        # Find text element
        text_elem = root.find('.//{http://www.tei-c.org/ns/1.0}text')
        if text_elem is None:
            text_elem = root.find('.//text')
                
        if text_elem is None:
            return structure
            
        # Extract books
        book_divs = text_elem.findall('.//{http://www.tei-c.org/ns/1.0}div[@type="book"]')
        if not book_divs:
            book_divs = text_elem.findall('.//div[@type="book"]')
        
        for book_div in book_divs:
            book_num = book_div.get('n', '')
            head_elem = book_div.find('.//{http://www.tei-c.org/ns/1.0}head')
            if head_elem is None:
                head_elem = book_div.find('.//head')
            if head_elem is not None and head_elem.text:
                structure["books"].append(head_elem.text.strip())
            elif book_num:
                structure["books"].append(f"Book {book_num}")
                
        # Extract chapters  
        chapter_divs = text_elem.findall('.//{http://www.tei-c.org/ns/1.0}div[@type="chapter"]')
        if not chapter_divs:
            chapter_divs = text_elem.findall('.//div[@type="chapter"]')
            
        for chapter_div in chapter_divs:
            chapter_num = chapter_div.get('n', '')
            head_elem = chapter_div.find('.//{http://www.tei-c.org/ns/1.0}head')
            if head_elem is None:
                head_elem = chapter_div.find('.//head')
            if head_elem is not None and head_elem.text:
                structure["chapters"].append(head_elem.text.strip())
            elif chapter_num:
                structure["chapters"].append(f"Chapter {chapter_num}")
                
        # Extract sections
        section_divs = text_elem.findall('.//{http://www.tei-c.org/ns/1.0}div[@type="section"]')
        if not section_divs:
            section_divs = text_elem.findall('.//div[@type="section"]')
            
        for section_div in section_divs:
            section_num = section_div.get('n', '')
            if section_num:
                structure["sections"].append(section_num)
                
        return structure

    def _extract_citations(self, root: ET.Element) -> List[Dict[str, str]]:
        """Extract citations and references from TEI document.
        
        Args:
            root: Root element of TEI document
            
        Returns:
            List of citation dictionaries
        """
        citations = []
        
        # Find text element
        text_elem = root.find('.//{http://www.tei-c.org/ns/1.0}text')
        if text_elem is None:
            text_elem = root.find('.//text')
                
        if text_elem is None:
            return citations
            
        # Extract references
        ref_elems = text_elem.findall('.//{http://www.tei-c.org/ns/1.0}ref')
        if not ref_elems:
            ref_elems = text_elem.findall('.//ref')
            
        for ref in ref_elems:
            citation = {}
            if ref.text:
                citation['text'] = ref.text.strip()
            if 'target' in ref.attrib:
                citation['target'] = ref.attrib['target']
            if citation:
                citations.append(citation)
                
        # Extract bibliographic citations
        bibl_elems = text_elem.findall('.//{http://www.tei-c.org/ns/1.0}bibl')
        if not bibl_elems:
            bibl_elems = text_elem.findall('.//bibl')
            
        for bibl in bibl_elems:
            citation = {}
            
            # Extract author
            author_elem = bibl.find('.//{http://www.tei-c.org/ns/1.0}author')
            if author_elem is None:
                author_elem = bibl.find('.//author')
            if author_elem is not None and author_elem.text:
                citation['author'] = author_elem.text.strip()
                
            # Extract title
            title_elem = bibl.find('.//{http://www.tei-c.org/ns/1.0}title')
            if title_elem is None:
                title_elem = bibl.find('.//title')
            if title_elem is not None and title_elem.text:
                citation['title'] = title_elem.text.strip()
                
            # Extract scope
            scope_elem = bibl.find('.//{http://www.tei-c.org/ns/1.0}biblScope')
            if scope_elem is None:
                scope_elem = bibl.find('.//biblScope')
            if scope_elem is not None and scope_elem.text:
                citation['scope'] = scope_elem.text.strip()
                
            if citation:
                citations.append(citation)
                
        return citations


class EntityExtractor:
    """Lightweight entity extractor using spaCy with optional EntityRuler patterns.

    Designed for deterministic tests without requiring large models. By default uses
    a blank English pipeline and only the EntityRuler if patterns are provided.
    """

    def __init__(self, patterns: Optional[List[Dict[str, Any]]] = None):
        self._nlp: Optional[Language] = None
        if spacy is not None:
            # Use a blank English model to avoid heavyweight downloads
            self._nlp = spacy.blank("en")
            if patterns:
                ruler = self._nlp.add_pipe("entity_ruler")  # type: ignore[arg-type]
                assert isinstance(ruler, EntityRuler)
                ruler.add_patterns(patterns)  # type: ignore[union-attr]

        self._has_patterns = bool(patterns)

    def extract_entities(self, text: str, document_id) -> List[Entity]:
        if not text or not text.strip():
            return []

        if self._nlp is None:
            # spaCy not available; return empty deterministic result
            return []

        doc = self._nlp(text)

        # Aggregate spans by text
        name_to_mentions: Dict[str, List[MentionData]] = {}
        for ent in doc.ents:
            ent_text = ent.text.strip()
            if not ent_text:
                continue
            start_char = ent.start_char
            end_char = ent.end_char
            context_window = 80
            start_ctx = max(0, start_char - context_window)
            end_ctx = min(len(text), end_char + context_window)
            context = text[start_ctx:end_ctx].strip()

            mention = MentionData(
                text=ent_text,
                context=context,
                start_position=start_char,
                end_position=end_char,
                document_id=document_id,
                confidence=0.9 if self._has_patterns else 0.5,
            )
            name_to_mentions.setdefault(ent_text, []).append(mention)

        entities: List[Entity] = []
        for name, mentions in name_to_mentions.items():
            ent_type = self._map_spacy_label_to_entity_type(mentions[0], doc)
            entity = Entity(
                name=name,
                entity_type=ent_type,
                source_document_id=document_id,
                mentions=mentions,
                confidence=max(m.confidence for m in mentions),
            )
            entities.append(entity)

        return entities

    def _map_spacy_label_to_entity_type(self, mention: MentionData, doc) -> EntityType:
        # Try to get label from span by matching characters
        for ent in doc.ents:
            if ent.start_char == mention.start_position and ent.end_char == mention.end_position:
                label = ent.label_.upper()
                break
        else:
            label = ""

        if label == "PERSON":
            return EntityType.PERSON
        if label in {"ORG"}:
            return EntityType.CONCEPT  # map ORG as generic concept for now
        if label in {"GPE", "LOC"}:
            return EntityType.PLACE
        if label in {"WORK_OF_ART"}:
            return EntityType.WORK
        return EntityType.CONCEPT


class RelationshipExtractor:
    """Simple rule-based relationship extractor for SVO patterns.

    This lightweight extractor is deterministic for tests and provides a
    placeholder until LLM-based extraction is integrated.
    """

    def __init__(self):
        # Common relation verbs in philosophical texts
        self._verbs = [
            "refutes", "criticizes", "influences", "cites", "agrees with", "disagrees with",
        ]

    def extract_relationships(self, text: str) -> List[Dict[str, Any]]:
        if not text or not text.strip():
            return []
        patterns = []
        # Build regex patterns for single-word verbs and two-word like "agrees with"
        for v in self._verbs:
            if " " in v:
                patterns.append(rf"\b([A-Z][a-z]+)\s+{re.escape(v)}\s+([A-Z][a-z]+)\b")
            else:
                patterns.append(rf"\b([A-Z][a-z]+)\s+{re.escape(v)}\s+([A-Z][a-z]+)\b")

        triples: List[Dict[str, Any]] = []
        for pat in patterns:
            for m in re.finditer(pat, text):
                subject = m.group(1)
                relation = re.search(r"\b([a-z]+(?:\s+[a-z]+)?)\b", m.group(0))
                object_ = m.group(2)
                if subject and object_:
                    triples.append({
                        "subject": subject,
                        "relation": relation.group(1) if relation else "relates to",
                        "object": object_,
                        "confidence": 0.7,
                    })
        return triples


class TripleValidator:
    """Validate and deduplicate extracted triples.

    - Ensures non-empty subject/relation/object
    - Enforces minimum confidence threshold
    - Deduplicates by (subject, relation, object) keeping highest confidence
    """

    def validate(self, triples: List[Dict[str, Any]], min_confidence: float = 0.6) -> List[Dict[str, Any]]:
        if not triples:
            return []
        best: Dict[tuple, Dict[str, Any]] = {}
        for t in triples:
            subject = str(t.get("subject", "")).strip()
            relation = str(t.get("relation", "")).strip()
            object_ = str(t.get("object", "")).strip()
            conf = float(t.get("confidence", 0.0))
            if not subject or not relation or not object_:
                continue
            if conf < min_confidence:
                continue
            key = (subject, relation, object_)
            existing = best.get(key)
            if existing is None or conf > float(existing.get("confidence", 0.0)):
                best[key] = {"subject": subject, "relation": relation, "object": object_, "confidence": conf}
        return list(best.values())