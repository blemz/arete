"""Test suite for Citation model following TDD principles.

The Citation model supports philosophical text analysis with comprehensive
source attribution, confidence scoring, and relationship tracking.
"""

import uuid
from typing import Dict, List, Optional
from uuid import UUID

import pytest
from pydantic import ValidationError

from src.arete.models.base import ProcessingStatus


class CitationType:
    """Citation types for philosophical texts - to be defined in implementation."""
    DIRECT_QUOTE = "direct_quote"
    PARAPHRASE = "paraphrase"
    REFERENCE = "reference"
    ALLUSION = "allusion"


class CitationContext:
    """Context information for citations - to be defined in implementation."""
    ARGUMENT = "argument"
    COUNTERARGUMENT = "counterargument"
    EXAMPLE = "example"
    DEFINITION = "definition"
    EXPLANATION = "explanation"


class TestCitationType:
    """Test CitationType enum functionality."""

    def test_citation_type_values(self):
        """Test that CitationType has expected values."""
        assert CitationType.DIRECT_QUOTE == "direct_quote"
        assert CitationType.PARAPHRASE == "paraphrase"
        assert CitationType.REFERENCE == "reference"
        assert CitationType.ALLUSION == "allusion"

    def test_citation_type_philosophical_coverage(self):
        """Test citation types cover philosophical citation patterns."""
        types = [
            CitationType.DIRECT_QUOTE,
            CitationType.PARAPHRASE,
            CitationType.REFERENCE,
            CitationType.ALLUSION
        ]
        assert len(types) == 4
        assert all(isinstance(t, str) for t in types)


class TestCitationContext:
    """Test CitationContext enum functionality."""

    def test_citation_context_values(self):
        """Test that CitationContext has expected values."""
        assert CitationContext.ARGUMENT == "argument"
        assert CitationContext.COUNTERARGUMENT == "counterargument"
        assert CitationContext.EXAMPLE == "example"
        assert CitationContext.DEFINITION == "definition"
        assert CitationContext.EXPLANATION == "explanation"

    def test_citation_context_philosophical_coverage(self):
        """Test context types cover philosophical reasoning patterns."""
        contexts = [
            CitationContext.ARGUMENT,
            CitationContext.COUNTERARGUMENT,
            CitationContext.EXAMPLE,
            CitationContext.DEFINITION,
            CitationContext.EXPLANATION
        ]
        assert len(contexts) == 5
        assert all(isinstance(c, str) for c in contexts)


class TestCitation:
    """Test Citation model functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.document_id = uuid.uuid4()
        self.chunk_id = uuid.uuid4()
        self.citation_id = uuid.uuid4()
        
        self.sample_citation_data = {
            "id": self.citation_id,
            "text": "Justice is the excellence of the soul and governs the harmony of all virtues.",
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "source_title": "Republic",
            "source_author": "Plato",
            "source_reference": "347e",
            "citation_type": CitationType.DIRECT_QUOTE,
            "start_char": 145,
            "end_char": 220,
            "confidence": 0.95
        }

    def test_citation_creation_minimal(self):
        """Test creating citation with minimal required fields."""
        from src.arete.models.citation import Citation
        
        minimal_data = {
            "text": "Virtue is knowledge.",
            "document_id": self.document_id,
            "source_title": "Meno",
            "source_author": "Plato"
        }
        
        citation = Citation(**minimal_data)
        
        assert citation.text == "Virtue is knowledge."
        assert citation.document_id == self.document_id
        assert citation.source_title == "Meno"
        assert citation.source_author == "Plato"
        assert citation.citation_type == CitationType.REFERENCE  # Default
        assert citation.confidence == 0.8  # Default confidence
        assert citation.processing_status == ProcessingStatus.PENDING
        assert citation.metadata == {}

    def test_citation_creation_full(self):
        """Test creating citation with all fields."""
        from src.arete.models.citation import Citation
        
        full_data = {
            **self.sample_citation_data,
            "chunk_id": self.chunk_id,
            "source_reference": "347e",
            "source_edition": "Loeb Classical Library",
            "source_translator": "Paul Shorey",
            "context": CitationContext.ARGUMENT,
            "confidence": 0.95,
            "processing_status": ProcessingStatus.COMPLETED,
            "metadata": {
                "bekker_number": "347e",
                "manuscript_source": "Parisinus_gr_1807",
                "verified_by": "human_annotator"
            }
        }
        
        citation = Citation(**full_data)
        
        assert citation.id == self.citation_id
        assert citation.text == self.sample_citation_data["text"]
        assert citation.document_id == self.document_id
        assert citation.chunk_id == self.chunk_id
        assert citation.source_title == "Republic"
        assert citation.source_author == "Plato"
        assert citation.source_reference == "347e"
        assert citation.source_edition == "Loeb Classical Library"
        assert citation.source_translator == "Paul Shorey"
        assert citation.citation_type == CitationType.DIRECT_QUOTE
        assert citation.context == CitationContext.ARGUMENT
        assert citation.start_char == 145
        assert citation.end_char == 220
        assert citation.confidence == 0.95
        assert citation.processing_status == ProcessingStatus.COMPLETED
        assert citation.metadata["bekker_number"] == "347e"

    def test_citation_text_validation(self):
        """Test citation text field validation."""
        base_data = {
            "document_id": self.document_id,
            "source_title": "Republic",
            "source_author": "Plato"
        }
        
        from src.arete.models.citation import Citation
        
        # Test missing text
        with pytest.raises(ValidationError, match="Field required"):
            Citation(**base_data)
            
        # Test empty text
        with pytest.raises(ValidationError, match="at least 1 character"):
            Citation(text="", **base_data)
            
        # Test whitespace-only text
        with pytest.raises(ValidationError, match="at least 1 character"):
            Citation(text="   ", **base_data)
            
        # Test text normalization
        citation = Citation(text="  Virtue is knowledge.  ", **base_data)
        assert citation.text == "Virtue is knowledge."

    def test_citation_source_validation(self):
        """Test source field validation."""
        base_data = {
            "text": "Virtue is knowledge.",
            "document_id": self.document_id
        }
        
        from src.arete.models.citation import Citation
        
        # Test missing source_title
        with pytest.raises(ValidationError, match="Field required"):
            Citation(source_author="Plato", **base_data)
            
        # Test missing source_author
        with pytest.raises(ValidationError, match="Field required"):
            Citation(source_title="Meno", **base_data)
            
        # Test empty source fields
        with pytest.raises(ValidationError, match="at least 1 character"):
            Citation(source_title="", source_author="Plato", **base_data)
            
        with pytest.raises(ValidationError, match="at least 1 character"):
            Citation(source_title="Meno", source_author="", **base_data)
            
        # Test source field normalization
        citation = Citation(
            source_title="  Republic  ",
            source_author="  Plato  ",
            **base_data
        )
        assert citation.source_title == "Republic"
        assert citation.source_author == "Plato"

    def test_citation_character_position_validation(self):
        """Test character position validation."""
        base_data = {
            "text": "Virtue is knowledge.",
            "document_id": self.document_id,
            "source_title": "Meno",
            "source_author": "Plato"
        }
        
        from src.arete.models.citation import Citation
        
        # Test negative start_char
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            Citation(start_char=-1, **base_data)
            
        # Test negative end_char
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            Citation(end_char=-1, **base_data)
            
        # Test end_char <= start_char
        with pytest.raises(ValidationError, match="end_char must be greater than start_char"):
            Citation(start_char=50, end_char=50, **base_data)
            
        with pytest.raises(ValidationError, match="end_char must be greater than start_char"):
            Citation(start_char=50, end_char=40, **base_data)
            
        # Test valid positions
        citation = Citation(start_char=0, end_char=19, **base_data)
        assert citation.start_char == 0
        assert citation.end_char == 19

    def test_citation_confidence_validation(self):
        """Test confidence score validation."""
        base_data = {
            "text": "Virtue is knowledge.",
            "document_id": self.document_id,
            "source_title": "Meno",
            "source_author": "Plato"
        }
        
        from src.arete.models.citation import Citation
        
        # Test confidence out of range
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            Citation(confidence=-0.1, **base_data)
            
        with pytest.raises(ValidationError, match="less than or equal to 1"):
            Citation(confidence=1.1, **base_data)
            
        # Test boundary values
        citation_min = Citation(confidence=0.0, **base_data)
        assert citation_min.confidence == 0.0
        
        citation_max = Citation(confidence=1.0, **base_data)
        assert citation_max.confidence == 1.0
        
        # Test default confidence
        citation_default = Citation(**base_data)
        assert citation_default.confidence == 0.8

    def test_citation_computed_properties(self):
        """Test computed properties."""
        from src.arete.models.citation import Citation
        
        citation = Citation(
            text="Virtue is knowledge, and no one does wrong willingly.",
            document_id=self.document_id,
            source_title="Protagoras",
            source_author="Plato",
            start_char=100,
            end_char=151
        )
        
        # Test computed_word_count
        expected_words = len(citation.text.split())
        assert citation.computed_word_count == expected_words
        
        # Test character_count
        assert citation.character_count == len(citation.text)
        
        # Test character_span
        assert citation.character_span == 51  # 151 - 100

    def test_citation_get_full_reference(self):
        """Test full reference generation."""
        from src.arete.models.citation import Citation
        
        citation = Citation(
            text="The unexamined life is not worth living.",
            document_id=self.document_id,
            source_title="Apology",
            source_author="Plato",
            source_reference="38a"
        )
        
        full_reference = citation.get_full_reference()
        assert "Plato" in full_reference
        assert "Apology" in full_reference
        assert "38a" in full_reference

    def test_citation_get_context_snippet(self):
        """Test context snippet extraction."""
        from src.arete.models.citation import Citation
        
        citation = Citation(
            text="Justice is the excellence of the soul.",
            document_id=self.document_id,
            source_title="Republic",
            source_author="Plato",
            start_char=10,
            end_char=48
        )
        
        # Mock document content for context
        document_content = "In this passage, Justice is the excellence of the soul and governs all virtues."
        
        context_snippet = citation.get_context_snippet(document_content, context_chars=20)
        assert "In this passage," in context_snippet
        assert citation.text in context_snippet

    def test_citation_relationship_tracking(self):
        """Test citation relationship functionality."""
        from src.arete.models.citation import Citation
        
        citation = Citation(
            text="Virtue is knowledge.",
            document_id=self.document_id,
            source_title="Meno",
            source_author="Plato"
        )
        
        related_citation_id = uuid.uuid4()
        citation.add_relationship(related_citation_id, "supports")
        
        assert len(citation.relationships) == 1
        assert citation.relationships[0]["citation_id"] == related_citation_id
        assert citation.relationships[0]["relationship_type"] == "supports"
        
        # Test relationship types
        citation.add_relationship(uuid.uuid4(), "contradicts")
        citation.add_relationship(uuid.uuid4(), "elaborates")
        
        assert len(citation.relationships) == 3
        relationship_types = [rel["relationship_type"] for rel in citation.relationships]
        assert "supports" in relationship_types
        assert "contradicts" in relationship_types
        assert "elaborates" in relationship_types

    def test_citation_philosophical_context(self):
        """Test philosophical context handling."""
        from src.arete.models.citation import Citation
        
        # Test argument context
        argument_citation = Citation(
            text="Therefore, virtue must be teachable.",
            document_id=self.document_id,
            source_title="Meno",
            source_author="Plato",
            context=CitationContext.ARGUMENT
        )
        assert argument_citation.context == CitationContext.ARGUMENT
        
        # Test counterargument context
        counter_citation = Citation(
            text="But if virtue were teachable, why don't virtuous parents have virtuous children?",
            document_id=self.document_id,
            source_title="Meno",
            source_author="Plato",
            context=CitationContext.COUNTERARGUMENT
        )
        assert counter_citation.context == CitationContext.COUNTERARGUMENT

    def test_citation_get_vectorizable_text(self):
        """Test vectorizable text generation."""
        from src.arete.models.citation import Citation
        
        citation = Citation(
            text="The Good is beyond being.",
            document_id=self.document_id,
            source_title="Republic",
            source_author="Plato",
            source_reference="509b",
            context=CitationContext.DEFINITION,
            metadata={"concept": "the_good", "topic": "metaphysics"}
        )
        
        vectorizable = citation.get_vectorizable_text()
        
        # Should include text and source information
        assert citation.text in vectorizable
        assert "Plato" in vectorizable
        assert "Republic" in vectorizable
        
        # Should include relevant metadata
        assert "the_good" in vectorizable
        assert "metaphysics" in vectorizable

    def test_citation_to_neo4j_dict(self):
        """Test Neo4j dictionary conversion."""
        from src.arete.models.citation import Citation
        
        citation = Citation(**self.sample_citation_data)
        neo4j_dict = citation.to_neo4j_dict()
        
        # Check core fields
        assert neo4j_dict["text"] == citation.text
        assert neo4j_dict["document_id"] == str(self.document_id)
        assert neo4j_dict["source_title"] == "Republic"
        assert neo4j_dict["source_author"] == "Plato"
        assert neo4j_dict["source_reference"] == "347e"
        assert neo4j_dict["citation_type"] == CitationType.DIRECT_QUOTE
        assert neo4j_dict["start_char"] == 145
        assert neo4j_dict["end_char"] == 220
        assert neo4j_dict["confidence"] == 0.95
        
        # Check computed fields
        assert neo4j_dict["computed_word_count"] == citation.computed_word_count
        assert neo4j_dict["character_count"] == citation.character_count
        assert neo4j_dict["character_span"] == citation.character_span

    def test_citation_to_weaviate_dict(self):
        """Test Weaviate dictionary conversion."""
        from src.arete.models.citation import Citation
        
        citation = Citation(**self.sample_citation_data)
        weaviate_dict = citation.to_weaviate_dict()
        
        # Check core fields
        assert weaviate_dict["text"] == citation.text
        assert weaviate_dict["source_title"] == "Republic"
        assert weaviate_dict["source_author"] == "Plato"
        assert weaviate_dict["citation_type"] == CitationType.DIRECT_QUOTE
        assert weaviate_dict["confidence"] == 0.95
        
        # Check vectorizable text
        assert "vectorizable_text" in weaviate_dict
        assert citation.text in weaviate_dict["vectorizable_text"]
        
        # Check computed fields
        assert weaviate_dict["computed_word_count"] == citation.computed_word_count
        assert weaviate_dict["character_count"] == citation.character_count

    def test_citation_string_representation(self):
        """Test string representation."""
        from src.arete.models.citation import Citation
        
        citation = Citation(**self.sample_citation_data)
        str_repr = str(citation)
        
        assert str(citation.id) in str_repr
        assert "Republic" in str_repr
        assert "Plato" in str_repr

    def test_citation_classical_references(self):
        """Test handling of classical reference formats."""
        from src.arete.models.citation import Citation
        
        # Test Stephanus numbers (Plato)
        plato_citation = Citation(
            text="The cave allegory demonstrates the philosopher's journey.",
            document_id=self.document_id,
            source_title="Republic",
            source_author="Plato",
            source_reference="514a-517a"
        )
        assert plato_citation.source_reference == "514a-517a"
        
        # Test Bekker numbers (Aristotle)
        aristotle_citation = Citation(
            text="Happiness is activity of soul in accordance with virtue.",
            document_id=self.document_id,
            source_title="Nicomachean Ethics",
            source_author="Aristotle",
            source_reference="1098a16-18"
        )
        assert aristotle_citation.source_reference == "1098a16-18"
        
        # Test DK numbers (Presocratics)
        presocratic_citation = Citation(
            text="You cannot step twice into the same river.",
            document_id=self.document_id,
            source_title="Fragments",
            source_author="Heraclitus",
            source_reference="DK 22 B30"
        )
        assert presocratic_citation.source_reference == "DK 22 B30"

    def test_citation_confidence_levels(self):
        """Test different confidence levels and their meanings."""
        from src.arete.models.citation import Citation
        
        base_data = {
            "text": "Virtue is knowledge.",
            "document_id": self.document_id,
            "source_title": "Meno",
            "source_author": "Plato"
        }
        
        # High confidence - direct quote with reference
        high_conf = Citation(
            **base_data,
            citation_type=CitationType.DIRECT_QUOTE,
            confidence=0.95,
            source_reference="87c"
        )
        assert high_conf.confidence >= 0.9
        
        # Medium confidence - paraphrase
        medium_conf = Citation(
            **base_data,
            citation_type=CitationType.PARAPHRASE,
            confidence=0.7
        )
        assert 0.6 <= medium_conf.confidence < 0.9
        
        # Low confidence - allusion
        low_conf = Citation(
            **base_data,
            citation_type=CitationType.ALLUSION,
            confidence=0.4
        )
        assert low_conf.confidence < 0.6

    def test_citation_metadata_handling(self):
        """Test citation metadata for scholarly attributes."""
        from src.arete.models.citation import Citation
        
        scholarly_metadata = {
            "manuscript_source": "Parisinus_gr_1807",
            "critical_apparatus": "OCT",
            "textual_variants": ["variant_1", "variant_2"],
            "scholarly_notes": "Text disputed by modern scholars",
            "digital_edition": "Perseus_4.0",
            "verification_status": "verified"
        }
        
        citation = Citation(
            text="Knowledge is recollection.",
            document_id=self.document_id,
            source_title="Phaedo",
            source_author="Plato",
            metadata=scholarly_metadata
        )
        
        assert citation.metadata["manuscript_source"] == "Parisinus_gr_1807"
        assert citation.metadata["critical_apparatus"] == "OCT"
        assert citation.metadata["textual_variants"] == ["variant_1", "variant_2"]
        assert citation.metadata["verification_status"] == "verified"

    def test_citation_extraction_patterns(self):
        """Test citation extraction from various philosophical text patterns."""
        from src.arete.models.citation import Citation
        
        # Test inline citation pattern
        inline_citation = Citation(
            text="As Socrates says in the Apology",
            document_id=self.document_id,
            source_title="Apology",
            source_author="Socrates",
            citation_type=CitationType.REFERENCE
        )
        assert inline_citation.citation_type == CitationType.REFERENCE
        
        # Test quotation pattern
        quote_citation = Citation(
            text='"The unexamined life is not worth living."',
            document_id=self.document_id,
            source_title="Apology",
            source_author="Socrates",
            citation_type=CitationType.DIRECT_QUOTE,
            source_reference="38a"
        )
        assert quote_citation.citation_type == CitationType.DIRECT_QUOTE
        assert '"' in quote_citation.text

    def test_citation_validation_edge_cases(self):
        """Test citation validation edge cases."""
        from src.arete.models.citation import Citation
        
        base_data = {
            "text": "Virtue is knowledge.",
            "document_id": self.document_id,
            "source_title": "Meno",
            "source_author": "Plato"
        }
        
        # Test very long text (should be allowed for philosophical passages)
        long_text = "This is a very long philosophical passage that discusses " * 20
        long_citation = Citation(
            text=long_text,
            document_id=self.document_id,
            source_title="Republic",
            source_author="Plato"
        )
        assert len(long_citation.text) > 100
        
        # Test special characters in references
        special_ref_citation = Citation(
            **base_data,
            source_reference="Fr. 22 B85 (DK)"
        )
        assert special_ref_citation.source_reference == "Fr. 22 B85 (DK)"


# Test fixtures for reusable test data
@pytest.fixture
def sample_citation_data() -> Dict:
    """Sample citation data for testing."""
    return {
        "text": "Justice is the excellence of the soul and governs the harmony of all virtues.",
        "document_id": uuid.uuid4(),
        "chunk_id": uuid.uuid4(),
        "source_title": "Republic",
        "source_author": "Plato",
        "source_reference": "347e",
        "citation_type": CitationType.DIRECT_QUOTE,
        "start_char": 145,
        "end_char": 220,
        "confidence": 0.95
    }


@pytest.fixture
def minimal_citation_data() -> Dict:
    """Minimal valid citation data for testing."""
    return {
        "text": "Virtue is knowledge.",
        "document_id": uuid.uuid4(),
        "source_title": "Meno",
        "source_author": "Plato"
    }


@pytest.fixture
def philosophical_citation_data() -> Dict:
    """Complex philosophical citation with full metadata."""
    return {
        "text": "The Good is beyond being, exceeding it in dignity and power.",
        "document_id": uuid.uuid4(),
        "source_title": "Republic",
        "source_author": "Plato",
        "source_reference": "509b6-10",
        "source_edition": "Oxford Classical Text",
        "source_translator": "Paul Shorey",
        "citation_type": CitationType.DIRECT_QUOTE,
        "context": CitationContext.DEFINITION,
        "confidence": 0.98,
        "start_char": 250,
        "end_char": 315,
        "metadata": {
            "manuscript_source": "Parisinus_gr_1807",
            "concept": "the_good",
            "topic": "metaphysics",
            "philosophical_significance": "fundamental_principle"
        }
    }


class TestCitationIntegration:
    """Integration tests for Citation model with database serialization."""

    def test_full_citation_lifecycle(self, sample_citation_data):
        """Test complete citation lifecycle from creation to serialization."""
        from src.arete.models.citation import Citation
        
        # 1. Create citation
        citation = Citation(**sample_citation_data)
        
        # 2. Verify initial state
        assert citation.processing_status == ProcessingStatus.PENDING
        assert citation.confidence == 0.95
        
        # 3. Process citation (simulate processing)
        citation.processing_status = ProcessingStatus.PROCESSING
        vectorizable_text = citation.get_vectorizable_text()
        full_reference = citation.get_full_reference()
        
        # 4. Update processing status
        citation.processing_status = ProcessingStatus.COMPLETED
        
        # 5. Test serialization for both databases
        neo4j_data = citation.to_neo4j_dict()
        weaviate_data = citation.to_weaviate_dict()
        
        # Verify both serializations are valid
        assert neo4j_data["processing_status"] == "completed"
        assert weaviate_data["confidence"] == citation.confidence
        assert weaviate_data["neo4j_id"] == str(citation.id)
        assert "vectorizable_text" in weaviate_data

    def test_citation_relationship_network(self):
        """Test citation relationship network functionality."""
        from src.arete.models.citation import Citation
        
        # Create multiple related citations
        virtue_citation = Citation(
            text="Virtue is knowledge.",
            document_id=uuid.uuid4(),
            source_title="Meno",
            source_author="Plato"
        )
        
        teaching_citation = Citation(
            text="If virtue is knowledge, then virtue can be taught.",
            document_id=uuid.uuid4(),
            source_title="Meno", 
            source_author="Plato"
        )
        
        paradox_citation = Citation(
            text="But virtuous parents don't always have virtuous children.",
            document_id=uuid.uuid4(),
            source_title="Meno",
            source_author="Plato"
        )
        
        # Create relationships
        virtue_citation.add_relationship(teaching_citation.id, "supports")
        teaching_citation.add_relationship(paradox_citation.id, "contradicted_by")
        
        # Verify relationship network
        assert len(virtue_citation.relationships) == 1
        assert len(teaching_citation.relationships) == 1
        assert virtue_citation.relationships[0]["relationship_type"] == "supports"
        assert teaching_citation.relationships[0]["relationship_type"] == "contradicted_by"