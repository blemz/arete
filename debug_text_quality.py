#!/usr/bin/env python3
"""
Debug the quality of text extracted from PDFs and chunked for relationship extraction.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arete.processing.extractors import PDFExtractor, RelationshipExtractor
from arete.processing.chunker import ChunkingStrategy
from uuid import uuid4

def debug_text_quality():
    """Debug text quality issues."""
    
    # Extract first page only to avoid timeout
    print("Extracting first page from The Republic...")
    pdf_extractor = PDFExtractor()
    
    try:
        # This should be fast for just first page
        extraction_result = pdf_extractor.extract_from_file("data/pdfs/Plato The Republic (Cambridge, Tom Griffith) Clean.pdf")
        text = extraction_result['text'][:5000]  # First 5000 chars only
        
        print(f"Extracted {len(text)} characters")
        print("\nFirst 500 characters (raw):")
        print("=" * 50)
        print(repr(text[:500]))
        
        print("\nFirst 500 characters (formatted):")
        print("=" * 50)
        print(text[:500])
        
        # Test chunking
        print("\nTesting chunking...")
        chunker = ChunkingStrategy.get_chunker("paragraph")
        chunks = chunker.chunk_text(text, uuid4())
        
        print(f"Created {len(chunks)} chunks")
        if chunks:
            print(f"\nFirst chunk (raw): {repr(chunks[0].text[:200])}")
            print(f"\nFirst chunk (formatted): {chunks[0].text[:200]}")
            
            # Test relationship extraction on first chunk
            print("\nTesting relationship extraction on first chunk...")
            rel_extractor = RelationshipExtractor()
            relationships = rel_extractor.extract_relationships(chunks[0].text)
            
            print(f"Found {len(relationships)} relationships in first chunk:")
            for i, rel in enumerate(relationships[:5]):
                print(f"  {i+1}. {rel['subject']} -> {rel['relation']} -> {rel['object']}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_text_quality()