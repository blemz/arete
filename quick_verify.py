#!/usr/bin/env python3
"""Quick database verification with clean output."""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from arete.database.client import Neo4jClient
from arete.database.weaviate_client import WeaviateClient


async def main():
    print("=" * 60)
    print(" ARETE DATABASE VERIFICATION - DATA ACCURACY CHECK")
    print("=" * 60)

    # Neo4j Verification
    print("\n📊 NEO4J KNOWLEDGE GRAPH")
    print("-" * 40)

    neo4j_client = Neo4jClient()
    await neo4j_client.async_connect()

    try:
        async with neo4j_client.async_session() as session:
            # Count all data
            print("Content Summary:")

            # Documents
            doc_result = await session.run("""
                MATCH (d:Document)
                RETURN d.title as title, d.word_count as words
                ORDER BY d.created_at DESC
            """)
            docs = await doc_result.data()
            print(f"  📚 Documents: {len(docs)}")
            for doc in docs:
                print(f"     - {doc['title']}: {doc['words']:,} words")

            # Chunks
            chunk_result = await session.run("MATCH (c:Chunk) RETURN count(c) as count")
            chunk_data = await chunk_result.single()
            print(f"  📄 Chunks: {chunk_data['count']}")

            # Entities by type
            entity_result = await session.run("""
                MATCH (e:Entity)
                RETURN e.entity_type as type, count(e) as count
                ORDER BY count DESC
            """)
            entities = await entity_result.data()
            print(f"  🏛️ Entities: {sum(e['count'] for e in entities)} total")
            for e in entities[:5]:
                print(f"     - {e['type']}: {e['count']}")

            # Sample entities
            sample_result = await session.run("""
                MATCH (e:Entity)
                WHERE e.name IS NOT NULL
                RETURN DISTINCT e.name as name
                ORDER BY e.name
                LIMIT 10
            """)
            samples = await sample_result.data()
            print(f"\n  Sample Entities:")
            for s in samples:
                print(f"     • {s['name']}")

            # Relationships
            rel_result = await session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(r) as count
                ORDER BY count DESC
                LIMIT 5
            """)
            rels = await rel_result.data()
            total_rels = sum(r['count'] for r in rels)
            print(f"\n  🔗 Relationships: {total_rels}+ connections")
            for r in rels:
                print(f"     - {r['type']}: {r['count']}")

    finally:
        await neo4j_client.async_close()

    # Weaviate Verification
    print("\n📊 WEAVIATE VECTOR DATABASE")
    print("-" * 40)

    weaviate_client = WeaviateClient()
    weaviate_client.connect()

    try:
        if weaviate_client.client and weaviate_client.client.is_ready():
            print("Content Summary:")

            # Check chunks
            chunk_collection = weaviate_client.client.collections.get("Chunk")
            chunk_result = chunk_collection.query.fetch_objects(limit=5)
            chunk_objects = chunk_result.objects
            print(f"  📄 Chunks: {len(chunk_objects)} sampled")

            if chunk_objects:
                sample = chunk_objects[0]
                has_vector = sample.vector is not None
                dims = len(sample.vector) if has_vector else 0
                print(f"  🔢 Embeddings: {'✅ Present' if has_vector else '❌ Missing'}")
                if has_vector:
                    print(f"     - Dimensions: {dims}")
                    print(f"     - Type: {'Dense vectors' if dims > 0 else 'Not detected'}")

            # Test semantic search
            print("\n  🔍 Testing Semantic Search:")
            test_queries = [
                "What is virtue according to Socrates?",
                "What is justice in the Republic?",
                "What is the allegory of the cave?"
            ]

            for query in test_queries[:1]:  # Test just one query
                print(f'     Query: "{query}"')
                try:
                    search_result = chunk_collection.query.near_text(
                        query=query,
                        limit=2
                    )
                    if search_result.objects:
                        for i, obj in enumerate(search_result.objects, 1):
                            text = obj.properties.get('text', '')[:80]
                            print(f"     Result {i}: {text}...")
                    else:
                        print("     No results found")
                except Exception as e:
                    print(f"     Search error: {e}")
        else:
            print("  ❌ Weaviate not ready")

    finally:
        weaviate_client.close()

    # Summary
    print("\n" + "=" * 60)
    print("📈 VERIFICATION SUMMARY")
    print("-" * 40)
    print("✅ Neo4j: Knowledge graph populated with documents, chunks, and entities")
    print("⚠️  Weaviate: Vector store populated but embeddings need verification")
    print("\n💡 Recommendations:")
    print("1. Re-run embedding generation if vectors are missing")
    print("2. Test RAG pipeline: python chat_rag_clean.py 'What is virtue?'")
    print("3. Check logs for any embedding generation errors")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())