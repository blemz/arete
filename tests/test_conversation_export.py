"""
Tests for conversation export functionality.

Tests cover export to different formats (PDF, Markdown, JSON), 
export validation, file generation, and integration with chat services.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import List, Dict, Any, Optional
import tempfile
import os
import json

from arete.services.conversation_export_service import (
    ConversationExportService,
    ExportFormat,
    ExportOptions,
    ExportResult
)
from arete.models.chat_session import (
    ChatSession,
    ChatMessage,
    MessageType,
    SessionStatus,
    ChatContext
)
from arete.services.chat_service import ChatService


class TestExportFormat:
    """Test export format enumeration and validation."""
    
    def test_export_format_values(self):
        """Test export format enum values."""
        assert ExportFormat.PDF.value == "pdf"
        assert ExportFormat.MARKDOWN.value == "markdown"
        assert ExportFormat.JSON.value == "json"
        assert ExportFormat.HTML.value == "html"
        assert ExportFormat.TXT.value == "txt"
    
    def test_export_format_from_string(self):
        """Test creating export format from string."""
        assert ExportFormat("pdf") == ExportFormat.PDF
        assert ExportFormat("markdown") == ExportFormat.MARKDOWN
        assert ExportFormat("json") == ExportFormat.JSON
    
    def test_invalid_export_format(self):
        """Test invalid export format raises error."""
        with pytest.raises(ValueError):
            ExportFormat("invalid_format")


class TestExportOptions:
    """Test export options configuration."""
    
    def test_export_options_defaults(self):
        """Test default export options."""
        options = ExportOptions()
        
        assert options.include_metadata is True
        assert options.include_citations is True
        assert options.include_timestamps is True
        assert options.include_context is True
        assert options.format_philosophical_quotes is True
        assert options.page_size == "A4"
        assert options.font_size == 12
    
    def test_export_options_customization(self):
        """Test customizing export options."""
        options = ExportOptions(
            include_metadata=False,
            include_citations=False,
            include_timestamps=False,
            page_size="Letter",
            font_size=14,
            custom_header="Custom Philosophy Session",
            watermark="Confidential"
        )
        
        assert options.include_metadata is False
        assert options.include_citations is False
        assert options.include_timestamps is False
        assert options.page_size == "Letter"
        assert options.font_size == 14
        assert options.custom_header == "Custom Philosophy Session"
        assert options.watermark == "Confidential"
    
    def test_export_options_validation(self):
        """Test export options validation."""
        # Valid font sizes
        valid_options = ExportOptions(font_size=10)
        assert valid_options.font_size == 10
        
        # Invalid font size should be adjusted
        with pytest.raises(ValueError):
            ExportOptions(font_size=6)  # Too small
        
        with pytest.raises(ValueError):
            ExportOptions(font_size=72)  # Too large
    
    def test_export_options_serialization(self):
        """Test export options to_dict serialization."""
        options = ExportOptions(
            include_metadata=False,
            page_size="Letter",
            custom_header="Test Header"
        )
        
        options_dict = options.to_dict()
        
        assert options_dict["include_metadata"] is False
        assert options_dict["page_size"] == "Letter"
        assert options_dict["custom_header"] == "Test Header"


class TestExportResult:
    """Test export result model."""
    
    def test_export_result_creation(self):
        """Test creating export result."""
        result = ExportResult(
            success=True,
            file_path="/tmp/export.pdf",
            format=ExportFormat.PDF,
            file_size=1024,
            export_time=2.5,
            message_count=10
        )
        
        assert result.success is True
        assert result.file_path == "/tmp/export.pdf"
        assert result.format == ExportFormat.PDF
        assert result.file_size == 1024
        assert result.export_time == 2.5
        assert result.message_count == 10
        assert result.error_message is None
    
    def test_export_result_failure(self):
        """Test export result for failed export."""
        result = ExportResult(
            success=False,
            error_message="Permission denied",
            format=ExportFormat.PDF
        )
        
        assert result.success is False
        assert result.error_message == "Permission denied"
        assert result.file_path is None
        assert result.file_size is None
    
    def test_export_result_serialization(self):
        """Test export result serialization."""
        result = ExportResult(
            success=True,
            file_path="/tmp/test.pdf",
            format=ExportFormat.PDF,
            file_size=2048,
            export_time=1.5,
            message_count=5
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["success"] is True
        assert result_dict["file_path"] == "/tmp/test.pdf"
        assert result_dict["format"] == "pdf"
        assert result_dict["file_size"] == 2048


class TestConversationExportService:
    """Test conversation export service functionality."""
    
    @pytest.fixture
    def export_service(self):
        """Create export service for testing."""
        return ConversationExportService()
    
    @pytest.fixture
    def sample_session(self):
        """Create sample chat session for export testing."""
        session = ChatSession(
            session_id="export_test_session",
            user_id="export_test_user",
            title="Philosophy Discussion on Virtue Ethics",
            status=SessionStatus.COMPLETED
        )
        
        # Add sample messages
        messages = [
            ChatMessage(
                message_id="msg_1",
                content="What is virtue according to Aristotle?",
                message_type=MessageType.USER,
                timestamp=datetime(2025, 8, 26, 10, 0, 0),
                user_id="export_test_user"
            ),
            ChatMessage(
                message_id="msg_2",
                content="For Aristotle, virtue (arete) is a disposition to act excellently, achieved through habituation and finding the golden mean between extremes of excess and deficiency.",
                message_type=MessageType.ASSISTANT,
                timestamp=datetime(2025, 8, 26, 10, 1, 0),
                citations=["Nicomachean Ethics 1103a", "Ethics 1107a"],
                metadata={
                    "provider": "anthropic",
                    "response_time": 1.2,
                    "token_count": 45
                }
            ),
            ChatMessage(
                message_id="msg_3",
                content="Can you give an example of the golden mean?",
                message_type=MessageType.USER,
                timestamp=datetime(2025, 8, 26, 10, 2, 0),
                user_id="export_test_user"
            ),
            ChatMessage(
                message_id="msg_4",
                content="Certainly! Courage is the golden mean between cowardice (deficiency) and recklessness (excess). A courageous person faces appropriate dangers at the right time, in the right way, for the right reasons.",
                message_type=MessageType.ASSISTANT,
                timestamp=datetime(2025, 8, 26, 10, 3, 0),
                citations=["Ethics 1115a", "Ethics 1117a"],
                metadata={
                    "provider": "anthropic",
                    "response_time": 0.8,
                    "token_count": 32
                }
            )
        ]
        
        for msg in messages:
            session.add_message(msg)
        
        # Set context
        session.context = ChatContext(
            student_level="undergraduate",
            philosophical_period="ancient",
            current_topic="virtue ethics",
            learning_objectives=["understand Aristotelian virtue", "golden mean concept"]
        )
        
        return session
    
    def test_export_to_json(self, export_service, sample_session):
        """Test exporting conversation to JSON format."""
        options = ExportOptions(include_metadata=True)
        
        result = export_service.export_session(
            sample_session,
            ExportFormat.JSON,
            options
        )
        
        assert result.success is True
        assert result.format == ExportFormat.JSON
        assert result.file_path is not None
        assert result.file_path.endswith('.json')
        assert result.message_count == 4
        assert result.export_time > 0
        
        # Verify JSON content
        with open(result.file_path, 'r', encoding='utf-8') as f:
            exported_data = json.load(f)
        
        assert exported_data["session_id"] == "export_test_session"
        assert exported_data["title"] == "Philosophy Discussion on Virtue Ethics"
        assert len(exported_data["messages"]) == 4
        assert exported_data["context"]["current_topic"] == "virtue ethics"
        
        # Clean up
        os.unlink(result.file_path)
    
    def test_export_to_markdown(self, export_service, sample_session):
        """Test exporting conversation to Markdown format."""
        options = ExportOptions(
            include_timestamps=True,
            include_citations=True,
            format_philosophical_quotes=True
        )
        
        result = export_service.export_session(
            sample_session,
            ExportFormat.MARKDOWN,
            options
        )
        
        assert result.success is True
        assert result.format == ExportFormat.MARKDOWN
        assert result.file_path.endswith('.md')
        assert result.message_count == 4
        
        # Verify Markdown content
        with open(result.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "# Philosophy Discussion on Virtue Ethics" in content
        assert "## User" in content
        assert "## Assistant" in content
        assert "What is virtue according to Aristotle?" in content
        assert "Nicomachean Ethics 1103a" in content
        assert "virtue (arete)" in content
        
        # Clean up
        os.unlink(result.file_path)
    
    @patch('arete.services.conversation_export_service.FPDF')
    def test_export_to_pdf(self, mock_fpdf, export_service, sample_session):
        """Test exporting conversation to PDF format."""
        # Mock FPDF instance
        mock_pdf = Mock()
        mock_fpdf.return_value = mock_pdf
        
        options = ExportOptions(
            include_metadata=True,
            page_size="A4",
            font_size=12
        )
        
        result = export_service.export_session(
            sample_session,
            ExportFormat.PDF,
            options
        )
        
        assert result.success is True
        assert result.format == ExportFormat.PDF
        assert result.file_path.endswith('.pdf')
        assert result.message_count == 4
        
        # Verify PDF creation calls
        mock_pdf.add_page.assert_called()
        mock_pdf.set_font.assert_called()
        mock_pdf.cell.assert_called()
        mock_pdf.output.assert_called()
    
    def test_export_to_html(self, export_service, sample_session):
        """Test exporting conversation to HTML format."""
        options = ExportOptions(
            include_timestamps=True,
            include_citations=True,
            custom_header="Philosophical Discussion Export"
        )
        
        result = export_service.export_session(
            sample_session,
            ExportFormat.HTML,
            options
        )
        
        assert result.success is True
        assert result.format == ExportFormat.HTML
        assert result.file_path.endswith('.html')
        
        # Verify HTML content
        with open(result.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "<html>" in content
        assert "<head>" in content
        assert "<title>Philosophy Discussion on Virtue Ethics</title>" in content
        assert "<div class=\"message user\">" in content
        assert "<div class=\"message assistant\">" in content
        assert "Philosophical Discussion Export" in content
        
        # Clean up
        os.unlink(result.file_path)
    
    def test_export_to_txt(self, export_service, sample_session):
        """Test exporting conversation to plain text format."""
        options = ExportOptions(
            include_timestamps=True,
            include_citations=False,
            include_metadata=False
        )
        
        result = export_service.export_session(
            sample_session,
            ExportFormat.TXT,
            options
        )
        
        assert result.success is True
        assert result.format == ExportFormat.TXT
        assert result.file_path.endswith('.txt')
        
        # Verify text content
        with open(result.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "Philosophy Discussion on Virtue Ethics" in content
        assert "User:" in content
        assert "Assistant:" in content
        assert "[2025-08-26 10:00:00]" in content
        assert "What is virtue according to Aristotle?" in content
        # Citations should be excluded
        assert "Nicomachean Ethics" not in content
        
        # Clean up
        os.unlink(result.file_path)
    
    def test_export_with_minimal_options(self, export_service, sample_session):
        """Test export with minimal options (no metadata, timestamps, etc.)."""
        options = ExportOptions(
            include_metadata=False,
            include_citations=False,
            include_timestamps=False,
            include_context=False
        )
        
        result = export_service.export_session(
            sample_session,
            ExportFormat.MARKDOWN,
            options
        )
        
        assert result.success is True
        
        # Verify minimal content
        with open(result.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "Philosophy Discussion on Virtue Ethics" in content
        assert "What is virtue according to Aristotle?" in content
        # Should not include timestamps
        assert "2025-08-26" not in content
        # Should not include citations
        assert "Nicomachean Ethics" not in content
        # Should not include context
        assert "undergraduate" not in content
        
        # Clean up
        os.unlink(result.file_path)
    
    def test_export_empty_session(self, export_service):
        """Test exporting empty session."""
        empty_session = ChatSession(
            session_id="empty_session",
            user_id="test_user",
            title="Empty Session"
        )
        
        result = export_service.export_session(
            empty_session,
            ExportFormat.MARKDOWN,
            ExportOptions()
        )
        
        assert result.success is True
        assert result.message_count == 0
        
        # Verify content
        with open(result.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "Empty Session" in content
        assert "No messages in this conversation" in content
        
        # Clean up
        os.unlink(result.file_path)
    
    def test_export_invalid_format(self, export_service, sample_session):
        """Test export with invalid format."""
        with pytest.raises(ValueError):
            export_service.export_session(
                sample_session,
                "invalid_format",  # Invalid format
                ExportOptions()
            )
    
    def test_export_file_permission_error(self, export_service, sample_session):
        """Test export with file permission error."""
        options = ExportOptions()
        
        # Mock open to raise PermissionError
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            result = export_service.export_session(
                sample_session,
                ExportFormat.JSON,
                options
            )
        
        assert result.success is False
        assert "Access denied" in result.error_message
        assert result.file_path is None
    
    def test_export_large_session(self, export_service):
        """Test exporting large session with many messages."""
        large_session = ChatSession(
            session_id="large_session",
            user_id="test_user",
            title="Large Philosophical Discussion"
        )
        
        # Add many messages
        for i in range(100):
            user_msg = ChatMessage(
                message_id=f"user_msg_{i}",
                content=f"User question {i} about philosophical concept",
                message_type=MessageType.USER,
                timestamp=datetime(2025, 8, 26, 10, i % 60, 0),
                user_id="test_user"
            )
            
            assistant_msg = ChatMessage(
                message_id=f"assistant_msg_{i}",
                content=f"Assistant response {i} explaining philosophical concept with detailed analysis and references to classical works.",
                message_type=MessageType.ASSISTANT,
                timestamp=datetime(2025, 8, 26, 10, i % 60, 30),
                citations=[f"Source {i}", f"Reference {i}"]
            )
            
            large_session.add_message(user_msg)
            large_session.add_message(assistant_msg)
        
        result = export_service.export_session(
            large_session,
            ExportFormat.JSON,
            ExportOptions()
        )
        
        assert result.success is True
        assert result.message_count == 200
        assert result.file_size > 10000  # Should be substantial file
        
        # Clean up
        os.unlink(result.file_path)
    
    def test_export_with_special_characters(self, export_service):
        """Test export with special characters and unicode."""
        special_session = ChatSession(
            session_id="special_chars_session",
            user_id="test_user",
            title="Φιλοσοφία Discussion with Special Characters"
        )
        
        special_messages = [
            ChatMessage(
                message_id="special_1",
                content="What about αρετή (virtue) in ancient Greek philosophy?",
                message_type=MessageType.USER,
                timestamp=datetime.now(),
                user_id="test_user"
            ),
            ChatMessage(
                message_id="special_2",
                content="The concept of αρετή (arete) is central to Greek ethics. It represents excellence of character—not just moral goodness, but flourishing in one's essential nature. As Aristotle wrote: \"Excellence, then, is not an act but a habit.\"",
                message_type=MessageType.ASSISTANT,
                timestamp=datetime.now(),
                citations=["Ἠθικὰ Νικομάχεια 1103a"]
            )
        ]
        
        for msg in special_messages:
            special_session.add_message(msg)
        
        result = export_service.export_session(
            special_session,
            ExportFormat.MARKDOWN,
            ExportOptions()
        )
        
        assert result.success is True
        
        # Verify unicode handling
        with open(result.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "Φιλοσοφία" in content
        assert "αρετή" in content
        assert "Ἠθικὰ Νικομάχεια" in content
        
        # Clean up
        os.unlink(result.file_path)


class TestExportServiceIntegration:
    """Test export service integration with other services."""
    
    @pytest.fixture
    def export_service(self):
        """Create export service for testing."""
        return ConversationExportService()
    
    @pytest.fixture
    def chat_service(self):
        """Create chat service for testing."""
        return ChatService()
    
    def test_export_from_chat_service(self, export_service, chat_service):
        """Test exporting session directly from chat service."""
        # Create session through chat service
        session = chat_service.create_session(
            user_id="integration_user",
            title="Integration Test Session"
        )
        
        # Add messages
        test_message = ChatMessage(
            message_id="integration_msg",
            content="Test message for integration",
            message_type=MessageType.USER,
            timestamp=datetime.now(),
            user_id="integration_user"
        )
        
        chat_service.add_message_to_session(session.session_id, test_message)
        
        # Export session
        result = export_service.export_session(
            session,
            ExportFormat.JSON,
            ExportOptions()
        )
        
        assert result.success is True
        assert result.message_count == 1
        
        # Verify exported content
        with open(result.file_path, 'r', encoding='utf-8') as f:
            exported_data = json.load(f)
        
        assert exported_data["session_id"] == session.session_id
        assert exported_data["title"] == "Integration Test Session"
        assert len(exported_data["messages"]) == 1
        
        # Clean up
        os.unlink(result.file_path)
    
    def test_bulk_export_sessions(self, export_service, chat_service):
        """Test bulk export of multiple sessions."""
        sessions = []
        
        # Create multiple sessions
        for i in range(3):
            session = chat_service.create_session(
                user_id="bulk_user",
                title=f"Bulk Export Session {i+1}"
            )
            
            # Add a message
            message = ChatMessage(
                message_id=f"bulk_msg_{i}",
                content=f"Message for session {i+1}",
                message_type=MessageType.USER,
                timestamp=datetime.now(),
                user_id="bulk_user"
            )
            
            chat_service.add_message_to_session(session.session_id, message)
            sessions.append(session)
        
        # Bulk export
        results = export_service.bulk_export_sessions(
            sessions,
            ExportFormat.MARKDOWN,
            ExportOptions()
        )
        
        assert len(results) == 3
        assert all(result.success for result in results)
        assert all(result.message_count == 1 for result in results)
        
        # Clean up
        for result in results:
            os.unlink(result.file_path)
    
    def test_export_with_user_preferences(self, export_service):
        """Test export respecting user preferences."""
        # This would test integration with user preferences service
        # for things like citation style, formatting preferences, etc.
        
        session = ChatSession(
            session_id="prefs_session",
            user_id="prefs_user",
            title="Preferences Test Session"
        )
        
        message = ChatMessage(
            message_id="prefs_msg",
            content="Test message with citation",
            message_type=MessageType.ASSISTANT,
            timestamp=datetime.now(),
            citations=["Republic 514a"]
        )
        
        session.add_message(message)
        
        # Export with different citation preferences
        chicago_options = ExportOptions(citation_style="chicago")
        mla_options = ExportOptions(citation_style="mla")
        
        chicago_result = export_service.export_session(
            session,
            ExportFormat.MARKDOWN,
            chicago_options
        )
        
        mla_result = export_service.export_session(
            session,
            ExportFormat.MARKDOWN,
            mla_options
        )
        
        assert chicago_result.success is True
        assert mla_result.success is True
        
        # Verify different citation formats (simplified test)
        with open(chicago_result.file_path, 'r') as f:
            chicago_content = f.read()
        
        with open(mla_result.file_path, 'r') as f:
            mla_content = f.read()
        
        # Both should contain the citation but potentially formatted differently
        assert "Republic 514a" in chicago_content
        assert "Republic 514a" in mla_content
        
        # Clean up
        os.unlink(chicago_result.file_path)
        os.unlink(mla_result.file_path)