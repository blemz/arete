#!/usr/bin/env python3
"""
Test relationship extraction on actual philosophical content after cleaning.
"""

import sys
import re
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arete.processing.extractors import PDFExtractor, RelationshipExtractor

def clean_pdf_text(text):
    """Clean up PDF text formatting issues."""
    # Fix excessive character spacing (very common in PDFs)
    # P U B L I S H E D -> PUBLISHED
    text = re.sub(r'\b([A-Z])\s+([A-Z])\s+([A-Z])\s+([A-Z])\s+([A-Z])\s+([A-Z])\s+([A-Z])\s+([A-Z])', r'\1\2\3\4\5\6\7\8', text)
    text = re.sub(r'\b([A-Z])\s+([A-Z])\s+([A-Z])\s+([A-Z])\s+([A-Z])\s+([A-Z])\s+([A-Z])', r'\1\2\3\4\5\6\7', text)
    text = re.sub(r'\b([A-Z])\s+([A-Z])\s+([A-Z])\s+([A-Z])\s+([A-Z])\s+([A-Z])', r'\1\2\3\4\5\6', text)
    text = re.sub(r'\b([A-Z])\s+([A-Z])\s+([A-Z])\s+([A-Z])\s+([A-Z])', r'\1\2\3\4\5', text)
    text = re.sub(r'\b([A-Z])\s+([A-Z])\s+([A-Z])\s+([A-Z])', r'\1\2\3\4', text)
    text = re.sub(r'\b([A-Z])\s+([A-Z])\s+([A-Z])', r'\1\2\3', text)
    text = re.sub(r'\b([A-Z])\s+([A-Z])\b', r'\1\2', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text.strip()

def find_philosophical_content(text):
    """Find actual philosophical content by looking for content markers."""
    
    # Look for actual philosophical content start markers
    content_markers = [
        "Every art and every inquiry",  # Nicomachean Ethics opening
        "happiness, then, is something",
        "virtue of character",
        "we must consider",
        "Now since happiness",
        "Book I",
        "Chapter 1"
    ]
    
    text_lower = text.lower()
    
    # Try to find content markers
    for marker in content_markers:
        marker_pos = text_lower.find(marker.lower())
        if marker_pos != -1:
            # Found marker, start from here
            content_start = marker_pos
            philosophical_content = text[content_start:content_start + 8000]
            print(f"Found philosophical content starting with: '{marker}'")
            return philosophical_content
    
    # Fallback: Skip first 25% and take substantial middle content
    skip_amount = len(text) // 4
    middle_content = text[skip_amount:skip_amount + 8000]
    print("Using middle portion of text as philosophical content")
    return middle_content

def test_philosophical_relationships():
    """Test relationship extraction on cleaned philosophical content."""
    
    print("Testing relationship extraction on philosophical content...")
    pdf_extractor = PDFExtractor()
    rel_extractor = RelationshipExtractor()
    
    try:
        # Extract from Aristotle's Ethics
        print("Extracting from Aristotle's Nicomachean Ethics...")
        extraction_result = pdf_extractor.extract_from_file("data/pdfs/Aristotle's Nicomachean Ethics.pdf")
        raw_text = extraction_result['text']
        
        print(f"Raw text: {len(raw_text)} characters")
        
        # Clean the text
        cleaned_text = clean_pdf_text(raw_text)
        print(f"Cleaned text: {len(cleaned_text)} characters")
        
        # Find philosophical content
        philosophical_text = find_philosophical_content(cleaned_text)
        print(f"Philosophical content: {len(philosophical_text)} characters")
        
        print(f"\nPhilosophical content sample:")
        print("=" * 60)
        print(philosophical_text[:500])
        print("=" * 60)
        
        # Test relationship extraction
        relationships = rel_extractor.extract_relationships(philosophical_text)
        
        print(f"\nFound {len(relationships)} relationships:")
        for i, rel in enumerate(relationships[:10]):
            print(f"  {i+1}. '{rel['subject']}' -> {rel['relation']} -> '{rel['object']}' (conf: {rel['confidence']})")
        
        if len(relationships) == 0:
            print("\nNo relationships found. Let's check what the extractor is looking for...")
            # Show available patterns
            print("Relationship extractor philosophical verbs:")
            for verb in rel_extractor._philosophical_verbs[:10]:
                print(f"  - {verb}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_philosophical_relationships()