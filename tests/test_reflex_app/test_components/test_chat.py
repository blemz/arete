"""Tests for chat component."""
import pytest
from unittest.mock import Mock, patch
import reflex as rx
from src.arete.ui.reflex_app.components.chat import ChatComponent


class TestChatComponent:
    """Test cases for ChatComponent."""

    @pytest.fixture
    def chat_component(self):
        """ChatComponent instance for testing."""
        return ChatComponent()

    def test_chat_component_initialization(self, chat_component):
        """Test chat component initialization."""
        assert chat_component is not None
        assert hasattr(chat_component, 'render')

    def test_render_empty_chat(self, chat_component):
        """Test rendering chat with no messages."""
        with patch('src.arete.ui.reflex_app.state.chat_state.ChatState') as mock_state:
            mock_state.messages = []
            mock_state.is_loading = False
            mock_state.error_message = ""
            
            rendered = chat_component.render()
            
            assert rendered is not None

    def test_render_chat_with_messages(self, chat_component):
        """Test rendering chat with messages."""
        messages = [
            {
                "role": "user",
                "content": "What is virtue?",
                "timestamp": "2025-01-01T12:00:00"
            },
            {
                "role": "assistant",
                "content": "Virtue is moral excellence.",
                "timestamp": "2025-01-01T12:00:01",
                "citations": [],
                "entities": []
            }
        ]
        
        with patch('src.arete.ui.reflex_app.state.chat_state.ChatState') as mock_state:
            mock_state.messages = messages
            mock_state.is_loading = False
            
            rendered = chat_component.render()
            
            assert rendered is not None

    def test_render_loading_state(self, chat_component):
        """Test rendering chat in loading state."""
        with patch('src.arete.ui.reflex_app.state.chat_state.ChatState') as mock_state:
            mock_state.messages = []
            mock_state.is_loading = True
            mock_state.current_message = "What is virtue?"
            
            rendered = chat_component.render()
            
            assert rendered is not None

    def test_render_error_state(self, chat_component):
        """Test rendering chat with error."""
        with patch('src.arete.ui.reflex_app.state.chat_state.ChatState') as mock_state:
            mock_state.messages = []
            mock_state.error_message = "Connection failed"
            mock_state.is_loading = False
            
            rendered = chat_component.render()
            
            assert rendered is not None

    def test_message_input_component(self, chat_component):
        """Test message input component."""
        input_component = chat_component.create_message_input()
        
        assert input_component is not None

    def test_send_message_button(self, chat_component):
        """Test send message button."""
        button = chat_component.create_send_button()
        
        assert button is not None

    def test_message_list_component(self, chat_component):
        """Test message list component."""
        messages = [
            {"role": "user", "content": "Hello", "timestamp": "2025-01-01T12:00:00"},
            {"role": "assistant", "content": "Hi!", "timestamp": "2025-01-01T12:00:01", "citations": [], "entities": []}
        ]
        
        message_list = chat_component.create_message_list(messages)
        
        assert message_list is not None

    def test_user_message_bubble(self, chat_component):
        """Test user message bubble rendering."""
        message = {
            "role": "user",
            "content": "What is virtue?",
            "timestamp": "2025-01-01T12:00:00"
        }
        
        bubble = chat_component.create_user_message_bubble(message)
        
        assert bubble is not None

    def test_assistant_message_bubble(self, chat_component):
        """Test assistant message bubble rendering."""
        message = {
            "role": "assistant",
            "content": "Virtue is moral excellence.",
            "timestamp": "2025-01-01T12:00:01",
            "citations": [{"chunk_id": "chunk_1", "source_text": "test"}],
            "entities": [{"name": "Virtue", "type": "Concept"}]
        }
        
        bubble = chat_component.create_assistant_message_bubble(message)
        
        assert bubble is not None

    def test_citation_display(self, chat_component):
        """Test citation display component."""
        citations = [
            {
                "chunk_id": "chunk_1",
                "source_text": "Virtue is the excellence of character.",
                "relevance_score": 0.85,
                "source": "Aristotle's Nicomachean Ethics"
            }
        ]
        
        citation_component = chat_component.create_citation_display(citations)
        
        assert citation_component is not None

    def test_entity_display(self, chat_component):
        """Test entity display component."""
        entities = [
            {"name": "Virtue", "type": "Concept", "description": "Moral excellence"},
            {"name": "Aristotle", "type": "Person", "description": "Greek philosopher"}
        ]
        
        entity_component = chat_component.create_entity_display(entities)
        
        assert entity_component is not None

    def test_typing_indicator(self, chat_component):
        """Test typing indicator component."""
        indicator = chat_component.create_typing_indicator()
        
        assert indicator is not None

    def test_error_message_display(self, chat_component):
        """Test error message display."""
        error_display = chat_component.create_error_display("Connection failed")
        
        assert error_display is not None

    def test_message_timestamp_formatting(self, chat_component):
        """Test message timestamp formatting."""
        timestamp = "2025-01-01T12:30:45"
        
        formatted = chat_component.format_timestamp(timestamp)
        
        assert formatted is not None
        assert isinstance(formatted, str)

    def test_message_content_sanitization(self, chat_component):
        """Test message content sanitization."""
        malicious_content = "<script>alert('xss')</script>Hello"
        
        sanitized = chat_component.sanitize_content(malicious_content)
        
        assert "<script>" not in sanitized
        assert "Hello" in sanitized

    def test_markdown_rendering(self, chat_component):
        """Test markdown content rendering."""
        markdown_content = "**Bold text** and *italic text*"
        
        rendered = chat_component.render_markdown(markdown_content)
        
        assert rendered is not None

    def test_code_block_rendering(self, chat_component):
        """Test code block rendering."""
        code_content = "```python\nprint('Hello, World!')\n```"
        
        rendered = chat_component.render_code_block(code_content)
        
        assert rendered is not None

    def test_citation_hover_preview(self, chat_component):
        """Test citation hover preview."""
        citation = {
            "chunk_id": "chunk_1",
            "source_text": "This is a long citation text that should be previewed on hover.",
            "relevance_score": 0.9
        }
        
        preview = chat_component.create_citation_hover_preview(citation)
        
        assert preview is not None

    def test_message_actions_menu(self, chat_component):
        """Test message actions menu."""
        message = {
            "role": "assistant",
            "content": "Test response",
            "timestamp": "2025-01-01T12:00:00"
        }
        
        actions_menu = chat_component.create_message_actions_menu(message)
        
        assert actions_menu is not None

    def test_conversation_export_button(self, chat_component):
        """Test conversation export button."""
        export_button = chat_component.create_export_button()
        
        assert export_button is not None

    def test_clear_conversation_button(self, chat_component):
        """Test clear conversation button."""
        clear_button = chat_component.create_clear_button()
        
        assert clear_button is not None

    def test_message_search_functionality(self, chat_component):
        """Test message search functionality."""
        search_component = chat_component.create_message_search()
        
        assert search_component is not None

    def test_auto_scroll_to_bottom(self, chat_component):
        """Test auto-scroll to bottom functionality."""
        with patch.object(chat_component, '_scroll_to_bottom') as mock_scroll:
            chat_component.handle_new_message()
            
            mock_scroll.assert_called_once()

    def test_message_copy_functionality(self, chat_component):
        """Test message copy to clipboard."""
        message_content = "This is a test message to copy."
        
        with patch('pyperclip.copy') as mock_copy:
            chat_component.copy_message_to_clipboard(message_content)
            
            mock_copy.assert_called_once_with(message_content)

    def test_regenerate_response_button(self, chat_component):
        """Test regenerate response button."""
        regenerate_button = chat_component.create_regenerate_button()
        
        assert regenerate_button is not None

    def test_follow_up_suggestions(self, chat_component):
        """Test follow-up question suggestions."""
        suggestions = [
            "What did Plato say about virtue?",
            "How does virtue relate to happiness?",
            "What are the cardinal virtues?"
        ]
        
        suggestion_component = chat_component.create_follow_up_suggestions(suggestions)
        
        assert suggestion_component is not None

    def test_keyboard_shortcuts(self, chat_component):
        """Test keyboard shortcuts handling."""
        with patch.object(chat_component, 'handle_keyboard_shortcut') as mock_handler:
            # Simulate Ctrl+Enter
            event = {"key": "Enter", "ctrlKey": True}
            chat_component.handle_keyboard_event(event)
            
            mock_handler.assert_called_once()

    def test_message_thread_rendering(self, chat_component):
        """Test message thread rendering."""
        thread_messages = [
            {"role": "user", "content": "What is virtue?"},
            {"role": "assistant", "content": "Virtue is..."},
            {"role": "user", "content": "Can you elaborate?"},
            {"role": "assistant", "content": "Certainly..."}
        ]
        
        thread = chat_component.create_message_thread(thread_messages)
        
        assert thread is not None

    def test_responsive_design_mobile(self, chat_component):
        """Test responsive design for mobile."""
        with patch.object(chat_component, 'is_mobile_view', return_value=True):
            mobile_layout = chat_component.render_mobile_layout()
            
            assert mobile_layout is not None

    def test_responsive_design_desktop(self, chat_component):
        """Test responsive design for desktop."""
        with patch.object(chat_component, 'is_mobile_view', return_value=False):
            desktop_layout = chat_component.render_desktop_layout()
            
            assert desktop_layout is not None

    def test_accessibility_features(self, chat_component):
        """Test accessibility features."""
        # Test ARIA labels
        message_bubble = chat_component.create_user_message_bubble({
            "role": "user",
            "content": "Test message",
            "timestamp": "2025-01-01T12:00:00"
        })
        
        assert message_bubble is not None
        # Should include appropriate ARIA attributes

    def test_drag_and_drop_file_upload(self, chat_component):
        """Test drag and drop file upload."""
        drop_zone = chat_component.create_file_drop_zone()
        
        assert drop_zone is not None

    def test_voice_input_button(self, chat_component):
        """Test voice input functionality."""
        voice_button = chat_component.create_voice_input_button()
        
        assert voice_button is not None

    def test_chat_theme_customization(self, chat_component):
        """Test chat theme customization."""
        with patch.object(chat_component, 'apply_theme') as mock_theme:
            chat_component.set_theme("dark")
            
            mock_theme.assert_called_once_with("dark")

    def test_message_reaction_system(self, chat_component):
        """Test message reaction system."""
        reactions = ["👍", "👎", "❤️", "🤔"]
        
        reaction_component = chat_component.create_message_reactions(reactions)
        
        assert reaction_component is not None

    def test_chat_performance_optimization(self, chat_component):
        """Test chat performance with large message history."""
        # Simulate large message history
        large_history = [
            {"role": "user", "content": f"Message {i}", "timestamp": f"2025-01-01T12:{i:02d}:00"}
            for i in range(100)
        ]
        
        with patch.object(chat_component, 'virtualize_messages') as mock_virtualize:
            chat_component.render_large_history(large_history)
            
            # Should use virtualization for performance
            mock_virtualize.assert_called_once()

    def test_chat_input_validation(self, chat_component):
        """Test chat input validation."""
        # Test empty input
        assert chat_component.validate_input("") == False
        
        # Test valid input
        assert chat_component.validate_input("What is virtue?") == True
        
        # Test input too long
        long_input = "x" * 10000
        assert chat_component.validate_input(long_input) == False

    def test_chat_animation_effects(self, chat_component):
        """Test chat animation effects."""
        with patch.object(chat_component, 'animate_message_appearance') as mock_animate:
            message = {"role": "assistant", "content": "New message"}
            chat_component.add_message_with_animation(message)
            
            mock_animate.assert_called_once()

    def test_chat_scroll_behavior(self, chat_component):
        """Test chat scroll behavior."""
        with patch.object(chat_component, 'should_auto_scroll') as mock_scroll_check:
            mock_scroll_check.return_value = True
            
            chat_component.handle_new_message()
            
            mock_scroll_check.assert_called_once()