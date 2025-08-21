#!/usr/bin/env python
"""
Test script to demonstrate configurable embedding models.

Shows how to test different models for philosophical content quality.
"""

import os
import time
from src.arete.services.embedding_service import EmbeddingService

# Test models ranked by quality/speed trade-off
TEST_MODELS = {
    "fast": "all-MiniLM-L6-v2",                              # 384 dims, English-only, fastest
    "multilingual_fast": "paraphrase-multilingual-MiniLM-L12-v2",  # 384 dims, multilingual, fast  
    "high_quality": "all-mpnet-base-v2",                     # 768 dims, English-only, best quality
    "multilingual_quality": "paraphrase-multilingual-mpnet-base-v2"  # 768 dims, multilingual, best overall
}

PHILOSOPHICAL_TEXTS = [
    "Virtue is the excellence of character and the mean between extremes.",
    "The unexamined life is not worth living, according to Socrates.",
    "Justice is giving each person their due, as Plato taught.",
    "Wisdom is knowing that you know nothing.",
    "ἀρετή ἐστι μεσότης - virtue is the mean between extremes"  # Greek text
]

def test_model(model_name: str, model_label: str):
    """Test a specific embedding model."""
    print(f"\n{'='*60}")
    print(f"Testing {model_label}: {model_name}")
    print('='*60)
    
    try:
        service = EmbeddingService(model_name=model_name)
        
        # Load model and time it
        start_time = time.time()
        service.load_model()
        load_time = time.time() - start_time
        
        print(f"✓ Model loaded in {load_time:.2f} seconds")
        print(f"✓ Embedding dimension: {service.get_embedding_dimension()}")
        
        # Test batch processing
        start_time = time.time()
        embeddings = service.generate_embeddings_batch(PHILOSOPHICAL_TEXTS[:3])  # Skip Greek for some models
        batch_time = time.time() - start_time
        
        print(f"✓ Generated {len(embeddings)} embeddings in {batch_time:.3f} seconds")
        print(f"✓ Average time per embedding: {batch_time/len(embeddings):.3f} seconds")
        
        # Test Greek text if multilingual
        if "multilingual" in model_name:
            greek_embedding = service.generate_embedding(PHILOSOPHICAL_TEXTS[4])
            print(f"✓ Greek text supported: {len(greek_embedding)} dimensions")
        
        return {
            "model": model_name,
            "load_time": load_time,
            "batch_time": batch_time,
            "avg_time": batch_time/len(embeddings),
            "dimension": service.get_embedding_dimension(),
            "multilingual": "multilingual" in model_name
        }
        
    except Exception as e:
        print(f"✗ Failed to test {model_name}: {e}")
        return None

def main():
    """Run embedding model comparison."""
    print("Arete Embedding Model Comparison")
    print("=" * 60)
    print("Testing different models for philosophical content...")
    
    results = []
    
    for label, model_name in TEST_MODELS.items():
        result = test_model(model_name, label)
        if result:
            results.append(result)
    
    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    
    for result in results:
        multilingual = "✓" if result["multilingual"] else "✗"
        print(f"{result['model'][:30]:<30} | {result['dimension']:>4}D | {result['avg_time']:>6.3f}s | {multilingual} ML")
    
    print(f"\n{'='*60}")
    print("RECOMMENDATION:")
    print("- For maximum quality: paraphrase-multilingual-mpnet-base-v2")
    print("- For speed: paraphrase-multilingual-MiniLM-L12-v2")
    print("- For English-only: all-mpnet-base-v2")
    print('='*60)
    
    print(f"\nTo change model, set in .env file:")
    print(f"EMBEDDING_MODEL=paraphrase-multilingual-mpnet-base-v2")

if __name__ == "__main__":
    main()