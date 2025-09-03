#!/usr/bin/env python3
"""
Check the actual content and language of documents in Weaviate.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def check_documents():
    """Check documents in Weaviate to see their language and content."""
    print("=== Checking Document Language and Content ===\n")
    
    try:
        import weaviate
        
        # Connect with minimal checks
        client = weaviate.connect_to_local(
            host="localhost", 
            port=8080,
            grpc_port=50051,
            skip_init_checks=True
        )
        
        print("Connected to Weaviate\n")
        
        # Get Document collection
        doc_collection = client.collections.get("Document")
        
        # Fetch all documents
        response = doc_collection.query.fetch_objects(limit=10)
        
        print(f"Found {len(response.objects)} documents:\n")
        
        for i, obj in enumerate(response.objects):
            props = obj.properties
            print(f"Document {i+1}:")
            print(f"  Title: {props.get('title', 'N/A')}")
            print(f"  Author: {props.get('author', 'N/A')}")
            print(f"  Language: {props.get('language', 'N/A')}")
            
            # Show first 200 chars of content to detect language
            content = props.get('content', '')
            if content:
                preview = content[:300].replace('\n', ' ')
                print(f"  Content preview: {preview}...")
            
            # Check metadata
            metadata = props.get('metadata', {})
            if metadata:
                print(f"  Metadata: {metadata}")
            
            print()
        
        client.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Check failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_documents()
    sys.exit(0 if success else 1)