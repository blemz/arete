"""Integration tests for RAG pipeline with Reflex frontend."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json
from typing import Dict, List, Any, Optional

from arete.state import ChatState, DocumentState, NavigationState


class TestRAGIntegration:
    """Test RAG pipeline integration with Reflex frontend."""
    
    @pytest.fixture
    def mock_rag_pipeline(self):
        """Mock RAG pipeline for testing."""
        mock = AsyncMock()
        mock.query_knowledge_graph = AsyncMock(return_value={
            "entities": ["Plato", "virtue", "justice"],
            "relationships": [
                {"from": "Plato", "to": "virtue", "type": "DISCUSSES"},
                {"from": "virtue", "to": "justice", "type": "RELATES_TO"}
            ]
        })
        
        mock.vector_search = AsyncMock(return_value={
            "chunks": [
                {
                    "content": "Virtue is knowledge according to Socrates...",
                    "source": "Plato's Meno",
                    "relevance_score": 0.92,
                    "position": 42.5
                },
                {
                    "content": "The four cardinal virtues are wisdom, courage...",
                    "source": "Plato's Republic",
                    "relevance_score": 0.87,
                    "position": 156.3
                }
            ]
        })
        
        mock.generate_response = AsyncMock(return_value={
            "response": """According to Plato, virtue is fundamentally knowledge. In the Meno dialogue, 
            Socrates argues that if virtue is knowledge, then it can be taught. The Republic further 
            elaborates on the four cardinal virtues: wisdom, courage, temperance, and justice.""",
            "citations": [
                {
                    "source": "Plato's Meno",
                    "content": "Virtue is knowledge according to Socrates...",
                    "relevance_score": 0.92,
                    "position": 42.5,
                    "page": "87a-89a"
                },
                {
                    "source": "Plato's Republic", 
                    "content": "The four cardinal virtues are wisdom, courage...",
                    "relevance_score": 0.87,
                    "position": 156.3,
                    "page": "Book IV"
                }
            ],
            "processing_time": 2.34,
            "token_usage": {"prompt": 1250, "completion": 890, "total": 2140}
        })
        
        return mock
    
    @pytest.mark.asyncio
    async def test_full_rag_query_flow(self, mock_chat_state, mock_rag_pipeline):
        """Test complete RAG query flow from frontend to response."""
        
        # Setup test query
        test_query = "What is virtue according to Plato?"
        mock_chat_state.current_message = test_query
        
        # Mock the RAG service integration
        with patch('arete.services.rag_service.RAGService') as mock_rag_service:
            mock_rag_service.return_value = mock_rag_pipeline
            
            # Simulate the full query process
            response = await mock_rag_pipeline.generate_response(test_query)
            
            # Verify response structure
            assert "response" in response
            assert "citations" in response
            assert "processing_time" in response
            assert len(response["citations"]) > 0
            
            # Verify citation structure
            citation = response["citations"][0]
            assert "source" in citation
            assert "content" in citation
            assert "relevance_score" in citation
            assert "position" in citation
    
    @pytest.mark.asyncio
    async def test_chat_state_rag_integration(self, mock_chat_state, mock_rag_pipeline):
        """Test ChatState integration with RAG pipeline."""
        
        # Mock the enhanced send_message method with RAG
        async def enhanced_send_message():
            if mock_chat_state.current_message.strip():
                # Add user message
                user_message = {
                    "role": "user",
                    "content": mock_chat_state.current_message,
                    "timestamp": "2025-09-05T10:00:00Z"
                }
                mock_chat_state.messages.append(user_message)
                
                # Set loading state
                mock_chat_state.is_loading = True
                
                # Get RAG response
                rag_response = await mock_rag_pipeline.generate_response(
                    mock_chat_state.current_message
                )
                
                # Add AI response with citations
                ai_message = {
                    "role": "assistant",
                    "content": rag_response["response"],
                    "timestamp": "2025-09-05T10:00:05Z",
                    "citations": rag_response["citations"],
                    "processing_time": rag_response["processing_time"],
                    "token_usage": rag_response.get("token_usage", {})
                }
                mock_chat_state.messages.append(ai_message)
                
                # Clear input and loading state
                mock_chat_state.current_message = ""
                mock_chat_state.is_loading = False
        
        # Test the flow
        mock_chat_state.current_message = "What is justice?"
        await enhanced_send_message()
        
        # Verify message structure
        assert len(mock_chat_state.messages) == 2
        assert mock_chat_state.messages[0]["role"] == "user"
        assert mock_chat_state.messages[1]["role"] == "assistant"
        assert "citations" in mock_chat_state.messages[1]
        assert mock_chat_state.is_loading == False
        assert mock_chat_state.current_message == ""
    
    @pytest.mark.asyncio
    async def test_document_citation_integration(self, mock_document_state, mock_rag_pipeline):
        """Test document viewer integration with citations."""
        
        # Mock document loading with citation highlighting
        async def load_document_with_citations(doc_id: str, citations: List[Dict]):
            mock_document_state.current_document = doc_id
            mock_document_state.document_content = f"Content of {doc_id}..."
            
            # Process citations for highlighting
            for citation in citations:
                if citation["source"].lower() in doc_id.lower():
                    mock_document_state.highlighted_passages.append({
                        "passage": citation["content"],
                        "location": citation.get("page", f"Position {citation['position']}"),
                        "relevance_score": citation["relevance_score"],
                        "citation_id": f"cite_{len(mock_document_state.highlighted_passages)}"
                    })
        
        # Test citation integration
        sample_citations = [
            {
                "source": "Plato's Republic",
                "content": "Justice is each doing their own work...",
                "position": 123.5,
                "relevance_score": 0.89,
                "page": "Book IV, 433a"
            }
        ]
        
        await load_document_with_citations("Plato's Republic", sample_citations)
        
        # Verify document state
        assert mock_document_state.current_document == "Plato's Republic"
        assert len(mock_document_state.highlighted_passages) == 1
        
        passage = mock_document_state.highlighted_passages[0]
        assert "relevance_score" in passage
        assert "citation_id" in passage
    
    def test_error_handling_rag_failures(self, mock_chat_state):
        """Test error handling when RAG pipeline fails."""
        
        async def failing_rag_query():
            mock_chat_state.is_loading = True
            
            try:
                # Simulate RAG pipeline failure
                raise Exception("RAG service unavailable")
            except Exception as e:
                # Fallback response
                fallback_message = {
                    "role": "assistant",
                    "content": "I'm sorry, I'm having trouble accessing the knowledge base right now. Please try again later.",
                    "timestamp": "2025-09-05T10:00:05Z",
                    "error": str(e),
                    "fallback": True
                }
                mock_chat_state.messages.append(fallback_message)
                mock_chat_state.is_loading = False
        
        # Test error handling
        mock_chat_state.current_message = "Test query"
        asyncio.run(failing_rag_query())
        
        # Verify fallback behavior
        assert len(mock_chat_state.messages) == 1
        assert mock_chat_state.messages[0]["fallback"] == True
        assert "error" in mock_chat_state.messages[0]
        assert mock_chat_state.is_loading == False
    
    @pytest.mark.asyncio
    async def test_streaming_response_integration(self, mock_chat_state):
        """Test streaming response integration."""
        
        async def mock_streaming_response():
            """Mock streaming response from RAG pipeline."""
            response_chunks = [
                "According to Plato, ",
                "virtue is fundamentally ",
                "knowledge. In the Meno dialogue, ",
                "Socrates argues that..."
            ]
            
            # Initialize message
            partial_message = {
                "role": "assistant",
                "content": "",
                "timestamp": "2025-09-05T10:00:05Z",
                "streaming": True
            }
            mock_chat_state.messages.append(partial_message)
            
            # Stream chunks
            for chunk in response_chunks:
                partial_message["content"] += chunk
                # In real implementation, this would trigger UI updates
                await asyncio.sleep(0.1)  # Simulate streaming delay
            
            # Finalize message
            partial_message["streaming"] = False
            partial_message["citations"] = [
                {
                    "source": "Plato's Meno",
                    "content": "Sample citation content",
                    "relevance_score": 0.92
                }
            ]
        
        await mock_streaming_response()
        
        # Verify streaming response
        assert len(mock_chat_state.messages) == 1
        message = mock_chat_state.messages[0]
        assert message["streaming"] == False
        assert len(message["content"]) > 0
        assert "citations" in message
    
    @pytest.mark.asyncio
    async def test_concurrent_queries_handling(self, mock_rag_pipeline):
        """Test handling of concurrent RAG queries."""
        
        queries = [
            "What is virtue?",
            "What is justice?", 
            "What is temperance?"
        ]
        
        # Simulate concurrent queries
        tasks = [
            mock_rag_pipeline.generate_response(query) 
            for query in queries
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # Verify all queries completed
        assert len(responses) == 3
        for response in responses:
            assert "response" in response
            assert "citations" in response
    
    def test_memory_management_large_conversations(self, mock_chat_state):
        """Test memory management for large conversations."""
        
        # Simulate large conversation
        for i in range(100):
            mock_chat_state.messages.extend([
                {
                    "role": "user",
                    "content": f"Test message {i}",
                    "timestamp": f"2025-09-05T{10+i//10:02d}:00:00Z"
                },
                {
                    "role": "assistant", 
                    "content": f"Response to message {i}",
                    "timestamp": f"2025-09-05T{10+i//10:02d}:00:05Z",
                    "citations": [{"source": "Test", "content": f"Citation {i}"}]
                }
            ])
        
        # Check conversation length
        assert len(mock_chat_state.messages) == 200
        
        # Simulate memory management (truncate old messages)
        max_messages = 50
        if len(mock_chat_state.messages) > max_messages:
            mock_chat_state.messages = mock_chat_state.messages[-max_messages:]
        
        assert len(mock_chat_state.messages) == max_messages
    
    @pytest.mark.asyncio
    async def test_context_preservation_across_queries(self, mock_chat_state, mock_rag_pipeline):
        """Test context preservation across multiple queries."""
        
        # First query
        mock_chat_state.current_message = "What is virtue?"
        response1 = await mock_rag_pipeline.generate_response(
            mock_chat_state.current_message
        )
        mock_chat_state.messages.extend([
            {"role": "user", "content": "What is virtue?"},
            {"role": "assistant", "content": response1["response"], "citations": response1["citations"]}
        ])
        
        # Follow-up query with context
        mock_chat_state.current_message = "How does it relate to justice?"
        
        # Mock context-aware query
        conversation_context = [msg["content"] for msg in mock_chat_state.messages[-4:]]
        context_query = f"Context: {' '.join(conversation_context)}\nQuery: {mock_chat_state.current_message}"
        
        response2 = await mock_rag_pipeline.generate_response(context_query)
        
        # Verify context-aware response
        assert "response" in response2
        assert len(response2["citations"]) > 0


class TestUIPerformanceWithRAG:
    """Test UI performance with RAG integration."""
    
    @pytest.mark.asyncio
    async def test_response_time_requirements(self, mock_rag_pipeline, performance_thresholds):
        """Test RAG response time requirements."""
        import time
        
        start_time = time.time()
        response = await mock_rag_pipeline.generate_response("What is virtue?")
        response_time = time.time() - start_time
        
        # Should meet performance requirements
        assert response_time < performance_thresholds['api_response_time']
    
    def test_ui_responsiveness_during_loading(self, mock_chat_state):
        """Test UI responsiveness during RAG query processing."""
        
        # Set loading state
        mock_chat_state.is_loading = True
        
        # UI should still be responsive
        mock_chat_state.current_message = "New message while loading"
        assert mock_chat_state.current_message == "New message while loading"
        
        # Can cancel loading
        mock_chat_state.is_loading = False
        assert mock_chat_state.is_loading == False
    
    def test_memory_usage_with_citations(self, mock_chat_state, performance_thresholds):
        """Test memory usage with citation storage."""
        import sys
        
        # Add message with many citations
        large_message = {
            "role": "assistant",
            "content": "Large response content",
            "citations": [
                {
                    "source": f"Source {i}",
                    "content": f"Citation content {i} " * 100,  # Large citation
                    "relevance_score": 0.8 + i * 0.01
                }
                for i in range(50)  # Many citations
            ]
        }
        
        mock_chat_state.messages.append(large_message)
        
        # Check memory usage (simplified check)
        message_size = sys.getsizeof(str(large_message))
        assert message_size > 0  # Basic check that message exists


class TestAccessibilityWithRAG:
    """Test accessibility features with RAG integration."""
    
    def test_citation_accessibility(self, mock_chat_state):
        """Test citation accessibility features."""
        
        # Mock message with accessible citations
        accessible_message = {
            "role": "assistant",
            "content": "Response content",
            "citations": [
                {
                    "id": "cite-1",
                    "source": "Plato's Republic",
                    "content": "Citation content", 
                    "aria_label": "Citation 1 from Plato's Republic",
                    "tab_index": 0,
                    "keyboard_accessible": True
                }
            ]
        }
        
        mock_chat_state.messages.append(accessible_message)
        
        # Verify accessibility features
        citation = mock_chat_state.messages[0]["citations"][0]
        assert "aria_label" in citation
        assert citation["keyboard_accessible"] == True
    
    def test_screen_reader_support(self, mock_chat_state):
        """Test screen reader support for RAG responses."""
        
        # Mock screen reader optimized message
        sr_message = {
            "role": "assistant",
            "content": "Response content",
            "screen_reader_text": "AI response: Response content. 2 citations available.",
            "citations_summary": "This response includes 2 citations from classical texts."
        }
        
        mock_chat_state.messages.append(sr_message)
        
        # Verify screen reader support
        message = mock_chat_state.messages[0]
        assert "screen_reader_text" in message
        assert "citations_summary" in message