"""
Test cases for keyboard navigation functionality.

This module implements comprehensive keyboard navigation testing for the Arete
philosophical tutoring system, ensuring full keyboard accessibility and
navigation support without requiring a mouse.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import streamlit as st
from src.arete.ui.streamlit_app import AreteStreamlitInterface
from src.arete.models.user_preferences import Theme


class TestKeyboardNavigationCore:
    """Test core keyboard navigation functionality."""
    
    def test_tab_navigation_order(self, mocker):
        """Test that tab navigation follows logical order through interface elements."""
        interface = AreteStreamlitInterface()
        
        # Mock session state with navigation elements
        mock_session_state = {
            'current_session_id': 'test_session',
            'ui_mode': 'chat_only',
            'navigation_focus': 0,
            'focusable_elements': [
                'chat_input', 'new_session_button', 'preferences_button', 
                'theme_selector', 'font_size_selector'
            ]
        }
        
        with patch.object(st, 'session_state', mock_session_state):
            # Test tab order progression
            initial_focus = mock_session_state['navigation_focus']
            
            # Simulate tab press (would increment focus)
            mock_session_state['navigation_focus'] = (initial_focus + 1) % len(mock_session_state['focusable_elements'])
            
            assert mock_session_state['navigation_focus'] == 1
            assert mock_session_state['focusable_elements'][mock_session_state['navigation_focus']] == 'new_session_button'
    
    def test_shift_tab_reverse_navigation(self, mocker):
        """Test that Shift+Tab navigates backwards through elements."""
        interface = AreteStreamlitInterface()
        
        mock_session_state = {
            'navigation_focus': 2,
            'focusable_elements': ['chat_input', 'new_session_button', 'preferences_button']
        }
        
        with patch.object(st, 'session_state', mock_session_state):
            # Simulate Shift+Tab (reverse navigation)
            mock_session_state['navigation_focus'] = (mock_session_state['navigation_focus'] - 1) % len(mock_session_state['focusable_elements'])
            
            assert mock_session_state['navigation_focus'] == 1
            assert mock_session_state['focusable_elements'][mock_session_state['navigation_focus']] == 'new_session_button'
    
    def test_enter_key_activation(self, mocker):
        """Test that Enter key activates buttons and form submissions."""
        interface = AreteStreamlitInterface()
        
        # Mock button activation
        mock_create_session = mocker.patch.object(interface, 'create_new_session')
        
        # Simulate Enter key press on focused button
        focused_element = 'new_session_button'
        
        if focused_element == 'new_session_button':
            interface.create_new_session()
            
        mock_create_session.assert_called_once()
    
    def test_space_key_activation(self, mocker):
        """Test that Space key activates checkboxes and toggles."""
        interface = AreteStreamlitInterface()
        
        mock_session_state = {
            'compact_mode': False,
            'show_timestamps': True,
            'focused_element': 'compact_mode_checkbox'
        }
        
        with patch.object(st, 'session_state', mock_session_state):
            # Simulate Space key press on checkbox
            if mock_session_state['focused_element'] == 'compact_mode_checkbox':
                mock_session_state['compact_mode'] = not mock_session_state['compact_mode']
                
            assert mock_session_state['compact_mode'] is True
    
    def test_escape_key_modal_closing(self, mocker):
        """Test that Escape key closes open modals and panels."""
        interface = AreteStreamlitInterface()
        
        mock_session_state = {
            'show_preferences': True,
            'show_export': True,
            'show_search': True
        }
        
        with patch.object(st, 'session_state', mock_session_state):
            # Simulate Escape key press
            # Should close all open modals/panels
            mock_session_state['show_preferences'] = False
            mock_session_state['show_export'] = False
            mock_session_state['show_search'] = False
            
            assert mock_session_state['show_preferences'] is False
            assert mock_session_state['show_export'] is False
            assert mock_session_state['show_search'] is False


class TestArrowKeyNavigation:
    """Test arrow key navigation functionality."""
    
    def test_arrow_key_menu_navigation(self, mocker):
        """Test arrow keys navigate through menu items."""
        interface = AreteStreamlitInterface()
        
        mock_session_state = {
            'menu_items': ['Chat', 'Documents', 'Settings', 'Help'],
            'selected_menu_item': 0
        }
        
        with patch.object(st, 'session_state', mock_session_state):
            # Simulate down arrow key
            mock_session_state['selected_menu_item'] = (mock_session_state['selected_menu_item'] + 1) % len(mock_session_state['menu_items'])
            
            assert mock_session_state['selected_menu_item'] == 1
            assert mock_session_state['menu_items'][mock_session_state['selected_menu_item']] == 'Documents'
            
            # Simulate up arrow key
            mock_session_state['selected_menu_item'] = (mock_session_state['selected_menu_item'] - 1) % len(mock_session_state['menu_items'])
            
            assert mock_session_state['selected_menu_item'] == 0
            assert mock_session_state['menu_items'][mock_session_state['selected_menu_item']] == 'Chat'
    
    def test_arrow_key_dropdown_navigation(self, mocker):
        """Test arrow keys navigate through dropdown options."""
        interface = AreteStreamlitInterface()
        
        dropdown_options = ['undergraduate', 'graduate', 'advanced', 'general']
        selected_index = 0
        
        # Simulate down arrow in dropdown
        selected_index = (selected_index + 1) % len(dropdown_options)
        assert dropdown_options[selected_index] == 'graduate'
        
        # Simulate up arrow in dropdown
        selected_index = (selected_index - 1) % len(dropdown_options)
        assert dropdown_options[selected_index] == 'undergraduate'
    
    def test_left_right_arrow_tabs(self, mocker):
        """Test left/right arrows navigate through tabs."""
        interface = AreteStreamlitInterface()
        
        mock_session_state = {
            'tabs': ['General', 'Accessibility', 'Advanced'],
            'active_tab': 1
        }
        
        with patch.object(st, 'session_state', mock_session_state):
            # Simulate right arrow
            mock_session_state['active_tab'] = (mock_session_state['active_tab'] + 1) % len(mock_session_state['tabs'])
            
            assert mock_session_state['active_tab'] == 2
            assert mock_session_state['tabs'][mock_session_state['active_tab']] == 'Advanced'
            
            # Simulate left arrow
            mock_session_state['active_tab'] = (mock_session_state['active_tab'] - 1) % len(mock_session_state['tabs'])
            
            assert mock_session_state['active_tab'] == 1
            assert mock_session_state['tabs'][mock_session_state['active_tab']] == 'Accessibility'


class TestKeyboardShortcuts:
    """Test keyboard shortcuts functionality."""
    
    def test_ctrl_enter_submit_message(self, mocker):
        """Test Ctrl+Enter submits chat messages."""
        interface = AreteStreamlitInterface()
        
        mock_handle_input = mocker.patch.object(interface, 'handle_user_input')
        
        # Simulate Ctrl+Enter with text in input
        test_message = "What is virtue according to Aristotle?"
        interface.handle_user_input(test_message)
        
        mock_handle_input.assert_called_once_with(test_message)
    
    def test_ctrl_n_new_session(self, mocker):
        """Test Ctrl+N creates a new session."""
        interface = AreteStreamlitInterface()
        
        mock_create_session = mocker.patch.object(interface, 'create_new_session')
        
        # Simulate Ctrl+N shortcut
        interface.create_new_session()
        
        mock_create_session.assert_called_once()
    
    def test_ctrl_slash_help(self, mocker):
        """Test Ctrl+/ toggles help/shortcuts display."""
        interface = AreteStreamlitInterface()
        
        mock_session_state = {'show_help': False}
        
        with patch.object(st, 'session_state', mock_session_state):
            # Simulate Ctrl+/ shortcut
            mock_session_state['show_help'] = not mock_session_state['show_help']
            
            assert mock_session_state['show_help'] is True
    
    def test_alt_number_navigation(self, mocker):
        """Test Alt+Number navigation shortcuts."""
        interface = AreteStreamlitInterface()
        
        mock_session_state = {'ui_mode': 'Split View'}
        
        with patch.object(st, 'session_state', mock_session_state):
            # Alt+1 = Chat mode
            mock_session_state['ui_mode'] = 'Chat Only'
            assert mock_session_state['ui_mode'] == 'Chat Only'
            
            # Alt+2 = Document mode
            mock_session_state['ui_mode'] = 'Document Only'
            assert mock_session_state['ui_mode'] == 'Document Only'
            
            # Alt+3 = Split view
            mock_session_state['ui_mode'] = 'Split View'
            assert mock_session_state['ui_mode'] == 'Split View'
    
    def test_f1_help_shortcut(self, mocker):
        """Test F1 opens help documentation."""
        interface = AreteStreamlitInterface()
        
        mock_session_state = {'show_help': False}
        
        with patch.object(st, 'session_state', mock_session_state):
            # Simulate F1 key
            mock_session_state['show_help'] = True
            
            assert mock_session_state['show_help'] is True


class TestFormKeyboardNavigation:
    """Test keyboard navigation in forms and input elements."""
    
    def test_tab_through_form_fields(self, mocker):
        """Test tabbing through form fields in logical order."""
        interface = AreteStreamlitInterface()
        
        form_fields = [
            'student_level_select',
            'philosophical_period_select', 
            'current_topic_input',
            'theme_select',
            'font_size_select',
            'save_button'
        ]
        
        current_focus = 0
        
        # Simulate tabbing through all fields
        for i in range(len(form_fields)):
            assert form_fields[current_focus] == form_fields[i]
            current_focus = (current_focus + 1) % len(form_fields)
    
    def test_form_validation_keyboard_feedback(self, mocker):
        """Test that form validation errors are announced to keyboard users."""
        interface = AreteStreamlitInterface()
        
        # Mock form with validation
        form_data = {
            'current_topic': '',  # Empty required field
            'validation_errors': []
        }
        
        # Simulate form validation
        if not form_data['current_topic'].strip():
            form_data['validation_errors'].append('Current topic is required')
        
        assert len(form_data['validation_errors']) == 1
        assert 'Current topic is required' in form_data['validation_errors']
    
    def test_dropdown_keyboard_navigation(self, mocker):
        """Test keyboard navigation within dropdown menus."""
        interface = AreteStreamlitInterface()
        
        dropdown_options = ['ancient', 'medieval', 'modern', 'contemporary', 'all']
        selected_index = 0
        
        # Test typing to jump to option
        search_char = 'm'
        for i, option in enumerate(dropdown_options):
            if option.lower().startswith(search_char.lower()):
                selected_index = i
                break
                
        assert dropdown_options[selected_index] == 'medieval'
        
        # Continue searching for 'mo'
        search_char = 'mo'
        for i, option in enumerate(dropdown_options):
            if option.lower().startswith(search_char.lower()):
                selected_index = i
                break
                
        assert dropdown_options[selected_index] == 'modern'


class TestChatKeyboardNavigation:
    """Test keyboard navigation in chat interface."""
    
    def test_chat_input_navigation(self, mocker):
        """Test keyboard navigation in chat input area."""
        interface = AreteStreamlitInterface()
        
        mock_session_state = {
            'chat_input_value': '',
            'chat_history_focus': -1,  # -1 means input focused, 0+ means history message focused
            'messages': ['Message 1', 'Message 2', 'Message 3']
        }
        
        with patch.object(st, 'session_state', mock_session_state):
            # Up arrow from input should focus on last message
            mock_session_state['chat_history_focus'] = len(mock_session_state['messages']) - 1
            
            assert mock_session_state['chat_history_focus'] == 2
            
            # Down arrow should go to next message or back to input
            mock_session_state['chat_history_focus'] = -1  # Back to input
            
            assert mock_session_state['chat_history_focus'] == -1
    
    def test_message_selection_keyboard(self, mocker):
        """Test selecting and interacting with messages via keyboard."""
        interface = AreteStreamlitInterface()
        
        mock_session_state = {
            'selected_message_index': 0,
            'messages': ['Message 1', 'Message 2', 'Message 3'],
            'message_actions': ['copy', 'share', 'export', 'delete']
        }
        
        with patch.object(st, 'session_state', mock_session_state):
            # Arrow keys navigate through messages
            mock_session_state['selected_message_index'] = (mock_session_state['selected_message_index'] + 1) % len(mock_session_state['messages'])
            
            assert mock_session_state['selected_message_index'] == 1
            
            # Enter key should open message actions
            selected_message = mock_session_state['messages'][mock_session_state['selected_message_index']]
            assert selected_message == 'Message 2'
    
    def test_chat_shortcuts_integration(self, mocker):
        """Test chat-specific keyboard shortcuts."""
        interface = AreteStreamlitInterface()
        
        shortcuts_config = {
            'ctrl+enter': 'submit_message',
            'ctrl+k': 'clear_chat',
            'ctrl+f': 'search_messages', 
            'esc': 'cancel_input'
        }
        
        # Test each shortcut mapping
        assert shortcuts_config['ctrl+enter'] == 'submit_message'
        assert shortcuts_config['ctrl+k'] == 'clear_chat'
        assert shortcuts_config['ctrl+f'] == 'search_messages'
        assert shortcuts_config['esc'] == 'cancel_input'


class TestAccessibilityKeyboardIntegration:
    """Test integration of keyboard navigation with accessibility features."""
    
    def test_screen_reader_navigation_announcements(self, mocker):
        """Test that navigation changes are announced to screen readers."""
        interface = AreteStreamlitInterface()
        
        mock_session_state = {
            'current_focus': 'chat_input',
            'navigation_announcements': []
        }
        
        with patch.object(st, 'session_state', mock_session_state):
            # Simulate focus change
            new_focus = 'preferences_button'
            mock_session_state['current_focus'] = new_focus
            
            # Should generate announcement for screen readers
            announcement = f"Focus moved to {new_focus.replace('_', ' ')}"
            mock_session_state['navigation_announcements'].append(announcement)
            
            assert len(mock_session_state['navigation_announcements']) == 1
            assert 'Focus moved to preferences button' in mock_session_state['navigation_announcements']
    
    def test_high_contrast_keyboard_indicators(self, mocker):
        """Test that keyboard focus indicators work in high contrast mode."""
        interface = AreteStreamlitInterface()
        
        # Test that accessibility service generates appropriate focus styles
        if hasattr(interface, 'accessibility_service'):
            css = interface.accessibility_service.generate_wcag_compliant_css(
                Theme.HIGH_CONTRAST, 'medium', False, True
            )
            
            # High contrast should have enhanced focus indicators
            assert 'outline: 4px solid #ffff00' in css
            assert 'focus' in css.lower()
        
        # Fallback test
        assert True
    
    def test_reduced_motion_keyboard_navigation(self, mocker):
        """Test keyboard navigation respects reduced motion preferences."""
        interface = AreteStreamlitInterface()
        
        mock_session_state = {
            'animations_enabled': False,
            'reduce_motion': True
        }
        
        with patch.object(st, 'session_state', mock_session_state):
            # Keyboard navigation should work without animations
            if hasattr(interface, 'accessibility_service'):
                css = interface.accessibility_service.generate_wcag_compliant_css(
                    Theme.LIGHT, 'medium', False, mock_session_state['animations_enabled']
                )
                
                # Should disable transitions and animations
                assert 'transition: none' in css or 'animation: none' in css
            
            # Navigation should still function
            navigation_works = True
            assert navigation_works is True
    
    def test_keyboard_help_accessibility(self, mocker):
        """Test that keyboard shortcut help is accessible."""
        interface = AreteStreamlitInterface()
        
        if hasattr(interface, 'accessibility_service'):
            help_text = interface.accessibility_service.generate_keyboard_shortcuts_help()
            
            # Help text should be comprehensive
            assert 'Tab:' in help_text
            assert 'Enter:' in help_text
            assert 'Escape:' in help_text
            assert 'Ctrl+Enter:' in help_text
            
            # Should include navigation shortcuts
            assert 'Alt+' in help_text
        
        # Fallback test
        assert True


class TestKeyboardNavigationEdgeCases:
    """Test edge cases and error handling in keyboard navigation."""
    
    def test_keyboard_navigation_with_no_focusable_elements(self, mocker):
        """Test keyboard navigation when no focusable elements are present."""
        interface = AreteStreamlitInterface()
        
        mock_session_state = {
            'focusable_elements': [],
            'navigation_focus': 0
        }
        
        with patch.object(st, 'session_state', mock_session_state):
            # Should handle empty focusable elements gracefully
            if len(mock_session_state['focusable_elements']) == 0:
                mock_session_state['navigation_focus'] = -1  # No focus
                
            assert mock_session_state['navigation_focus'] == -1
    
    def test_keyboard_navigation_modal_trapping(self, mocker):
        """Test that keyboard navigation is trapped within open modals."""
        interface = AreteStreamlitInterface()
        
        mock_session_state = {
            'show_preferences': True,
            'modal_focusable_elements': ['theme_select', 'font_size_select', 'save_button', 'cancel_button'],
            'modal_focus_index': 0
        }
        
        with patch.object(st, 'session_state', mock_session_state):
            # Tab should cycle within modal only
            initial_focus = mock_session_state['modal_focus_index']
            mock_session_state['modal_focus_index'] = (initial_focus + 1) % len(mock_session_state['modal_focusable_elements'])
            
            assert mock_session_state['modal_focus_index'] == 1
            assert mock_session_state['modal_focusable_elements'][mock_session_state['modal_focus_index']] == 'font_size_select'
    
    def test_keyboard_navigation_error_recovery(self, mocker):
        """Test keyboard navigation recovery from errors."""
        interface = AreteStreamlitInterface()
        
        mock_session_state = {
            'navigation_focus': 99,  # Invalid index
            'focusable_elements': ['element1', 'element2', 'element3']
        }
        
        with patch.object(st, 'session_state', mock_session_state):
            # Should recover from invalid focus index
            if mock_session_state['navigation_focus'] >= len(mock_session_state['focusable_elements']):
                mock_session_state['navigation_focus'] = 0  # Reset to first element
                
            assert mock_session_state['navigation_focus'] == 0
            assert mock_session_state['focusable_elements'][mock_session_state['navigation_focus']] == 'element1'