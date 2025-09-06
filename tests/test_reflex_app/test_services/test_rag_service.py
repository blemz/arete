"""Tests for RAG service."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.arete.ui.reflex_app.services.rag_service import RAGService


class TestRAGService:
    """Test cases for RAGService."""

    @pytest.fixture
    def rag_service(self, mock_neo4j_client, mock_weaviate_client, mock_embedding_service):
        """RAGService instance for testing."""
        return RAGService(
            neo4j_client=mock_neo4j_client,
            weaviate_client=mock_weaviate_client,
            embedding_service=mock_embedding_service
        )

    @pytest.mark.asyncio
    async def test_generate_response_success(self, rag_service, sample_chunk, sample_entity, mock_chat_response):
        """Test successful response generation."""
        # Mock retrieval components
        rag_service.weaviate_client.search_by_vector.return_value = [(sample_chunk, 0.85)]
        
        with patch.object(rag_service.neo4j_client, 'session') as mock_session:
            mock_result = Mock()
            mock_result.data.return_value = [{"entity": {"name": "Virtue", "type": "Concept"}}]
            mock_session.return_value.__enter__.return_value.run.return_value = mock_result
            
            with patch.object(rag_service, '_call_llm') as mock_llm:
                mock_llm.return_value = "Virtue, according to Socrates, is a form of knowledge."
                
                result = await rag_service.generate_response("What is virtue?")
                
                assert "response" in result
                assert "citations" in result
                assert "entities" in result
                assert result["response"] == "Virtue, according to Socrates, is a form of knowledge."

    @pytest.mark.asyncio
    async def test_generate_response_with_context(self, rag_service, sample_chunk):
        """Test response generation with conversation context."""
        rag_service.weaviate_client.search_by_vector.return_value = [(sample_chunk, 0.85)]
        
        context = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hello! How can I help you with philosophy today?"}
        ]
        
        with patch.object(rag_service, '_call_llm') as mock_llm:
            mock_llm.return_value = "Building on our previous discussion, virtue is..."
            
            result = await rag_service.generate_response("Tell me more about virtue", context=context)
            
            assert result["response"] == "Building on our previous discussion, virtue is..."
            mock_llm.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_similar_chunks(self, rag_service, sample_chunk):
        """Test similar chunk search."""
        rag_service.weaviate_client.search_by_vector.return_value = [
            (sample_chunk, 0.85),
            (sample_chunk, 0.75)
        ]
        rag_service.embedding_service.get_embedding.return_value = [0.1] * 1536
        
        results = await rag_service.search_similar_chunks("virtue", top_k=2)
        
        assert len(results) == 2
        assert results[0][1] == 0.85  # First result has higher score
        assert results[1][1] == 0.75  # Second result has lower score

    @pytest.mark.asyncio
    async def test_search_similar_chunks_empty_query(self, rag_service):
        """Test search with empty query."""
        results = await rag_service.search_similar_chunks("", top_k=5)
        
        assert results == []

    @pytest.mark.asyncio
    async def test_get_related_entities(self, rag_service):
        """Test related entity retrieval."""
        with patch.object(rag_service.neo4j_client, 'session') as mock_session:
            mock_result = Mock()
            mock_result.data.return_value = [
                {"entity": {"name": "Justice", "type": "Concept", "description": "Fairness and righteousness"}},
                {"entity": {"name": "Wisdom", "type": "Concept", "description": "Deep understanding and insight"}}
            ]
            mock_session.return_value.__enter__.return_value.run.return_value = mock_result
            
            entities = await rag_service.get_related_entities("virtue")
            
            assert len(entities) == 2
            assert entities[0]["name"] == "Justice"
            assert entities[1]["name"] == "Wisdom"

    @pytest.mark.asyncio
    async def test_get_related_entities_no_results(self, rag_service):
        """Test related entity retrieval with no results."""
        with patch.object(rag_service.neo4j_client, 'session') as mock_session:
            mock_result = Mock()
            mock_result.data.return_value = []
            mock_session.return_value.__enter__.return_value.run.return_value = mock_result
            
            entities = await rag_service.get_related_entities("nonexistent_concept")
            
            assert entities == []

    @pytest.mark.asyncio
    async def test_hybrid_search(self, rag_service, sample_chunk):
        """Test hybrid search combining vector and graph search."""
        # Mock vector search results
        rag_service.weaviate_client.search_by_vector.return_value = [(sample_chunk, 0.85)]
        
        # Mock graph search results
        with patch.object(rag_service.neo4j_client, 'session') as mock_session:
            mock_result = Mock()
            mock_result.data.return_value = [
                {"chunk": {"id": "chunk_1", "content": "Graph-retrieved chunk about virtue"}}
            ]
            mock_session.return_value.__enter__.return_value.run.return_value = mock_result
            
            results = await rag_service.hybrid_search("virtue", alpha=0.5)
            
            assert len(results) > 0
            # Should combine results from both vector and graph search

    @pytest.mark.asyncio
    async def test_rerank_results(self, rag_service, sample_chunk):
        """Test result reranking."""
        chunks = [
            (sample_chunk, 0.7),
            (sample_chunk, 0.8),
            (sample_chunk, 0.6)
        ]
        
        with patch.object(rag_service, '_calculate_relevance_score') as mock_relevance:
            mock_relevance.side_effect = [0.9, 0.85, 0.75]  # Reranked scores
            
            reranked = await rag_service.rerank_results(chunks, "virtue ethics")
            
            assert len(reranked) == 3
            assert reranked[0][1] == 0.9  # Highest reranked score first

    def test_build_context_from_chunks(self, rag_service, sample_chunk):
        """Test context building from retrieved chunks."""
        chunks = [
            (sample_chunk, 0.85),
            (sample_chunk, 0.75)
        ]
        
        context = rag_service.build_context_from_chunks(chunks, max_tokens=500)
        
        assert len(context) > 0
        assert "virtue" in context.lower() or "wisdom" in context.lower()
        assert len(context.split()) <= 500  # Respects token limit

    def test_extract_citations_from_chunks(self, rag_service, sample_chunk):
        """Test citation extraction from chunks."""
        chunks = [
            (sample_chunk, 0.85),
            (sample_chunk, 0.75)
        ]
        
        citations = rag_service.extract_citations_from_chunks(chunks)
        
        assert len(citations) == 2
        for citation in citations:
            assert "chunk_id" in citation
            assert "source_text" in citation
            assert "relevance_score" in citation

    @pytest.mark.asyncio
    async def test_generate_fallback_response(self, rag_service):
        """Test fallback response generation when LLM fails."""
        with patch.object(rag_service, '_call_llm') as mock_llm:
            mock_llm.side_effect = Exception("LLM service unavailable")
            
            with patch.object(rag_service, '_generate_template_response') as mock_template:
                mock_template.return_value = "I apologize, but I'm having trouble generating a response right now."
                
                result = await rag_service.generate_response("What is virtue?")
                
                assert "error" in result or "apologize" in result.get("response", "").lower()

    @pytest.mark.asyncio
    async def test_validate_and_clean_query(self, rag_service):
        """Test query validation and cleaning."""
        # Test normal query
        cleaned = rag_service.validate_and_clean_query("What is virtue?")
        assert cleaned == "What is virtue?"
        
        # Test query with special characters
        cleaned = rag_service.validate_and_clean_query("<script>What is virtue?</script>")
        assert "<script>" not in cleaned
        assert "What is virtue?" in cleaned
        
        # Test empty query
        cleaned = rag_service.validate_and_clean_query("")
        assert cleaned == ""

    @pytest.mark.asyncio
    async def test_get_conversation_context(self, rag_service):
        """Test conversation context extraction."""
        history = [
            {"role": "user", "content": "What is virtue?"},
            {"role": "assistant", "content": "Virtue is moral excellence..."},
            {"role": "user", "content": "How does it relate to happiness?"}
        ]
        
        context = rag_service.get_conversation_context(history, max_turns=2)
        
        assert len(context) <= 4  # 2 turns = 4 messages max
        assert any("virtue" in msg["content"].lower() for msg in context)

    @pytest.mark.asyncio
    async def test_handle_complex_query(self, rag_service, sample_chunk):
        """Test handling of complex multi-part queries."""
        complex_query = "What is virtue according to Aristotle and how does it differ from Plato's conception?"
        
        rag_service.weaviate_client.search_by_vector.return_value = [(sample_chunk, 0.85)]
        
        with patch.object(rag_service, '_parse_complex_query') as mock_parser:
            mock_parser.return_value = {
                "main_concepts": ["virtue"],
                "philosophers": ["Aristotle", "Plato"],
                "comparison_requested": True
            }
            
            with patch.object(rag_service, '_call_llm') as mock_llm:
                mock_llm.return_value = "Aristotle and Plato had different views on virtue..."
                
                result = await rag_service.generate_response(complex_query)
                
                assert "Aristotle" in result["response"] or "aristotle" in result["response"]

    @pytest.mark.asyncio
    async def test_cache_embeddings(self, rag_service):
        """Test embedding caching for performance."""
        query = "What is virtue?"
        
        # First call should generate embedding
        embedding1 = await rag_service._get_cached_embedding(query)
        
        # Second call should use cached embedding
        embedding2 = await rag_service._get_cached_embedding(query)
        
        assert embedding1 == embedding2
        # Verify caching is working if implemented

    @pytest.mark.asyncio
    async def test_error_recovery_mechanisms(self, rag_service):
        """Test error recovery and graceful degradation."""
        # Test when vector search fails
        rag_service.weaviate_client.search_by_vector.side_effect = Exception("Vector search failed")
        
        with patch.object(rag_service, '_fallback_to_keyword_search') as mock_fallback:
            mock_fallback.return_value = [("fallback_chunk", 0.5)]
            
            result = await rag_service.search_similar_chunks("virtue")
            
            # Should fall back to keyword search
            mock_fallback.assert_called_once()

    @pytest.mark.asyncio
    async def test_response_quality_validation(self, rag_service):
        """Test response quality validation."""
        with patch.object(rag_service, '_call_llm') as mock_llm:
            # Test low quality response
            mock_llm.return_value = "I don't know."
            
            with patch.object(rag_service, '_validate_response_quality') as mock_validator:
                mock_validator.return_value = False
                
                with patch.object(rag_service, '_regenerate_response') as mock_regenerate:
                    mock_regenerate.return_value = "Virtue is moral excellence according to classical philosophy."
                    
                    result = await rag_service.generate_response("What is virtue?")
                    
                    # Should regenerate low quality response
                    mock_regenerate.assert_called_once()

    def test_token_management(self, rag_service):
        """Test token counting and management."""
        text = "This is a test sentence for token counting."
        
        token_count = rag_service.count_tokens(text)
        
        assert isinstance(token_count, int)
        assert token_count > 0
        assert token_count < len(text)  # Tokens should be fewer than characters

    @pytest.mark.asyncio
    async def test_batch_processing(self, rag_service):
        """Test batch processing of multiple queries."""
        queries = [
            "What is virtue?",
            "What is justice?",
            "What is wisdom?"
        ]
        
        with patch.object(rag_service, 'generate_response') as mock_generate:
            mock_generate.side_effect = [
                {"response": "Virtue is...", "citations": [], "entities": []},
                {"response": "Justice is...", "citations": [], "entities": []},
                {"response": "Wisdom is...", "citations": [], "entities": []}
            ]
            
            results = await rag_service.batch_process_queries(queries)
            
            assert len(results) == 3
            assert all("response" in result for result in results)

    def test_response_formatting(self, rag_service):
        """Test response formatting and structure."""
        raw_response = "Virtue is moral excellence. It includes courage, temperance, and justice."
        citations = [{"chunk_id": "chunk_1", "source_text": "test", "relevance_score": 0.8}]
        entities = [{"name": "Virtue", "type": "Concept"}]
        
        formatted = rag_service.format_response(raw_response, citations, entities)
        
        assert "response" in formatted
        assert "citations" in formatted
        assert "entities" in formatted
        assert len(formatted["citations"]) == 1
        assert len(formatted["entities"]) == 1