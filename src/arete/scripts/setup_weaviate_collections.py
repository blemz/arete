#!/usr/bin/env python3
"""
Setup Weaviate collections for Arete system.
Creates the Chunk collection with proper schema.
"""

import weaviate
from weaviate import connect_to_local
import weaviate.classes.config as wvc
import sys

def setup_chunk_collection():
    """Create the Chunk collection in Weaviate."""
    
    print("Connecting to Weaviate...")
    
    # Connect with extended timeout
    with connect_to_local(
        skip_init_checks=True,  # Skip gRPC checks that are failing
    ) as client:
        
        try:
            # Check if Chunk collection already exists
            existing_collections = client.collections.list_all()
            print(f"Existing collections: {existing_collections}")
            
            if "Chunk" in existing_collections:
                print("Chunk collection already exists, deleting and recreating...")
                client.collections.delete("Chunk")
            
            # Create Chunk collection with proper schema
            print("Creating Chunk collection...")
            
            chunk_collection = client.collections.create(
                name="Chunk",
                properties=[
                    wvc.Property(
                        name="chunk_id",
                        data_type=wvc.DataType.TEXT,
                        description="Unique identifier for the chunk"
                    ),
                    wvc.Property(
                        name="content",
                        data_type=wvc.DataType.TEXT,
                        description="Text content of the chunk"
                    ),
                    wvc.Property(
                        name="document_id",
                        data_type=wvc.DataType.TEXT,
                        description="ID of the parent document"
                    ),
                    wvc.Property(
                        name="chunk_type",
                        data_type=wvc.DataType.TEXT,
                        description="Type of chunk (paragraph, section, etc.)"
                    ),
                    wvc.Property(
                        name="position",
                        data_type=wvc.DataType.INT,
                        description="Position within the document"
                    ),
                    wvc.Property(
                        name="metadata",
                        data_type=wvc.DataType.OBJECT,
                        description="Additional metadata",
                        nested_properties=[
                            wvc.Property(
                                name="source",
                                data_type=wvc.DataType.TEXT
                            ),
                            wvc.Property(
                                name="page",
                                data_type=wvc.DataType.INT
                            ),
                            wvc.Property(
                                name="section",
                                data_type=wvc.DataType.TEXT
                            )
                        ]
                    )
                ],
                vectorizer_config=wvc.Configure.Vectorizer.none(),  # We'll provide vectors
                generative_config=None,
            )
            
            print("✅ Chunk collection created successfully")
            
            # Verify collection was created
            collections_after = client.collections.list_all()
            print(f"Collections after creation: {collections_after}")
            
            # Get collection info
            chunk_info = client.collections.get("Chunk")
            print(f"Chunk collection exists: {chunk_info is not None}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating Chunk collection: {e}")
            return False


if __name__ == "__main__":
    success = setup_chunk_collection()
    sys.exit(0 if success else 1)