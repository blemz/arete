#!/usr/bin/env python3
"""
Minimal test focusing on the most basic functionality.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_clients():
    """Test just client creation and basic connectivity."""
    print("=== Testing Basic Client Creation ===")
    
    # Test Neo4j
    try:
        from arete.database.client import Neo4jClient
        neo4j = Neo4jClient()
        neo4j.connect()
        
        # Use session to run a simple query
        with neo4j.session() as session:
            result = session.run("RETURN 1 as test").single()
            print(f"[SUCCESS] Neo4j: {result['test']}")
        neo4j.close()
    except Exception as e:
        print(f"[ERROR] Neo4j: {e}")
        return False
    
    # Test Weaviate (just connection, no search)
    try:
        from arete.database.weaviate_client import WeaviateClient
        weaviate = WeaviateClient()
        weaviate.connect()
        health = weaviate.health_check()
        print(f"[SUCCESS] Weaviate health: {health}")
        weaviate.close()
    except Exception as e:
        print(f"[ERROR] Weaviate: {e}")
        return False
    
    return True

def test_embedding():
    """Test embedding generation only."""
    print("\n=== Testing Embedding Generation ===")
    
    try:
        from arete.services.embedding_factory import get_embedding_service
        service = get_embedding_service()
        
        embedding = service.generate_embedding("Hello world")
        print(f"[SUCCESS] Generated {len(embedding)}-dim embedding")
        return True
        
    except Exception as e:
        print(f"[ERROR] Embedding: {e}")
        return False

def test_repository_creation():
    """Test repository creation without actual search."""
    print("\n=== Testing Repository Creation ===")
    
    try:
        from arete.repositories.embedding import create_embedding_repository
        repo = create_embedding_repository()
        print(f"[SUCCESS] Created embedding repository: {type(repo).__name__}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Repository: {e}")
        return False

if __name__ == "__main__":
    print("Minimal RAG Component Tests")
    print("="*40)
    
    tests = [
        test_clients,
        test_embedding,
        test_repository_creation
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"[ERROR] Test crashed: {e}")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n=== FINAL: {passed}/{total} tests passed ===")
    
    if passed == total:
        print("[SUCCESS] Core components working!")
        print("Ready to proceed with search functionality.")
    else:
        print("[ERROR] Core issues need to be fixed first.")
    
    sys.exit(0 if passed == total else 1)