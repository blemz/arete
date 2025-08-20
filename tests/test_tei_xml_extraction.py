"""Test suite for TEI-XML text extraction."""

import tempfile
from pathlib import Path
from typing import Dict
from xml.etree import ElementTree as ET

import pytest

from src.arete.processing.extractors import TEIXMLExtractor


class TestTEIXMLExtractor:
    """Test TEI-XML text extraction functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = TEIXMLExtractor()

    def test_extractor_initialization(self):
        """Test TEIXMLExtractor initialization with default options."""
        extractor = TEIXMLExtractor()
        assert extractor is not None
        assert extractor.preserve_structure is True

    def test_extractor_with_options(self):
        """Test TEIXMLExtractor with custom options."""
        extractor = TEIXMLExtractor(preserve_structure=False)
        assert extractor.preserve_structure is False

    def test_extract_from_file_validation(self):
        """Test file path validation for TEI-XML files."""
        # Test non-existent file
        with pytest.raises(FileNotFoundError):
            self.extractor.extract_from_file("/nonexistent/file.xml")
            
        # Test non-XML file
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp.write(b"Not an XML file")
            tmp.flush()
            
            with pytest.raises(ValueError, match="File must have .xml or .tei extension"):
                self.extractor.extract_from_file(tmp.name)

    def test_extract_from_string_validation(self):
        """Test string content validation for TEI-XML."""
        # Test empty string
        with pytest.raises(ValueError, match="XML content cannot be empty"):
            self.extractor.extract_from_string("")
            
        # Test string without TEI elements
        invalid_xml = "<root><p>This is not TEI-XML</p></root>"
        with pytest.raises(ValueError, match="Invalid TEI-XML: missing TEI root element"):
            self.extractor.extract_from_string(invalid_xml)

    def test_extract_minimal_tei_document(self):
        """Test extraction from minimal valid TEI document."""
        minimal_tei = """<?xml version="1.0" encoding="UTF-8"?>
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <teiHeader>
                <fileDesc>
                    <titleStmt>
                        <title>Test Document</title>
                        <author>Test Author</author>
                    </titleStmt>
                </fileDesc>
            </teiHeader>
            <text>
                <body>
                    <p>This is a test paragraph.</p>
                </body>
            </text>
        </TEI>"""
        
        result = self.extractor.extract_from_string(minimal_tei)
        
        assert "text" in result
        assert "metadata" in result
        assert len(result["text"]) > 0

    def test_extract_plato_republic_sample(self):
        """Test extraction from Plato's Republic sample TEI."""
        plato_tei = """<?xml version="1.0" encoding="UTF-8"?>
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <teiHeader>
                <fileDesc>
                    <titleStmt>
                        <title>Republic</title>
                        <author>Plato</author>
                        <editor>Benjamin Jowett</editor>
                    </titleStmt>
                    <publicationStmt>
                        <date>380 BCE</date>
                    </publicationStmt>
                </fileDesc>
            </teiHeader>
            <text>
                <body>
                    <div type="book" n="1">
                        <head>Book I</head>
                        <p>I went down yesterday to the Piraeus with Glaucon the son of Ariston, 
                        that I might offer up my prayers to the goddess.</p>
                        <sp who="#SOCRATES">
                            <p>What is justice? This is the question we must answer.</p>
                        </sp>
                    </div>
                </body>
            </text>
        </TEI>"""
        
        result = self.extractor.extract_from_string(plato_tei)
        
        assert result["metadata"]["title"] == "Republic"
        assert result["metadata"]["author"] == "Plato" 
        assert "Piraeus" in result["text"]
        assert "justice" in result["text"]

    def test_extract_aristotle_ethics_sample(self):
        """Test extraction from Aristotle's Ethics sample TEI."""
        aristotle_tei = """<?xml version="1.0" encoding="UTF-8"?>
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <teiHeader>
                <fileDesc>
                    <titleStmt>
                        <title>Nicomachean Ethics</title>
                        <author>Aristotle</author>
                    </titleStmt>
                </fileDesc>
            </teiHeader>
            <text>
                <body>
                    <div type="book" n="1">
                        <div type="chapter" n="1">
                            <head>Chapter 1</head>
                            <p>Every art and every inquiry, and similarly every action and pursuit, 
                            is thought to aim at some good; and for this reason the good has rightly 
                            been declared to be that at which all things aim.</p>
                        </div>
                    </div>
                </body>
            </text>
        </TEI>"""
        
        result = self.extractor.extract_from_string(aristotle_tei)
        
        assert result["metadata"]["title"] == "Nicomachean Ethics"
        assert result["metadata"]["author"] == "Aristotle"
        assert "Every art and every inquiry" in result["text"]

    def test_extract_with_greek_text(self):
        """Test extraction from TEI with Greek text."""
        greek_tei = """<?xml version="1.0" encoding="UTF-8"?>
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <teiHeader>
                <fileDesc>
                    <titleStmt>
                        <title>Πολιτεία</title>
                        <author>Πλάτων</author>
                    </titleStmt>
                </fileDesc>
            </teiHeader>
            <text>
                <body>
                    <p>τί ἐστι δικαιοσύνη;</p>
                    <p lang="en">What is justice?</p>
                </body>
            </text>
        </TEI>"""
        
        result = self.extractor.extract_from_string(greek_tei)
        
        assert result["metadata"]["title"] == "Πολιτεία"
        assert result["metadata"]["author"] == "Πλάτων"
        assert "δικαιοσύνη" in result["text"]

    def test_extract_structure_preservation(self):
        """Test preservation of document structure."""
        structured_tei = """<?xml version="1.0" encoding="UTF-8"?>
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <teiHeader>
                <fileDesc>
                    <titleStmt>
                        <title>Structured Document</title>
                    </titleStmt>
                </fileDesc>
            </teiHeader>
            <text>
                <body>
                    <div type="book" n="1">
                        <head>Book One</head>
                        <div type="chapter" n="1">
                            <head>Chapter One</head>
                            <p>First paragraph.</p>
                        </div>
                        <div type="chapter" n="2">
                            <head>Chapter Two</head>
                            <p>Second paragraph.</p>
                        </div>
                    </div>
                </body>
            </text>
        </TEI>"""
        
        result = self.extractor.extract_from_string(structured_tei)
        
        assert "structure" in result
        structure = result["structure"]
        assert "books" in structure
        assert "chapters" in structure

    def test_extract_speaker_dialogue(self):
        """Test extraction of speaker dialogue from philosophical texts."""
        dialogue_tei = """<?xml version="1.0" encoding="UTF-8"?>
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <teiHeader>
                <fileDesc>
                    <titleStmt>
                        <title>Dialogue Sample</title>
                        <author>Plato</author>
                    </titleStmt>
                </fileDesc>
            </teiHeader>
            <text>
                <body>
                    <sp who="#SOCRATES">
                        <speaker>Socrates</speaker>
                        <p>Tell me, what is virtue?</p>
                    </sp>
                    <sp who="#MENO">
                        <speaker>Meno</speaker>
                        <p>It is not difficult to tell you, Socrates.</p>
                    </sp>
                </body>
            </text>
        </TEI>"""
        
        result = self.extractor.extract_from_string(dialogue_tei)
        
        assert "Socrates" in result["text"]
        assert "Meno" in result["text"]
        assert "virtue" in result["text"]

    def test_extract_citations_and_references(self):
        """Test extraction of citations and references."""
        cited_tei = """<?xml version="1.0" encoding="UTF-8"?>
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <teiHeader>
                <fileDesc>
                    <titleStmt>
                        <title>Text with Citations</title>
                    </titleStmt>
                </fileDesc>
            </teiHeader>
            <text>
                <body>
                    <p>As Aristotle says in the <ref target="ethics.1094a1">Ethics</ref>, 
                    every action aims at some good.</p>
                    <p>Compare with <bibl><author>Plato</author>, 
                    <title>Republic</title> <biblScope>514a</biblScope></bibl>.</p>
                </body>
            </text>
        </TEI>"""
        
        result = self.extractor.extract_from_string(cited_tei)
        
        assert "citations" in result
        assert "Aristotle" in result["text"]
        assert "Ethics" in result["text"]

    def test_extract_perseus_format(self):
        """Test extraction from Perseus Digital Library format."""
        perseus_tei = """<?xml version="1.0" encoding="UTF-8"?>
        <TEI.2>
            <teiHeader>
                <fileDesc>
                    <titleStmt>
                        <title>Apology</title>
                        <author>Plato</author>
                    </titleStmt>
                </fileDesc>
            </teiHeader>
            <text>
                <body>
                    <div type="section" n="17a">
                        <milestone unit="page" n="17a"/>
                        <p>How you have felt, O men of Athens, at hearing the speeches of my accusers, 
                        I cannot tell.</p>
                    </div>
                </body>
            </text>
        </TEI.2>"""
        
        result = self.extractor.extract_from_string(perseus_tei)
        
        assert result["metadata"]["title"] == "Apology"
        assert "17a" in result["text"] or "men of Athens" in result["text"]

    def test_extract_metadata_comprehensive(self):
        """Test comprehensive metadata extraction."""
        full_metadata_tei = """<?xml version="1.0" encoding="UTF-8"?>
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <teiHeader>
                <fileDesc>
                    <titleStmt>
                        <title>Complete Title</title>
                        <author>Ancient Author</author>
                        <editor>Modern Editor</editor>
                        <translator>Translator Name</translator>
                    </titleStmt>
                    <publicationStmt>
                        <publisher>University Press</publisher>
                        <date>2024</date>
                    </publicationStmt>
                    <sourceDesc>
                        <p>Original work from 4th century BCE</p>
                    </sourceDesc>
                </fileDesc>
                <profileDesc>
                    <langUsage>
                        <language ident="en">English</language>
                        <language ident="grc">Ancient Greek</language>
                    </langUsage>
                </profileDesc>
            </teiHeader>
            <text>
                <body>
                    <p>Sample text.</p>
                </body>
            </text>
        </TEI>"""
        
        result = self.extractor.extract_from_string(full_metadata_tei)
        
        metadata = result["metadata"]
        assert metadata["title"] == "Complete Title"
        assert metadata["author"] == "Ancient Author"
        assert "editor" in metadata
        assert "translator" in metadata
        assert "language" in metadata

    def test_extract_result_structure(self):
        """Test the structure of extraction results."""
        sample_tei = """<?xml version="1.0" encoding="UTF-8"?>
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <teiHeader>
                <fileDesc>
                    <titleStmt>
                        <title>Test</title>
                    </titleStmt>
                </fileDesc>
            </teiHeader>
            <text>
                <body>
                    <p>Test content.</p>
                </body>
            </text>
        </TEI>"""
        
        result = self.extractor.extract_from_string(sample_tei)
        
        # Test expected result structure
        expected_keys = {"text", "metadata", "structure", "citations"}
        assert all(key in result for key in expected_keys)
        assert isinstance(result["metadata"], dict)
        assert isinstance(result["structure"], dict)
        assert isinstance(result["citations"], list)

    def test_extract_from_file_integration(self):
        """Test extracting from actual TEI-XML file."""
        tei_content = """<?xml version="1.0" encoding="UTF-8"?>
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <teiHeader>
                <fileDesc>
                    <titleStmt>
                        <title>File Test</title>
                        <author>Test Author</author>
                    </titleStmt>
                </fileDesc>
            </teiHeader>
            <text>
                <body>
                    <p>Content from file.</p>
                </body>
            </text>
        </TEI>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as tmp:
            tmp.write(tei_content)
            tmp.flush()
            
            result = self.extractor.extract_from_file(tmp.name)
            
            assert result["metadata"]["title"] == "File Test"
            assert "Content from file" in result["text"]

    def test_extract_with_preserve_structure_false(self):
        """Test extraction without structure preservation."""
        extractor = TEIXMLExtractor(preserve_structure=False)
        
        structured_tei = """<?xml version="1.0" encoding="UTF-8"?>
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <teiHeader>
                <fileDesc>
                    <titleStmt>
                        <title>No Structure</title>
                    </titleStmt>
                </fileDesc>
            </teiHeader>
            <text>
                <body>
                    <div type="book">
                        <p>Just the text content.</p>
                    </div>
                </body>
            </text>
        </TEI>"""
        
        result = extractor.extract_from_string(structured_tei)
        
        assert "text" in result
        assert "Just the text content" in result["text"]

    def test_error_handling_malformed_xml(self):
        """Test handling of malformed XML."""
        malformed_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <teiHeader>
                <fileDesc>
                    <titleStmt>
                        <title>Malformed</title>
                    </titleStmt>
                </fileDesc>
            </teiHeader>
            <text>
                <body>
                    <p>Unclosed paragraph
                </body>
            </text>
        </TEI>"""
        
        # Should handle malformed XML gracefully
        # This test verifies that the parser can handle common XML issues
        with pytest.raises((ET.ParseError, ValueError)):
            self.extractor.extract_from_string(malformed_xml)

    def test_extract_philosophical_terminology(self):
        """Test preservation of philosophical terminology."""
        philosophical_tei = """<?xml version="1.0" encoding="UTF-8"?>
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <teiHeader>
                <fileDesc>
                    <titleStmt>
                        <title>Philosophical Terms</title>
                    </titleStmt>
                </fileDesc>
            </teiHeader>
            <text>
                <body>
                    <p>The concept of <term>eudaimonia</term> is central to <name>Aristotle</name>'s 
                    ethical theory. It represents the highest <term>good</term> or flourishing.</p>
                    <p>Similarly, <term>arete</term> (virtue) is the excellence of character 
                    that enables eudaimonia.</p>
                </body>
            </text>
        </TEI>"""
        
        result = self.extractor.extract_from_string(philosophical_tei)
        
        philosophical_terms = ["eudaimonia", "Aristotle", "arete", "virtue"]
        for term in philosophical_terms:
            assert term in result["text"]

    def test_extract_multiple_languages(self):
        """Test extraction from multilingual TEI documents."""
        multilingual_tei = """<?xml version="1.0" encoding="UTF-8"?>
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <teiHeader>
                <fileDesc>
                    <titleStmt>
                        <title>Multilingual Text</title>
                    </titleStmt>
                </fileDesc>
            </teiHeader>
            <text>
                <body>
                    <p xml:lang="grc">ἀρετή</p>
                    <p xml:lang="en">virtue</p>
                    <p xml:lang="la">virtus</p>
                </body>
            </text>
        </TEI>"""
        
        result = self.extractor.extract_from_string(multilingual_tei)
        
        assert "ἀρετή" in result["text"]
        assert "virtue" in result["text"]
        assert "virtus" in result["text"]