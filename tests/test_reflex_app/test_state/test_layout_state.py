"""Tests for layout state management."""
import pytest
from unittest.mock import Mock, patch
from src.arete.ui.reflex_app.state.layout_state import LayoutState


class TestLayoutState:
    """Test cases for LayoutState."""

    @pytest.fixture
    def layout_state(self):
        """LayoutState instance for testing."""
        return LayoutState()

    def test_initial_state(self, layout_state):
        """Test initial state values."""
        assert layout_state.chat_panel_width == 50  # Default 50% split
        assert layout_state.document_panel_width == 50
        assert layout_state.sidebar_collapsed == False
        assert layout_state.current_theme == "light"
        assert layout_state.mobile_view == False

    def test_set_panel_split(self, layout_state):
        """Test setting panel split ratio."""
        layout_state.set_panel_split(60, 40)
        
        assert layout_state.chat_panel_width == 60
        assert layout_state.document_panel_width == 40

    def test_set_panel_split_validation(self, layout_state):
        """Test panel split validation."""
        # Valid splits
        layout_state.set_panel_split(70, 30)
        assert layout_state.chat_panel_width == 70
        
        # Invalid splits (don't sum to 100)
        layout_state.set_panel_split(60, 50)
        # Should maintain previous valid state or normalize
        assert layout_state.chat_panel_width + layout_state.document_panel_width == 100

    def test_toggle_sidebar(self, layout_state):
        """Test sidebar toggle functionality."""
        assert layout_state.sidebar_collapsed == False
        
        layout_state.toggle_sidebar()
        assert layout_state.sidebar_collapsed == True
        
        layout_state.toggle_sidebar()
        assert layout_state.sidebar_collapsed == False

    def test_set_theme(self, layout_state):
        """Test theme setting."""
        layout_state.set_theme("dark")
        assert layout_state.current_theme == "dark"
        
        layout_state.set_theme("light")
        assert layout_state.current_theme == "light"

    def test_set_invalid_theme(self, layout_state):
        """Test setting invalid theme."""
        original_theme = layout_state.current_theme
        layout_state.set_theme("invalid_theme")
        
        # Should maintain previous theme or default to light
        assert layout_state.current_theme in ["light", "dark", original_theme]

    def test_toggle_mobile_view(self, layout_state):
        """Test mobile view toggle."""
        assert layout_state.mobile_view == False
        
        layout_state.toggle_mobile_view()
        assert layout_state.mobile_view == True
        
        layout_state.toggle_mobile_view()
        assert layout_state.mobile_view == False

    def test_set_mobile_view(self, layout_state):
        """Test explicitly setting mobile view."""
        layout_state.set_mobile_view(True)
        assert layout_state.mobile_view == True
        
        layout_state.set_mobile_view(False)
        assert layout_state.mobile_view == False

    def test_resize_chat_panel(self, layout_state):
        """Test resizing chat panel."""
        layout_state.resize_chat_panel(65)
        
        assert layout_state.chat_panel_width == 65
        assert layout_state.document_panel_width == 35

    def test_resize_chat_panel_bounds(self, layout_state):
        """Test chat panel resize bounds."""
        # Test minimum bound
        layout_state.resize_chat_panel(10)
        assert layout_state.chat_panel_width >= 20  # Minimum width
        
        # Test maximum bound
        layout_state.resize_chat_panel(95)
        assert layout_state.chat_panel_width <= 80  # Maximum width

    def test_resize_document_panel(self, layout_state):
        """Test resizing document panel."""
        layout_state.resize_document_panel(60)
        
        assert layout_state.document_panel_width == 60
        assert layout_state.chat_panel_width == 40

    def test_reset_layout(self, layout_state):
        """Test resetting layout to defaults."""
        # Modify layout
        layout_state.set_panel_split(70, 30)
        layout_state.toggle_sidebar()
        layout_state.set_theme("dark")
        
        # Reset
        layout_state.reset_layout()
        
        assert layout_state.chat_panel_width == 50
        assert layout_state.document_panel_width == 50
        assert layout_state.sidebar_collapsed == False
        assert layout_state.current_theme == "light"

    def test_get_layout_config(self, layout_state):
        """Test getting layout configuration."""
        layout_state.set_panel_split(60, 40)
        layout_state.set_theme("dark")
        layout_state.toggle_sidebar()
        
        config = layout_state.get_layout_config()
        
        assert config["chat_panel_width"] == 60
        assert config["document_panel_width"] == 40
        assert config["theme"] == "dark"
        assert config["sidebar_collapsed"] == True

    def test_set_layout_config(self, layout_state):
        """Test setting layout from configuration."""
        config = {
            "chat_panel_width": 65,
            "document_panel_width": 35,
            "theme": "dark",
            "sidebar_collapsed": True,
            "mobile_view": True
        }
        
        layout_state.set_layout_config(config)
        
        assert layout_state.chat_panel_width == 65
        assert layout_state.document_panel_width == 35
        assert layout_state.current_theme == "dark"
        assert layout_state.sidebar_collapsed == True
        assert layout_state.mobile_view == True

    def test_get_css_variables(self, layout_state):
        """Test getting CSS variables for layout."""
        layout_state.set_panel_split(60, 40)
        
        css_vars = layout_state.get_css_variables()
        
        assert "--chat-panel-width" in css_vars
        assert "--document-panel-width" in css_vars
        assert css_vars["--chat-panel-width"] == "60%"
        assert css_vars["--document-panel-width"] == "40%"

    def test_is_panel_collapsed(self, layout_state):
        """Test checking if panel is collapsed."""
        # Initially not collapsed
        assert layout_state.is_panel_collapsed("chat") == False
        assert layout_state.is_panel_collapsed("document") == False
        
        # Collapse chat panel by setting width to 0
        layout_state.resize_chat_panel(0)
        assert layout_state.is_panel_collapsed("chat") == True

    def test_maximize_panel(self, layout_state):
        """Test maximizing a panel."""
        layout_state.maximize_panel("chat")
        
        assert layout_state.chat_panel_width >= 80
        assert layout_state.document_panel_width <= 20

    def test_minimize_panel(self, layout_state):
        """Test minimizing a panel."""
        layout_state.minimize_panel("document")
        
        assert layout_state.document_panel_width <= 20
        assert layout_state.chat_panel_width >= 80

    def test_set_responsive_breakpoint(self, layout_state):
        """Test setting responsive breakpoint."""
        # Simulate mobile breakpoint
        layout_state.set_responsive_breakpoint(768)
        
        assert layout_state.mobile_view == True
        assert layout_state.chat_panel_width == 100  # Full width on mobile

    def test_get_available_themes(self, layout_state):
        """Test getting available themes."""
        themes = layout_state.get_available_themes()
        
        assert "light" in themes
        assert "dark" in themes
        assert isinstance(themes, list)
        assert len(themes) >= 2

    def test_save_layout_preferences(self, layout_state):
        """Test saving layout preferences."""
        layout_state.set_panel_split(60, 40)
        layout_state.set_theme("dark")
        
        with patch.object(layout_state, '_save_to_storage') as mock_save:
            layout_state.save_layout_preferences("user_123")
            
            mock_save.assert_called_once()
            saved_data = mock_save.call_args[0][1]
            assert saved_data["chat_panel_width"] == 60
            assert saved_data["theme"] == "dark"

    def test_load_layout_preferences(self, layout_state):
        """Test loading layout preferences."""
        saved_preferences = {
            "chat_panel_width": 65,
            "document_panel_width": 35,
            "theme": "dark",
            "sidebar_collapsed": True
        }
        
        with patch.object(layout_state, '_load_from_storage') as mock_load:
            mock_load.return_value = saved_preferences
            
            layout_state.load_layout_preferences("user_123")
            
            assert layout_state.chat_panel_width == 65
            assert layout_state.current_theme == "dark"
            assert layout_state.sidebar_collapsed == True

    def test_get_panel_styles(self, layout_state):
        """Test getting panel styles."""
        layout_state.set_panel_split(60, 40)
        
        chat_styles = layout_state.get_panel_styles("chat")
        document_styles = layout_state.get_panel_styles("document")
        
        assert "width" in chat_styles
        assert "width" in document_styles
        assert chat_styles["width"] == "60%"
        assert document_styles["width"] == "40%"

    def test_handle_window_resize(self, layout_state):
        """Test handling window resize events."""
        # Simulate window resize to mobile size
        layout_state.handle_window_resize(600, 800)
        
        assert layout_state.mobile_view == True
        
        # Simulate window resize to desktop size
        layout_state.handle_window_resize(1200, 800)
        
        assert layout_state.mobile_view == False

    def test_set_panel_visibility(self, layout_state):
        """Test setting panel visibility."""
        layout_state.set_panel_visibility("document", False)
        
        assert layout_state.document_panel_visible == False
        assert layout_state.chat_panel_width == 100  # Chat takes full width

    def test_toggle_panel_visibility(self, layout_state):
        """Test toggling panel visibility."""
        layout_state.toggle_panel_visibility("document")
        
        assert layout_state.document_panel_visible == False
        
        layout_state.toggle_panel_visibility("document")
        
        assert layout_state.document_panel_visible == True

    def test_get_mobile_layout_config(self, layout_state):
        """Test getting mobile-specific layout config."""
        layout_state.set_mobile_view(True)
        
        mobile_config = layout_state.get_mobile_layout_config()
        
        assert mobile_config["chat_panel_width"] == 100
        assert mobile_config["document_panel_width"] == 0
        assert mobile_config["stack_panels"] == True

    def test_set_animation_enabled(self, layout_state):
        """Test enabling/disabling layout animations."""
        layout_state.set_animation_enabled(True)
        assert layout_state.animations_enabled == True
        
        layout_state.set_animation_enabled(False)
        assert layout_state.animations_enabled == False

    def test_get_transition_styles(self, layout_state):
        """Test getting CSS transition styles."""
        layout_state.set_animation_enabled(True)
        
        transitions = layout_state.get_transition_styles()
        
        assert "transition" in transitions
        assert "width" in transitions["transition"]

    def test_validate_layout_state(self, layout_state):
        """Test layout state validation."""
        # Valid state
        assert layout_state.validate_layout_state() == True
        
        # Invalid state (panels don't sum to 100)
        layout_state.chat_panel_width = 60
        layout_state.document_panel_width = 50
        
        assert layout_state.validate_layout_state() == False

    def test_auto_correct_layout(self, layout_state):
        """Test auto-correction of invalid layout."""
        # Set invalid state
        layout_state.chat_panel_width = 60
        layout_state.document_panel_width = 50
        
        layout_state.auto_correct_layout()
        
        # Should be corrected
        assert layout_state.chat_panel_width + layout_state.document_panel_width == 100

    def test_export_layout_settings(self, layout_state):
        """Test exporting layout settings."""
        layout_state.set_panel_split(60, 40)
        layout_state.set_theme("dark")
        
        exported = layout_state.export_layout_settings()
        
        assert "version" in exported
        assert "settings" in exported
        assert exported["settings"]["chat_panel_width"] == 60
        assert exported["settings"]["theme"] == "dark"

    def test_import_layout_settings(self, layout_state):
        """Test importing layout settings."""
        settings = {
            "version": "1.0",
            "settings": {
                "chat_panel_width": 65,
                "document_panel_width": 35,
                "theme": "dark"
            }
        }
        
        layout_state.import_layout_settings(settings)
        
        assert layout_state.chat_panel_width == 65
        assert layout_state.current_theme == "dark"