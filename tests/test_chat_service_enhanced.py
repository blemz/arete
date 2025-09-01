"""
Enhanced tests for chat service with user experience features.

Tests cover bookmarking, conversation history, enhanced search,
user preferences, and export functionality following the proven
contract-based testing methodology.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import uuid
import json

from arete.models.chat_session import (
    ChatSession,
    ChatMessage,
    MessageType,
    SessionStatus,
    ChatContext
)
from arete.services.chat_service import ChatService


class TestSessionBookmarking:
    """Test session bookmarking and favorites functionality."""
    
    @pytest.fixture
    def chat_service(self):
        """Create chat service for testing."""
        return ChatService()
    
    def test_bookmark_session(self, chat_service):
        """Test bookmarking a session."""
        session = chat_service.create_session(
            user_id="user_bookmark",
            title="Important Discussion"
        )
        
        # Bookmark the session
        result = chat_service.bookmark_session(session.session_id, True)
        
        assert result is True
        bookmarked_session = chat_service.get_session(session.session_id)
        assert bookmarked_session.is_bookmarked is True
    
    def test_unbookmark_session(self, chat_service):
        """Test removing bookmark from session."""
        session = chat_service.create_session(
            user_id="user_unbookmark",
            title="Temporary Discussion"
        )
        
        # Bookmark then unbookmark
        chat_service.bookmark_session(session.session_id, True)
        result = chat_service.bookmark_session(session.session_id, False)
        
        assert result is True
        unbookmarked_session = chat_service.get_session(session.session_id)
        assert unbookmarked_session.is_bookmarked is False
    
    def test_list_bookmarked_sessions(self, chat_service):
        """Test listing only bookmarked sessions."""
        user_id = "user_bookmarks"
        
        # Create sessions, bookmark some
        session1 = chat_service.create_session(user_id, "Regular Session")
        session2 = chat_service.create_session(user_id, "Important Session")
        session3 = chat_service.create_session(user_id, "Another Session")
        
        chat_service.bookmark_session(session2.session_id, True)
        
        # List bookmarked sessions
        bookmarked = chat_service.list_user_sessions(
            user_id, 
            bookmarked_only=True
        )
        
        assert len(bookmarked) == 1
        assert bookmarked[0].title == "Important Session"
        assert bookmarked[0].is_bookmarked is True
    
    def test_bookmark_nonexistent_session(self, chat_service):
        """Test bookmarking non-existent session."""
        result = chat_service.bookmark_session("nonexistent", True)
        assert result is False


class TestEnhancedSessionSearch:
    """Test enhanced search functionality across conversation history."""
    
    @pytest.fixture
    def chat_service_with_data(self):
        """Create chat service with sample philosophical conversations."""
        service = ChatService()
        
        # Create sessions with philosophical content
        aristotle_session = service.create_session(
            user_id="philosopher_user",
            title="Aristotelian Virtue Ethics"
        )
        
        plato_session = service.create_session(
            user_id="philosopher_user", 
            title="Platonic Justice Theory"
        )
        
        kant_session = service.create_session(
            user_id="philosopher_user",
            title="Kantian Moral Philosophy"
        )
        
        # Add messages to sessions
        aristotle_messages = [
            ChatMessage(
                message_id="msg_a1",
                content="What is virtue according to Aristotle?",
                message_type=MessageType.USER,
                timestamp=datetime.now(),
                user_id="philosopher_user"
            ),
            ChatMessage(
                message_id="msg_a2",
                content="For Aristotle, virtue (arete) is a disposition to act excellently, achieved through habituation and the golden mean between extremes.",
                message_type=MessageType.ASSISTANT,
                timestamp=datetime.now(),
                citations=["Nicomachean Ethics 1103a", "Ethics 1107a"]
            )
        ]
        
        plato_messages = [
            ChatMessage(
                message_id="msg_p1",
                content="Explain Plato's theory of justice",
                message_type=MessageType.USER,
                timestamp=datetime.now(),
                user_id="philosopher_user"
            ),
            ChatMessage(
                message_id="msg_p2", 
                content="Plato defines justice as harmony in the soul, where reason rules over spirit and appetite, mirroring the just state.",
                message_type=MessageType.ASSISTANT,
                timestamp=datetime.now(),
                citations=["Republic 441c", "Republic 443d"]
            )
        ]
        
        kant_messages = [
            ChatMessage(
                message_id="msg_k1",
                content="What is the categorical imperative?",
                message_type=MessageType.USER,
                timestamp=datetime.now(),
                user_id="philosopher_user"
            ),
            ChatMessage(
                message_id="msg_k2",
                content="The categorical imperative is Kant's principle that we should act only according to maxims we could will to be universal laws.",
                message_type=MessageType.ASSISTANT,
                timestamp=datetime.now(),
                citations=["Groundwork 421", "Critique of Practical Reason"]
            )
        ]
        
        # Add messages to sessions
        for msg in aristotle_messages:
            service.add_message_to_session(aristotle_session.session_id, msg)
        
        for msg in plato_messages:
            service.add_message_to_session(plato_session.session_id, msg)
            
        for msg in kant_messages:
            service.add_message_to_session(kant_session.session_id, msg)
        
        return service
    
    def test_search_by_philosophical_concept(self, chat_service_with_data):
        """Test searching by philosophical concepts."""
        results = chat_service_with_data.search_sessions(
            user_id="philosopher_user",
            query="virtue",
            search_content=True
        )
        
        assert len(results) == 1
        assert "Aristotelian" in results[0].title
    
    def test_search_by_citation_reference(self, chat_service_with_data):
        """Test searching by classical text citations."""
        results = chat_service_with_data.search_sessions(
            user_id="philosopher_user", 
            query="Republic",
            search_content=True
        )
        
        assert len(results) == 1
        assert "Platonic" in results[0].title
    
    def test_advanced_content_search(self, chat_service_with_data):
        """Test advanced search across message content."""
        # Search for specific philosophical term
        results = chat_service_with_data.search_sessions(
            user_id="philosopher_user",
            query="categorical imperative",
            search_content=True
        )
        
        assert len(results) == 1
        assert "Kantian" in results[0].title
    
    def test_search_with_filters(self, chat_service_with_data):
        """Test search with additional filters."""
        # This would test enhanced search with date ranges, status filters, etc.
        results = chat_service_with_data.search_sessions(
            user_id="philosopher_user",
            query="justice",
            search_content=True,
            status_filter=SessionStatus.ACTIVE
        )
        
        assert len(results) == 1
        assert results[0].status == SessionStatus.ACTIVE
    
    def test_empty_search_results(self, chat_service_with_data):
        """Test search with no matching results."""
        results = chat_service_with_data.search_sessions(
            user_id="philosopher_user",
            query="nonexistent_concept",
            search_content=True
        )
        
        assert len(results) == 0


class TestConversationHistory:
    """Test conversation history management and navigation."""
    
    @pytest.fixture
    def chat_service(self):
        """Create chat service for testing."""
        return ChatService()
    
    def test_get_conversation_history(self, chat_service):
        """Test retrieving complete conversation history."""
        session = chat_service.create_session(
            user_id="history_user",
            title="Philosophy Discussion"
        )
        
        # Add conversation thread
        messages = [
            ChatMessage(
                message_id=f"msg_{i}",
                content=f"Message {i}",
                message_type=MessageType.USER if i % 2 == 0 else MessageType.ASSISTANT,
                timestamp=datetime.now() - timedelta(minutes=10-i),
                user_id="history_user"
            )
            for i in range(6)
        ]
        
        for msg in messages:
            chat_service.add_message_to_session(session.session_id, msg)
        
        history = chat_service.get_conversation_history(session.session_id)
        
        assert len(history) == 6
        assert history[0].content == "Message 0"  # Chronological order
        assert history[-1].content == "Message 5"
    
    def test_get_conversation_thread(self, chat_service):
        """Test retrieving conversation thread around specific message."""
        session = chat_service.create_session(
            user_id="thread_user",
            title="Thread Test"
        )
        
        # Add messages
        for i in range(10):
            message = ChatMessage(
                message_id=f"thread_msg_{i}",
                content=f"Thread message {i}",
                message_type=MessageType.USER if i % 2 == 0 else MessageType.ASSISTANT,
                timestamp=datetime.now() - timedelta(minutes=10-i),
                user_id="thread_user"
            )
            chat_service.add_message_to_session(session.session_id, message)
        
        # Get thread around message 5 (3 messages before, 3 after)
        thread = chat_service.get_conversation_thread(
            session.session_id,
            message_id="thread_msg_5",
            context_size=3
        )
        
        assert len(thread) == 7  # 3 before + target + 3 after
        assert thread[3].message_id == "thread_msg_5"  # Target in middle
    
    def test_conversation_history_pagination(self, chat_service):
        """Test paginated conversation history."""
        session = chat_service.create_session(
            user_id="pagination_user",
            title="Pagination Test"
        )
        
        # Add many messages
        for i in range(50):
            message = ChatMessage(
                message_id=f"page_msg_{i}",
                content=f"Paginated message {i}",
                message_type=MessageType.USER if i % 2 == 0 else MessageType.ASSISTANT,
                timestamp=datetime.now() - timedelta(minutes=50-i),
                user_id="pagination_user"
            )
            chat_service.add_message_to_session(session.session_id, message)
        
        # Get first page (10 messages)
        page1 = chat_service.get_conversation_history(
            session.session_id,
            limit=10,
            offset=0
        )
        
        # Get second page
        page2 = chat_service.get_conversation_history(
            session.session_id,
            limit=10,
            offset=10
        )
        
        assert len(page1) == 10
        assert len(page2) == 10
        assert page1[0].content == "Paginated message 0"
        assert page2[0].content == "Paginated message 10"
    
    def test_conversation_summary_generation(self, chat_service):
        """Test generating conversation summaries."""
        session = chat_service.create_session(
            user_id="summary_user",
            title="Summary Test"
        )
        
        # Add philosophical conversation
        philosophical_messages = [
            ChatMessage(
                message_id="sum_1",
                content="What is the nature of knowledge according to Plato?",
                message_type=MessageType.USER,
                timestamp=datetime.now(),
                user_id="summary_user"
            ),
            ChatMessage(
                message_id="sum_2",
                content="Plato distinguishes between knowledge (episteme) and opinion (doxa), arguing that true knowledge concerns eternal Forms rather than the changing material world.",
                message_type=MessageType.ASSISTANT,
                timestamp=datetime.now(),
                citations=["Republic 476e", "Meno 97a"]
            )
        ]
        
        for msg in philosophical_messages:
            chat_service.add_message_to_session(session.session_id, msg)
        
        summary = chat_service.generate_conversation_summary(session.session_id)
        
        assert summary is not None
        assert "knowledge" in summary.lower()
        assert "plato" in summary.lower()


class TestSessionStatistics:
    """Test enhanced session statistics and analytics."""
    
    @pytest.fixture
    def chat_service(self):
        """Create chat service for testing."""
        return ChatService()
    
    def test_detailed_user_statistics(self, chat_service):
        """Test detailed user statistics generation."""
        user_id = "stats_user"
        
        # Create multiple sessions with different characteristics
        session1 = chat_service.create_session(user_id, "Active Discussion")
        session2 = chat_service.create_session(user_id, "Completed Discussion") 
        session3 = chat_service.create_session(user_id, "Paused Discussion")
        
        # Add messages and set statuses
        for i in range(5):
            msg = ChatMessage(
                message_id=f"stats_msg_1_{i}",
                content=f"Message {i}",
                message_type=MessageType.USER if i % 2 == 0 else MessageType.ASSISTANT,
                timestamp=datetime.now(),
                user_id=user_id
            )
            chat_service.add_message_to_session(session1.session_id, msg)
        
        chat_service.update_session(session2.session_id, status=SessionStatus.COMPLETED)
        chat_service.update_session(session3.session_id, status=SessionStatus.PAUSED)
        
        stats = chat_service.get_detailed_user_statistics(user_id)
        
        assert stats["total_sessions"] == 3
        assert stats["active_sessions"] == 1
        assert stats["completed_sessions"] == 1
        assert stats["paused_sessions"] == 1
        assert stats["total_messages"] == 5
        assert "most_active_period" in stats
        assert "average_session_length" in stats
    
    def test_session_activity_timeline(self, chat_service):
        """Test session activity timeline generation."""
        user_id = "timeline_user"
        
        session = chat_service.create_session(user_id, "Timeline Test")
        
        # Add messages at different times
        base_time = datetime.now()
        for i in range(5):
            msg = ChatMessage(
                message_id=f"timeline_msg_{i}",
                content=f"Timeline message {i}",
                message_type=MessageType.USER if i % 2 == 0 else MessageType.ASSISTANT,
                timestamp=base_time + timedelta(hours=i),
                user_id=user_id
            )
            chat_service.add_message_to_session(session.session_id, msg)
        
        timeline = chat_service.get_session_activity_timeline(session.session_id)
        
        assert len(timeline) == 5
        assert all("timestamp" in entry for entry in timeline)
        assert all("message_type" in entry for entry in timeline)
        assert timeline[0]["timestamp"] < timeline[-1]["timestamp"]  # Chronological
    
    def test_philosophical_topic_analysis(self, chat_service):
        """Test analysis of philosophical topics discussed."""
        user_id = "topics_user"
        
        session = chat_service.create_session(user_id, "Topics Analysis")
        
        # Add messages with philosophical content
        philosophical_content = [
            "What is virtue according to Aristotle?",
            "Explain Kant's categorical imperative",
            "How does Plato define justice?",
            "What is Stoic philosophy about?"
        ]
        
        for i, content in enumerate(philosophical_content):
            msg = ChatMessage(
                message_id=f"topic_msg_{i}",
                content=content,
                message_type=MessageType.USER,
                timestamp=datetime.now(),
                user_id=user_id
            )
            chat_service.add_message_to_session(session.session_id, msg)
        
        topic_analysis = chat_service.analyze_philosophical_topics(session.session_id)
        
        assert "topics" in topic_analysis
        assert "philosophers_mentioned" in topic_analysis
        assert "ethical_themes" in topic_analysis
        
        # Should detect major philosophers
        philosophers = topic_analysis["philosophers_mentioned"]
        assert any("aristotle" in p.lower() for p in philosophers)
        assert any("kant" in p.lower() for p in philosophers)
        assert any("plato" in p.lower() for p in philosophers)


class TestSessionPreferences:
    """Test user preferences and settings management."""
    
    @pytest.fixture
    def chat_service(self):
        """Create chat service for testing."""
        return ChatService()
    
    def test_user_preferences_creation(self, chat_service):
        """Test creating user preferences."""
        user_id = "prefs_user"
        
        preferences = {
            "theme": "dark",
            "citation_style": "chicago",
            "auto_save": True,
            "notification_settings": {
                "email": False,
                "push": True
            },
            "display_preferences": {
                "show_timestamps": True,
                "message_grouping": "by_type",
                "font_size": "medium"
            }
        }
        
        result = chat_service.set_user_preferences(user_id, preferences)
        
        assert result is True
        stored_prefs = chat_service.get_user_preferences(user_id)
        assert stored_prefs["theme"] == "dark"
        assert stored_prefs["citation_style"] == "chicago"
        assert stored_prefs["display_preferences"]["font_size"] == "medium"
    
    def test_partial_preferences_update(self, chat_service):
        """Test updating only specific preference categories."""
        user_id = "partial_prefs_user"
        
        # Set initial preferences
        initial_prefs = {
            "theme": "light",
            "citation_style": "mla",
            "auto_save": False
        }
        chat_service.set_user_preferences(user_id, initial_prefs)
        
        # Update only theme
        partial_update = {"theme": "dark"}
        result = chat_service.update_user_preferences(user_id, partial_update)
        
        assert result is True
        updated_prefs = chat_service.get_user_preferences(user_id)
        assert updated_prefs["theme"] == "dark"
        assert updated_prefs["citation_style"] == "mla"  # Unchanged
        assert updated_prefs["auto_save"] is False  # Unchanged
    
    def test_default_preferences(self, chat_service):
        """Test default preferences for new users."""
        user_id = "default_user"
        
        prefs = chat_service.get_user_preferences(user_id)
        
        # Should return default preferences
        assert prefs is not None
        assert "theme" in prefs
        assert "citation_style" in prefs
        assert prefs["theme"] == "light"  # Default theme
        assert prefs["citation_style"] == "chicago"  # Default citation
    
    def test_preferences_validation(self, chat_service):
        """Test validation of preference values."""
        user_id = "validation_user"
        
        invalid_prefs = {
            "theme": "invalid_theme",
            "citation_style": "unknown_style",
            "font_size": "too_large"
        }
        
        result = chat_service.set_user_preferences(user_id, invalid_prefs)
        
        # Should reject invalid preferences
        assert result is False
        
        valid_prefs = {
            "theme": "dark",
            "citation_style": "apa",
            "font_size": "large"
        }
        
        result = chat_service.set_user_preferences(user_id, valid_prefs)
        assert result is True


class TestSessionIntegrationFeatures:
    """Test integration features for enhanced user experience."""
    
    @pytest.fixture
    def chat_service(self):
        """Create chat service for testing."""
        return ChatService()
    
    def test_session_tagging_system(self, chat_service):
        """Test adding and managing tags for sessions."""
        user_id = "tags_user"
        session = chat_service.create_session(user_id, "Tagged Session")
        
        # Add tags
        tags = ["aristotle", "virtue_ethics", "undergraduate"]
        result = chat_service.add_session_tags(session.session_id, tags)
        
        assert result is True
        tagged_session = chat_service.get_session(session.session_id)
        assert set(tagged_session.tags) == set(tags)
    
    def test_search_by_tags(self, chat_service):
        """Test searching sessions by tags."""
        user_id = "tag_search_user"
        
        # Create sessions with different tags
        session1 = chat_service.create_session(user_id, "Aristotle Session")
        session2 = chat_service.create_session(user_id, "Plato Session") 
        session3 = chat_service.create_session(user_id, "Kant Session")
        
        chat_service.add_session_tags(session1.session_id, ["aristotle", "ethics"])
        chat_service.add_session_tags(session2.session_id, ["plato", "metaphysics"])
        chat_service.add_session_tags(session3.session_id, ["kant", "ethics"])
        
        # Search by tag
        ethics_sessions = chat_service.search_sessions_by_tags(
            user_id, 
            tags=["ethics"]
        )
        
        assert len(ethics_sessions) == 2
        session_titles = [s.title for s in ethics_sessions]
        assert "Aristotle Session" in session_titles
        assert "Kant Session" in session_titles
    
    def test_session_collaboration_preparation(self, chat_service):
        """Test preparing session for collaboration/sharing."""
        user_id = "collab_user"
        session = chat_service.create_session(user_id, "Collaborative Session")
        
        # Add some content
        message = ChatMessage(
            message_id="collab_msg",
            content="Collaborative discussion content",
            message_type=MessageType.USER,
            timestamp=datetime.now(),
            user_id=user_id
        )
        chat_service.add_message_to_session(session.session_id, message)
        
        # Prepare for sharing
        share_data = chat_service.prepare_session_for_sharing(session.session_id)
        
        assert share_data is not None
        assert "session_id" in share_data
        assert "title" in share_data
        assert "message_count" in share_data
        assert "shareable_link" in share_data
        assert share_data["message_count"] == 1