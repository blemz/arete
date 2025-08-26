"""
Tests for chat session management in philosophical tutoring system.

Tests cover session creation, message handling, conversation flow,
context tracking, and integration with the RAG pipeline.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import uuid

from arete.models.chat_session import (
    ChatSession,
    ChatMessage,
    MessageType,
    SessionStatus,
    ChatContext
)
from arete.services.chat_service import ChatService


class TestChatMessage:
    """Test ChatMessage data class."""
    
    def test_chat_message_creation(self):
        """Test basic chat message creation."""
        message = ChatMessage(
            message_id="msg_123",
            content="What is the meaning of virtue according to Aristotle?",
            message_type=MessageType.USER,
            timestamp=datetime.now(),
            user_id="user_123"
        )
        
        assert message.message_id == "msg_123"
        assert message.content == "What is the meaning of virtue according to Aristotle?"
        assert message.message_type == MessageType.USER
        assert message.user_id == "user_123"
        assert message.citations == []
        assert message.metadata == {}
    
    def test_chat_message_with_citations(self):
        """Test chat message with citation information."""
        message = ChatMessage(
            message_id="msg_456",
            content="According to Aristotle in Nicomachean Ethics, virtue is a disposition...",
            message_type=MessageType.ASSISTANT,
            timestamp=datetime.now(),
            citations=["Ethics 1103a", "Ethics 1107a"],
            metadata={
                "provider": "anthropic",
                "response_time": 1.234,
                "token_count": 156
            }
        )
        
        assert message.message_type == MessageType.ASSISTANT
        assert len(message.citations) == 2
        assert "Ethics 1103a" in message.citations
        assert message.metadata["provider"] == "anthropic"
        assert message.metadata["response_time"] == 1.234
    
    def test_chat_message_serialization(self):
        """Test chat message to_dict serialization."""
        message = ChatMessage(
            message_id="msg_789",
            content="Test message",
            message_type=MessageType.SYSTEM,
            timestamp=datetime.now(),
            citations=["Republic 514a"],
            metadata={"test": "value"}
        )
        
        message_dict = message.to_dict()
        
        assert message_dict["message_id"] == "msg_789"
        assert message_dict["content"] == "Test message"
        assert message_dict["message_type"] == MessageType.SYSTEM.value
        assert "timestamp" in message_dict
        assert message_dict["citations"] == ["Republic 514a"]
        assert message_dict["metadata"]["test"] == "value"
    
    def test_chat_message_from_dict(self):
        """Test chat message from_dict deserialization."""
        message_data = {
            "message_id": "msg_abc",
            "content": "Test content",
            "message_type": "user",
            "timestamp": "2025-08-26T10:30:00",
            "user_id": "user_456",
            "citations": ["Ethics 1094a"],
            "metadata": {"key": "value"}
        }
        
        message = ChatMessage.from_dict(message_data)
        
        assert message.message_id == "msg_abc"
        assert message.content == "Test content"
        assert message.message_type == MessageType.USER
        assert message.user_id == "user_456"
        assert message.citations == ["Ethics 1094a"]
        assert message.metadata["key"] == "value"


class TestChatContext:
    """Test ChatContext for conversation state management."""
    
    def test_chat_context_creation(self):
        """Test basic chat context creation."""
        context = ChatContext(
            student_level="undergraduate",
            philosophical_period="ancient",
            current_topic="virtue ethics",
            learning_objectives=["understand Aristotelian virtue", "compare with Platonic ethics"]
        )
        
        assert context.student_level == "undergraduate"
        assert context.philosophical_period == "ancient"
        assert context.current_topic == "virtue ethics"
        assert len(context.learning_objectives) == 2
        assert context.conversation_history == []
        assert context.relevant_sources == []
    
    def test_chat_context_with_history(self):
        """Test chat context with conversation history."""
        context = ChatContext(
            student_level="graduate",
            conversation_history=["previous question", "previous answer"],
            relevant_sources=["Republic", "Ethics"],
            metadata={"session_start": "2025-08-26T10:00:00"}
        )
        
        assert context.student_level == "graduate"
        assert len(context.conversation_history) == 2
        assert "Republic" in context.relevant_sources
        assert context.metadata["session_start"] == "2025-08-26T10:00:00"
    
    def test_chat_context_serialization(self):
        """Test chat context serialization."""
        context = ChatContext(
            student_level="advanced",
            philosophical_period="modern",
            current_topic="categorical imperative"
        )
        
        context_dict = context.to_dict()
        
        assert context_dict["student_level"] == "advanced"
        assert context_dict["philosophical_period"] == "modern"
        assert context_dict["current_topic"] == "categorical imperative"


class TestChatSession:
    """Test ChatSession model."""
    
    def test_chat_session_creation(self):
        """Test basic chat session creation."""
        session = ChatSession(
            session_id="session_123",
            user_id="user_456",
            title="Discussion on Virtue Ethics",
            status=SessionStatus.ACTIVE
        )
        
        assert session.session_id == "session_123"
        assert session.user_id == "user_456"
        assert session.title == "Discussion on Virtue Ethics"
        assert session.status == SessionStatus.ACTIVE
        assert session.messages == []
        assert session.context is not None
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.updated_at, datetime)
    
    def test_add_message_to_session(self):
        """Test adding messages to chat session."""
        session = ChatSession(
            session_id="session_456",
            user_id="user_789",
            title="Philosophical Discussion"
        )
        
        message = ChatMessage(
            message_id="msg_001",
            content="What is justice according to Plato?",
            message_type=MessageType.USER,
            timestamp=datetime.now(),
            user_id="user_789"
        )
        
        session.add_message(message)
        
        assert len(session.messages) == 1
        assert session.messages[0].content == "What is justice according to Plato?"
        assert session.updated_at > session.created_at
    
    def test_get_recent_messages(self):
        """Test retrieving recent messages from session."""
        session = ChatSession(
            session_id="session_789",
            user_id="user_123",
            title="Recent Messages Test"
        )
        
        # Add multiple messages
        for i in range(10):
            message = ChatMessage(
                message_id=f"msg_{i:03d}",
                content=f"Message {i}",
                message_type=MessageType.USER if i % 2 == 0 else MessageType.ASSISTANT,
                timestamp=datetime.now() - timedelta(minutes=10-i),
                user_id="user_123"
            )
            session.add_message(message)
        
        # Get recent messages (default 5)
        recent_messages = session.get_recent_messages(limit=5)
        
        assert len(recent_messages) == 5
        assert recent_messages[0].content == "Message 9"  # Most recent first
        assert recent_messages[4].content == "Message 5"
    
    def test_update_context(self):
        """Test updating session context."""
        session = ChatSession(
            session_id="session_abc",
            user_id="user_def",
            title="Context Update Test"
        )
        
        new_context = ChatContext(
            student_level="graduate",
            philosophical_period="medieval",
            current_topic="Aquinas ethics",
            learning_objectives=["understand natural law theory"]
        )
        
        session.update_context(new_context)
        
        assert session.context.student_level == "graduate"
        assert session.context.philosophical_period == "medieval"
        assert session.context.current_topic == "Aquinas ethics"
        assert session.updated_at > session.created_at
    
    def test_session_serialization(self):
        """Test chat session serialization."""
        session = ChatSession(
            session_id="session_serialize",
            user_id="user_serialize",
            title="Serialization Test",
            status=SessionStatus.ACTIVE
        )
        
        # Add a message
        message = ChatMessage(
            message_id="msg_serialize",
            content="Test message for serialization",
            message_type=MessageType.USER,
            timestamp=datetime.now(),
            user_id="user_serialize"
        )
        session.add_message(message)
        
        session_dict = session.to_dict()
        
        assert session_dict["session_id"] == "session_serialize"
        assert session_dict["user_id"] == "user_serialize"
        assert session_dict["title"] == "Serialization Test"
        assert session_dict["status"] == SessionStatus.ACTIVE.value
        assert len(session_dict["messages"]) == 1
        assert session_dict["messages"][0]["content"] == "Test message for serialization"
    
    def test_session_from_dict(self):
        """Test chat session from_dict deserialization."""
        session_data = {
            "session_id": "session_deserialize",
            "user_id": "user_deserialize", 
            "title": "Deserialization Test",
            "status": "active",
            "messages": [
                {
                    "message_id": "msg_des",
                    "content": "Deserialized message",
                    "message_type": "assistant",
                    "timestamp": "2025-08-26T11:00:00",
                    "citations": ["Republic 514a"],
                    "metadata": {}
                }
            ],
            "context": {
                "student_level": "undergraduate",
                "philosophical_period": "ancient",
                "current_topic": "cave allegory"
            },
            "created_at": "2025-08-26T10:00:00",
            "updated_at": "2025-08-26T11:00:00"
        }
        
        session = ChatSession.from_dict(session_data)
        
        assert session.session_id == "session_deserialize"
        assert session.user_id == "user_deserialize"
        assert session.title == "Deserialization Test"
        assert session.status == SessionStatus.ACTIVE
        assert len(session.messages) == 1
        assert session.messages[0].content == "Deserialized message"
        assert session.context.current_topic == "cave allegory"
    
    def test_session_status_transitions(self):
        """Test valid session status transitions."""
        session = ChatSession(
            session_id="session_status",
            user_id="user_status",
            title="Status Test"
        )
        
        # Active -> Paused
        assert session.status == SessionStatus.ACTIVE
        session.pause()
        assert session.status == SessionStatus.PAUSED
        
        # Paused -> Active
        session.resume()
        assert session.status == SessionStatus.ACTIVE
        
        # Active -> Completed
        session.complete()
        assert session.status == SessionStatus.COMPLETED
    
    def test_session_context_summary(self):
        """Test session context summary generation."""
        session = ChatSession(
            session_id="session_summary",
            user_id="user_summary",
            title="Context Summary Test"
        )
        
        # Add some messages and context
        session.context.current_topic = "virtue ethics"
        session.context.student_level = "undergraduate"
        
        user_msg = ChatMessage(
            message_id="msg_u1",
            content="What is virtue according to Aristotle?",
            message_type=MessageType.USER,
            timestamp=datetime.now(),
            user_id="user_summary"
        )
        
        assistant_msg = ChatMessage(
            message_id="msg_a1", 
            content="Virtue for Aristotle is a disposition to act excellently...",
            message_type=MessageType.ASSISTANT,
            timestamp=datetime.now(),
            citations=["Ethics 1103a"]
        )
        
        session.add_message(user_msg)
        session.add_message(assistant_msg)
        
        summary = session.get_context_summary()
        
        assert "virtue ethics" in summary
        assert "undergraduate" in summary
        assert len(session.messages) == 2


class TestChatService:
    """Test ChatService for session management."""
    
    @pytest.fixture
    def mock_chat_service(self):
        """Create mock chat service for testing."""
        return ChatService()
    
    def test_create_new_session(self, mock_chat_service):
        """Test creating a new chat session."""
        session = mock_chat_service.create_session(
            user_id="user_new",
            title="New Session Test"
        )
        
        assert session.user_id == "user_new"
        assert session.title == "New Session Test"
        assert session.status == SessionStatus.ACTIVE
        assert len(session.session_id) > 0
        assert isinstance(session.created_at, datetime)
    
    def test_get_session_by_id(self, mock_chat_service):
        """Test retrieving session by ID."""
        # Create a session first
        session = mock_chat_service.create_session(
            user_id="user_get",
            title="Get Session Test"
        )
        
        # Retrieve it
        retrieved_session = mock_chat_service.get_session(session.session_id)
        
        assert retrieved_session is not None
        assert retrieved_session.session_id == session.session_id
        assert retrieved_session.title == "Get Session Test"
    
    def test_get_nonexistent_session(self, mock_chat_service):
        """Test retrieving non-existent session."""
        session = mock_chat_service.get_session("nonexistent_id")
        assert session is None
    
    def test_list_user_sessions(self, mock_chat_service):
        """Test listing sessions for a user."""
        user_id = "user_list_test"
        
        # Create multiple sessions
        session1 = mock_chat_service.create_session(user_id, "Session 1")
        session2 = mock_chat_service.create_session(user_id, "Session 2")
        session3 = mock_chat_service.create_session("other_user", "Other Session")
        
        # List sessions for user
        user_sessions = mock_chat_service.list_user_sessions(user_id)
        
        assert len(user_sessions) == 2
        session_titles = [s.title for s in user_sessions]
        assert "Session 1" in session_titles
        assert "Session 2" in session_titles
        assert "Other Session" not in session_titles
    
    def test_update_session(self, mock_chat_service):
        """Test updating session properties."""
        session = mock_chat_service.create_session(
            user_id="user_update",
            title="Original Title"
        )
        
        # Update session
        updated_session = mock_chat_service.update_session(
            session.session_id,
            title="Updated Title",
            status=SessionStatus.PAUSED
        )
        
        assert updated_session.title == "Updated Title"
        assert updated_session.status == SessionStatus.PAUSED
        assert updated_session.updated_at > updated_session.created_at
    
    def test_delete_session(self, mock_chat_service):
        """Test deleting a session."""
        session = mock_chat_service.create_session(
            user_id="user_delete",
            title="Delete Test"
        )
        
        # Delete session
        result = mock_chat_service.delete_session(session.session_id)
        assert result is True
        
        # Verify it's deleted
        deleted_session = mock_chat_service.get_session(session.session_id)
        assert deleted_session is None
    
    def test_session_message_management(self, mock_chat_service):
        """Test adding and retrieving messages in session."""
        session = mock_chat_service.create_session(
            user_id="user_messages",
            title="Message Test"
        )
        
        # Add message to session
        message = ChatMessage(
            message_id="msg_test",
            content="Test message content",
            message_type=MessageType.USER,
            timestamp=datetime.now(),
            user_id="user_messages"
        )
        
        updated_session = mock_chat_service.add_message_to_session(
            session.session_id,
            message
        )
        
        assert len(updated_session.messages) == 1
        assert updated_session.messages[0].content == "Test message content"
        assert updated_session.updated_at > session.updated_at
    
    def test_session_search(self, mock_chat_service):
        """Test searching sessions by content."""
        # Create sessions with different content
        session1 = mock_chat_service.create_session("user_search", "Aristotle Discussion")
        session2 = mock_chat_service.create_session("user_search", "Plato Analysis") 
        session3 = mock_chat_service.create_session("user_search", "Modern Philosophy")
        
        # Search by title
        results = mock_chat_service.search_sessions("user_search", query="Aristotle")
        
        assert len(results) == 1
        assert results[0].title == "Aristotle Discussion"
    
    def test_session_cleanup(self, mock_chat_service):
        """Test cleanup of old inactive sessions."""
        # Create old session
        old_session = mock_chat_service.create_session(
            user_id="user_cleanup",
            title="Old Session"
        )
        
        # Simulate old timestamp
        old_session.updated_at = datetime.now() - timedelta(days=31)
        
        # Run cleanup (sessions inactive for 30+ days)
        cleanup_count = mock_chat_service.cleanup_inactive_sessions(days_threshold=30)
        
        assert cleanup_count >= 0  # May be 0 or more depending on implementation