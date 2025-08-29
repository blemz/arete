#!/usr/bin/env python3
"""
Quick test of chunking functionality.
"""

import sys
from pathlib import Path
from uuid import uuid4

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arete.processing.chunker import ChunkingStrategy
from arete.models.chunk import ChunkType

def test_chunking():
    """Test the chunking system with minimal data."""
    print("Testing chunking system...")
    
    # Simple test text
    test_text = """This is the first paragraph. It contains some text.

This is the second paragraph. It has different content.

This is the third paragraph. We want to see if chunking works."""
    
    print(f"Test text length: {len(test_text)} characters")
    
    # Create chunker
    chunker = ChunkingStrategy.get_chunker("paragraph")
    print(f"Chunker created: {type(chunker)}")
    
    # Generate chunks
    document_id = uuid4()
    print(f"Processing with document_id: {document_id}")
    
    try:
        chunks = chunker.chunk_text(test_text, document_id)
        print(f"SUCCESS: Created {len(chunks)} chunks")
        
        for i, chunk in enumerate(chunks):
            print(f"  Chunk {i+1}: {chunk.text[:50]}...")
            print(f"    Type: {chunk.chunk_type}")
            print(f"    Sequence: {chunk.sequence_number}")
            print(f"    Position: {chunk.start_position}-{chunk.end_position}")
            print()
            
    except Exception as e:
        print(f"ERROR in chunking: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chunking()