"""UI state management for global interface settings."""

import reflex as rx
from typing import Literal


class UIState(rx.State):
    """Global UI state for theme, navigation, and responsive design."""
    
    # Theme management
    dark_mode: bool = False
    theme: Literal["light", "dark", "auto"] = "light"
    
    # Navigation state
    sidebar_open: bool = True
    mobile_menu_open: bool = False
    current_page: str = "chat"
    
    # Layout preferences
    chat_document_split: bool = False
    document_panel_width: int = 40  # Percentage
    
    # Reading preferences
    font_size: Literal["sm", "md", "lg", "xl"] = "md"
    line_height: Literal["normal", "relaxed", "loose"] = "relaxed"
    
    # Accessibility
    high_contrast: bool = False
    reduce_motion: bool = False
    focus_indicators: bool = True
    
    def toggle_dark_mode(self):
        """Toggle dark mode theme."""
        self.dark_mode = not self.dark_mode
        self.theme = "dark" if self.dark_mode else "light"
    
    def set_theme(self, theme: Literal["light", "dark", "auto"]):
        """Set theme preference."""
        self.theme = theme
        self.dark_mode = theme == "dark"
    
    def toggle_sidebar(self):
        """Toggle sidebar visibility."""
        self.sidebar_open = not self.sidebar_open
    
    def toggle_mobile_menu(self):
        """Toggle mobile menu."""
        self.mobile_menu_open = not self.mobile_menu_open
    
    def set_current_page(self, page: str):
        """Set current active page."""
        self.current_page = page
        # Close mobile menu when navigating
        self.mobile_menu_open = False
    
    def toggle_chat_document_split(self):
        """Toggle split view between chat and document."""
        self.chat_document_split = not self.chat_document_split
    
    def set_document_panel_width(self, width: int):
        """Set document panel width percentage."""
        self.document_panel_width = max(20, min(80, width))
    
    def set_font_size(self, size: Literal["sm", "md", "lg", "xl"]):
        """Set reading font size."""
        self.font_size = size
    
    def set_line_height(self, height: Literal["normal", "relaxed", "loose"]):
        """Set reading line height."""
        self.line_height = height
    
    def toggle_high_contrast(self):
        """Toggle high contrast accessibility mode."""
        self.high_contrast = not self.high_contrast
    
    def toggle_reduce_motion(self):
        """Toggle reduced motion for accessibility."""
        self.reduce_motion = not self.reduce_motion
    
    def toggle_focus_indicators(self):
        """Toggle focus indicators for keyboard navigation."""
        self.focus_indicators = not self.focus_indicators
    
    @rx.var
    def theme_class(self) -> str:
        """Get CSS class for current theme."""
        classes = []
        if self.dark_mode:
            classes.append("dark")
        if self.high_contrast:
            classes.append("high-contrast")
        if self.reduce_motion:
            classes.append("reduce-motion")
        return " ".join(classes)
    
    @rx.var
    def font_size_class(self) -> str:
        """Get CSS class for font size."""
        return f"text-{self.font_size}"
    
    @rx.var
    def line_height_class(self) -> str:
        """Get CSS class for line height."""
        height_map = {
            "normal": "leading-normal",
            "relaxed": "leading-relaxed", 
            "loose": "leading-loose"
        }
        return height_map.get(self.line_height, "leading-relaxed")
    
    @rx.var
    def is_mobile(self) -> bool:
        """Check if current viewport is mobile-sized."""
        # This would be implemented with client-side detection
        # For now, return False as placeholder
        return False
    
    @rx.var
    def sidebar_width(self) -> str:
        """Calculate sidebar width based on state."""
        if not self.sidebar_open:
            return "0px"
        return "280px" if not self.is_mobile else "100%"
    
    @rx.var
    def content_margin(self) -> str:
        """Calculate content margin based on sidebar."""
        if not self.sidebar_open or self.is_mobile:
            return "0px"
        return "280px"