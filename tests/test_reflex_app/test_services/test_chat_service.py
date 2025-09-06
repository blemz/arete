"""Tests for chat service."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.arete.ui.reflex_app.services.chat_service import ChatService


class TestChatService:
    """Test cases for ChatService."""

    @pytest.fixture
    def chat_service(self, mock_rag_service):
        """ChatService instance for testing."""
        return ChatService(rag_service=mock_rag_service)

    @pytest.mark.asyncio
    async def test_send_message_success(self, chat_service, mock_chat_response):
        """Test successful message sending."""
        chat_service.rag_service.generate_response.return_value = mock_chat_response
        
        result = await chat_service.send_message("What is virtue?")
        
        assert result["response"] == "Virtue, according to Socrates, is a form of knowledge."
        assert len(result["citations"]) == 1
        assert result["citations"][0]["relevance_score"] == 0.9
        chat_service.rag_service.generate_response.assert_called_once_with("What is virtue?")

    @pytest.mark.asyncio
    async def test_send_message_empty_query(self, chat_service):
        """Test handling of empty query."""
        result = await chat_service.send_message("")
        
        assert "error" in result
        assert result["error"] == "Query cannot be empty"

    @pytest.mark.asyncio
    async def test_send_message_rag_service_error(self, chat_service):
        """Test handling of RAG service errors."""
        chat_service.rag_service.generate_response.side_effect = Exception("RAG service error")
        
        result = await chat_service.send_message("What is virtue?")
        
        assert "error" in result
        assert "RAG service error" in result["error"]

    @pytest.mark.asyncio
    async def test_send_message_with_context(self, chat_service, mock_chat_response):
        """Test message sending with conversation context."""
        chat_service.rag_service.generate_response.return_value = mock_chat_response
        context = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi there!"}]
        
        result = await chat_service.send_message("What is virtue?", context=context)
        
        assert result["response"] == "Virtue, according to Socrates, is a form of knowledge."
        chat_service.rag_service.generate_response.assert_called_once_with("What is virtue?", context=context)

    def test_format_citations(self, chat_service):
        """Test citation formatting."""
        citations = [
            {
                "chunk_id": "chunk_1",
                "source_text": "Long text that needs to be truncated because it exceeds the maximum length",
                "relevance_score": 0.9,
                "source": "Plato's Republic"
            }
        ]
        
        formatted = chat_service.format_citations(citations)
        
        assert len(formatted) == 1
        assert formatted[0]["preview"] == "Long text that needs to be truncated because it ex..."
        assert formatted[0]["relevance_score"] == 0.9

    def test_extract_entities_from_response(self, chat_service, mock_chat_response):
        """Test entity extraction from response."""
        entities = chat_service.extract_entities_from_response(mock_chat_response)
        
        assert len(entities) == 1
        assert entities[0]["name"] == "Virtue"
        assert entities[0]["type"] == "Concept"

    def test_validate_query_valid(self, chat_service):
        """Test query validation with valid input."""
        assert chat_service.validate_query("What is virtue?") is True

    def test_validate_query_empty(self, chat_service):
        """Test query validation with empty input."""
        assert chat_service.validate_query("") is False
        assert chat_service.validate_query("   ") is False

    def test_validate_query_too_long(self, chat_service):
        """Test query validation with overly long input."""
        long_query = "What is virtue? " * 200  # Very long query
        assert chat_service.validate_query(long_query) is False

    @pytest.mark.asyncio
    async def test_get_conversation_summary(self, chat_service):
        """Test conversation summary generation."""
        with patch.object(chat_service, '_generate_summary') as mock_summary:
            mock_summary.return_value = "Discussion about virtue and ethics"
            
            history = [
                {"role": "user", "content": "What is virtue?"},
                {"role": "assistant", "content": "Virtue is moral excellence..."}
            ]
            
            summary = await chat_service.get_conversation_summary(history)
            
            assert summary == "Discussion about virtue and ethics"
            mock_summary.assert_called_once_with(history)

    @pytest.mark.asyncio
    async def test_clear_conversation(self, chat_service):
        """Test conversation clearing."""
        # Simulate some conversation state
        chat_service._conversation_id = "test_123"
        
        await chat_service.clear_conversation()
        
        # Should reset conversation state
        assert chat_service._conversation_id is None

    def test_get_message_statistics(self, chat_service):
        """Test message statistics calculation."""
        history = [
            {"role": "user", "content": "What is virtue?"},
            {"role": "assistant", "content": "Virtue is moral excellence..."},
            {"role": "user", "content": "Tell me more"},
            {"role": "assistant", "content": "In Aristotelian ethics..."}
        ]
        
        stats = chat_service.get_message_statistics(history)
        
        assert stats["total_messages"] == 4
        assert stats["user_messages"] == 2
        assert stats["assistant_messages"] == 2
        assert stats["avg_message_length"] > 0

    @pytest.mark.asyncio
    async def test_suggest_follow_up_questions(self, chat_service):
        """Test follow-up question suggestion."""
        with patch.object(chat_service, '_generate_suggestions') as mock_suggestions:
            mock_suggestions.return_value = [
                "What did Aristotle say about virtue?",
                "How does Plato define justice?",
                "What is the relationship between virtue and happiness?"
            ]
            
            last_response = "Virtue is moral excellence according to Aristotle."
            suggestions = await chat_service.suggest_follow_up_questions(last_response)
            
            assert len(suggestions) == 3
            assert "Aristotle" in suggestions[0]
            mock_suggestions.assert_called_once_with(last_response)

    def test_sanitize_input(self, chat_service):
        """Test input sanitization."""
        malicious_input = "<script>alert('xss')</script>What is virtue?"
        sanitized = chat_service.sanitize_input(malicious_input)
        
        assert "<script>" not in sanitized
        assert "What is virtue?" in sanitized

    @pytest.mark.asyncio
    async def test_handle_rate_limiting(self, chat_service):
        """Test rate limiting handling."""
        with patch.object(chat_service, '_check_rate_limit') as mock_rate_check:
            mock_rate_check.return_value = False  # Rate limit exceeded
            
            result = await chat_service.send_message("What is virtue?")
            
            assert "error" in result
            assert "rate limit" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_export_conversation(self, chat_service):
        """Test conversation export functionality."""
        history = [
            {"role": "user", "content": "What is virtue?", "timestamp": "2025-01-01 12:00:00"},
            {"role": "assistant", "content": "Virtue is moral excellence...", "timestamp": "2025-01-01 12:00:01"}
        ]
        
        exported = await chat_service.export_conversation(history, format="json")
        
        assert "conversation" in exported
        assert len(exported["conversation"]) == 2
        assert exported["format"] == "json"
        assert "exported_at" in exported

    def test_message_preprocessing(self, chat_service):
        """Test message preprocessing."""
        raw_message = "  What is VIRTUE?!  "
        processed = chat_service.preprocess_message(raw_message)
        
        assert processed == "What is virtue?"
        assert processed.strip() == processed
        assert not processed.isupper()

    @pytest.mark.asyncio
    async def test_concurrent_message_handling(self, chat_service, mock_chat_response):
        """Test handling of concurrent messages."""
        chat_service.rag_service.generate_response.return_value = mock_chat_response
        
        # Simulate concurrent requests
        import asyncio
        tasks = [
            chat_service.send_message("What is virtue?"),
            chat_service.send_message("What is justice?"),
            chat_service.send_message("What is wisdom?")
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should complete without errors
        assert len(results) == 3
        for result in results:
            assert not isinstance(result, Exception)

    def test_error_recovery(self, chat_service):
        """Test error recovery mechanisms."""
        with patch.object(chat_service.rag_service, 'generate_response') as mock_generate:
            # First call fails, second succeeds
            mock_generate.side_effect = [
                Exception("Temporary failure"),
                {"response": "Recovered response", "citations": [], "entities": []}
            ]
            
            # Should implement retry logic
            with patch.object(chat_service, '_retry_with_backoff') as mock_retry:
                mock_retry.return_value = {"response": "Recovered response", "citations": [], "entities": []}
                
                result = chat_service.handle_with_retry("What is virtue?")
                
                assert result["response"] == "Recovered response"