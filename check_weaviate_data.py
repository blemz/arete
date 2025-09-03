#!/usr/bin/env python3
"""
Check what data is actually in Weaviate collections.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def check_weaviate_data():
    """Check what's in Weaviate collections."""
    print("=== Checking Weaviate Data ===\n")
    
    try:
        import weaviate
        
        # Connect directly with minimal checks
        client = weaviate.connect_to_local(
            host="localhost", 
            port=8080,
            grpc_port=50051,
            skip_init_checks=True  # Skip OIDC and other checks
        )
        
        print("Connected to Weaviate\n")
        
        # Check if collections exist
        try:
            collections = client.collections.list_all()
            print(f"Collections found: {collections}")
            
            # Check Chunk collection specifically
            if "Chunk" in collections:
                chunk_collection = client.collections.get("Chunk")
                
                # Get object count
                response = chunk_collection.aggregate.over_all(total_count=True)
                count = response.total_count if hasattr(response, 'total_count') else 0
                print(f"\nChunk collection has {count} objects")
                
                # Try to fetch a few objects
                if count > 0:
                    print("\nSample chunks:")
                    objects = chunk_collection.query.fetch_objects(limit=3)
                    for i, obj in enumerate(objects.objects):
                        props = obj.properties
                        content = props.get("content", "")[:100] + "..." if props.get("content") else "No content"
                        print(f"  Chunk {i+1}: {content}")
            else:
                print("Chunk collection does not exist!")
                
            # Check Document collection
            if "Document" in collections:
                doc_collection = client.collections.get("Document")
                response = doc_collection.aggregate.over_all(total_count=True)
                count = response.total_count if hasattr(response, 'total_count') else 0
                print(f"\nDocument collection has {count} objects")
                
                if count > 0:
                    print("\nSample documents:")
                    objects = doc_collection.query.fetch_objects(limit=3)
                    for i, obj in enumerate(objects.objects):
                        props = obj.properties
                        title = props.get("title", "No title")
                        author = props.get("author", "No author")
                        language = props.get("language", "No language")
                        content_preview = props.get("content", "")[:200] + "..." if props.get("content") else "No content"
                        print(f"  Document {i+1}:")
                        print(f"    Title: {title}")
                        print(f"    Author: {author}")
                        print(f"    Language: {language}")
                        print(f"    Content preview: {content_preview}")
                        print()
            else:
                print("Document collection does not exist!")
                
            # Check Entity collection  
            if "Entity" in collections:
                entity_collection = client.collections.get("Entity")
                response = entity_collection.aggregate.over_all(total_count=True)
                count = response.total_count if hasattr(response, 'total_count') else 0
                print(f"\nEntity collection has {count} objects")
            else:
                print("Entity collection does not exist!")
                
        except Exception as e:
            print(f"Error checking collections: {str(e)}")
            
        client.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Check failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_weaviate_data()
    sys.exit(0 if success else 1)