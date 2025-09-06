"""Tests for chat state management."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.arete.ui.reflex_app.state.chat_state import ChatState


class TestChatState:
    """Test cases for ChatState."""

    @pytest.fixture
    def chat_state(self):
        """ChatState instance for testing."""
        return ChatState()

    def test_initial_state(self, chat_state):
        """Test initial state values."""
        assert chat_state.messages == []
        assert chat_state.current_message == ""
        assert chat_state.is_loading == False
        assert chat_state.error_message == ""
        assert chat_state.session_id is not None

    def test_add_user_message(self, chat_state):
        """Test adding user message."""
        chat_state.add_user_message("What is virtue?")
        
        assert len(chat_state.messages) == 1
        assert chat_state.messages[0]["role"] == "user"
        assert chat_state.messages[0]["content"] == "What is virtue?"
        assert "timestamp" in chat_state.messages[0]

    def test_add_assistant_message(self, chat_state):
        """Test adding assistant message."""
        response_data = {
            "response": "Virtue is moral excellence.",
            "citations": [{"chunk_id": "chunk_1", "source_text": "test"}],
            "entities": [{"name": "Virtue", "type": "Concept"}]
        }
        
        chat_state.add_assistant_message(response_data)
        
        assert len(chat_state.messages) == 1
        assert chat_state.messages[0]["role"] == "assistant"
        assert chat_state.messages[0]["content"] == "Virtue is moral excellence."
        assert chat_state.messages[0]["citations"] == response_data["citations"]
        assert chat_state.messages[0]["entities"] == response_data["entities"]

    def test_set_loading_state(self, chat_state):
        """Test setting loading state."""
        chat_state.set_loading(True)
        assert chat_state.is_loading == True
        
        chat_state.set_loading(False)
        assert chat_state.is_loading == False

    def test_set_error_message(self, chat_state):
        """Test setting error message."""
        chat_state.set_error("Connection failed")
        assert chat_state.error_message == "Connection failed"

    def test_clear_error(self, chat_state):
        """Test clearing error message."""
        chat_state.set_error("Test error")
        chat_state.clear_error()
        assert chat_state.error_message == ""

    def test_clear_messages(self, chat_state):
        """Test clearing all messages."""
        chat_state.add_user_message("Test message")
        chat_state.add_assistant_message({"response": "Test response", "citations": [], "entities": []})
        
        assert len(chat_state.messages) == 2
        
        chat_state.clear_messages()
        assert chat_state.messages == []

    def test_update_current_message(self, chat_state):
        """Test updating current message input."""
        chat_state.update_current_message("What is")
        assert chat_state.current_message == "What is"
        
        chat_state.update_current_message("What is virtue?")
        assert chat_state.current_message == "What is virtue?"

    def test_get_conversation_history(self, chat_state):
        """Test getting conversation history."""
        chat_state.add_user_message("Hello")
        chat_state.add_assistant_message({"response": "Hi there!", "citations": [], "entities": []})
        chat_state.add_user_message("What is virtue?")
        
        history = chat_state.get_conversation_history()
        
        assert len(history) == 3
        assert history[0]["content"] == "Hello"
        assert history[1]["content"] == "Hi there!"
        assert history[2]["content"] == "What is virtue?"

    def test_get_conversation_history_with_limit(self, chat_state):
        """Test getting limited conversation history."""
        for i in range(5):
            chat_state.add_user_message(f"Message {i}")
        
        history = chat_state.get_conversation_history(limit=3)
        
        assert len(history) == 3
        assert history[0]["content"] == "Message 2"  # Should get last 3

    def test_get_last_assistant_message(self, chat_state):
        """Test getting last assistant message."""
        chat_state.add_user_message("Hello")
        chat_state.add_assistant_message({"response": "Hi there!", "citations": [], "entities": []})
        chat_state.add_user_message("What is virtue?")
        chat_state.add_assistant_message({"response": "Virtue is excellence.", "citations": [], "entities": []})
        
        last_message = chat_state.get_last_assistant_message()
        
        assert last_message["content"] == "Virtue is excellence."
        assert last_message["role"] == "assistant"

    def test_get_last_assistant_message_none(self, chat_state):
        """Test getting last assistant message when none exists."""
        chat_state.add_user_message("Hello")
        
        last_message = chat_state.get_last_assistant_message()
        
        assert last_message is None

    def test_has_messages(self, chat_state):
        """Test checking if chat has messages."""
        assert chat_state.has_messages() == False
        
        chat_state.add_user_message("Test")
        assert chat_state.has_messages() == True

    def test_get_message_count(self, chat_state):
        """Test getting message count."""
        assert chat_state.get_message_count() == 0
        
        chat_state.add_user_message("Test 1")
        chat_state.add_assistant_message({"response": "Response 1", "citations": [], "entities": []})
        
        assert chat_state.get_message_count() == 2

    def test_get_user_message_count(self, chat_state):
        """Test getting user message count."""
        chat_state.add_user_message("Test 1")
        chat_state.add_assistant_message({"response": "Response 1", "citations": [], "entities": []})
        chat_state.add_user_message("Test 2")
        
        assert chat_state.get_user_message_count() == 2

    def test_get_assistant_message_count(self, chat_state):
        """Test getting assistant message count."""
        chat_state.add_user_message("Test 1")
        chat_state.add_assistant_message({"response": "Response 1", "citations": [], "entities": []})
        chat_state.add_assistant_message({"response": "Response 2", "citations": [], "entities": []})
        
        assert chat_state.get_assistant_message_count() == 2

    @pytest.mark.asyncio
    async def test_send_message(self, chat_state):
        """Test sending a message through the chat state."""
        chat_state.current_message = "What is virtue?"
        
        with patch.object(chat_state, 'chat_service') as mock_service:
            mock_service.send_message.return_value = {
                "response": "Virtue is moral excellence.",
                "citations": [],
                "entities": []
            }
            
            await chat_state.send_message()
            
            # Should add both user and assistant messages
            assert len(chat_state.messages) == 2
            assert chat_state.messages[0]["role"] == "user"
            assert chat_state.messages[1]["role"] == "assistant"
            assert chat_state.current_message == ""  # Should be cleared

    @pytest.mark.asyncio
    async def test_send_message_error_handling(self, chat_state):
        """Test error handling in send message."""
        chat_state.current_message = "What is virtue?"
        
        with patch.object(chat_state, 'chat_service') as mock_service:
            mock_service.send_message.side_effect = Exception("Service error")
            
            await chat_state.send_message()
            
            assert chat_state.error_message == "Service error"
            assert chat_state.is_loading == False

    @pytest.mark.asyncio
    async def test_send_empty_message(self, chat_state):
        """Test sending empty message."""
        chat_state.current_message = ""
        
        await chat_state.send_message()
        
        assert len(chat_state.messages) == 0
        assert chat_state.error_message == "Message cannot be empty"

    def test_export_conversation(self, chat_state):
        """Test exporting conversation."""
        chat_state.add_user_message("What is virtue?")
        chat_state.add_assistant_message({
            "response": "Virtue is moral excellence.",
            "citations": [{"chunk_id": "chunk_1"}],
            "entities": [{"name": "Virtue"}]
        })
        
        exported = chat_state.export_conversation()
        
        assert "session_id" in exported
        assert "messages" in exported
        assert "exported_at" in exported
        assert len(exported["messages"]) == 2

    def test_import_conversation(self, chat_state):
        """Test importing conversation."""
        conversation_data = {
            "session_id": "test_session",
            "messages": [
                {"role": "user", "content": "Hello", "timestamp": "2025-01-01T12:00:00"},
                {"role": "assistant", "content": "Hi!", "timestamp": "2025-01-01T12:00:01", "citations": [], "entities": []}
            ]
        }
        
        chat_state.import_conversation(conversation_data)
        
        assert chat_state.session_id == "test_session"
        assert len(chat_state.messages) == 2
        assert chat_state.messages[0]["content"] == "Hello"

    def test_get_citations_from_message(self, chat_state):
        """Test extracting citations from a specific message."""
        chat_state.add_assistant_message({
            "response": "Test response",
            "citations": [
                {"chunk_id": "chunk_1", "source_text": "Citation 1"},
                {"chunk_id": "chunk_2", "source_text": "Citation 2"}
            ],
            "entities": []
        })
        
        citations = chat_state.get_citations_from_message(0)
        
        assert len(citations) == 2
        assert citations[0]["chunk_id"] == "chunk_1"

    def test_get_entities_from_message(self, chat_state):
        """Test extracting entities from a specific message."""
        chat_state.add_assistant_message({
            "response": "Test response",
            "citations": [],
            "entities": [
                {"name": "Virtue", "type": "Concept"},
                {"name": "Socrates", "type": "Person"}
            ]
        })
        
        entities = chat_state.get_entities_from_message(0)
        
        assert len(entities) == 2
        assert entities[0]["name"] == "Virtue"
        assert entities[1]["type"] == "Person"

    def test_search_messages(self, chat_state):
        """Test searching through messages."""
        chat_state.add_user_message("What is virtue?")
        chat_state.add_assistant_message({"response": "Virtue is moral excellence.", "citations": [], "entities": []})
        chat_state.add_user_message("What about justice?")
        chat_state.add_assistant_message({"response": "Justice is fairness.", "citations": [], "entities": []})
        
        results = chat_state.search_messages("virtue")
        
        assert len(results) == 2  # Both user question and assistant response
        assert "virtue" in results[0]["content"].lower()

    def test_get_message_statistics(self, chat_state):
        """Test getting conversation statistics."""
        chat_state.add_user_message("Short")
        chat_state.add_assistant_message({"response": "This is a longer response with more words.", "citations": [], "entities": []})
        
        stats = chat_state.get_message_statistics()
        
        assert "total_messages" in stats
        assert "user_messages" in stats
        assert "assistant_messages" in stats
        assert "average_length" in stats
        assert stats["total_messages"] == 2

    def test_undo_last_exchange(self, chat_state):
        """Test undoing last question-answer exchange."""
        chat_state.add_user_message("What is virtue?")
        chat_state.add_assistant_message({"response": "Virtue is...", "citations": [], "entities": []})
        chat_state.add_user_message("What is justice?")
        chat_state.add_assistant_message({"response": "Justice is...", "citations": [], "entities": []})
        
        assert len(chat_state.messages) == 4
        
        chat_state.undo_last_exchange()
        
        assert len(chat_state.messages) == 2
        assert chat_state.messages[-1]["content"] == "Virtue is..."

    def test_regenerate_last_response(self, chat_state):
        """Test regenerating last assistant response."""
        chat_state.add_user_message("What is virtue?")
        chat_state.add_assistant_message({"response": "Old response", "citations": [], "entities": []})
        
        with patch.object(chat_state, 'chat_service') as mock_service:
            mock_service.send_message.return_value = {
                "response": "New response",
                "citations": [],
                "entities": []
            }
            
            chat_state.regenerate_last_response()
            
            assert len(chat_state.messages) == 2
            assert chat_state.messages[1]["content"] == "New response"

    def test_set_typing_indicator(self, chat_state):
        """Test setting typing indicator."""
        chat_state.set_typing_indicator(True)
        assert chat_state.is_typing == True
        
        chat_state.set_typing_indicator(False)
        assert chat_state.is_typing == False

    def test_validate_message_input(self, chat_state):
        """Test message input validation."""
        assert chat_state.validate_message_input("Valid message") == True
        assert chat_state.validate_message_input("") == False
        assert chat_state.validate_message_input("   ") == False
        
        # Test very long message
        long_message = "x" * 10000
        assert chat_state.validate_message_input(long_message) == False

    def test_format_message_for_display(self, chat_state):
        """Test formatting message for display."""
        message = {
            "role": "assistant",
            "content": "Virtue is moral excellence.",
            "timestamp": "2025-01-01T12:00:00",
            "citations": [{"chunk_id": "chunk_1"}],
            "entities": [{"name": "Virtue"}]
        }
        
        formatted = chat_state.format_message_for_display(message)
        
        assert "display_time" in formatted
        assert "has_citations" in formatted
        assert "has_entities" in formatted
        assert formatted["has_citations"] == True
        assert formatted["has_entities"] == True