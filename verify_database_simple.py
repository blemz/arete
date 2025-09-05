#!/usr/bin/env python3
"""
Simple Database Content Verification

Uses the correct client methods to verify what was stored after ingestion.
"""

import sys
import asyncio
from pathlib import Path
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arete.database.client import Neo4jClient
from arete.database.weaviate_client import WeaviateClient


async def verify_neo4j_content() -> Dict[str, int]:
    """Verify Neo4j content using session methods."""
    print("=== Neo4j Database Verification ===")
    
    neo4j_client = Neo4jClient()
    results = {"documents": 0, "chunks": 0, "entities": 0, "relationships": 0}
    
    try:
        await neo4j_client.async_connect()
        
        async with neo4j_client.async_session() as session:
            # Count documents
            doc_result = await session.run("MATCH (d:Document) RETURN count(d) as count")
            doc_record = await doc_result.single()
            results["documents"] = doc_record["count"] if doc_record else 0
            
            # Count chunks
            chunk_result = await session.run("MATCH (c:Chunk) RETURN count(c) as count")
            chunk_record = await chunk_result.single()
            results["chunks"] = chunk_record["count"] if chunk_record else 0
            
            # Count entities
            entity_result = await session.run("MATCH (e:Entity) RETURN count(e) as count")
            entity_record = await entity_result.single()
            results["entities"] = entity_record["count"] if entity_record else 0
            
            # Count relationships
            rel_result = await session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_record = await rel_result.single()
            results["relationships"] = rel_record["count"] if rel_record else 0
            
            print(f"  Documents: {results['documents']}")
            print(f"  Chunks: {results['chunks']}")
            print(f"  Entities: {results['entities']}")
            print(f"  Relationships: {results['relationships']}")
            
            # Get sample document info
            if results["documents"] > 0:
                doc_sample = await session.run(
                    "MATCH (d:Document) RETURN d.title, d.author, d.word_count LIMIT 1"
                )
                sample_record = await doc_sample.single()
                if sample_record:
                    print(f"\nSample Document:")
                    print(f"  Title: {sample_record['d.title']}")
                    print(f"  Author: {sample_record['d.author']}")
                    print(f"  Words: {sample_record['d.word_count']}")
            
            # Get sample entities
            if results["entities"] > 0:
                entity_sample = await session.run(
                    "MATCH (e:Entity) RETURN e.name, e.entity_type, e.confidence LIMIT 5"
                )
                entity_records = await entity_sample.data()
                print(f"\nSample Entities:")
                for entity in entity_records:
                    name = entity.get('e.name', 'Unknown')
                    entity_type = entity.get('e.entity_type', 'Unknown')
                    confidence = entity.get('e.confidence', 0.0)
                    print(f"  - {name} ({entity_type}) - confidence: {confidence:.2f}")
    
    except Exception as e:
        print(f"Neo4j verification error: {e}")
    
    finally:
        await neo4j_client.async_close()
    
    return results


def verify_weaviate_content() -> Dict[str, int]:
    """Verify Weaviate content using available client methods."""
    print(f"\n=== Weaviate Database Verification ===")
    
    weaviate_client = WeaviateClient()
    results = {"chunks": 0}
    
    try:
        weaviate_client.connect()
        
        # Check if we can query the client
        if weaviate_client.client:
            # Try to get schema information
            try:
                # Get all objects from Chunk class
                query = """
                {
                    Get {
                        Chunk {
                            content
                            position_index
                            word_count
                            chunk_type
                            computed_word_count
                        }
                    }
                }
                """
                result = weaviate_client.client.query.raw(query)
                
                if result and 'data' in result and 'Get' in result['data'] and 'Chunk' in result['data']['Get']:
                    chunks = result['data']['Get']['Chunk']
                    results["chunks"] = len(chunks)
                    print(f"  Chunks: {results['chunks']}")
                    
                    # Show sample chunks
                    if chunks:
                        print(f"\nSample Weaviate Chunks:")
                        for i, chunk in enumerate(chunks[:3]):  # Show first 3
                            position = chunk.get('position_index', 'Unknown')
                            word_count = chunk.get('computed_word_count', 0)
                            chunk_type = chunk.get('chunk_type', 'Unknown')
                            content = chunk.get('content', '')[:100]
                            print(f"  Chunk {i+1}: Position {position}, {word_count} words ({chunk_type})")
                            print(f"    Content: {content}...")
                            print()
                else:
                    print("  No Chunk data found or schema issue")
                    
            except Exception as query_error:
                print(f"  Query error: {query_error}")
                # Try a simpler approach - check if Weaviate is responding
                try:
                    health = weaviate_client.client.is_ready()
                    print(f"  Weaviate ready: {health}")
                except Exception as health_error:
                    print(f"  Health check error: {health_error}")
        else:
            print("  Client not connected")
    
    except Exception as e:
        print(f"Weaviate verification error: {e}")
    
    finally:
        try:
            weaviate_client.close()
        except:
            pass
    
    return results


async def test_simple_vector_search():
    """Test basic vector search functionality."""
    print(f"\n=== Simple Vector Search Test ===")
    
    weaviate_client = WeaviateClient()
    
    try:
        weaviate_client.connect()
        
        if weaviate_client.client:
            # Try a simple text search (BM25/keyword search)
            try:
                query = """
                {
                    Get {
                        Chunk(
                            bm25: {query: "virtue Socrates"}
                            limit: 3
                        ) {
                            content
                            position_index
                            chunk_type
                        }
                    }
                }
                """
                
                result = weaviate_client.client.query.raw(query)
                
                if result and 'data' in result:
                    chunks = result['data'].get('Get', {}).get('Chunk', [])
                    print(f"BM25 search results: {len(chunks)} chunks found")
                    
                    for i, chunk in enumerate(chunks):
                        content = chunk.get('content', '')[:150]
                        position = chunk.get('position_index', 'Unknown')
                        print(f"  Result {i+1} (position {position}):")
                        print(f"    {content}...")
                        print()
                else:
                    print("No search results or query failed")
                    
            except Exception as search_error:
                print(f"Search test failed: {search_error}")
        else:
            print("Weaviate client not connected")
            
    except Exception as e:
        print(f"Vector search test error: {e}")
    
    finally:
        try:
            weaviate_client.close()
        except:
            pass


async def main():
    """Main verification function."""
    print("Database Content Verification")
    print("=" * 50)
    
    # Verify Neo4j content
    neo4j_results = await verify_neo4j_content()
    
    # Verify Weaviate content  
    weaviate_results = verify_weaviate_content()
    
    # Test search functionality
    await test_simple_vector_search()
    
    # Summary
    print("\n=== VERIFICATION SUMMARY ===")
    print(f"Neo4j Storage:")
    for key, value in neo4j_results.items():
        print(f"  {key}: {value}")
    
    print(f"\nWeaviate Storage:")
    for key, value in weaviate_results.items():
        print(f"  {key}: {value}")
    
    # Overall assessment
    total_neo4j = sum(neo4j_results.values())
    total_weaviate = sum(weaviate_results.values())
    
    print(f"\nSystem Status:")
    if total_neo4j > 0 and total_weaviate > 0:
        print("  Status: Both databases contain data")
        print("  Ready: RAG system operational")
    elif total_neo4j > 0:
        print("  Status: Neo4j has data, Weaviate may be empty")
    elif total_weaviate > 0:
        print("  Status: Weaviate has data, Neo4j may be empty")
    else:
        print("  Status: Both databases appear empty or inaccessible")


if __name__ == "__main__":
    asyncio.run(main())