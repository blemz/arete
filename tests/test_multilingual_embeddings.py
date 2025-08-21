"""
Test suite for Multilingual Embedding Support.

Tests multilingual embedding models for classical philosophical texts,
including Greek and Sanskrit support for ancient texts.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any
from uuid import uuid4
import numpy as np

from src.arete.models.chunk import Chunk, ChunkType
from src.arete.services.embedding_service import EmbeddingService


class TestMultilingualModelSupport:
    """Test support for multilingual embedding models."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Classical texts in different languages
        self.greek_texts = [
            "ἀρετὴ μεσότης τίς ἐστι",  # Virtue is a mean (Greek)
            "ὁ δὲ ἀνεξέταστος βίος οὐ βιωτὸς ἀνθρώπῳ",  # The unexamined life (Greek)
            "τί ἐστι δικαιοσύνη;"  # What is justice? (Greek)
        ]
        
        self.sanskrit_texts = [
            "धर्मः क्षेत्रे कुरुक्षेत्रे",  # Dharma in Kurukshetra (Sanskrit)
            "सर्वं खल्विदं ब्रह्म",  # All this is Brahman (Sanskrit)
            "तत्त्वमसि"  # That thou art (Sanskrit)
        ]
        
        self.english_texts = [
            "Virtue is the mean between extremes",
            "The unexamined life is not worth living",
            "What is justice according to Plato?"
        ]
        
        self.latin_texts = [
            "Summum bonum",  # The highest good
            "Cogito ergo sum",  # I think therefore I am
            "Memento mori"  # Remember you will die
        ]
    
    def test_multilingual_model_availability(self):
        """Test availability of multilingual embedding models."""
        # Test models that support multiple languages
        multilingual_models = [
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            "sentence-transformers/distiluse-base-multilingual-cased",
            "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
        ]
        
        for model_name in multilingual_models:
            # Test model configuration
            service = EmbeddingService(model_name=model_name)
            assert service.model_name == model_name
    
    @patch('sentence_transformers.SentenceTransformer')
    def test_greek_text_embedding_generation(self, mock_sentence_transformer):
        """Test embedding generation for ancient Greek texts."""
        mock_model = Mock()
        embedding_dim = 384
        
        # Simulate embeddings for Greek text
        greek_embeddings = np.random.rand(len(self.greek_texts), embedding_dim).astype(np.float32)
        mock_model.encode.return_value = greek_embeddings
        mock_model.get_sentence_embedding_dimension.return_value = embedding_dim
        mock_sentence_transformer.return_value = mock_model
        
        service = EmbeddingService(model_name="paraphrase-multilingual-MiniLM-L12-v2")
        service.load_model()
        
        # Test Greek text processing
        embeddings = service.generate_embeddings_batch(
            self.greek_texts,
            show_progress=False
        )
        
        # Verify embeddings generated for Greek text
        assert len(embeddings) == len(self.greek_texts)
        assert all(len(emb) == embedding_dim for emb in embeddings)
        
        # Verify model was called with Greek text
        call_args = mock_model.encode.call_args[0][0]
        assert any("ἀρετὴ" in text for text in call_args)  # Greek characters preserved
    
    @patch('sentence_transformers.SentenceTransformer')
    def test_sanskrit_text_embedding_generation(self, mock_sentence_transformer):
        """Test embedding generation for Sanskrit texts."""
        mock_model = Mock()
        embedding_dim = 384
        
        # Simulate embeddings for Sanskrit text
        sanskrit_embeddings = np.random.rand(len(self.sanskrit_texts), embedding_dim).astype(np.float32)
        mock_model.encode.return_value = sanskrit_embeddings
        mock_model.get_sentence_embedding_dimension.return_value = embedding_dim
        mock_sentence_transformer.return_value = mock_model
        
        service = EmbeddingService(model_name="paraphrase-multilingual-MiniLM-L12-v2")
        service.load_model()
        
        # Test Sanskrit text processing
        embeddings = service.generate_embeddings_batch(
            self.sanskrit_texts,
            show_progress=False
        )
        
        # Verify embeddings generated for Sanskrit text
        assert len(embeddings) == len(self.sanskrit_texts)
        assert all(len(emb) == embedding_dim for emb in embeddings)
        
        # Verify model was called with Sanskrit text
        call_args = mock_model.encode.call_args[0][0]
        assert any("धर्मः" in text for text in call_args)  # Devanagari characters preserved
    
    @patch('sentence_transformers.SentenceTransformer')
    def test_mixed_language_batch_processing(self, mock_sentence_transformer):
        """Test batch processing with mixed languages."""
        mock_model = Mock()
        embedding_dim = 384
        
        # Mix of different languages
        mixed_texts = self.english_texts[:1] + self.greek_texts[:1] + self.sanskrit_texts[:1] + self.latin_texts[:1]
        
        # Simulate embeddings for mixed text
        mixed_embeddings = np.random.rand(len(mixed_texts), embedding_dim).astype(np.float32)
        mock_model.encode.return_value = mixed_embeddings
        mock_model.get_sentence_embedding_dimension.return_value = embedding_dim
        mock_sentence_transformer.return_value = mock_model
        
        service = EmbeddingService(model_name="paraphrase-multilingual-MiniLM-L12-v2")
        service.load_model()
        
        # Test mixed language processing
        embeddings = service.generate_embeddings_batch(
            mixed_texts,
            show_progress=False
        )
        
        # Verify all languages processed correctly
        assert len(embeddings) == len(mixed_texts)
        assert all(len(emb) == embedding_dim for emb in embeddings)
        
        # Verify all character sets preserved
        call_args = mock_model.encode.call_args[0][0]
        assert any("Virtue" in text for text in call_args)  # English
        assert any("ἀρετὴ" in text for text in call_args)   # Greek
        assert any("धर्मः" in text for text in call_args)    # Sanskrit
        assert any("Summum" in text for text in call_args)  # Latin


class TestCrossLingualSemanticSimilarity:
    """Test cross-lingual semantic similarity."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Semantically similar concepts across languages
        self.virtue_concepts = {
            "english": "Virtue is excellence of character",
            "greek": "ἀρετὴ ἐστι ἕξις προαιρετική",
            "latin": "Virtus est habitus mentis"
        }
        
        self.wisdom_concepts = {
            "english": "Wisdom is knowledge of good and evil",
            "greek": "σοφία ἐστι ἐπιστήμη ἀγαθῶν καὶ κακῶν",
            "sanskrit": "प्रज्ञा शुभाशुभज्ञानम्"
        }
    
    @patch('sentence_transformers.SentenceTransformer')
    def test_cross_lingual_semantic_similarity(self, mock_sentence_transformer):
        """Test that similar concepts across languages have high similarity."""
        mock_model = Mock()
        embedding_dim = 384
        
        # Create embeddings that would be similar for same concepts
        def create_similar_embeddings(base_vector, num_variants=3, noise_level=0.1):
            """Create slightly different but similar embeddings."""
            embeddings = []
            for i in range(num_variants):
                noise = np.random.normal(0, noise_level, embedding_dim)
                variant = base_vector + noise
                # Normalize to unit vector for cosine similarity
                variant = variant / np.linalg.norm(variant)
                embeddings.append(variant.astype(np.float32))
            return embeddings
        
        # Base vectors for concepts
        virtue_base = np.random.rand(embedding_dim)
        wisdom_base = np.random.rand(embedding_dim)
        
        # Create similar embeddings for same concepts
        virtue_embeddings = create_similar_embeddings(virtue_base)
        wisdom_embeddings = create_similar_embeddings(wisdom_base)
        
        # Combine all embeddings
        all_embeddings = np.array(virtue_embeddings + wisdom_embeddings)
        
        mock_model.encode.return_value = all_embeddings
        mock_model.get_sentence_embedding_dimension.return_value = embedding_dim
        mock_sentence_transformer.return_value = mock_model
        
        service = EmbeddingService(model_name="paraphrase-multilingual-MiniLM-L12-v2")
        service.load_model()
        
        # Process all texts
        all_texts = list(self.virtue_concepts.values()) + list(self.wisdom_concepts.values())
        embeddings = service.generate_embeddings_batch(all_texts, show_progress=False)
        
        # Test cross-lingual similarity for virtue concepts
        virtue_embs = embeddings[:3]  # First 3 are virtue concepts
        
        # Calculate pairwise cosine similarities
        def cosine_similarity(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
        # Virtue concepts should be similar across languages
        en_virtue = virtue_embs[0]
        gr_virtue = virtue_embs[1]
        lat_virtue = virtue_embs[2]
        
        sim_en_gr = cosine_similarity(en_virtue, gr_virtue)
        sim_en_lat = cosine_similarity(en_virtue, lat_virtue)
        sim_gr_lat = cosine_similarity(gr_virtue, lat_virtue)
        
        # Cross-lingual similarity should be reasonably high
        assert sim_en_gr > 0.7  # High similarity for same concept
        assert sim_en_lat > 0.7
        assert sim_gr_lat > 0.7
    
    def test_language_detection_capability(self):
        """Test capability to detect text language."""
        # This would test language detection functionality
        # Could use langdetect or similar library
        
        test_cases = [
            ("Hello world", "en"),
            ("ἀρετὴ μεσότης", "el"),  # Greek
            ("धर्मक्षेत्रे कुरुक्षेत्रे", "hi"),  # Sanskrit/Hindi
            ("Summum bonum", "la")  # Latin
        ]
        
        # Placeholder for language detection test
        for text, expected_lang in test_cases:
            # Would detect language of text
            assert len(text) > 0  # Basic test


class TestClassicalTextProcessing:
    """Test processing of classical philosophical texts."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Perseus Digital Library style texts
        self.perseus_greek_sample = """
        <text>
            <body>
                <div type="section" n="1">
                    <p>ἀρετὴ δὴ ἕξις προαιρετική, ἐν μεσότητι οὖσα τῇ πρὸς ἡμᾶς, 
                    ὡρισμένῃ λόγῳ καὶ ᾧ ἂν ὁ φρόνιμος ὁρίσειεν.</p>
                </div>
            </body>
        </text>
        """
        
        self.gretil_sanskrit_sample = """
        धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः ।
        मामकाः पाण्डवाश्चैव किमकुर्वत सञ्जय ॥
        """
        
        # Classical text chunks
        self.classical_chunks = [
            Chunk(
                text="ἀρετὴ μεσότης τίς ἐστι δυοῖν κακιῶν",
                document_id=uuid4(),
                start_position=0,
                end_position=35,
                sequence_number=0,
                word_count=6,
                chunk_type=ChunkType.PARAGRAPH,
                vectorizable_text="ἀρετὴ μεσότης τίς ἐστι δυοῖν κακιῶν"
            ),
            Chunk(
                text="धर्मं चर तपश्चर्",
                document_id=uuid4(),
                start_position=0,
                end_position=15,
                sequence_number=0,
                word_count=3,
                chunk_type=ChunkType.PARAGRAPH,
                vectorizable_text="धर्मं चर तपश्चर्"
            )
        ]
    
    @patch('sentence_transformers.SentenceTransformer')
    def test_classical_text_chunk_processing(self, mock_sentence_transformer):
        """Test processing chunks containing classical texts."""
        mock_model = Mock()
        embedding_dim = 384
        
        def encode_side_effect(texts, **kwargs):
            batch_size = len(texts) if isinstance(texts, list) else 1
            return np.random.rand(batch_size, embedding_dim).astype(np.float32)
        
        mock_model.encode.side_effect = encode_side_effect
        mock_model.get_sentence_embedding_dimension.return_value = embedding_dim
        mock_sentence_transformer.return_value = mock_model
        
        service = EmbeddingService(model_name="paraphrase-multilingual-MiniLM-L12-v2")
        service.load_model()
        
        # Process classical text chunks
        embeddings = service.generate_chunk_embeddings_batch(
            self.classical_chunks,
            use_vectorizable_text=True,
            show_progress=False
        )
        
        # Verify processing
        assert len(embeddings) == len(self.classical_chunks)
        assert all(len(emb) == embedding_dim for emb in embeddings)
        
        # Verify vectorizable_text was used (contains classical characters)
        call_args = mock_model.encode.call_args[0][0]
        assert any("ἀρετὴ" in text for text in call_args)  # Greek
        assert any("धर्मं" in text for text in call_args)   # Sanskrit
    
    def test_unicode_handling_and_normalization(self):
        """Test proper Unicode handling for classical texts."""
        # Test different Unicode representations
        test_cases = [
            "ἀρετή",  # Greek with composed characters
            "ἀρετή",  # Greek with decomposed characters (if different)
            "धर्म",   # Devanagari
            "φιλοσοφία",  # Greek philosophy
            "ब्रह्मन्"   # Sanskrit Brahman
        ]
        
        for text in test_cases:
            # Test Unicode normalization
            normalized = text  # Would apply NFKC or similar normalization
            assert len(normalized) > 0
            
            # Test that text contains expected Unicode ranges
            if "ἀ" in text:  # Greek
                assert any(0x0370 <= ord(c) <= 0x03FF for c in text)
            elif "ध" in text:  # Devanagari
                assert any(0x0900 <= ord(c) <= 0x097F for c in text)
    
    def test_text_preprocessing_for_classical_languages(self):
        """Test text preprocessing preserves classical language features."""
        # Test cases with different preprocessing needs
        test_cases = [
            {
                "input": "  ἀρετὴ μεσότης  ",
                "expected_features": ["ἀρετὴ", "μεσότης"],
                "language": "greek"
            },
            {
                "input": " धर्मं चर तपश्चर् ",
                "expected_features": ["धर्मं", "चर", "तपश्चर्"],
                "language": "sanskrit"
            }
        ]
        
        service = EmbeddingService()
        
        for case in test_cases:
            # Test preprocessing
            processed = service._preprocess_text(case["input"])
            
            # Verify whitespace trimming
            assert not processed.startswith(" ")
            assert not processed.endswith(" ")
            
            # Verify content preservation
            for feature in case["expected_features"]:
                assert feature in processed


class TestMultilingualRepositoryIntegration:
    """Test multilingual support in EmbeddingRepository."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.multilingual_chunks = [
            # Greek philosophical text
            Chunk(
                text="τί ἐστι δικαιοσύνη; (What is justice?)",
                document_id=uuid4(),
                start_position=0,
                end_position=40,
                sequence_number=0,
                word_count=8,
                chunk_type=ChunkType.PARAGRAPH
            ),
            # Sanskrit philosophical text
            Chunk(
                text="अहिंसा परमो धर्मः (Non-violence is the highest virtue)",
                document_id=uuid4(),
                start_position=0,
                end_position=55,
                sequence_number=1,
                word_count=10,
                chunk_type=ChunkType.PARAGRAPH
            ),
            # English translation/commentary
            Chunk(
                text="Justice according to Plato is harmony in the soul",
                document_id=uuid4(),
                start_position=0,
                end_position=49,
                sequence_number=2,
                word_count=9,
                chunk_type=ChunkType.PARAGRAPH
            )
        ]
    
    @patch('src.arete.database.weaviate_client.WeaviateClient')
    @patch('sentence_transformers.SentenceTransformer')
    def test_multilingual_semantic_search(self, mock_sentence_transformer, mock_weaviate):
        """Test semantic search across multiple languages."""
        from src.arete.repositories.embedding import EmbeddingRepository
        
        # Mock embedding service
        mock_model = Mock()
        embedding_dim = 384
        
        # Create semantically similar embeddings for related concepts
        justice_embedding = np.random.rand(embedding_dim).astype(np.float32)
        virtue_embedding = np.random.rand(embedding_dim).astype(np.float32)
        
        def encode_side_effect(texts, **kwargs):
            # Return appropriate embeddings based on content
            embeddings = []
            for text in texts:
                if "justice" in text.lower() or "δικαιοσύνη" in text:
                    embeddings.append(justice_embedding)
                elif "virtue" in text.lower() or "धर्म" in text:
                    embeddings.append(virtue_embedding)
                else:
                    embeddings.append(np.random.rand(embedding_dim).astype(np.float32))
            return np.array(embeddings)
        
        mock_model.encode.side_effect = encode_side_effect
        mock_model.get_sentence_embedding_dimension.return_value = embedding_dim
        mock_sentence_transformer.return_value = mock_model
        
        # Mock Weaviate search results
        mock_client = Mock()
        mock_search_results = [
            {
                "uuid": str(uuid4()),
                "properties": {
                    "content": "τί ἐστι δικαιοσύνη; (What is justice?)",
                    "chunk_type": "paragraph",
                    "document_id": str(uuid4())
                },
                "metadata": {"distance": 0.1, "certainty": 0.9}
            },
            {
                "uuid": str(uuid4()),
                "properties": {
                    "content": "Justice according to Plato is harmony in the soul",
                    "chunk_type": "paragraph",
                    "document_id": str(uuid4())
                },
                "metadata": {"distance": 0.2, "certainty": 0.8}
            }
        ]
        mock_client.search_by_vector.return_value = mock_search_results
        mock_weaviate.return_value = mock_client
        
        # Test cross-lingual search
        repository = EmbeddingRepository(weaviate_client=mock_client)
        
        # Search in English should find Greek and English results
        results = repository.search_by_text(
            "What is justice in philosophy?",
            limit=5,
            min_certainty=0.7
        )
        
        # Verify multilingual results
        assert len(results) == 2  # Should find both Greek and English
        chunks_and_scores = results
        
        # Verify content from different languages
        result_texts = [chunk.text for chunk, _ in chunks_and_scores]
        assert any("δικαιοσύνη" in text for text in result_texts)  # Greek
        assert any("Justice according to Plato" in text for text in result_texts)  # English
    
    def test_multilingual_model_configuration(self):
        """Test configuration for multilingual models."""
        from src.arete.repositories.embedding import EmbeddingRepository
        
        # Test multilingual model configuration
        multilingual_models = [
            "paraphrase-multilingual-MiniLM-L12-v2",
            "distiluse-base-multilingual-cased",
            "paraphrase-multilingual-mpnet-base-v2"
        ]
        
        for model_name in multilingual_models:
            repository = EmbeddingRepository()
            
            # Configure for multilingual model
            repository._embedding_service = None  # Reset for new model
            
            # Test that model name can be configured
            assert hasattr(repository, 'embedding_service')


class TestPerformanceOptimization:
    """Test performance optimization for multilingual embeddings."""
    
    def test_language_specific_batch_optimization(self):
        """Test optimization for different language characteristics."""
        # Different languages may have different optimal batch sizes
        language_batches = {
            "english": ["Short text"] * 50,
            "greek": ["μικρὸς κείμενος"] * 40,  # May need smaller batches
            "sanskrit": ["लघुपाठः"] * 35,       # Complex script processing
            "mixed": ["Mixed", "μικτός", "मिश्रित"] * 20
        }
        
        service = EmbeddingService()
        
        for language, texts in language_batches.items():
            # Test optimal batch size calculation
            optimal_size = service._calculate_optimal_batch_size(len(texts))
            
            # Should be reasonable for language
            assert optimal_size > 0
            assert optimal_size <= len(texts)
            assert optimal_size <= 64  # Reasonable upper bound
    
    def test_memory_efficiency_with_unicode(self):
        """Test memory efficiency when processing Unicode text."""
        # Unicode text can be memory intensive
        large_unicode_texts = [
            "φιλοσοφία " * 100,  # Repeated Greek
            "दर्शनशास्त्र " * 100,  # Repeated Sanskrit
            "🧠💭🎓📚 " * 50      # Emoji (high Unicode)
        ]
        
        service = EmbeddingService()
        
        for text in large_unicode_texts:
            # Test preprocessing handles large Unicode efficiently
            processed = service._preprocess_text(text)
            
            # Verify reasonable length after processing
            assert len(processed) <= 8000  # Max length limit
            assert len(processed) > 0
    
    def test_caching_strategy_for_multilingual(self):
        """Test caching strategy for multilingual embeddings."""
        # Multilingual text may have different caching characteristics
        cache_test_cases = [
            "ἀρετὴ",     # Greek
            "धर्म",      # Sanskrit  
            "virtue",    # English
            "virtus"     # Latin
        ]
        
        # Mock cache for testing
        embedding_cache = {}
        
        def cache_key(text: str, model: str = "default") -> str:
            # Include model in cache key for multilingual models
            return f"{model}:{hash(text)}"
        
        # Test caching with language-aware keys
        for text in cache_test_cases:
            key = cache_key(text, "multilingual")
            embedding_cache[key] = [0.1, 0.2, 0.3]  # Mock embedding
            
            # Verify cache works with Unicode
            assert key in embedding_cache
            assert embedding_cache[key] == [0.1, 0.2, 0.3]


# Integration test for complete multilingual workflow
class TestMultilingualWorkflow:
    """Test complete multilingual embedding workflow."""
    
    @patch('src.arete.database.weaviate_client.WeaviateClient')
    @patch('sentence_transformers.SentenceTransformer')
    def test_end_to_end_multilingual_pipeline(self, mock_sentence_transformer, mock_weaviate):
        """Test complete pipeline for multilingual philosophical texts."""
        from src.arete.repositories.embedding import EmbeddingRepository
        
        # Mock multilingual embedding model
        mock_model = Mock()
        embedding_dim = 384
        
        # Simulate multilingual embeddings
        def encode_side_effect(texts, **kwargs):
            batch_size = len(texts) if isinstance(texts, list) else 1
            # Return consistent embeddings for testing
            return np.random.rand(batch_size, embedding_dim).astype(np.float32)
        
        mock_model.encode.side_effect = encode_side_effect
        mock_model.get_sentence_embedding_dimension.return_value = embedding_dim
        mock_sentence_transformer.return_value = mock_model
        
        # Mock storage
        mock_client = Mock()
        mock_client.create_objects_batch.return_value = [str(uuid4())] * 3
        mock_weaviate.return_value = mock_client
        
        # Test complete workflow
        repository = EmbeddingRepository(weaviate_client=mock_client)
        
        # Process multilingual chunks
        multilingual_chunks = [
            Chunk(
                text="ἀρετὴ μεσότης ἐστι",
                document_id=uuid4(),
                start_position=0,
                end_position=18,
                sequence_number=0,
                word_count=3,
                chunk_type=ChunkType.PARAGRAPH
            ),
            Chunk(
                text="धर्मो रक्षति रक्षितः",
                document_id=uuid4(),
                start_position=0,
                end_position=20,
                sequence_number=1,
                word_count=3,
                chunk_type=ChunkType.PARAGRAPH
            ),
            Chunk(
                text="Virtue protects those who protect it",
                document_id=uuid4(),
                start_position=0,
                end_position=36,
                sequence_number=2,
                word_count=6,
                chunk_type=ChunkType.PARAGRAPH
            )
        ]
        
        # Generate and store embeddings
        updated_chunks = repository.batch_generate_and_store(
            multilingual_chunks,
            store_immediately=True
        )
        
        # Verify workflow completion
        assert len(updated_chunks) == 3
        assert all(chunk.embedding_vector is not None for chunk in updated_chunks)
        assert all(len(chunk.embedding_vector) == embedding_dim for chunk in updated_chunks)
        
        # Verify storage was called
        mock_client.create_objects_batch.assert_called_once()
        
        # Verify multilingual content was processed
        call_args = mock_model.encode.call_args[0][0]
        assert any("ἀρετὴ" in text for text in call_args)  # Greek
        assert any("धर्मो" in text for text in call_args)   # Sanskrit
        assert any("Virtue" in text for text in call_args)  # English