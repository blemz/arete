#!/usr/bin/env python
"""
Test script for Ollama embedding integration with Qwen3-Embedding-8B.

Demonstrates how to use state-of-the-art embedding models via Ollama
for maximum quality philosophical text embeddings.
"""

import os
import time
from src.arete.services.embedding_factory import get_embedding_service
from src.arete.models.chunk import Chunk, ChunkType
from uuid import uuid4

# Philosophical test texts including multilingual content
PHILOSOPHICAL_TEXTS = [
    "Virtue is the excellence of character and the mean between extremes of excess and deficiency.",
    "The unexamined life is not worth living, according to Socrates.",
    "Justice is giving each person their due, as Plato argued in the Republic.",
    "ἀρετή ἐστι μεσότης - virtue is the mean between extremes (Aristotle, Greek)",
    "Virtus est animi habitus naturae modo atque rationi consentaneus - Virtue is a disposition of the soul in accordance with nature and reason (Latin)",
    "धर्म - dharma encompasses duty, righteousness, and natural law (Sanskrit concept)"
]

def test_ollama_embedding_service():
    """Test Ollama embedding service with Qwen3-Embedding-8B."""
    print("="*80)
    print("ARETE OLLAMA EMBEDDING TEST")
    print("="*80)
    print("Testing state-of-the-art Qwen3-Embedding-8B via Ollama")
    print()
    
    try:
        # Create Ollama service
        print("1. Initializing Ollama Embedding Service...")
        service = get_embedding_service(model_name="dengcao/qwen3-embedding-8b:q8_0")
        
        print(f"   Service type: {type(service).__name__}")
        print(f"   Model: {service.model_name}")
        print(f"   Base URL: {service.base_url}")
        
        # Check availability
        print("\n2. Checking Ollama availability...")
        if not service.is_available():
            print("   ✗ Ollama server not available at", service.base_url)
            print("   Please start Ollama: ollama serve")
            return False
        print("   ✓ Ollama server is available")
        
        # Check model availability
        print("\n3. Checking model availability...")
        if not service.is_model_available():
            print("   ✗ Qwen3-Embedding-8B model not found locally")
            print("   Attempting to pull model...")
            
            success = service.pull_model_if_needed()
            if not success:
                print("   ✗ Failed to pull model")
                print("   Please manually run: ollama pull dengcao/qwen3-embedding-8b:q8_0")
                return False
            print("   ✓ Model pulled successfully")
        else:
            print("   ✓ Qwen3-Embedding-8B model is available")
        
        # Get model info
        print("\n4. Model Information:")
        info = service.get_model_info()
        for key, value in info.items():
            if key not in ['error']:
                print(f"   {key}: {value}")
        
        # Test single embedding
        print("\n5. Testing single embedding generation...")
        test_text = PHILOSOPHICAL_TEXTS[0]
        print(f"   Text: {test_text[:60]}...")
        
        start_time = time.time()
        embedding = service.generate_embedding(test_text)
        embed_time = time.time() - start_time
        
        print(f"   ✓ Generated embedding in {embed_time:.3f} seconds")
        print(f"   ✓ Embedding dimension: {len(embedding)}")
        print(f"   ✓ First 5 values: {embedding[:5]}")
        
        # Test batch processing
        print("\n6. Testing batch embedding generation...")
        start_time = time.time()
        embeddings = service.generate_embeddings_batch(PHILOSOPHICAL_TEXTS[:3])
        batch_time = time.time() - start_time
        
        print(f"   ✓ Generated {len(embeddings)} embeddings in {batch_time:.3f} seconds")
        print(f"   ✓ Average time per embedding: {batch_time/len(embeddings):.3f} seconds")
        
        # Test multilingual capability
        print("\n7. Testing multilingual philosophical content...")
        multilingual_texts = PHILOSOPHICAL_TEXTS[3:6]  # Greek, Latin, Sanskrit
        
        for i, text in enumerate(multilingual_texts):
            try:
                embedding = service.generate_embedding(text)
                script = "Greek" if i == 0 else "Latin" if i == 1 else "Sanskrit"
                print(f"   ✓ {script} text embedded: {len(embedding)} dimensions")
            except Exception as e:
                print(f"   ✗ Failed to embed {script} text: {e}")
        
        # Test with Chunk models
        print("\n8. Testing Chunk model integration...")
        chunk = Chunk(
            text=PHILOSOPHICAL_TEXTS[1],
            document_id=uuid4(),
            position=0,
            start_char=0,
            end_char=len(PHILOSOPHICAL_TEXTS[1]),
            chunk_type=ChunkType.PARAGRAPH
        )
        
        chunk_embedding = service.generate_chunk_embedding(chunk)
        chunk.embedding_vector = chunk_embedding
        
        print(f"   ✓ Chunk embedded: {len(chunk.embedding_vector)} dimensions")
        print(f"   ✓ Chunk ready for Weaviate storage")
        
        # Performance summary
        print("\n9. Performance Summary:")
        final_stats = service.get_model_info()
        print(f"   Total embeddings generated: {final_stats['embeddings_generated']}")
        print(f"   Cache hits: {final_stats['cache_hits']}")
        print(f"   Cache hit rate: {final_stats['cache_hit_rate']:.1%}")
        print(f"   Model dimension: {final_stats.get('embedding_dimension', 'Unknown')}")
        
        print("\n" + "="*80)
        print("✓ OLLAMA EMBEDDING SERVICE TEST SUCCESSFUL")
        print("✓ Qwen3-Embedding-8B (MTEB Leaderboard #1) is ready for use!")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure Ollama is installed and running: ollama serve")
        print("2. Pull the model: ollama pull dengcao/qwen3-embedding-8b:q8_0")
        print("3. Check Ollama is accessible at http://localhost:11434")
        
        return False

def test_model_comparison():
    """Compare different embedding models."""
    print("\n" + "="*80)
    print("EMBEDDING MODEL COMPARISON")
    print("="*80)
    
    models_to_test = [
        ("sentence-transformers", "all-MiniLM-L6-v2", "Fast baseline"),
        ("sentence-transformers", "paraphrase-multilingual-mpnet-base-v2", "Current default"),
        ("ollama", "dengcao/qwen3-embedding-8b:q8_0", "SOTA via Ollama")
    ]
    
    test_text = "Virtue ethics emphasizes character over actions or consequences."
    
    for service_type, model_name, description in models_to_test:
        print(f"\nTesting {description} ({model_name}):")
        
        try:
            service = get_embedding_service(model_name=model_name)
            
            # Check availability
            if service_type == "ollama":
                if not service.is_available():
                    print("   ✗ Ollama not available, skipping")
                    continue
                if not service.is_model_available():
                    print("   ✗ Model not available, skipping")
                    continue
            else:
                if hasattr(service, 'load_model'):
                    service.load_model()
            
            # Time embedding generation
            start_time = time.time()
            embedding = service.generate_embedding(test_text)
            gen_time = time.time() - start_time
            
            print(f"   ✓ Dimensions: {len(embedding)}")
            print(f"   ✓ Generation time: {gen_time:.3f} seconds")
            print(f"   ✓ Service: {type(service).__name__}")
            
        except Exception as e:
            print(f"   ✗ Failed: {e}")

def main():
    """Run comprehensive Ollama embedding tests."""
    print("Starting Ollama Embedding Integration Tests...\n")
    
    # Test Ollama service
    ollama_success = test_ollama_embedding_service()
    
    # Compare models if Ollama worked
    if ollama_success:
        test_model_comparison()
    
    print(f"\n{'='*80}")
    print("HOW TO USE OLLAMA EMBEDDINGS:")
    print("="*80)
    print("1. Set in .env file:")
    print("   EMBEDDING_MODEL=dengcao/qwen3-embedding-8b:q8_0")
    print("2. Restart your application")
    print("3. Enjoy MTEB leaderboard #1 embedding quality!")
    print("="*80)

if __name__ == "__main__":
    main()