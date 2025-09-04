#!/usr/bin/env python3
"""
Clear all data from Neo4j and Weaviate databases.

This script safely removes all nodes, relationships, and objects
from both databases to prepare for fresh ingestion.

Usage:
    python clear_databases.py
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arete.database.client import Neo4jClient
from arete.database.weaviate_client import WeaviateClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("clear_databases")


async def clear_neo4j():
    """Clear all data from Neo4j database."""
    logger.info("Clearing Neo4j database...")
    
    neo4j_client = Neo4jClient()
    await neo4j_client.async_connect()
    
    try:
        # Get count before clearing
        count_query = """
        MATCH (n)
        RETURN count(n) as node_count
        """
        
        async with neo4j_client.async_session() as session:
            result = await session.run(count_query)
            records = await result.data()
            node_count = records[0]['node_count'] if records else 0
            
            logger.info(f"Found {node_count} nodes in Neo4j")
            
            if node_count > 0:
                # Clear all nodes and relationships
                clear_query = """
                MATCH (n)
                DETACH DELETE n
                """
                
                logger.info("Deleting all nodes and relationships...")
                await session.run(clear_query)
                
                # Verify clearing
                result = await session.run(count_query)
                records = await result.data()
                remaining = records[0]['node_count'] if records else 0
                
                if remaining == 0:
                    logger.info("Neo4j database cleared successfully")
                else:
                    logger.warning(f"{remaining} nodes still remain")
            else:
                logger.info("Neo4j database was already empty")
                
    finally:
        await neo4j_client.async_close()


def clear_weaviate():
    """Clear all data from Weaviate database."""
    logger.info("Clearing Weaviate database...")
    
    weaviate_client = WeaviateClient()
    weaviate_client.connect()
    
    try:
        # Try to get the Chunk collection and check if it exists
        try:
            collection = weaviate_client.client.collections.get("Chunk")
            
            # Count objects
            count_result = collection.aggregate.over_all(total_count=True)
            count = count_result.total_count
            
            logger.info(f"Found {count} objects in Weaviate Chunk collection")
            
            if count > 0:
                # Delete all objects by deleting the entire collection
                logger.info("Deleting Chunk collection...")
                weaviate_client.client.collections.delete("Chunk")
                logger.info("Weaviate Chunk collection deleted successfully")
            else:
                logger.info("Weaviate Chunk collection was already empty")
                
        except Exception as e:
            # Collection might not exist
            logger.info(f"Chunk collection may not exist or is already empty: {e}")
            
        # Try to delete Document collection if it exists
        try:
            doc_collection = weaviate_client.client.collections.get("Document")
            doc_count_result = doc_collection.aggregate.over_all(total_count=True)
            doc_count = doc_count_result.total_count
            
            logger.info(f"Found {doc_count} objects in Document collection")
            
            if doc_count > 0:
                logger.info("Deleting Document collection...")
                weaviate_client.client.collections.delete("Document")
                logger.info("Weaviate Document collection deleted successfully")
                
        except Exception as e:
            logger.info(f"Document collection may not exist or is already empty: {e}")
            
        # Try to delete Entity collection if it exists
        try:
            entity_collection = weaviate_client.client.collections.get("Entity")
            entity_count_result = entity_collection.aggregate.over_all(total_count=True)
            entity_count = entity_count_result.total_count
            
            logger.info(f"Found {entity_count} objects in Entity collection")
            
            if entity_count > 0:
                logger.info("Deleting Entity collection...")
                weaviate_client.client.collections.delete("Entity")
                logger.info("Weaviate Entity collection deleted successfully")
                
        except Exception as e:
            logger.info(f"Entity collection may not exist or is already empty: {e}")
            
        logger.info("Weaviate database clearing completed")
            
    except Exception as e:
        logger.error(f"Error clearing Weaviate: {e}")
    
    finally:
        weaviate_client.close()


async def main():
    """Main clearing function."""
    logger.info("=" * 60)
    logger.info("ARETE DATABASE CLEARING TOOL")
    logger.info("=" * 60)
    
    # Confirm with user
    print("\nWARNING: This will permanently delete ALL data from:")
    print("   - Neo4j database (all nodes and relationships)")
    print("   - Weaviate database (all vector embeddings)")
    print()
    
    response = input("Are you sure you want to continue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        logger.info("Operation cancelled by user")
        return
    
    # Clear both databases
    try:
        await clear_neo4j()
        clear_weaviate()
        
        logger.info("=" * 60)
        logger.info("DATABASE CLEARING COMPLETE")
        logger.info("Both Neo4j and Weaviate are now empty and ready for fresh data")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error during database clearing: {e}")
        logger.error("Some data may not have been cleared properly")


if __name__ == "__main__":
    asyncio.run(main())