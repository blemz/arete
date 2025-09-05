"""Layout state management for split-view system."""

import reflex as rx
from typing import Dict, Any, Optional, Literal, Tuple
import json


class LayoutState(rx.State):
    """State management for split-view layout system."""
    
    # Layout modes
    layout_mode: Literal["chat", "split", "document"] = "chat"
    previous_layout_mode: Literal["chat", "split", "document"] = "chat"
    
    # Split configuration
    split_orientation: Literal["horizontal", "vertical"] = "horizontal"
    chat_panel_width: int = 50  # Percentage for horizontal split
    chat_panel_height: int = 60  # Percentage for vertical split
    
    # Panel states
    chat_panel_collapsed: bool = False
    document_panel_collapsed: bool = False
    chat_panel_expanded: bool = False
    document_panel_expanded: bool = False
    
    # Resize state
    is_resizing: bool = False
    resize_start_position: Tuple[int, int] = (0, 0)
    resize_start_width: int = 50
    resize_start_height: int = 60
    
    # Responsive state
    is_mobile: bool = False
    is_tablet: bool = False
    window_width: int = 1920
    window_height: int = 1080
    
    # Layout persistence
    layout_preferences: Dict[str, Any] = {}
    
    # Cross-panel communication
    active_citation_id: Optional[str] = None
    synchronized_scroll_position: float = 0.0
    shared_search_query: str = ""
    shared_highlight_ids: list[str] = []
    
    # Document context
    active_document_id: Optional[str] = None
    document_tabs: list[Dict[str, Any]] = []
    active_tab_index: int = 0
    
    # Performance optimization
    render_debounce_timer: Optional[str] = None
    last_resize_time: float = 0.0
    
    def __init__(self):
        super().__init__()
        self.load_layout_preferences()
    
    # Layout Mode Management
    
    def set_layout_mode(self, mode: Literal["chat", "split", "document"]):
        """Set the layout mode with smooth transitions."""
        if mode != self.layout_mode:
            self.previous_layout_mode = self.layout_mode
            self.layout_mode = mode
            
            # Reset expanded states when changing modes
            self.chat_panel_expanded = False
            self.document_panel_expanded = False
            
            # Auto-adjust for mobile
            if self.is_mobile and mode == "split":
                self.layout_mode = "chat"  # Default to chat on mobile
            
            self.save_layout_preferences()
    
    def toggle_split_orientation(self):
        """Toggle between horizontal and vertical split."""
        if self.layout_mode == "split":
            self.split_orientation = "vertical" if self.split_orientation == "horizontal" else "horizontal"
            self.save_layout_preferences()
    
    def toggle_chat_expanded(self):
        """Toggle chat panel expanded state in split view."""
        if self.layout_mode == "split":
            self.chat_panel_expanded = not self.chat_panel_expanded
            if self.chat_panel_expanded:
                self.document_panel_expanded = False
    
    def toggle_document_expanded(self):
        """Toggle document panel expanded state in split view."""
        if self.layout_mode == "split":
            self.document_panel_expanded = not self.document_panel_expanded
            if self.document_panel_expanded:
                self.chat_panel_expanded = False
    
    # Resizable Panel Management
    
    def start_resize(self, event):
        """Start panel resizing."""
        self.is_resizing = True
        self.resize_start_position = (event.client_x, event.client_y)
        self.resize_start_width = self.chat_panel_width
        self.resize_start_height = self.chat_panel_height
    
    def handle_resize(self, event):
        """Handle panel resizing during mouse move."""
        if not self.is_resizing or self.layout_mode != "split":
            return
        
        import time
        current_time = time.time()
        
        # Debounce resize events for performance
        if current_time - self.last_resize_time < 0.016:  # ~60fps
            return
        
        self.last_resize_time = current_time
        
        if self.split_orientation == "horizontal":
            # Calculate new width based on mouse position
            delta_x = event.client_x - self.resize_start_position[0]
            container_width = self.window_width
            
            if container_width > 0:
                delta_percent = (delta_x / container_width) * 100
                new_width = self.resize_start_width + delta_percent
                
                # Constrain between 20% and 80%
                self.chat_panel_width = max(20, min(80, int(new_width)))
        else:
            # Calculate new height based on mouse position
            delta_y = event.client_y - self.resize_start_position[1]
            container_height = self.window_height
            
            if container_height > 0:
                delta_percent = (delta_y / container_height) * 100
                new_height = self.resize_start_height + delta_percent
                
                # Constrain between 20% and 80%
                self.chat_panel_height = max(20, min(80, int(new_height)))
    
    def end_resize(self, event):
        """End panel resizing."""
        if self.is_resizing:
            self.is_resizing = False
            self.save_layout_preferences()
    
    # Responsive Design
    
    def handle_window_resize(self, event):
        """Handle window resize events."""
        self.window_width = event.inner_width
        self.window_height = event.inner_height
        
        # Update responsive breakpoints
        self.is_mobile = self.window_width < 768
        self.is_tablet = 768 <= self.window_width < 1024
        
        # Auto-switch to appropriate layout for mobile
        if self.is_mobile and self.layout_mode == "split":
            self.set_layout_mode("chat")
        
        self.save_layout_preferences()
    
    # Cross-Panel Communication
    
    def set_active_citation(self, citation_id: str):
        """Set active citation for cross-panel synchronization."""
        self.active_citation_id = citation_id
        
        # Auto-switch to split view if not already there
        if self.layout_mode == "chat":
            self.set_layout_mode("split")
    
    def sync_scroll_position(self, position: float):
        """Synchronize scroll position between panels."""
        self.synchronized_scroll_position = position
    
    def set_shared_search_query(self, query: str):
        """Set shared search query across panels."""
        self.shared_search_query = query
    
    def add_shared_highlight(self, highlight_id: str):
        """Add shared highlight across panels."""
        if highlight_id not in self.shared_highlight_ids:
            self.shared_highlight_ids.append(highlight_id)
    
    def remove_shared_highlight(self, highlight_id: str):
        """Remove shared highlight across panels."""
        if highlight_id in self.shared_highlight_ids:
            self.shared_highlight_ids.remove(highlight_id)
    
    def clear_shared_highlights(self):
        """Clear all shared highlights."""
        self.shared_highlight_ids.clear()
    
    # Document Tab Management
    
    def add_document_tab(self, document_id: str, title: str, url: str):
        """Add a new document tab."""
        tab_data = {
            "id": document_id,
            "title": title,
            "url": url,
            "is_active": len(self.document_tabs) == 0
        }
        
        # Check if tab already exists
        existing_index = self.get_document_tab_index(document_id)
        if existing_index >= 0:
            self.set_active_document_tab(existing_index)
            return
        
        self.document_tabs.append(tab_data)
        self.active_tab_index = len(self.document_tabs) - 1
        self.active_document_id = document_id
        
        # Auto-switch to split or document view
        if self.layout_mode == "chat":
            self.set_layout_mode("split")
    
    def remove_document_tab(self, index: int):
        """Remove a document tab."""
        if 0 <= index < len(self.document_tabs):
            removed_tab = self.document_tabs.pop(index)
            
            # Adjust active tab index
            if index == self.active_tab_index:
                if self.document_tabs:
                    self.active_tab_index = min(index, len(self.document_tabs) - 1)
                    self.active_document_id = self.document_tabs[self.active_tab_index]["id"]
                else:
                    self.active_tab_index = 0
                    self.active_document_id = None
            elif index < self.active_tab_index:
                self.active_tab_index -= 1
    
    def set_active_document_tab(self, index: int):
        """Set active document tab."""
        if 0 <= index < len(self.document_tabs):
            self.active_tab_index = index
            self.active_document_id = self.document_tabs[index]["id"]
            
            # Update tab states
            for i, tab in enumerate(self.document_tabs):
                tab["is_active"] = (i == index)
    
    def get_document_tab_index(self, document_id: str) -> int:
        """Get the index of a document tab by ID."""
        for i, tab in enumerate(self.document_tabs):
            if tab["id"] == document_id:
                return i
        return -1
    
    # Layout Persistence
    
    def save_layout_preferences(self):
        """Save layout preferences to browser storage."""
        preferences = {
            "layout_mode": self.layout_mode,
            "split_orientation": self.split_orientation,
            "chat_panel_width": self.chat_panel_width,
            "chat_panel_height": self.chat_panel_height,
            "window_width": self.window_width,
            "window_height": self.window_height
        }
        
        self.layout_preferences = preferences
        
        # Store in browser localStorage (would need browser integration)
        # For now, keep in memory
    
    def load_layout_preferences(self):
        """Load layout preferences from browser storage."""
        # In a real implementation, this would load from localStorage
        # For now, use defaults
        default_preferences = {
            "layout_mode": "chat",
            "split_orientation": "horizontal",
            "chat_panel_width": 50,
            "chat_panel_height": 60,
            "window_width": 1920,
            "window_height": 1080
        }
        
        self.layout_preferences = default_preferences
        
        # Apply loaded preferences
        self.layout_mode = default_preferences["layout_mode"]
        self.split_orientation = default_preferences["split_orientation"]
        self.chat_panel_width = default_preferences["chat_panel_width"]
        self.chat_panel_height = default_preferences["chat_panel_height"]
        self.window_width = default_preferences["window_width"]
        self.window_height = default_preferences["window_height"]
    
    def reset_layout_preferences(self):
        """Reset layout preferences to defaults."""
        self.layout_mode = "chat"
        self.split_orientation = "horizontal"
        self.chat_panel_width = 50
        self.chat_panel_height = 60
        self.chat_panel_collapsed = False
        self.document_panel_collapsed = False
        self.chat_panel_expanded = False
        self.document_panel_expanded = False
        self.save_layout_preferences()
    
    # Performance Optimization
    
    def debounce_render(self, delay: float = 0.1):
        """Debounce render updates for performance."""
        import asyncio
        
        async def delayed_render():
            await asyncio.sleep(delay)
            self.render_debounce_timer = None
        
        if self.render_debounce_timer:
            # Cancel previous timer
            pass
        
        self.render_debounce_timer = "active"
        # In a real implementation, would use proper async timer
    
    # Computed Properties
    
    @rx.var
    def effective_chat_width(self) -> int:
        """Get effective chat panel width considering expanded states."""
        if self.layout_mode != "split":
            return 100 if self.layout_mode == "chat" else 0
        
        if self.chat_panel_expanded:
            return 80
        elif self.document_panel_expanded:
            return 20
        else:
            return self.chat_panel_width
    
    @rx.var
    def effective_document_width(self) -> int:
        """Get effective document panel width considering expanded states."""
        if self.layout_mode != "split":
            return 100 if self.layout_mode == "document" else 0
        
        return 100 - self.effective_chat_width
    
    @rx.var
    def effective_chat_height(self) -> int:
        """Get effective chat panel height considering expanded states."""
        if self.layout_mode != "split":
            return 100 if self.layout_mode == "chat" else 0
        
        if self.chat_panel_expanded:
            return 80
        elif self.document_panel_expanded:
            return 20
        else:
            return self.chat_panel_height
    
    @rx.var
    def effective_document_height(self) -> int:
        """Get effective document panel height considering expanded states."""
        if self.layout_mode != "split":
            return 100 if self.layout_mode == "document" else 0
        
        return 100 - self.effective_chat_height
    
    @rx.var
    def should_show_mobile_warning(self) -> bool:
        """Determine if mobile layout warning should be shown."""
        return self.is_mobile and self.layout_mode == "split"
    
    @rx.var
    def active_document_tab(self) -> Dict[str, Any]:
        """Get the currently active document tab."""
        if self.document_tabs and 0 <= self.active_tab_index < len(self.document_tabs):
            return self.document_tabs[self.active_tab_index]
        return {"id": "", "title": "", "url": "", "is_active": False}