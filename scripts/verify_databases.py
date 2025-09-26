#!/usr/bin/env python3
"""
Verify data integrity in Neo4j and Weaviate databases.

This script checks that all data is correctly stored and properly structured
for the Arete Graph-RAG system.

Usage:
    python verify_databases.py
"""

import asyncio
import sys
import logging
from pathlib import Path
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arete.database.client import Neo4jClient
from arete.database.weaviate_client import WeaviateClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("verify_databases")


async def verify_neo4j() -> Dict[str, Any]:
    """Verify Neo4j database structure and content."""
    logger.info("🔍 Verifying Neo4j database...")
    
    neo4j_client = Neo4jClient()
    await neo4j_client.async_connect()
    
    stats = {}
    
    try:
        async with neo4j_client.async_session() as session:
            # Count all nodes by type
            node_counts_query = """
            CALL apoc.meta.stats() YIELD labels
            RETURN labels
            """
            
            # Alternative query if apoc is not available
            basic_counts_query = """
            MATCH (n)
            RETURN labels(n)[0] as label, count(n) as count
            ORDER BY count DESC
            """
            
            try:
                result = await session.run(node_counts_query)
                records = await result.data()
                if records:
                    stats['node_counts'] = records[0]['labels']
                else:
                    # Fallback to basic query
                    result = await session.run(basic_counts_query)
                    records = await result.data()
                    stats['node_counts'] = {record['label']: record['count'] for record in records}
            except:
                # Use basic query
                result = await session.run(basic_counts_query)
                records = await result.data()
                stats['node_counts'] = {record['label']: record['count'] for record in records}
            
            # Count relationships
            rel_counts_query = """
            MATCH ()-[r]->()
            RETURN type(r) as relationship_type, count(r) as count
            ORDER BY count DESC
            """
            
            result = await session.run(rel_counts_query)
            records = await result.data()
            stats['relationship_counts'] = {record['relationship_type']: record['count'] for record in records}
            
            # Get sample entities
            sample_entities_query = """
            MATCH (e:Entity)
            RETURN e.name as name, e.type as type, e.description as description
            LIMIT 5
            """
            
            result = await session.run(sample_entities_query)
            records = await result.data()
            stats['sample_entities'] = records
            
            # Get sample chunks
            sample_chunks_query = """
            MATCH (c:Chunk)
            RETURN c.text[0..100] as text_preview, c.sequence_number as seq_num, c.document_id as doc_id
            ORDER BY c.sequence_number
            LIMIT 5
            """
            
            result = await session.run(sample_chunks_query)
            records = await result.data()
            stats['sample_chunks'] = records
            
            # Check document structure
            document_query = """
            MATCH (d:Document)
            RETURN d.title as title, d.author as author, d.word_count as word_count
            LIMIT 3
            """
            
            result = await session.run(document_query)
            records = await result.data()
            stats['documents'] = records
            
            # Check relationships between entities
            entity_relationships_query = """
            MATCH (e1:Entity)-[r]->(e2:Entity)
            RETURN e1.name as from_entity, type(r) as relationship, e2.name as to_entity, r.description as description
            LIMIT 10
            """
            
            result = await session.run(entity_relationships_query)
            records = await result.data()
            stats['entity_relationships'] = records
            
        logger.info("✅ Neo4j verification completed")
        return stats
        
    finally:
        await neo4j_client.async_close()


def verify_weaviate() -> Dict[str, Any]:
    """Verify Weaviate database structure and content."""
    logger.info("🔍 Verifying Weaviate database...")
    
    weaviate_client = WeaviateClient()
    weaviate_client.connect()
    
    stats = {}
    
    try:
        # Check Chunk collection
        try:
            chunk_collection = weaviate_client.client.collections.get("Chunk")
            chunk_count_result = chunk_collection.aggregate.over_all(total_count=True)
            stats['chunk_count'] = chunk_count_result.total_count
            
            # Get sample chunks with metadata
            chunk_response = chunk_collection.query.fetch_objects(limit=5)
            sample_chunks = []
            for obj in chunk_response.objects:
                props = obj.properties
                sample_chunks.append({
                    'id': str(obj.uuid),
                    'text_preview': props.get('text', '')[:100] + '...' if len(props.get('text', '')) > 100 else props.get('text', ''),
                    'sequence_number': props.get('sequence_number'),
                    'document_id': props.get('document_id'),
                    'has_embedding': obj.vector is not None,
                    'embedding_dimensions': len(obj.vector) if obj.vector else 0
                })
            stats['sample_chunks'] = sample_chunks
            
        except Exception as e:
            stats['chunk_error'] = str(e)
        
        # Check Document collection
        try:
            doc_collection = weaviate_client.client.collections.get("Document")
            doc_count_result = doc_collection.aggregate.over_all(total_count=True)
            stats['document_count'] = doc_count_result.total_count
            
            # Get sample documents
            doc_response = doc_collection.query.fetch_objects(limit=3)
            sample_docs = []
            for obj in doc_response.objects:
                props = obj.properties
                sample_docs.append({
                    'id': str(obj.uuid),
                    'title': props.get('title'),
                    'author': props.get('author'),
                    'word_count': props.get('word_count'),
                    'has_embedding': obj.vector is not None
                })
            stats['sample_documents'] = sample_docs
            
        except Exception as e:
            stats['document_error'] = str(e)
        
        # Check Entity collection
        try:
            entity_collection = weaviate_client.client.collections.get("Entity")
            entity_count_result = entity_collection.aggregate.over_all(total_count=True)
            stats['entity_count'] = entity_count_result.total_count
            
            # Get sample entities
            entity_response = entity_collection.query.fetch_objects(limit=5)
            sample_entities = []
            for obj in entity_response.objects:
                props = obj.properties
                sample_entities.append({
                    'id': str(obj.uuid),
                    'name': props.get('name'),
                    'type': props.get('type'),
                    'description': props.get('description', '')[:100] + '...' if len(props.get('description', '')) > 100 else props.get('description', ''),
                    'has_embedding': obj.vector is not None
                })
            stats['sample_entities'] = sample_entities
            
        except Exception as e:
            stats['entity_error'] = str(e)
        
        logger.info("✅ Weaviate verification completed")
        return stats
        
    finally:
        weaviate_client.close()


def print_verification_report(neo4j_stats: Dict[str, Any], weaviate_stats: Dict[str, Any]):
    """Print comprehensive verification report."""
    print("\n" + "=" * 80)
    print("ARETE DATABASE VERIFICATION REPORT")
    print("=" * 80)
    
    # Neo4j Report
    print("\nNEO4J DATABASE STATUS")
    print("-" * 40)
    
    if 'node_counts' in neo4j_stats:
        print("Node Counts:")
        for label, count in neo4j_stats['node_counts'].items():
            print(f"  {label}: {count}")
    
    if 'relationship_counts' in neo4j_stats:
        print("\nRelationship Counts:")
        for rel_type, count in neo4j_stats['relationship_counts'].items():
            print(f"  {rel_type}: {count}")
    
    if 'documents' in neo4j_stats and neo4j_stats['documents']:
        print("\nDocuments:")
        for doc in neo4j_stats['documents']:
            print(f"  '{doc['title']}' by {doc['author']} ({doc['word_count']} words)")
    
    if 'sample_entities' in neo4j_stats and neo4j_stats['sample_entities']:
        print("\nSample Entities:")
        for entity in neo4j_stats['sample_entities'][:3]:
            print(f"  {entity['name']} ({entity['type']}): {entity['description'][:50]}...")
    
    if 'entity_relationships' in neo4j_stats and neo4j_stats['entity_relationships']:
        print("\nSample Relationships:")
        for rel in neo4j_stats['entity_relationships'][:3]:
            print(f"  {rel['from_entity']} --[{rel['relationship']}]--> {rel['to_entity']}")
    
    if 'sample_chunks' in neo4j_stats and neo4j_stats['sample_chunks']:
        print(f"\nSample Chunks (showing sequence order):")
        for chunk in neo4j_stats['sample_chunks']:
            print(f"  Seq #{chunk['seq_num']}: {chunk['text_preview']}...")
    
    # Weaviate Report
    print("\nWEAVIATE DATABASE STATUS")
    print("-" * 40)
    
    if 'chunk_count' in weaviate_stats:
        print(f"Chunk Objects: {weaviate_stats['chunk_count']}")
    
    if 'document_count' in weaviate_stats:
        print(f"Document Objects: {weaviate_stats['document_count']}")
        
    if 'entity_count' in weaviate_stats:
        print(f"Entity Objects: {weaviate_stats['entity_count']}")
    
    if 'sample_chunks' in weaviate_stats and weaviate_stats['sample_chunks']:
        print(f"\nSample Chunks with Embeddings:")
        for chunk in weaviate_stats['sample_chunks'][:3]:
            embedding_status = "YES" if chunk['has_embedding'] else "NO"
            print(f"  {embedding_status} Seq #{chunk['sequence_number']}: {chunk['text_preview']}")
            if chunk['has_embedding']:
                print(f"    Embedding: {chunk['embedding_dimensions']} dimensions")
    
    if 'sample_documents' in weaviate_stats and weaviate_stats['sample_documents']:
        print(f"\nSample Documents:")
        for doc in weaviate_stats['sample_documents']:
            embedding_status = "YES" if doc['has_embedding'] else "NO"
            print(f"  {embedding_status} '{doc['title']}' by {doc['author']}")
    
    if 'sample_entities' in weaviate_stats and weaviate_stats['sample_entities']:
        print(f"\nSample Entities:")
        for entity in weaviate_stats['sample_entities'][:3]:
            embedding_status = "YES" if entity['has_embedding'] else "NO"
            print(f"  {embedding_status} {entity['name']} ({entity['type']})")
    
    # Summary
    print(f"\nVERIFICATION SUMMARY")
    print("-" * 40)
    
    # Calculate totals
    total_neo4j_nodes = sum(neo4j_stats.get('node_counts', {}).values())
    total_neo4j_rels = sum(neo4j_stats.get('relationship_counts', {}).values())
    total_weaviate_objects = (
        weaviate_stats.get('chunk_count', 0) + 
        weaviate_stats.get('document_count', 0) + 
        weaviate_stats.get('entity_count', 0)
    )
    
    print(f"Neo4j: {total_neo4j_nodes} nodes, {total_neo4j_rels} relationships")
    print(f"Weaviate: {total_weaviate_objects} objects with embeddings")
    
    # Check for any errors
    errors = []
    if 'chunk_error' in weaviate_stats:
        errors.append(f"Chunk collection error: {weaviate_stats['chunk_error']}")
    if 'document_error' in weaviate_stats:
        errors.append(f"Document collection error: {weaviate_stats['document_error']}")
    if 'entity_error' in weaviate_stats:
        errors.append(f"Entity collection error: {weaviate_stats['entity_error']}")
    
    if errors:
        print(f"\nERRORS DETECTED:")
        for error in errors:
            print(f"  {error}")
    else:
        print(f"\nAll systems operational - ready for Graph-RAG queries!")
    
    print("=" * 80)


async def main():
    """Main verification function."""
    logger.info("Starting database verification...")
    
    # Verify both databases
    neo4j_stats = await verify_neo4j()
    weaviate_stats = verify_weaviate()
    
    # Generate report
    print_verification_report(neo4j_stats, weaviate_stats)


if __name__ == "__main__":
    asyncio.run(main())