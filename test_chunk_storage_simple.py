#!/usr/bin/env python3
"""Simple test for chunk storage without embeddings"""

import asyncio
import sys
from pathlib import Path
import numpy as np
import io

# Fix Unicode on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.arete.config import Settings
from src.arete.database.client import Neo4jClient
from src.arete.database.weaviate_client import WeaviateClient
from src.arete.models.chunk import Chunk, ChunkType

async def test_simple_chunk_storage():
    """Test storing chunks with mock embeddings"""
    
    # Initialize configuration
    config = Settings()
    
    # Initialize clients
    neo4j_client = Neo4jClient(
        uri=config.neo4j_uri,
        auth=config.neo4j_auth
    )
    
    weaviate_client = WeaviateClient(
        url=config.weaviate_url,
        headers=None
    )
    
    try:
        # Connect to databases
        print("Connecting to databases...")
        await neo4j_client.async_connect()
        weaviate_client.connect()
        print("✓ Connected to databases")
        
        # Create a test chunk with mock embedding
        import uuid
        test_text = "Socrates believed that the unexamined life is not worth living."
        test_chunk = Chunk(
            text=test_text,
            document_id=uuid.uuid4(),
            position=0,
            start_char=0,
            end_char=len(test_text),
            chunk_type=ChunkType.SEMANTIC,
            metadata={"test": True}
        )
        
        # Use a mock embedding (4096 dimensions as expected)
        test_chunk.embedding_vector = [0.1] * 4096
        print(f"✓ Created test chunk with {len(test_chunk.embedding_vector)}-dimensional mock embedding")
        
        # Test Neo4j storage
        print("\n=== Testing Neo4j Chunk Storage ===")
        try:
            # Store in Neo4j using the new chunk-specific method
            result = await neo4j_client.async_save_chunk(test_chunk)
            print(f"✓ Chunk stored in Neo4j: {result}")
            
            # Test batch method with a single chunk
            batch_result = await neo4j_client.async_batch_save_chunks([test_chunk])
            print(f"✓ Batch save completed with {len(batch_result)} chunks")
            
            # Verify storage
            async with neo4j_client.async_session() as session:
                query = "MATCH (c:Chunk {position: $position}) RETURN c LIMIT 1"
                result = await session.run(query, position=0)
                record = await result.single()
                if record:
                    print(f"✓ Chunk verified in Neo4j: {record['c']['text'][:50]}...")
                else:
                    print("✗ Could not verify chunk in Neo4j")
                    
        except Exception as e:
            print(f"✗ Neo4j storage failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test Weaviate storage
        print("\n=== Testing Weaviate Chunk Storage ===")
        try:
            # Test single object creation
            chunk_dict = test_chunk.to_weaviate_dict()
            print(f"Weaviate dict keys: {chunk_dict.keys()}")
            
            obj_id = weaviate_client.create_object(
                class_name='Chunk',
                properties=chunk_dict,
                vector=test_chunk.embedding_vector
            )
            print(f"✓ Single chunk stored in Weaviate with ID: {obj_id}")
            
            # Test batch creation
            test_chunks = []
            doc_id = uuid.uuid4()
            for i in range(3):
                chunk_text = f"Test chunk {i+2}: Knowledge is virtue."
                chunk = Chunk(
                    text=chunk_text,
                    document_id=doc_id,
                    position=i+1,
                    start_char=100 * (i+1),
                    end_char=100 * (i+1) + len(chunk_text),
                    chunk_type=ChunkType.SEMANTIC,
                    metadata={"test": True}
                )
                chunk.embedding_vector = [0.2 + i*0.1] * 4096
                test_chunks.append(chunk)
            
            # Prepare batch
            batch_objects = [
                {
                    'properties': chunk.to_weaviate_dict(),
                    'vector': chunk.embedding_vector
                }
                for chunk in test_chunks
            ]
            
            # Store batch
            batch_ids = weaviate_client.create_objects_batch('Chunk', batch_objects)
            print(f"✓ Batch of {len(batch_ids)} chunks stored in Weaviate")
            print(f"   IDs: {batch_ids[:2]}..." if len(batch_ids) > 2 else f"   IDs: {batch_ids}")
                
        except Exception as e:
            print(f"✗ Weaviate storage failed: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n=== Tests completed! ===")
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up connections
        await neo4j_client.async_close()
        weaviate_client.close()
        print("\nConnections closed.")

if __name__ == "__main__":
    success = asyncio.run(test_simple_chunk_storage())
    sys.exit(0 if success else 1)