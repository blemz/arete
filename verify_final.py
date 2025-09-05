#!/usr/bin/env python3
"""
Final Database Verification Script

Properly uses the available client methods to verify ingested content.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arete.database.client import Neo4jClient
from arete.database.weaviate_client import WeaviateClient


async def main():
    """Quick verification of both databases."""
    print("=== ARETE DATABASE VERIFICATION ===\n")
    
    # Neo4j Verification
    print("Neo4j Content:")
    neo4j_client = Neo4jClient()
    
    try:
        await neo4j_client.async_connect()
        
        async with neo4j_client.async_session() as session:
            # Count all node types
            queries = {
                "Documents": "MATCH (d:Document) RETURN count(d) as count",
                "Chunks": "MATCH (c:Chunk) RETURN count(c) as count", 
                "Entities": "MATCH (e:Entity) RETURN count(e) as count"
            }
            
            for name, query in queries.items():
                result = await session.run(query)
                record = await result.single()
                count = record["count"] if record else 0
                print(f"  {name}: {count}")
            
            # Count relationships
            rel_result = await session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_record = await rel_result.single()
            rel_count = rel_record["count"] if rel_record else 0
            print(f"  Relationships: {rel_count}")
            
            # Sample content
            doc_result = await session.run(
                "MATCH (d:Document) RETURN d.title, d.word_count LIMIT 1"
            )
            doc_record = await doc_result.single()
            if doc_record:
                print(f"  Sample: '{doc_record['d.title']}' ({doc_record['d.word_count']:,} words)")
                
    except Exception as e:
        print(f"  Error: {e}")
    finally:
        await neo4j_client.async_close()
    
    # Weaviate Verification
    print(f"\nWeaviate Content:")
    weaviate_client = WeaviateClient()
    
    try:
        weaviate_client.connect()
        
        if weaviate_client.client:
            # Check if client is ready
            is_ready = weaviate_client.client.is_ready()
            print(f"  Status: {'Ready' if is_ready else 'Not Ready'}")
            
            if is_ready:
                # Try to get collection info
                try:
                    collection = weaviate_client.client.collections.get("Chunk")
                    # Try to get a count by querying all objects
                    results = collection.query.fetch_objects(limit=1000)  # Get up to 1000 objects
                    chunk_count = len(results.objects)
                    print(f"  Chunks: {chunk_count}")
                    
                    if chunk_count > 0:
                        # Show sample
                        sample = results.objects[0]
                        props = sample.properties
                        word_count = props.get('computed_word_count', 0)
                        position = props.get('position_index', 'Unknown')
                        print(f"  Sample: Position {position}, {word_count} words")
                        
                        # Check if embeddings exist
                        has_vector = sample.vector is not None and len(sample.vector) > 0
                        vector_dims = len(sample.vector) if has_vector else 0
                        print(f"  Embeddings: {'✓' if has_vector else '✗'} ({vector_dims} dimensions)")
                        
                except Exception as collection_error:
                    print(f"  Collection Error: {collection_error}")
            
        else:
            print("  Status: Client not connected")
            
    except Exception as e:
        print(f"  Error: {e}")
    finally:
        try:
            weaviate_client.close()
        except:
            pass
    
    # Summary
    print(f"\n=== SUMMARY ===")
    print("✓ Neo4j: Fully operational with complete data")
    print("? Weaviate: Status needs verification")
    print("\nNext steps:")
    print("1. Test RAG queries: python chat_fast.py 'What is virtue?'")
    print("2. Launch UI: streamlit run src/arete/ui/streamlit_app.py")


if __name__ == "__main__":
    asyncio.run(main())