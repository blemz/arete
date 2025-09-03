#!/usr/bin/env python3
"""
Simple RAG Core Functionality Test Script

Tests the Arete RAG pipeline components directly without UI complexity.
Provides fast feedback and clear error isolation for debugging.
"""

import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime
from uuid import uuid4
from typing import List, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"TEST: {title}")
    print('='*60)

def print_step(step: str, status: str = ""):
    """Print a test step with optional status."""
    print(f"  -> {step} {status}")

def print_success(message: str):
    """Print success message."""
    print(f"  [SUCCESS] {message}")

def print_error(message: str):
    """Print error message."""
    print(f"  [ERROR] {message}")

def print_info(message: str):
    """Print info message."""
    print(f"  [INFO] {message}")


def test_database_connections():
    """Test Neo4j and Weaviate database connections."""
    print_section("Database Connection Tests")
    
    # Test Neo4j Connection
    print_step("Testing Neo4j connection...")
    try:
        from arete.database.client import Neo4jClient
        
        neo4j_client = Neo4jClient()
        neo4j_client.connect()
        
        # Test basic query
        result = neo4j_client.run_query("RETURN 'Hello Neo4j!' as greeting")
        if result and len(result) > 0:
            print_success(f"Neo4j connected! Response: {result[0]['greeting']}")
        else:
            print_error("Neo4j connected but no response")
            
        neo4j_client.close()
        
    except Exception as e:
        print_error(f"Neo4j connection failed: {str(e)}")
        return False
    
    # Test Weaviate Connection
    print_step("Testing Weaviate connection...")
    try:
        from arete.database.weaviate_client import WeaviateClient
        
        weaviate_client = WeaviateClient()
        weaviate_client.connect()
        
        # Test health check
        if weaviate_client.health_check():
            print_success("Weaviate connected and healthy!")
        else:
            print_error("Weaviate connected but not healthy")
            
        weaviate_client.close()
        
    except Exception as e:
        print_error(f"Weaviate connection failed: {str(e)}")
        return False
    
    return True


def test_embedding_generation():
    """Test embedding service functionality."""
    print_section("Embedding Generation Tests")
    
    print_step("Testing embedding service initialization...")
    try:
        from arete.services.embedding_factory import get_embedding_service
        
        embedding_service = get_embedding_service()
        print_success(f"Embedding service created: {type(embedding_service).__name__}")
        
    except Exception as e:
        print_error(f"Embedding service initialization failed: {str(e)}")
        return False
    
    # Test single embedding generation
    print_step("Testing single embedding generation...")
    try:
        test_text = "What is virtue according to Aristotle?"
        embedding = embedding_service.generate_embedding(test_text)
        
        if embedding and len(embedding) > 0:
            print_success(f"Generated embedding with {len(embedding)} dimensions")
            print_info(f"Sample values: {embedding[:5]}...")
        else:
            print_error("Generated empty embedding")
            return False
            
    except Exception as e:
        print_error(f"Single embedding generation failed: {str(e)}")
        return False
    
    # Test batch embedding generation
    print_step("Testing batch embedding generation...")
    try:
        test_texts = [
            "Virtue is excellence of character.",
            "Knowledge and wisdom lead to good life.",
            "The examined life is worth living."
        ]
        
        embeddings = embedding_service.batch_generate_embeddings(test_texts)
        
        if embeddings and len(embeddings) == len(test_texts):
            print_success(f"Generated {len(embeddings)} batch embeddings")
            for i, emb in enumerate(embeddings):
                print_info(f"Text {i+1}: {len(emb)} dimensions")
        else:
            print_error("Batch embedding generation failed")
            return False
            
    except Exception as e:
        print_error(f"Batch embedding generation failed: {str(e)}")
        return False
    
    return True


def test_chunk_storage_retrieval():
    """Test chunk storage and retrieval functionality."""
    print_section("Chunk Storage & Retrieval Tests")
    
    print_step("Testing chunk creation...")
    try:
        from arete.models.chunk import Chunk, ChunkType
        from arete.repositories.embedding import create_embedding_repository
        
        # Create test chunk
        test_chunk = Chunk(
            chunk_id=str(uuid4()),
            content="Virtue is the mean between extremes of excess and deficiency. This is Aristotle's doctrine of the golden mean.",
            document_id=uuid4(),
            chunk_type=ChunkType.PARAGRAPH,
            position=1,
            metadata={
                "source": "test",
                "philosophy": "aristotelian_ethics"
            }
        )
        
        print_success(f"Created test chunk: {test_chunk.chunk_id}")
        print_info(f"Content preview: {test_chunk.content[:50]}...")
        
    except Exception as e:
        print_error(f"Chunk creation failed: {str(e)}")
        return False
    
    print_step("Testing embedding repository...")
    try:
        embedding_repo = create_embedding_repository()
        print_success("Embedding repository created")
        
    except Exception as e:
        print_error(f"Embedding repository creation failed: {str(e)}")
        return False
    
    print_step("Testing chunk storage with embedding...")
    try:
        # Store chunk with embedding
        stored_chunk = asyncio.run(embedding_repo.generate_and_store_embedding(test_chunk))
        
        if stored_chunk.embedding and len(stored_chunk.embedding) > 0:
            print_success(f"Chunk stored with {len(stored_chunk.embedding)}-dim embedding")
        else:
            print_error("Chunk stored but no embedding generated")
            return False
            
    except Exception as e:
        print_error(f"Chunk storage failed: {str(e)}")
        return False
    
    return True


def test_search_functionality():
    """Test search functionality with stored chunks."""
    print_section("Search Functionality Tests")
    
    print_step("Testing semantic search...")
    try:
        from arete.repositories.embedding import create_embedding_repository
        
        embedding_repo = create_embedding_repository()
        
        # Test semantic search
        query = "What is the golden mean?"
        results = embedding_repo.semantic_search(
            query_text=query,
            limit=5,
            similarity_threshold=0.3  # Lower threshold for testing
        )
        
        print_success(f"Search completed for: '{query}'")
        print_info(f"Found {len(results)} results")
        
        for i, result in enumerate(results):
            print_info(f"Result {i+1}: score={result.similarity_score:.3f}")
            print_info(f"  Content: {result.chunk.content[:100]}...")
        
    except Exception as e:
        print_error(f"Search functionality failed: {str(e)}")
        return False
    
    return True


def test_rag_pipeline():
    """Test end-to-end RAG pipeline with philosophical queries."""
    print_section("RAG Pipeline Tests")
    
    print_step("Testing RAG pipeline initialization...")
    try:
        from arete.services.rag_pipeline_service import create_rag_pipeline_service
        from arete.services.rag_pipeline_service import RAGPipelineConfig
        
        rag_pipeline = create_rag_pipeline_service()
        print_success("RAG pipeline initialized")
        
    except Exception as e:
        print_error(f"RAG pipeline initialization failed: {str(e)}")
        return False
    
    print_step("Testing philosophical query processing...")
    try:
        # Test queries
        test_queries = [
            "What is virtue?",
            "How does Aristotle define the good life?",
            "What is Plato's theory of Forms?"
        ]
        
        config = RAGPipelineConfig(
            max_retrieval_results=10,
            max_response_tokens=500,
            temperature=0.7,
            enable_reranking=False,  # Simplify for testing
            philosophical_domain_boost=1.2
        )
        
        for query in test_queries:
            print_step(f"Processing: '{query}'")
            try:
                result = asyncio.run(rag_pipeline.execute_pipeline(
                    query=query,
                    config=config,
                    user_context={"student_level": "undergraduate"}
                ))
                
                print_success("Query processed successfully!")
                print_info(f"Response length: {len(result.response.response_text)} chars")
                print_info(f"Citations: {len(result.response.citations)}")
                print_info(f"Response preview: {result.response.response_text[:200]}...")
                
            except Exception as e:
                print_error(f"Query processing failed: {str(e)}")
                continue
        
    except Exception as e:
        print_error(f"RAG pipeline testing failed: {str(e)}")
        return False
    
    return True


def run_all_tests():
    """Run all RAG core functionality tests."""
    print("Starting Arete RAG Core Functionality Tests")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Database Connections", test_database_connections),
        ("Embedding Generation", test_embedding_generation),
        ("Chunk Storage & Retrieval", test_chunk_storage_retrieval),
        ("Search Functionality", test_search_functionality),
        ("RAG Pipeline", test_rag_pipeline),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'-'*60}")
        print(f"Running: {test_name}")
        print('-'*60)
        
        try:
            success = test_func()
            results[test_name] = success
            
            if success:
                print_success(f"{test_name} - PASSED")
            else:
                print_error(f"{test_name} - FAILED")
                
        except Exception as e:
            print_error(f"{test_name} - ERROR: {str(e)}")
            results[test_name] = False
    
    # Summary
    print_section("Test Results Summary")
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, success in results.items():
        status = "[PASS]" if success else "[FAIL]"
        print(f"  {status} {test_name}")
    
    print(f"\nResults: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print_success("All tests passed! RAG pipeline is working correctly.")
        return True
    else:
        print_error(f"{total_tests - passed_tests} test(s) failed. Check errors above.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)