#!/usr/bin/env python
"""
Example: Using Different Embedding Models in Arete

Shows how to easily switch between sentence-transformers and Ollama models
for different use cases and quality requirements.
"""

from src.arete.services.embedding_factory import get_embedding_service
from src.arete.models.chunk import Chunk, ChunkType
from uuid import uuid4
import time

def example_model_switching():
    """Demonstrate switching between different embedding models."""
    
    philosophical_text = "Aristotle's concept of virtue as the golden mean between extremes of excess and deficiency represents a foundational principle in ethical philosophy."
    
    print("Arete Embedding Model Usage Examples")
    print("=" * 60)
    
    # Example 1: Fast prototyping with MiniLM
    print("\n1. FAST PROTOTYPING - MiniLM (384 dims)")
    print("-" * 40)
    
    fast_service = get_embedding_service(model_name="all-MiniLM-L6-v2")
    if hasattr(fast_service, 'load_model'):
        fast_service.load_model()
    
    start = time.time()
    fast_embedding = fast_service.generate_embedding(philosophical_text)
    fast_time = time.time() - start
    
    print(f"Model: {fast_service.model_name}")
    print(f"Dimensions: {len(fast_embedding)}")
    print(f"Time: {fast_time:.3f} seconds")
    print(f"Use case: Quick development, English-only content")
    
    # Example 2: Production quality with multilingual MPNet  
    print("\n2. PRODUCTION QUALITY - Multilingual MPNet (768 dims)")
    print("-" * 40)
    
    quality_service = get_embedding_service(model_name="paraphrase-multilingual-mpnet-base-v2")
    if hasattr(quality_service, 'load_model'):
        quality_service.load_model()
    
    start = time.time()
    quality_embedding = quality_service.generate_embedding(philosophical_text)
    quality_time = time.time() - start
    
    print(f"Model: {quality_service.model_name}")
    print(f"Dimensions: {len(quality_embedding)}")
    print(f"Time: {quality_time:.3f} seconds")
    print(f"Use case: Production deployment, multilingual support")
    
    # Example 3: State-of-the-art with Qwen3 via Ollama
    print("\n3. STATE-OF-THE-ART - Qwen3 via Ollama (8192 dims)")
    print("-" * 40)
    
    try:
        sota_service = get_embedding_service(model_name="dengcao/qwen3-embedding-8b:q8_0")
        
        if sota_service.is_available() and sota_service.is_model_available():
            start = time.time()
            sota_embedding = sota_service.generate_embedding(philosophical_text)
            sota_time = time.time() - start
            
            print(f"Model: {sota_service.model_name}")
            print(f"Dimensions: {len(sota_embedding)}")
            print(f"Time: {sota_time:.3f} seconds")
            print(f"Use case: Maximum quality, research applications")
            
            # Quality comparison
            print(f"\nQuality Comparison:")
            print(f"- Fast model: {len(fast_embedding)} dims in {fast_time:.3f}s")
            print(f"- Quality model: {len(quality_embedding)} dims in {quality_time:.3f}s") 
            print(f"- SOTA model: {len(sota_embedding)} dims in {sota_time:.3f}s")
            
        else:
            print("Ollama/Qwen3 not available")
            print("To enable: ollama serve && ollama pull dengcao/qwen3-embedding-8b:q8_0")
            
    except Exception as e:
        print(f"Ollama service unavailable: {e}")
        print("Install Ollama and run: ollama pull dengcao/qwen3-embedding-8b:q8_0")

def example_environment_configuration():
    """Show how to configure models via environment variables."""
    
    print("\n" + "=" * 60)
    print("ENVIRONMENT CONFIGURATION")
    print("=" * 60)
    
    print("\nOption 1: .env file configuration")
    print("-" * 30)
    print("# For development (fast):")
    print("EMBEDDING_MODEL=all-MiniLM-L6-v2")
    print()
    print("# For production (quality + multilingual):")
    print("EMBEDDING_MODEL=paraphrase-multilingual-mpnet-base-v2")
    print()
    print("# For maximum quality (requires Ollama):")
    print("EMBEDDING_MODEL=dengcao/qwen3-embedding-8b:q8_0")
    
    print("\nOption 2: Runtime selection")
    print("-" * 30)
    print("# Python code:")
    print("service = get_embedding_service(model_name='your-model-choice')")
    print("embedding = service.generate_embedding('your text')")

def example_chunk_integration():
    """Show integration with Chunk models."""
    
    print("\n" + "=" * 60)
    print("CHUNK MODEL INTEGRATION") 
    print("=" * 60)
    
    # Create a philosophical text chunk
    chunk = Chunk(
        text="The concept of eudaimonia in Aristotelian ethics represents human flourishing achieved through the cultivation of virtue and the realization of one's potential.",
        document_id=uuid4(),
        position=0,
        start_char=0,
        end_char=151,
        chunk_type=ChunkType.PARAGRAPH
    )
    
    print(f"Original chunk: {chunk.text[:60]}...")
    print(f"Vectorizable text: {chunk.get_vectorizable_text()[:60]}...")
    
    # Get embedding service (uses default from config)
    service = get_embedding_service()
    if hasattr(service, 'load_model') and hasattr(service, 'is_model_loaded'):
        if not service.is_model_loaded():
            service.load_model()
    
    # Generate embedding for chunk
    embedding = service.generate_chunk_embedding(chunk)
    chunk.embedding_vector = embedding
    
    print(f"\nEmbedding generated:")
    print(f"- Model: {service.model_name}")
    print(f"- Dimensions: {len(embedding)}")
    print(f"- Chunk ready for Weaviate: {chunk.embedding_vector is not None}")
    
    # Show serialization
    weaviate_data = chunk.to_weaviate_dict()
    print(f"- Serialized keys: {list(weaviate_data.keys())[:5]}...")

if __name__ == "__main__":
    print("Running Arete Embedding Model Usage Examples...\n")
    
    example_model_switching()
    example_environment_configuration()
    example_chunk_integration()
    
    print("\n" + "=" * 60)
    print("✓ Examples completed!")
    print("Choose the model that best fits your quality/speed requirements.")
    print("=" * 60)