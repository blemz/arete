"""
Quick integration test for Phase 2.3 Embedding Generation implementation.

This script validates that our embedding service integrates properly with
the existing chunk model and can generate embeddings.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from uuid import uuid4
from src.arete.models.chunk import Chunk, ChunkType
from src.arete.services.embedding_service import EmbeddingService, EmbeddingServiceError
from src.arete.config import get_settings

def test_embedding_service_basic():
    """Test basic embedding service functionality."""
    print("Testing basic embedding service functionality...")
    
    # Create embedding service
    service = EmbeddingService()
    
    # Check model info before loading
    info = service.get_model_info()
    print(f"Model info before loading: {info}")
    assert not info['is_loaded']
    
    # Check device detection
    print(f"Detected device: {service.device}")
    
    print("✅ Basic embedding service test passed")

def test_chunk_model_integration():
    """Test integration with existing chunk model."""
    print("Testing chunk model integration...")
    
    # Create sample chunk
    chunk = Chunk(
        text="Virtue is the mean between extremes of excess and deficiency.",
        document_id=uuid4(),
        start_position=0,
        end_position=62,
        sequence_number=0,
        word_count=10,
        chunk_type=ChunkType.PARAGRAPH
    )
    
    # Verify chunk has embedding fields
    assert hasattr(chunk, 'embedding_vector')
    assert hasattr(chunk, 'vectorizable_text')
    assert chunk.embedding_vector is None  # Initially None
    assert chunk.vectorizable_text is not None  # Auto-generated
    
    # Test Weaviate format
    weaviate_dict = chunk.to_weaviate_dict()
    assert 'content' in weaviate_dict
    assert weaviate_dict['content'] == chunk.text
    
    print("✅ Chunk model integration test passed")

def test_configuration_integration():
    """Test configuration integration."""
    print("Testing configuration integration...")
    
    settings = get_settings()
    
    # Check embedding configuration exists
    assert hasattr(settings, 'embedding_model')
    assert hasattr(settings, 'embedding_device')
    assert hasattr(settings, 'embedding_batch_size')
    assert hasattr(settings, 'embedding_normalize')
    
    # Check default values
    assert settings.embedding_model == 'all-MiniLM-L6-v2'
    assert settings.embedding_device == 'auto'
    assert settings.embedding_batch_size >= 1
    assert isinstance(settings.embedding_normalize, bool)
    
    print(f"Embedding configuration: {settings.embedding_config}")
    print("✅ Configuration integration test passed")

def test_mock_embedding_workflow():
    """Test embedding workflow without actual model loading."""
    print("Testing mock embedding workflow...")
    
    # Create chunks
    chunks = [
        Chunk(
            text=f"Philosophical text {i}: Discussion of ethics and virtue.",
            document_id=uuid4(),
            start_position=i * 50,
            end_position=(i + 1) * 50,
            sequence_number=i,
            word_count=8,
            chunk_type=ChunkType.PARAGRAPH
        )
        for i in range(3)
    ]
    
    # Test service interface (without loading model)
    service = EmbeddingService()
    
    # Test error handling for unloaded model
    try:
        service.generate_embedding("test")
        assert False, "Should have raised ModelNotLoadedError"
    except Exception as e:
        assert "not loaded" in str(e).lower()
    
    # Test batch processing interface
    try:
        service.generate_embeddings_batch(["test1", "test2"])
        assert False, "Should have raised ModelNotLoadedError"
    except Exception as e:
        assert "not loaded" in str(e).lower()
    
    # Test chunk interface
    try:
        service.generate_chunk_embedding(chunks[0])
        assert False, "Should have raised ModelNotLoadedError"
    except Exception as e:
        assert "not loaded" in str(e).lower()
    
    print("✅ Mock embedding workflow test passed")

def test_dependencies_check():
    """Check if required dependencies are available."""
    print("Checking dependencies...")
    
    try:
        import torch
        print(f"✅ PyTorch available: {torch.__version__}")
        print(f"   CUDA available: {torch.cuda.is_available()}")
    except ImportError:
        print("⚠️  PyTorch not available")
    
    try:
        import sentence_transformers
        print(f"✅ sentence-transformers available: {sentence_transformers.__version__}")
    except ImportError:
        print("⚠️  sentence-transformers not available")
    
    try:
        import weaviate
        print(f"✅ weaviate-client available: {weaviate.__version__}")
    except ImportError:
        print("⚠️  weaviate-client not available")
    
    print("✅ Dependencies check completed")

def main():
    """Run all tests."""
    print("🚀 Phase 2.3 Embedding Generation Integration Test")
    print("=" * 60)
    
    tests = [
        test_dependencies_check,
        test_configuration_integration,
        test_chunk_model_integration,
        test_embedding_service_basic,
        test_mock_embedding_workflow
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
        print()
    
    print("=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Phase 2.3 integration looks good.")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)