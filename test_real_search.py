#!/usr/bin/env python3
"""
Test real vector search with actual philosophical queries.
Searches the ingested Apology and Charmides content.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_philosophical_search():
    """Test search with real philosophical queries."""
    print("=== Testing Philosophical Content Search ===\n")
    
    try:
        from arete.database.weaviate_client import WeaviateClient
        from arete.services.embedding_factory import get_embedding_service
        
        # Connect to Weaviate
        client = WeaviateClient()
        client.connect()
        print("[SUCCESS] Connected to Weaviate")
        
        # Get embedding service
        embedding_service = get_embedding_service()
        print("[SUCCESS] Embedding service ready")
        
        # Test queries related to Apology and Charmides
        test_queries = [
            "What does Socrates say about wisdom?",
            "What is the nature of temperance?",
            "Why was Socrates accused?",
            "What is self-knowledge?",
            "What does Socrates think about death?"
        ]
        
        print("\n--- Searching Philosophical Content ---")
        for query in test_queries:
            print(f"\nQuery: '{query}'")
            
            # Generate embedding for query
            query_embedding = embedding_service.generate_embedding(query)
            print(f"  Generated {len(query_embedding)}-dim embedding")
            
            # Search in Chunk collection
            try:
                results = client.search_by_vector(
                    collection_name="Chunk",
                    query_vector=query_embedding,
                    limit=3,
                    min_certainty=0.5
                )
                
                print(f"  Found {len(results)} results")
                
                for i, result in enumerate(results[:2]):  # Show first 2 results
                    props = result.get("properties", {})
                    content = props.get("content", "")[:150] + "..." if props.get("content") else "No content"
                    certainty = result.get("metadata", {}).get("certainty", 0)
                    print(f"  Result {i+1} (certainty: {certainty:.3f}):")
                    print(f"    {content}")
                    
            except Exception as e:
                print(f"  [ERROR] Search failed: {str(e)}")
        
        client.close()
        print("\n[SUCCESS] All searches completed!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_philosophical_search()
    sys.exit(0 if success else 1)