#!/usr/bin/env python3
"""
Simple focused test to validate basic functionality quickly.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_basic_weaviate():
    """Test basic Weaviate functionality."""
    print("Testing basic Weaviate connection...")
    
    try:
        from arete.database.weaviate_client import WeaviateClient
        
        client = WeaviateClient()
        client.connect()
        
        print("[SUCCESS] Weaviate connected")
        
        # Test health
        if client.health_check():
            print("[SUCCESS] Weaviate healthy")
        else:
            print("[ERROR] Weaviate not healthy")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Weaviate test failed: {str(e)}")
        return False

def test_basic_search():
    """Test basic vector search functionality."""
    print("\nTesting basic search functionality...")
    
    try:
        from arete.database.weaviate_client import WeaviateClient
        
        client = WeaviateClient()
        client.connect()
        
        # Test search with dummy vector
        dummy_vector = [0.1] * 384  # Typical embedding dimension
        
        results = client.search_by_vector(
            collection_name="Chunk",
            query_vector=dummy_vector,
            limit=5,
            min_certainty=0.1  # Very low threshold
        )
        
        print(f"[SUCCESS] Search completed, found {len(results)} results")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Search test failed: {str(e)}")
        return False

def test_embedding_service():
    """Test embedding generation."""
    print("\nTesting embedding generation...")
    
    try:
        from arete.services.embedding_factory import get_embedding_service
        
        service = get_embedding_service()
        
        # Test simple embedding
        text = "What is virtue?"
        embedding = service.generate_embedding(text)
        
        print(f"[SUCCESS] Generated embedding with {len(embedding)} dimensions")
        return True
        
    except Exception as e:
        print(f"[ERROR] Embedding test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== Simple RAG Component Tests ===\n")
    
    tests = [
        test_basic_weaviate,
        test_embedding_service, 
        test_basic_search
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"[ERROR] Test crashed: {str(e)}")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n=== Results: {passed}/{total} passed ===")
    
    if passed == total:
        print("[SUCCESS] All basic tests passed!")
    else:
        print("[ERROR] Some tests failed")
    
    sys.exit(0 if passed == total else 1)