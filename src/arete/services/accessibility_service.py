"""
Accessibility Service for WCAG 2.1 AA Compliance.

This service provides comprehensive accessibility features including WCAG 2.1 AA
compliance, keyboard navigation support, screen reader compatibility, and
responsive design utilities for the Arete philosophical tutoring system.
"""

from typing import Dict, List, Optional, Tuple
from enum import Enum
import re
from dataclasses import dataclass
from arete.models.user_preferences import Theme


class AccessibilityLevel(Enum):
    """Accessibility compliance levels."""
    A = "A"
    AA = "AA"
    AAA = "AAA"


class ColorContrastRatio(Enum):
    """Color contrast ratio standards."""
    AA_NORMAL = 4.5      # WCAG AA for normal text
    AA_LARGE = 3.0       # WCAG AA for large text (18pt+ or 14pt+ bold)
    AAA_NORMAL = 7.0     # WCAG AAA for normal text
    AAA_LARGE = 4.5      # WCAG AAA for large text


@dataclass
class AccessibilityConfig:
    """Configuration for accessibility features."""
    level: AccessibilityLevel = AccessibilityLevel.AA
    enable_keyboard_navigation: bool = True
    enable_screen_reader_support: bool = True
    enable_high_contrast: bool = False
    font_size_multiplier: float = 1.0
    reduce_motion: bool = False
    enable_focus_indicators: bool = True
    aria_live_announcements: bool = True


class AccessibilityService:
    """Service for implementing WCAG 2.1 AA compliance and accessibility features."""
    
    def __init__(self, config: Optional[AccessibilityConfig] = None):
        """Initialize the accessibility service."""
        self.config = config or AccessibilityConfig()
        self._contrast_cache: Dict[Tuple[str, str], float] = {}
        
    def generate_wcag_compliant_css(
        self,
        theme: Theme,
        font_size: str = "medium",
        compact_mode: bool = False,
        animations_enabled: bool = True
    ) -> str:
        """Generate WCAG 2.1 AA compliant CSS."""
        css_parts = [
            self._get_base_accessibility_css(),
            self._get_theme_specific_css(theme),
            self._get_font_accessibility_css(font_size),
            self._get_focus_indicators_css(),
            self._get_keyboard_navigation_css(),
            self._get_screen_reader_css(),
            self._get_motion_css(animations_enabled),
            self._get_responsive_css(compact_mode)
        ]
        
        return "\n".join(filter(None, css_parts))
    
    def _get_base_accessibility_css(self) -> str:
        """Get base accessibility CSS that applies to all themes."""
        return """
        <style>
        /* WCAG 2.1 AA Base Accessibility Styles */
        
        /* Focus management */
        *:focus {
            outline: 3px solid #4A90E2 !important;
            outline-offset: 2px !important;
        }
        
        /* Skip links for screen readers */
        .skip-link {
            position: absolute;
            top: -40px;
            left: 6px;
            background: #000000;
            color: #ffffff;
            padding: 8px;
            text-decoration: none;
            border-radius: 3px;
            z-index: 1000;
        }
        .skip-link:focus {
            top: 6px;
        }
        
        /* Ensure minimum touch target size (44px) */
        button, .stButton > button, [role="button"] {
            min-height: 44px !important;
            min-width: 44px !important;
            padding: 8px 16px !important;
        }
        
        /* Text selection and readability */
        .main {
            line-height: 1.5 !important;
            word-spacing: 0.16em !important;
        }
        
        /* Paragraph spacing */
        p {
            margin-bottom: 1em !important;
        }
        
        /* Link accessibility */
        a {
            text-decoration: underline !important;
        }
        a:focus, a:hover {
            text-decoration: underline !important;
            outline: 2px solid currentColor !important;
            outline-offset: 2px !important;
        }
        
        /* Form accessibility */
        input, textarea, select {
            border: 2px solid #666 !important;
        }
        input:focus, textarea:focus, select:focus {
            border-color: #4A90E2 !important;
            box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.3) !important;
        }
        
        /* Error and status messages */
        [role="alert"], .stAlert {
            border: 2px solid currentColor !important;
            padding: 1rem !important;
            margin: 1rem 0 !important;
        }
        
        /* Table accessibility */
        table {
            border-collapse: collapse !important;
        }
        th, td {
            border: 1px solid #666 !important;
            padding: 8px !important;
        }
        th {
            font-weight: bold !important;
            background-color: rgba(0, 0, 0, 0.05) !important;
        }
        </style>
        """
        
    def _get_theme_specific_css(self, theme: Theme) -> str:
        """Get theme-specific CSS with WCAG compliant colors."""
        if theme == Theme.LIGHT:
            return """
            <style>
            /* Light Theme - WCAG AA Compliant */
            .stApp {
                background-color: #ffffff !important;
                color: #212529 !important;
            }
            .stSidebar {
                background-color: #f8f9fa !important;
                border-right: 1px solid #dee2e6 !important;
            }
            .stChatMessage[data-testid="message"] {
                background-color: #f8f9fa !important;
                border-left: 4px solid #007bff !important;
                color: #212529 !important;
            }
            </style>
            """
            
        elif theme == Theme.DARK:
            return """
            <style>
            /* Dark Theme - WCAG AA Compliant */
            .stApp {
                background-color: #212529 !important;
                color: #f8f9fa !important;
            }
            .stSidebar {
                background-color: #343a40 !important;
                border-right: 1px solid #495057 !important;
            }
            .stChatMessage[data-testid="message"] {
                background-color: #343a40 !important;
                border-left: 4px solid #17a2b8 !important;
                color: #f8f9fa !important;
            }
            </style>
            """
            
        return ""
        
    def _get_font_accessibility_css(self, font_size: str) -> str:
        """Get font accessibility CSS with proper sizing and spacing."""
        font_sizes = {
            "small": "0.9rem",
            "medium": "1rem", 
            "large": "1.25rem",
            "extra_large": "1.5rem"
        }
        
        size = font_sizes.get(font_size, "1rem")
        
        return f"""
        <style>
        /* Font Accessibility */
        .main {{
            font-size: {size} !important;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif !important;
        }}
        
        /* Ensure relative sizing for better scalability */
        h1 {{ font-size: calc({size} * 2.5) !important; }}
        h2 {{ font-size: calc({size} * 2) !important; }}
        h3 {{ font-size: calc({size} * 1.75) !important; }}
        h4 {{ font-size: calc({size} * 1.5) !important; }}
        h5 {{ font-size: calc({size} * 1.25) !important; }}
        h6 {{ font-size: calc({size} * 1.1) !important; }}
        
        /* Improve text spacing */
        p, li {{
            line-height: 1.6 !important;
            margin-bottom: 0.75em !important;
        }}
        </style>
        """
        
    def _get_focus_indicators_css(self) -> str:
        """Get CSS for enhanced focus indicators."""
        if not self.config.enable_focus_indicators:
            return ""
            
        return """
        <style>
        /* Enhanced Focus Indicators */
        .stSelectbox > div > div:focus-within {
            outline: 3px solid #4A90E2 !important;
            outline-offset: 2px !important;
        }
        
        .stTextInput > div > div > input:focus {
            outline: 3px solid #4A90E2 !important;
            outline-offset: 2px !important;
            border-color: #4A90E2 !important;
        }
        
        .stTextArea > div > div > textarea:focus {
            outline: 3px solid #4A90E2 !important;
            outline-offset: 2px !important;
            border-color: #4A90E2 !important;
        }
        
        /* Tab navigation indicators */
        .stTabs [role="tab"]:focus {
            outline: 3px solid #4A90E2 !important;
            outline-offset: 2px !important;
        }
        </style>
        """
        
    def _get_keyboard_navigation_css(self) -> str:
        """Get CSS for enhanced keyboard navigation."""
        if not self.config.enable_keyboard_navigation:
            return ""
            
        return """
        <style>
        /* Keyboard Navigation Enhancement */
        [tabindex]:focus {
            outline: 3px solid #4A90E2 !important;
            outline-offset: 2px !important;
        }
        
        /* Skip navigation */
        .skip-nav {
            position: absolute;
            top: -40px;
            left: 6px;
            background: #4A90E2;
            color: white;
            padding: 8px;
            text-decoration: none;
            z-index: 1000;
        }
        .skip-nav:focus {
            top: 6px;
        }
        
        /* Ensure keyboard users can see hover states */
        button:focus, .stButton > button:focus {
            background-color: #0056b3 !important;
            border-color: #004085 !important;
        }
        </style>
        """
        
    def _get_screen_reader_css(self) -> str:
        """Get CSS for screen reader support."""
        if not self.config.enable_screen_reader_support:
            return ""
            
        return """
        <style>
        /* Screen Reader Support */
        .sr-only {
            position: absolute !important;
            width: 1px !important;
            height: 1px !important;
            padding: 0 !important;
            margin: -1px !important;
            overflow: hidden !important;
            clip: rect(0, 0, 0, 0) !important;
            white-space: nowrap !important;
            border: 0 !important;
        }
        
        .sr-only-focusable:focus {
            position: static !important;
            width: auto !important;
            height: auto !important;
            padding: inherit !important;
            margin: inherit !important;
            overflow: visible !important;
            clip: auto !important;
            white-space: normal !important;
        }
        </style>
        """
        
    def _get_motion_css(self, animations_enabled: bool) -> str:
        """Get CSS for motion and animation control."""
        if animations_enabled and not self.config.reduce_motion:
            return """
            <style>
            /* Respectful animations */
            .stSpinner {
                animation-duration: 1s !important;
            }
            </style>
            """
        else:
            return """
            <style>
            /* Reduced motion */
            *, *::before, *::after {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
                scroll-behavior: auto !important;
            }
            
            @media (prefers-reduced-motion: reduce) {
                *, *::before, *::after {
                    animation-duration: 0.01ms !important;
                    animation-iteration-count: 1 !important;
                    transition-duration: 0.01ms !important;
                }
            }
            </style>
            """
            
    def _get_responsive_css(self, compact_mode: bool) -> str:
        """Get responsive CSS for different screen sizes."""
        base_responsive = """
        <style>
        /* Responsive Design */
        @media (max-width: 768px) {
            .main {
                padding: 1rem 0.5rem !important;
            }
            
            button, .stButton > button {
                min-height: 48px !important;
                min-width: 48px !important;
                font-size: 1.1rem !important;
            }
            
            .stTextInput input, .stTextArea textarea {
                font-size: 16px !important; /* Prevent zoom on iOS */
            }
        }
        
        @media (max-width: 480px) {
            .main {
                font-size: 1.1rem !important;
            }
            
            button, .stButton > button {
                min-height: 52px !important;
                padding: 12px 20px !important;
            }
        }
        """
        
        if compact_mode:
            base_responsive += """
            /* Compact Mode */
            .stChatMessage {
                margin: 0.25rem 0 !important;
                padding: 0.75rem !important;
            }
            
            .main {
                padding-top: 1rem !important;
            }
            """
            
        return base_responsive + "</style>"
        
    def generate_aria_attributes(self, element_type: str, content: str = "") -> Dict[str, str]:
        """Generate appropriate ARIA attributes for UI elements."""
        attributes = {}
        
        if element_type == "chat_message":
            attributes.update({
                "role": "log",
                "aria-live": "polite",
                "aria-label": f"Chat message: {content[:50]}..."
            })
            
        elif element_type == "sidebar":
            attributes.update({
                "role": "navigation",
                "aria-label": "Main navigation"
            })
            
        elif element_type == "main_content":
            attributes.update({
                "role": "main",
                "aria-label": "Main content area"
            })
            
        elif element_type == "button":
            attributes.update({
                "role": "button",
                "aria-pressed": "false"
            })
            
        elif element_type == "form":
            attributes.update({
                "role": "form",
                "aria-label": "User input form"
            })
            
        return attributes