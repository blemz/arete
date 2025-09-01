"""
Keyboard Navigation Service for Comprehensive Keyboard Support.

This service provides comprehensive keyboard navigation functionality including
shortcuts, focus management, screen reader integration, and full keyboard
accessibility for the Arete philosophical tutoring system.
"""

from typing import Dict, List, Optional, Callable, Tuple
from enum import Enum
from dataclasses import dataclass
import streamlit as st


class NavigationDirection(Enum):
    """Navigation direction options."""
    FORWARD = "forward"
    BACKWARD = "backward"
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


class FocusableElementType(Enum):
    """Types of focusable elements."""
    BUTTON = "button"
    INPUT = "input"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    LINK = "link"
    TAB = "tab"
    MENU_ITEM = "menu_item"


@dataclass
class FocusableElement:
    """Represents a focusable UI element."""
    id: str
    element_type: FocusableElementType
    label: str
    description: Optional[str] = None
    shortcut: Optional[str] = None
    callback: Optional[Callable] = None
    is_modal: bool = False
    tab_index: int = 0


@dataclass
class KeyboardShortcut:
    """Represents a keyboard shortcut."""
    key_combination: str
    description: str
    callback: Callable
    context: str = "global"  # global, modal, chat, etc.


class KeyboardNavigationService:
    """Service for implementing comprehensive keyboard navigation."""
    
    def __init__(self):
        """Initialize the keyboard navigation service."""
        self.focusable_elements: List[FocusableElement] = []
        self.shortcuts: Dict[str, KeyboardShortcut] = {}
        self.current_focus_index: int = -1
        self.modal_focus_trap: bool = False
        self.focus_history: List[int] = []
        
        self._initialize_default_shortcuts()
    
    def _initialize_default_shortcuts(self):
        """Initialize default keyboard shortcuts."""
        default_shortcuts = [
            KeyboardShortcut("ctrl+enter", "Submit chat message", self._submit_chat_message, "chat"),
            KeyboardShortcut("ctrl+n", "Create new session", self._create_new_session, "global"),
            KeyboardShortcut("ctrl+/", "Show keyboard shortcuts help", self._show_help, "global"),
            KeyboardShortcut("ctrl+k", "Clear chat", self._clear_chat, "chat"),
            KeyboardShortcut("ctrl+f", "Search messages", self._search_messages, "global"),
            KeyboardShortcut("alt+1", "Switch to Chat Only mode", self._switch_to_chat_mode, "global"),
            KeyboardShortcut("alt+2", "Switch to Document Only mode", self._switch_to_document_mode, "global"),
            KeyboardShortcut("alt+3", "Switch to Split View mode", self._switch_to_split_view, "global"),
            KeyboardShortcut("f1", "Show help", self._show_help, "global"),
            KeyboardShortcut("escape", "Close modals/Cancel", self._escape_action, "global"),
        ]
        
        for shortcut in default_shortcuts:
            self.shortcuts[shortcut.key_combination] = shortcut
    
    def register_focusable_element(self, element: FocusableElement) -> None:
        """Register a focusable element for keyboard navigation."""
        self.focusable_elements.append(element)
        # Sort by tab index
        self.focusable_elements.sort(key=lambda e: e.tab_index)
    
    def register_shortcut(self, shortcut: KeyboardShortcut) -> None:
        """Register a keyboard shortcut."""
        self.shortcuts[shortcut.key_combination] = shortcut
    
    def get_current_focus_element(self) -> Optional[FocusableElement]:
        """Get the currently focused element."""
        if 0 <= self.current_focus_index < len(self.focusable_elements):
            return self.focusable_elements[self.current_focus_index]
        return None
    
    def move_focus(self, direction: NavigationDirection) -> bool:
        """Move focus in the specified direction."""
        if not self.focusable_elements:
            return False
        
        previous_index = self.current_focus_index
        
        if direction == NavigationDirection.FORWARD:
            self.current_focus_index = (self.current_focus_index + 1) % len(self.focusable_elements)
        elif direction == NavigationDirection.BACKWARD:
            self.current_focus_index = (self.current_focus_index - 1) % len(self.focusable_elements)
        elif direction in [NavigationDirection.DOWN, NavigationDirection.UP]:
            # For vertical navigation (menus, lists)
            self._handle_vertical_navigation(direction)
        elif direction in [NavigationDirection.LEFT, NavigationDirection.RIGHT]:
            # For horizontal navigation (tabs, toolbars)
            self._handle_horizontal_navigation(direction)
        
        # Update focus history
        if previous_index != self.current_focus_index:
            self.focus_history.append(previous_index)
            if len(self.focus_history) > 10:  # Limit history size
                self.focus_history.pop(0)
            
            # Announce focus change for screen readers
            self._announce_focus_change()
            return True
        
        return False
    
    def _handle_vertical_navigation(self, direction: NavigationDirection) -> None:
        """Handle vertical navigation (up/down arrows)."""
        current_element = self.get_current_focus_element()
        if not current_element:
            return
        
        # Find elements of the same type for vertical navigation
        same_type_elements = [
            i for i, elem in enumerate(self.focusable_elements)
            if elem.element_type == current_element.element_type
        ]
        
        if not same_type_elements:
            return
        
        current_position = same_type_elements.index(self.current_focus_index)
        
        if direction == NavigationDirection.DOWN:
            new_position = (current_position + 1) % len(same_type_elements)
        else:  # UP
            new_position = (current_position - 1) % len(same_type_elements)
        
        self.current_focus_index = same_type_elements[new_position]
    
    def _handle_horizontal_navigation(self, direction: NavigationDirection) -> None:
        """Handle horizontal navigation (left/right arrows)."""
        current_element = self.get_current_focus_element()
        if not current_element or current_element.element_type != FocusableElementType.TAB:
            return
        
        # Find tab elements for horizontal navigation
        tab_elements = [
            i for i, elem in enumerate(self.focusable_elements)
            if elem.element_type == FocusableElementType.TAB
        ]
        
        if not tab_elements:
            return
        
        current_position = tab_elements.index(self.current_focus_index)
        
        if direction == NavigationDirection.RIGHT:
            new_position = (current_position + 1) % len(tab_elements)
        else:  # LEFT
            new_position = (current_position - 1) % len(tab_elements)
        
        self.current_focus_index = tab_elements[new_position]
    
    def activate_current_element(self) -> bool:
        """Activate the currently focused element (Enter key)."""
        current_element = self.get_current_focus_element()
        if current_element and current_element.callback:
            try:
                current_element.callback()
                self._announce_action(f"Activated {current_element.label}")
                return True
            except Exception as e:
                self._announce_action(f"Error activating {current_element.label}: {str(e)}")
        
        return False
    
    def toggle_current_element(self) -> bool:
        """Toggle the currently focused element (Space key for checkboxes)."""
        current_element = self.get_current_focus_element()
        if not current_element:
            return False
        
        if current_element.element_type in [FocusableElementType.CHECKBOX, FocusableElementType.RADIO]:
            if current_element.callback:
                try:
                    current_element.callback()
                    self._announce_action(f"Toggled {current_element.label}")
                    return True
                except Exception as e:
                    self._announce_action(f"Error toggling {current_element.label}: {str(e)}")
        
        return False
    
    def handle_shortcut(self, key_combination: str, context: str = "global") -> bool:
        """Handle keyboard shortcut execution."""
        if key_combination in self.shortcuts:
            shortcut = self.shortcuts[key_combination]
            
            # Check context compatibility
            if shortcut.context == "global" or shortcut.context == context:
                try:
                    shortcut.callback()
                    self._announce_action(f"Executed shortcut: {shortcut.description}")
                    return True
                except Exception as e:
                    self._announce_action(f"Error executing shortcut {key_combination}: {str(e)}")
        
        return False
    
    def escape_action(self) -> bool:
        """Handle Escape key press."""
        # Close modals, cancel operations, etc.
        if self.modal_focus_trap:
            self._close_modal()
            return True
        
        # Clear current operation or selection
        return self._cancel_current_operation()
    
    def set_modal_focus_trap(self, enabled: bool, modal_elements: List[FocusableElement] = None) -> None:
        """Enable or disable modal focus trapping."""
        self.modal_focus_trap = enabled
        
        if enabled and modal_elements:
            # Temporarily replace focusable elements with modal elements
            self._previous_elements = self.focusable_elements.copy()
            self.focusable_elements = modal_elements
            self.current_focus_index = 0 if modal_elements else -1
        elif not enabled:
            # Restore previous elements
            if hasattr(self, '_previous_elements'):
                self.focusable_elements = self._previous_elements
                delattr(self, '_previous_elements')
            self.current_focus_index = -1
    
    def _announce_focus_change(self) -> None:
        """Announce focus change for screen readers."""
        current_element = self.get_current_focus_element()
        if current_element:
            announcement = f"Focus on {current_element.label}"
            if current_element.description:
                announcement += f", {current_element.description}"
            
            self._add_screen_reader_announcement(announcement)
    
    def _announce_action(self, message: str) -> None:
        """Announce an action for screen readers."""
        self._add_screen_reader_announcement(message)
    
    def _add_screen_reader_announcement(self, message: str) -> None:
        """Add a message to screen reader announcements."""
        if not hasattr(st.session_state, 'screen_reader_announcements'):
            st.session_state.screen_reader_announcements = []
        
        st.session_state.screen_reader_announcements.append(message)
        
        # Keep only recent announcements
        if len(st.session_state.screen_reader_announcements) > 5:
            st.session_state.screen_reader_announcements.pop(0)
    
    def get_keyboard_shortcuts_help(self) -> str:
        """Generate help text for keyboard shortcuts."""
        help_text = "Keyboard Shortcuts:\\n\\n"
        
        # Group shortcuts by context
        contexts = {}
        for shortcut in self.shortcuts.values():
            if shortcut.context not in contexts:
                contexts[shortcut.context] = []
            contexts[shortcut.context].append(shortcut)
        
        for context, shortcuts_list in contexts.items():
            help_text += f"{context.capitalize()} Shortcuts:\\n"
            for shortcut in shortcuts_list:
                key_display = shortcut.key_combination.replace("ctrl", "Ctrl").replace("alt", "Alt")
                help_text += f"  {key_display}: {shortcut.description}\\n"
            help_text += "\\n"
        
        # Add navigation shortcuts
        help_text += "Navigation:\\n"
        help_text += "  Tab: Navigate forward\\n"
        help_text += "  Shift+Tab: Navigate backward\\n"
        help_text += "  Arrow keys: Navigate menus and tabs\\n"
        help_text += "  Enter: Activate buttons and links\\n"
        help_text += "  Space: Toggle checkboxes and radio buttons\\n"
        help_text += "  Escape: Close modals and cancel operations\\n"
        
        return help_text
    
    def generate_navigation_javascript(self) -> str:
        """Generate JavaScript for enhanced keyboard navigation."""
        return \"\"\"\n        <script>\n        document.addEventListener('keydown', function(event) {\n            // Prevent default behavior for our managed shortcuts\n            const managedKeys = ['Tab', 'Enter', 'Escape', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'];\n            \n            if (managedKeys.includes(event.key)) {\n                // Let Streamlit handle basic navigation\n                return;\n            }\n            \n            // Handle custom shortcuts\n            const keyCombo = [];\n            if (event.ctrlKey) keyCombo.push('ctrl');\n            if (event.altKey) keyCombo.push('alt');\n            if (event.shiftKey) keyCombo.push('shift');\n            keyCombo.push(event.key.toLowerCase());\n            \n            const shortcut = keyCombo.join('+');\n            \n            // Send shortcut to Streamlit\n            if (window.parent && window.parent.postMessage) {\n                window.parent.postMessage({\n                    type: 'keyboard_shortcut',\n                    shortcut: shortcut\n                }, '*');\n            }\n        });\n        \n        // Focus management\n        function setFocusIndicator(element) {\n            // Ensure focus is visible\n            element.style.outline = '3px solid #4A90E2';\n            element.style.outlineOffset = '2px';\n            element.scrollIntoView({ behavior: 'smooth', block: 'nearest' });\n        }\n        \n        // Screen reader announcements\n        function announceToScreenReader(message) {\n            const announcement = document.getElementById('screen-reader-announcements');\n            if (announcement) {\n                announcement.textContent = message;\n                announcement.setAttribute('aria-live', 'polite');\n            }\n        }\n        </script>\n        \n        <!-- Screen reader announcement area -->\n        <div id=\"screen-reader-announcements\" \n             aria-live=\"polite\" \n             aria-atomic=\"true\" \n             style=\"position: absolute; left: -10000px; width: 1px; height: 1px; overflow: hidden;\">\n        </div>\n        \"\"\"\n    \n    def get_focus_management_css(self) -> str:\n        \"\"\"Generate CSS for focus management.\"\"\"\n        return \"\"\"\n        <style>\n        /* Enhanced focus management */\n        \n        /* Ensure focus is always visible */\n        *:focus {\n            outline: 3px solid #4A90E2 !important;\n            outline-offset: 2px !important;\n            box-shadow: 0 0 0 1px rgba(74, 144, 226, 0.3) !important;\n        }\n        \n        /* Focus within containers */\n        .stSelectbox:focus-within,\n        .stTextInput:focus-within,\n        .stTextArea:focus-within {\n            outline: 2px solid #4A90E2 !important;\n            outline-offset: 1px !important;\n        }\n        \n        /* Skip link styling */\n        .skip-link {\n            position: absolute;\n            top: -40px;\n            left: 6px;\n            background: #4A90E2;\n            color: white;\n            padding: 8px 16px;\n            text-decoration: none;\n            border-radius: 4px;\n            font-weight: bold;\n            z-index: 1000;\n            transition: top 0.2s ease;\n        }\n        \n        .skip-link:focus {\n            top: 6px;\n        }\n        \n        /* Focus indicators for custom elements */\n        [role=\"button\"]:focus,\n        [role=\"tab\"]:focus,\n        [role=\"menuitem\"]:focus {\n            outline: 3px solid #4A90E2 !important;\n            outline-offset: 2px !important;\n            background-color: rgba(74, 144, 226, 0.1) !important;\n        }\n        \n        /* Modal focus trapping */\n        .modal-overlay {\n            position: fixed;\n            top: 0;\n            left: 0;\n            right: 0;\n            bottom: 0;\n            background: rgba(0, 0, 0, 0.5);\n            z-index: 1000;\n        }\n        \n        .modal-content {\n            position: fixed;\n            top: 50%;\n            left: 50%;\n            transform: translate(-50%, -50%);\n            background: white;\n            padding: 20px;\n            border-radius: 8px;\n            max-width: 600px;\n            max-height: 80vh;\n            overflow-y: auto;\n            z-index: 1001;\n        }\n        \n        /* High contrast mode focus indicators */\n        @media (prefers-contrast: high) {\n            *:focus {\n                outline: 4px solid #ffff00 !important;\n                outline-offset: 2px !important;\n            }\n        }\n        \n        /* Reduced motion */\n        @media (prefers-reduced-motion: reduce) {\n            * {\n                transition: none !important;\n                animation: none !important;\n            }\n            \n            .skip-link {\n                transition: none !important;\n            }\n        }\n        </style>\n        \"\"\"\n    \n    # Shortcut callback implementations\n    def _submit_chat_message(self):\n        \"\"\"Submit chat message shortcut callback.\"\"\"\n        # This would be implemented to submit the current chat input\n        if hasattr(st.session_state, 'chat_input_value') and st.session_state.chat_input_value:\n            # Trigger message submission\n            st.session_state.submit_message = True\n    \n    def _create_new_session(self):\n        \"\"\"Create new session shortcut callback.\"\"\"\n        st.session_state.create_new_session = True\n    \n    def _show_help(self):\n        \"\"\"Show help shortcut callback.\"\"\"\n        st.session_state.show_help = not getattr(st.session_state, 'show_help', False)\n    \n    def _clear_chat(self):\n        \"\"\"Clear chat shortcut callback.\"\"\"\n        st.session_state.clear_chat = True\n    \n    def _search_messages(self):\n        \"\"\"Search messages shortcut callback.\"\"\"\n        st.session_state.show_search = not getattr(st.session_state, 'show_search', False)\n    \n    def _switch_to_chat_mode(self):\n        \"\"\"Switch to chat mode shortcut callback.\"\"\"\n        st.session_state.ui_mode = \"Chat Only\"\n    \n    def _switch_to_document_mode(self):\n        \"\"\"Switch to document mode shortcut callback.\"\"\"\n        st.session_state.ui_mode = \"Document Only\"\n    \n    def _switch_to_split_view(self):\n        \"\"\"Switch to split view shortcut callback.\"\"\"\n        st.session_state.ui_mode = \"Split View\"\n    \n    def _escape_action(self):\n        \"\"\"Escape key action callback.\"\"\"\n        self.escape_action()\n    \n    def _close_modal(self):\n        \"\"\"Close modal callback.\"\"\"\n        st.session_state.show_preferences = False\n        st.session_state.show_export = False\n        st.session_state.show_search = False\n        st.session_state.show_sharing = False\n        self.set_modal_focus_trap(False)\n    \n    def _cancel_current_operation(self):\n        \"\"\"Cancel current operation callback.\"\"\"\n        # Clear any current input or selection\n        if hasattr(st.session_state, 'chat_input_value'):\n            st.session_state.chat_input_value = ''\n        \n        # Clear search\n        if hasattr(st.session_state, 'search_query'):\n            st.session_state.search_query = ''\n        \n        return True