#!/usr/bin/env python3
"""
Verify Database Content After Ingestion

Quick verification script to check what was actually stored in Neo4j and Weaviate
after the AI-restructured text ingestion process.
"""

import sys
import asyncio
from pathlib import Path
from typing import Dict, Any, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arete.config import get_settings
from arete.database.client import Neo4jClient
from arete.database.weaviate_client import WeaviateClient


async def verify_neo4j_content() -> Dict[str, Any]:
    """Verify what's stored in Neo4j."""
    print("=== Neo4j Database Verification ===")
    
    neo4j_client = Neo4jClient()
    try:
        await neo4j_client.async_connect()
        
        # Count nodes by type
        queries = {
            "documents": "MATCH (d:Document) RETURN count(d) as count",
            "chunks": "MATCH (c:Chunk) RETURN count(c) as count",
            "entities": "MATCH (e:Entity) RETURN count(e) as count",
            "relationships": "MATCH ()-[r]->() RETURN count(r) as count"
        }
        
        results = {}
        for name, query in queries.items():
            result = await neo4j_client.async_execute_query(query)
            count = result[0]["count"] if result else 0
            results[name] = count
            print(f"  {name.capitalize()}: {count}")
        
        # Get sample document
        doc_query = """
        MATCH (d:Document) 
        RETURN d.title, d.author, d.word_count, d.id
        LIMIT 1
        """
        doc_result = await neo4j_client.async_execute_query(doc_query)
        if doc_result:
            doc = doc_result[0]
            print(f"\nSample Document:")
            print(f"  Title: {doc['d.title']}")
            print(f"  Author: {doc['d.author']}")
            print(f"  Words: {doc['d.word_count']}")
            print(f"  ID: {doc['d.id']}")
        
        # Get sample entities
        entity_query = """
        MATCH (e:Entity)
        RETURN e.name, e.entity_type, e.confidence
        LIMIT 5
        """
        entity_results = await neo4j_client.async_execute_query(entity_query)
        if entity_results:
            print(f"\nSample Entities ({len(entity_results)}):")
            for entity in entity_results:
                print(f"  - {entity['e.name']} ({entity['e.entity_type']}) - confidence: {entity['e.confidence']:.2f}")
        
        # Get sample chunks
        chunk_query = """
        MATCH (c:Chunk)
        RETURN c.position, c.word_count, c.chunk_type, substring(c.text, 0, 100) as text_preview
        ORDER BY c.position
        LIMIT 3
        """
        chunk_results = await neo4j_client.async_execute_query(chunk_query)
        if chunk_results:
            print(f"\nSample Chunks ({len(chunk_results)}):")
            for chunk in chunk_results:
                print(f"  Position {chunk['c.position']}: {chunk['c.word_count']} words ({chunk['c.chunk_type']})")
                print(f"    Preview: {chunk['text_preview']}...")
        
        return results
        
    except Exception as e:
        print(f"Neo4j verification failed: {e}")
        return {}
    finally:
        await neo4j_client.async_close()


async def verify_weaviate_content() -> Dict[str, Any]:
    """Verify what's stored in Weaviate."""
    print(f"\n=== Weaviate Database Verification ===")
    
    weaviate_client = WeaviateClient()
    try:
        weaviate_client.connect()
        
        # Check if schema exists
        schema = weaviate_client.get_schema()
        classes = [cls['class'] for cls in schema.get('classes', [])]
        print(f"Available classes: {classes}")
        
        results = {}
        
        if 'Chunk' in classes:
            # Count objects in Chunk class
            chunk_count = weaviate_client.get_object_count('Chunk')
            results['chunks'] = chunk_count
            print(f"  Chunks: {chunk_count}")
            
            # Get sample chunks with metadata
            sample_query = """
            {
                Get {
                    Chunk(limit: 3) {
                        content
                        position_index
                        word_count
                        chunk_type
                        metadata_section_title
                        computed_word_count
                    }
                }
            }
            """
            
            try:
                sample_result = weaviate_client.client.query.raw(sample_query)
                if sample_result and 'data' in sample_result:
                    chunks = sample_result['data']['Get']['Chunk']
                    print(f"\nSample Weaviate Chunks ({len(chunks)}):")
                    for i, chunk in enumerate(chunks):
                        print(f"  Chunk {i+1}:")
                        print(f"    Position: {chunk.get('position_index')}")
                        print(f"    Words: {chunk.get('computed_word_count')} ({chunk.get('chunk_type')})")
                        print(f"    Section: {chunk.get('metadata_section_title', 'Unknown')}")
                        content_preview = chunk.get('content', '')[:100]
                        print(f"    Content: {content_preview}...")
                        
                        # Check if embedding exists by attempting a vector search
                        try:
                            vector_search = weaviate_client.client.query.get('Chunk').with_limit(1).with_additional(['vector']).do()
                            has_vectors = bool(vector_search.get('data', {}).get('Get', {}).get('Chunk'))
                            print(f"    Has embedding: {has_vectors}")
                        except:
                            print(f"    Has embedding: Unknown")
                        print()
            except Exception as e:
                print(f"  Error getting sample chunks: {e}")
        else:
            print("  No 'Chunk' class found in schema")
            results['chunks'] = 0
        
        return results
        
    except Exception as e:
        print(f"Weaviate verification failed: {e}")
        return {}
    finally:
        await weaviate_client.async_close()


async def test_vector_search() -> None:
    """Test if vector search is working."""
    print(f"\n=== Vector Search Test ===")
    
    weaviate_client = WeaviateClient()
    try:
        weaviate_client.connect()
        
        # Test a simple semantic search
        test_query = "What is virtue according to Socrates?"
        print(f"Testing search: '{test_query}'")
        
        try:
            # Get embedding service to generate query vector
            from arete.services.embedding_factory import get_embedding_service
            embedding_service = get_embedding_service()
            
            query_embeddings = await embedding_service.generate_embeddings([test_query])
            if query_embeddings and query_embeddings[0]:
                query_vector = query_embeddings[0]
                print(f"Generated query vector: {len(query_vector)} dimensions")
                
                # Perform vector search
                results = weaviate_client.search_by_vector(
                    'Chunk', 
                    query_vector, 
                    limit=3,
                    additional_properties=['distance']
                )
                
                print(f"Search results: {len(results)} chunks found")
                for i, result in enumerate(results):
                    distance = result.get('_additional', {}).get('distance', 'unknown')
                    content_preview = result.get('content', '')[:150]
                    print(f"  Result {i+1} (distance: {distance}):")
                    print(f"    {content_preview}...")
                    print()
                
            else:
                print("Failed to generate query embedding")
                
        except Exception as e:
            print(f"Vector search test failed: {e}")
    
    except Exception as e:
        print(f"Vector search setup failed: {e}")
    finally:
        await weaviate_client.async_close()


async def main():
    """Main verification function."""
    print("Database Content Verification")
    print("=" * 50)
    
    # Verify Neo4j content
    neo4j_results = await verify_neo4j_content()
    
    # Verify Weaviate content  
    weaviate_results = await verify_weaviate_content()
    
    # Test vector search functionality
    await test_vector_search()
    
    # Summary
    print("\n=== VERIFICATION SUMMARY ===")
    print(f"Neo4j Storage:")
    for key, value in neo4j_results.items():
        print(f"  {key}: {value}")
    
    print(f"\nWeaviate Storage:")
    for key, value in weaviate_results.items():
        print(f"  {key}: {value}")
    
    print(f"\nSystem Status:")
    total_neo4j = sum(neo4j_results.values())
    total_weaviate = sum(weaviate_results.values())
    
    if total_neo4j > 0 and total_weaviate > 0:
        print("  ✅ Both databases contain data")
        print("  ✅ RAG system ready for queries")
    elif total_neo4j > 0:
        print("  ⚠️  Neo4j has data, Weaviate empty")
    elif total_weaviate > 0:
        print("  ⚠️  Weaviate has data, Neo4j empty") 
    else:
        print("  ❌ Both databases appear empty")


if __name__ == "__main__":
    asyncio.run(main())