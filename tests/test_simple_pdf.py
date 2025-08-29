#!/usr/bin/env python3
"""
Test PDF extraction with a simpler approach to identify the timeout issue.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arete.processing.extractors import PDFExtractor, RelationshipExtractor

def test_pdf_extraction():
    """Test PDF extraction quickly."""
    
    print("Testing PDF extraction...")
    pdf_extractor = PDFExtractor()
    
    try:
        print("Attempting to extract from Aristotle's Nicomachean Ethics...")
        extraction_result = pdf_extractor.extract_from_file("data/pdfs/Aristotle's Nicomachean Ethics.pdf")
        text = extraction_result['text']
        
        print(f"SUCCESS: Extracted {len(text)} characters")
        
        # Test a small sample for relationships
        sample = text[:2000]  # First 2000 chars
        print(f"\nTesting relationship extraction on sample ({len(sample)} chars)...")
        
        rel_extractor = RelationshipExtractor()
        relationships = rel_extractor.extract_relationships(sample)
        
        print(f"Found {len(relationships)} relationships:")
        for i, rel in enumerate(relationships[:10]):
            print(f"  {i+1}. '{rel['subject']}' -> {rel['relation']} -> '{rel['object']}'")
            
        print(f"\nFirst 300 chars of text:")
        print(text[:300])
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_extraction()