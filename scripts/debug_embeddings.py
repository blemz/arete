#!/usr/bin/env python3
"""
Debug script for testing embedding generation in isolation.

This script loads already-processed chunks from Neo4j and generates embeddings
without re-running the entire ingestion pipeline. Useful for debugging embedding
service issues quickly.

Usage:
    python debug_embeddings.py [--document-id UUID] [--limit N]
"""

import asyncio
import sys
import time
import logging
import argparse
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arete.models.chunk import Chunk
from arete.services.embedding_factory import get_embedding_service
from arete.config import get_settings
from arete.database.client import Neo4jClient
from arete.database.weaviate_client import WeaviateClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'logs/debug_embeddings_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger("debug_embeddings")


async def fetch_chunks_from_neo4j(
    document_id: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Fetch chunks from Neo4j database.
    
    Args:
        document_id: Optional document ID to filter chunks
        limit: Maximum number of chunks to fetch
        
    Returns:
        List of chunk dictionaries
    """
    logger.info("Connecting to Neo4j...")
    neo4j_client = Neo4jClient()
    await neo4j_client.async_connect()
    
    try:
        # Build query based on parameters
        if document_id:
            query = """
            MATCH (c:Chunk {document_id: $doc_id})
            RETURN c
            ORDER BY c.sequence_number
            """
            if limit:
                query += f" LIMIT {limit}"
            params = {"doc_id": document_id}
        else:
            query = """
            MATCH (c:Chunk)
            RETURN c
            ORDER BY c.created_at DESC, c.sequence_number
            """
            if limit:
                query += f" LIMIT {limit}"
            params = {}
        
        logger.info(f"Executing query: {query[:100]}...")
        
        # Execute query and get data
        async with neo4j_client.async_session() as session:
            result = await session.run(query, params)
            records = await result.data()
        
        chunks = []
        for record in records:
            chunk_node = record['c']
            chunk_dict = dict(chunk_node)
            chunks.append(chunk_dict)
        
        logger.info(f"Fetched {len(chunks)} chunks from Neo4j")
        return chunks
        
    finally:
        await neo4j_client.async_close()


async def test_embedding_generation(chunks_data: List[Dict[str, Any]]) -> List[Chunk]:
    """
    Test embedding generation for chunks.
    
    Args:
        chunks_data: List of chunk dictionaries from Neo4j
        
    Returns:
        List of Chunk objects with embeddings
    """
    logger.info("=== Starting Embedding Generation Test ===")
    
    # Convert Neo4j data to Chunk objects
    chunks = []
    for chunk_data in chunks_data:
        try:
            # Handle metadata field - it might be stored as JSON string in Neo4j
            if 'metadata' in chunk_data and isinstance(chunk_data['metadata'], str):
                import json
                try:
                    chunk_data['metadata'] = json.loads(chunk_data['metadata'])
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse metadata JSON, using empty dict")
                    chunk_data['metadata'] = {}
            
            # Create Chunk from Neo4j data
            chunk = Chunk.from_neo4j_dict(chunk_data)
            chunks.append(chunk)
        except Exception as e:
            logger.error(f"Failed to create chunk from data: {e}")
            logger.debug(f"Problematic chunk data keys: {list(chunk_data.keys())}")
            if 'text' in chunk_data:
                logger.debug(f"Text preview: {chunk_data['text'][:100]}...")
    
    logger.info(f"Created {len(chunks)} Chunk objects")
    
    if not chunks:
        logger.error("No valid chunks to process")
        return []
    
    # Initialize embedding service
    logger.info("Initializing embedding service...")
    embedding_service = get_embedding_service()
    logger.info(f"Using embedding service: {embedding_service.__class__.__name__}")
    
    # Log service details
    if hasattr(embedding_service, 'get_model_info'):
        model_info = embedding_service.get_model_info()
        logger.info(f"Model info: {model_info}")
    
    if hasattr(embedding_service, 'get_dimensions'):
        dimensions = embedding_service.get_dimensions()
        logger.info(f"Expected embedding dimensions: {dimensions}")
    
    # Test service availability
    if hasattr(embedding_service, 'is_available'):
        is_available = embedding_service.is_available()
        logger.info(f"Service available: {is_available}")
        if not is_available:
            logger.error("Embedding service is not available!")
            return chunks
    
    # Generate embeddings in batches
    batch_size = 10  # Smaller batch size for testing
    embeddings_generated = 0
    failed_chunks = []
    
    logger.info(f"Processing {len(chunks)} chunks in batches of {batch_size}...")
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        batch_texts = [chunk.text for chunk in batch]
        batch_num = i // batch_size + 1
        total_batches = (len(chunks) - 1) // batch_size + 1
        
        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} chunks)")
        
        # Log sample text for debugging
        if batch_num == 1:
            sample_text = batch_texts[0][:100] + "..." if len(batch_texts[0]) > 100 else batch_texts[0]
            logger.debug(f"Sample text: {sample_text}")
        
        try:
            # Generate embeddings for batch
            start_time = time.time()
            logger.debug(f"Calling embedding service with {len(batch_texts)} texts")
            
            # Try the async method
            try:
                batch_embeddings = await embedding_service.generate_embeddings(batch_texts)
                logger.debug(f"Successfully called async generate_embeddings")
            except AttributeError as e:
                logger.warning(f"Async method not available: {e}")
                # Fall back to sync method
                if hasattr(embedding_service, 'generate_embeddings_batch'):
                    batch_embeddings = embedding_service.generate_embeddings_batch(batch_texts)
                    logger.debug(f"Successfully called sync generate_embeddings_batch")
                else:
                    raise AttributeError("No suitable embedding generation method found")
            
            elapsed = time.time() - start_time
            logger.info(f"Generated {len(batch_embeddings)} embeddings in {elapsed:.2f}s")
            
            # Validate embeddings
            if batch_embeddings:
                first_embedding = batch_embeddings[0]
                if first_embedding:
                    dims = len(first_embedding)
                    logger.debug(f"First embedding dimensions: {dims}")
                    
                    # Check for dimension consistency
                    all_dims = [len(emb) if emb else 0 for emb in batch_embeddings]
                    unique_dims = set(all_dims)
                    if len(unique_dims) > 1:
                        logger.warning(f"Inconsistent embedding dimensions: {unique_dims}")
                    else:
                        logger.debug(f"All embeddings have consistent dimensions: {dims}")
            
            # Assign embeddings to chunks
            for chunk, embedding in zip(batch, batch_embeddings):
                if embedding:
                    chunk.embedding_vector = embedding
                    embeddings_generated += 1
                else:
                    logger.warning(f"Empty embedding for chunk {chunk.id}")
                    failed_chunks.append(chunk.id)
                    
        except Exception as e:
            logger.error(f"Error generating embeddings for batch {batch_num}: {e}")
            logger.exception("Full traceback:")
            for chunk in batch:
                failed_chunks.append(chunk.id)
    
    # Summary
    logger.info("=== Embedding Generation Summary ===")
    logger.info(f"Total chunks: {len(chunks)}")
    logger.info(f"Embeddings generated: {embeddings_generated}")
    logger.info(f"Failed chunks: {len(failed_chunks)}")
    
    if embeddings_generated > 0:
        success_rate = (embeddings_generated / len(chunks)) * 100
        logger.info(f"Success rate: {success_rate:.1f}%")
    
    if failed_chunks:
        logger.warning(f"Failed chunk IDs: {failed_chunks[:5]}...")  # Show first 5
    
    return chunks


async def store_embeddings_in_weaviate(chunks: List[Chunk]) -> bool:
    """
    Store chunks with embeddings in Weaviate.
    
    Args:
        chunks: List of chunks with embeddings
        
    Returns:
        Success status
    """
    logger.info("=== Starting Weaviate Storage Test ===")
    
    # Filter chunks with embeddings
    chunks_with_embeddings = [c for c in chunks if c.embedding_vector]
    logger.info(f"Chunks with embeddings: {len(chunks_with_embeddings)}/{len(chunks)}")
    
    if not chunks_with_embeddings:
        logger.error("No chunks have embeddings to store")
        return False
    
    # Initialize Weaviate client
    logger.info("Connecting to Weaviate...")
    weaviate_client = WeaviateClient()
    weaviate_client.connect()
    
    try:
        # Store chunks in Weaviate
        stored_count = 0
        failed_count = 0
        
        for i, chunk in enumerate(chunks_with_embeddings):
            try:
                # Prepare chunk data
                chunk_dict = chunk.to_weaviate_dict()
                
                # Log details for first chunk
                if i == 0:
                    logger.debug(f"First chunk Weaviate data keys: {list(chunk_dict.keys())}")
                    if chunk.embedding_vector:
                        logger.debug(f"Embedding dimensions: {len(chunk.embedding_vector)}")
                
                # Store in Weaviate
                weaviate_client.create_object(
                    'Chunk',
                    chunk_dict,
                    chunk.embedding_vector
                )
                stored_count += 1
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Progress: {i + 1}/{len(chunks_with_embeddings)} stored")
                    
            except Exception as e:
                logger.error(f"Failed to store chunk {chunk.id}: {e}")
                failed_count += 1
                
                # Log detailed error for first failure
                if failed_count == 1:
                    logger.debug(f"Failed chunk details: {chunk_dict}")
        
        # Summary
        logger.info(f"=== Weaviate Storage Summary ===")
        logger.info(f"Successfully stored: {stored_count}")
        logger.info(f"Failed to store: {failed_count}")
        
        if stored_count > 0:
            success_rate = (stored_count / len(chunks_with_embeddings)) * 100
            logger.info(f"Storage success rate: {success_rate:.1f}%")
        
        return stored_count > 0
        
    finally:
        await weaviate_client.async_close()


async def main():
    """Main debug function."""
    parser = argparse.ArgumentParser(
        description="Debug embedding generation for Arete chunks"
    )
    parser.add_argument(
        "--document-id",
        type=str,
        help="Document ID to filter chunks (optional)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of chunks to process (default: 50)"
    )
    parser.add_argument(
        "--skip-storage",
        action="store_true",
        help="Skip Weaviate storage test"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Update log level if specified
    if args.log_level != "INFO":
        logging.getLogger().setLevel(getattr(logging, args.log_level))
        logger.setLevel(getattr(logging, args.log_level))
    
    logger.info("=" * 80)
    logger.info("ARETE EMBEDDING DEBUG TOOL")
    logger.info("=" * 80)
    
    # Load configuration
    config = get_settings()
    logger.info(f"Embedding Provider: {config.embedding_provider}")
    logger.info(f"Embedding Model: {config.embedding_model}")
    # Note: embedding_dimensions is provider-specific and may not always be set
    if hasattr(config, 'embedding_dimensions'):
        logger.info(f"Embedding Dimensions: {config.embedding_dimensions}")
    else:
        logger.info(f"Embedding Dimensions: Will be determined by provider/model")
    
    # Step 1: Fetch chunks from Neo4j
    logger.info("\n=== Step 1: Fetching Chunks from Neo4j ===")
    chunks_data = await fetch_chunks_from_neo4j(
        document_id=args.document_id,
        limit=args.limit
    )
    
    if not chunks_data:
        logger.error("No chunks found in Neo4j")
        return
    
    logger.info(f"Found {len(chunks_data)} chunks to process")
    
    # Show sample chunk info
    if chunks_data:
        first_chunk = chunks_data[0]
        logger.debug(f"Sample chunk keys: {list(first_chunk.keys())}")
        if 'text' in first_chunk:
            text_preview = first_chunk['text'][:100] + "..." if len(first_chunk['text']) > 100 else first_chunk['text']
            logger.debug(f"Sample text: {text_preview}")
    
    # Step 2: Generate embeddings
    logger.info("\n=== Step 2: Testing Embedding Generation ===")
    chunks_with_embeddings = await test_embedding_generation(chunks_data)
    
    if not chunks_with_embeddings:
        logger.error("No chunks processed successfully")
        return
    
    # Count successful embeddings
    success_count = sum(1 for c in chunks_with_embeddings if c.embedding_vector)
    logger.info(f"Successfully generated embeddings: {success_count}/{len(chunks_with_embeddings)}")
    
    # Step 3: Optionally test Weaviate storage
    if not args.skip_storage and success_count > 0:
        logger.info("\n=== Step 3: Testing Weaviate Storage ===")
        storage_success = await store_embeddings_in_weaviate(chunks_with_embeddings)
        
        if storage_success:
            logger.info("✅ Weaviate storage test successful")
        else:
            logger.error("❌ Weaviate storage test failed")
    elif args.skip_storage:
        logger.info("\n=== Step 3: Skipping Weaviate Storage (--skip-storage flag) ===")
    else:
        logger.warning("\n=== Step 3: Skipping Weaviate Storage (no embeddings) ===")
    
    logger.info("\n" + "=" * 80)
    logger.info("DEBUG SESSION COMPLETE")
    logger.info("=" * 80)


if __name__ == "__main__":
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    
    # Run the async main function
    asyncio.run(main())