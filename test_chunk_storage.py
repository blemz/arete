#!/usr/bin/env python3
"""Test chunk storage in Neo4j and Weaviate"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.arete.config import Settings
from src.arete.database.client import Neo4jClient
from src.arete.database.weaviate_client import WeaviateClient
from src.arete.models.chunk import Chunk
from src.arete.services.embedding_service import EmbeddingService

async def test_chunk_storage():
    """Test storing chunks in both Neo4j and Weaviate"""
    
    # Initialize configuration
    config = Settings()
    
    # Initialize clients
    neo4j_client = Neo4jClient(
        uri=config.neo4j_uri,
        auth=config.neo4j_auth
    )
    
    weaviate_client = WeaviateClient(
        url=config.weaviate_url,
        headers=config.weaviate_headers
    )
    
    # Initialize embedding service
    embedding_service = EmbeddingService(config)
    
    try:
        # Connect to databases
        print("Connecting to databases...")
        await neo4j_client.async_connect()
        weaviate_client.connect()
        print("✓ Connected to databases")
        
        # Create a test chunk
        test_text = "Socrates believed that the unexamined life is not worth living."
        test_chunk = Chunk(
            text=test_text,
            document_id="test-doc-001",
            chunk_number=1,
            start_pos=0,
            end_pos=len(test_text),
            metadata={"test": True}
        )
        
        # Generate embedding for the chunk
        print("\nGenerating embedding...")
        embedding = await embedding_service.async_generate_embeddings([test_text])
        if embedding and len(embedding) > 0:
            test_chunk.embedding_vector = embedding[0]
            print(f"✓ Generated {len(test_chunk.embedding_vector)}-dimensional embedding")
        else:
            print("✗ Failed to generate embedding")
            return False
        
        # Test Neo4j storage
        print("\n=== Testing Neo4j Chunk Storage ===")
        try:
            chunk_dict = test_chunk.to_neo4j_dict()
            print(f"Chunk dict keys: {chunk_dict.keys()}")
            
            # Store in Neo4j
            result = await neo4j_client.async_save_entity('Chunk', chunk_dict)
            print(f"✓ Chunk stored in Neo4j")
            
            # Verify storage
            async with neo4j_client.async_session() as session:
                query = "MATCH (c:Chunk {chunk_number: $chunk_number}) RETURN c LIMIT 1"
                result = await session.run(query, chunk_number=1)
                record = await result.single()
                if record:
                    print(f"✓ Chunk verified in Neo4j: {record['c']['text'][:50]}...")
                else:
                    print("✗ Could not verify chunk in Neo4j")
                    
        except Exception as e:
            print(f"✗ Neo4j storage failed: {e}")
            return False
        
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
            test_chunk_2 = Chunk(
                text="Knowledge is virtue, according to Socrates.",
                document_id="test-doc-001",
                chunk_number=2,
                start_pos=100,
                end_pos=145,
                metadata={"test": True}
            )
            
            # Generate embedding for second chunk
            embedding_2 = await embedding_service.async_generate_embeddings([test_chunk_2.text])
            if embedding_2 and len(embedding_2) > 0:
                test_chunk_2.embedding_vector = embedding_2[0]
                
                # Prepare batch
                batch_objects = [
                    {
                        'properties': test_chunk_2.to_weaviate_dict(),
                        'vector': test_chunk_2.embedding_vector
                    }
                ]
                
                # Store batch
                batch_ids = weaviate_client.create_objects_batch('Chunk', batch_objects)
                print(f"✓ Batch of {len(batch_ids)} chunks stored in Weaviate")
                
        except Exception as e:
            print(f"✗ Weaviate storage failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        print("\n=== All tests passed! ===")
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
    success = asyncio.run(test_chunk_storage())
    sys.exit(0 if success else 1)