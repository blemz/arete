"""Panel management system for coordinated split-view interactions."""

import reflex as rx
from typing import Dict, Any, Optional, List, Callable
from ...state.layout_state import LayoutState
from ...state.chat_state import ChatState
from ...state.document_state import DocumentState


class PanelManager:
    """Manages coordination between chat and document panels."""
    
    @staticmethod
    def sync_citation_highlight(citation_id: str, source_panel: str):
        """Synchronize citation highlighting across panels."""
        # Set active citation in layout state
        LayoutState.set_active_citation(citation_id)
        
        # Update document highlighting if citation clicked in chat
        if source_panel == "chat":
            DocumentState.highlight_citation(citation_id)
            DocumentState.scroll_to_citation(citation_id)
        
        # Update chat context if citation clicked in document
        elif source_panel == "document":
            ChatState.set_citation_context(citation_id)
    
    @staticmethod
    def sync_search_across_panels(query: str, source_panel: str):
        """Synchronize search query across both panels."""
        LayoutState.set_shared_search_query(query)
        
        if source_panel == "chat":
            DocumentState.perform_search(query)
        elif source_panel == "document":
            ChatState.set_search_context(query)
    
    @staticmethod
    def handle_document_selection(document_id: str, title: str, url: str):
        """Handle document selection and tab management."""
        # Add or activate document tab
        LayoutState.add_document_tab(document_id, title, url)
        
        # Load document content
        DocumentState.load_document(document_id, url)
        
        # Switch to appropriate layout mode
        if LayoutState.layout_mode == "chat":
            LayoutState.set_layout_mode("split")
    
    @staticmethod
    def handle_chat_citation_click(citation_id: str, document_id: str, position: float):
        """Handle citation click from chat interface."""
        # Ensure document is loaded
        if document_id != LayoutState.active_document_id:
            # Load the cited document
            DocumentState.load_document_by_citation(citation_id)
        
        # Synchronize citation highlight
        PanelManager.sync_citation_highlight(citation_id, "chat")
        
        # Scroll to citation position
        DocumentState.scroll_to_position(position)
        
        # Switch to split view if needed
        if LayoutState.layout_mode == "chat":
            LayoutState.set_layout_mode("split")


class CrossPanelCommunication(rx.Component):
    """Component for handling cross-panel communication events."""
    
    def render(self) -> rx.Component:
        return rx.box(
            # Hidden component that handles cross-panel events
            rx.script("""
                // Citation synchronization
                window.syncCitation = function(citationId, sourcePanel) {
                    const event = new CustomEvent('citation-sync', {
                        detail: { citationId, sourcePanel }
                    });
                    window.dispatchEvent(event);
                };
                
                // Search synchronization
                window.syncSearch = function(query, sourcePanel) {
                    const event = new CustomEvent('search-sync', {
                        detail: { query, sourcePanel }
                    });
                    window.dispatchEvent(event);
                };
                
                // Scroll synchronization
                window.syncScroll = function(position, sourcePanel) {
                    const event = new CustomEvent('scroll-sync', {
                        detail: { position, sourcePanel }
                    });
                    window.dispatchEvent(event);
                };
                
                // Handle resize events
                let resizeTimeout;
                window.addEventListener('resize', function() {
                    clearTimeout(resizeTimeout);
                    resizeTimeout = setTimeout(function() {
                        const event = new CustomEvent('window-resize', {
                            detail: {
                                innerWidth: window.innerWidth,
                                innerHeight: window.innerHeight
                            }
                        });
                        window.dispatchEvent(event);
                    }, 100);
                });
                
                // Keyboard shortcuts for layout switching
                window.addEventListener('keydown', function(e) {
                    if (e.ctrlKey || e.metaKey) {
                        switch(e.key) {
                            case '1':
                                e.preventDefault();
                                window.dispatchEvent(new CustomEvent('layout-change', {
                                    detail: { mode: 'chat' }
                                }));
                                break;
                            case '2':
                                e.preventDefault();
                                window.dispatchEvent(new CustomEvent('layout-change', {
                                    detail: { mode: 'split' }
                                }));
                                break;
                            case '3':
                                e.preventDefault();
                                window.dispatchEvent(new CustomEvent('layout-change', {
                                    detail: { mode: 'document' }
                                }));
                                break;
                            case 'Tab':
                                if (e.shiftKey) {
                                    e.preventDefault();
                                    window.dispatchEvent(new CustomEvent('toggle-split-orientation'));
                                }
                                break;
                        }
                    }
                });
                
                // Focus management
                window.manageFocus = function(targetPanel) {
                    const chatPanel = document.getElementById('chat-panel');
                    const documentPanel = document.getElementById('document-panel');
                    
                    if (targetPanel === 'chat' && chatPanel) {
                        const firstInput = chatPanel.querySelector('input, textarea, button');
                        if (firstInput) firstInput.focus();
                    } else if (targetPanel === 'document' && documentPanel) {
                        const firstScrollable = documentPanel.querySelector('[tabindex], input, button');
                        if (firstScrollable) firstScrollable.focus();
                    }
                };
            """),
            style={"display": "none"}
        )


class ResponsiveLayoutManager:
    """Manages responsive layout adaptations."""
    
    @staticmethod
    def get_layout_for_screen_size(width: int, height: int) -> Dict[str, Any]:
        """Get optimal layout configuration for screen size."""
        if width < 768:  # Mobile
            return {
                "layout_mode": "chat",  # Default to chat on mobile
                "split_orientation": "vertical",
                "chat_panel_height": 60,
                "force_single_panel": True
            }
        elif width < 1024:  # Tablet
            return {
                "layout_mode": "split",
                "split_orientation": "vertical",
                "chat_panel_height": 50,
                "force_single_panel": False
            }
        else:  # Desktop
            return {
                "layout_mode": "split",
                "split_orientation": "horizontal",
                "chat_panel_width": 50,
                "force_single_panel": False
            }
    
    @staticmethod
    def adapt_layout_for_content(chat_content_height: int, document_content_height: int) -> Dict[str, Any]:
        """Adapt layout based on content requirements."""
        total_content = chat_content_height + document_content_height
        
        if total_content == 0:
            return {"chat_panel_width": 50, "chat_panel_height": 50}
        
        # Calculate optimal split based on content
        chat_ratio = chat_content_height / total_content
        document_ratio = document_content_height / total_content
        
        # Ensure minimum 20% for each panel
        chat_percent = max(20, min(80, int(chat_ratio * 100)))
        
        return {
            "chat_panel_width": chat_percent,
            "chat_panel_height": chat_percent
        }


class LayoutPresetManager:
    """Manages layout presets and templates."""
    
    PRESETS = {
        "research": {
            "layout_mode": "split",
            "split_orientation": "horizontal",
            "chat_panel_width": 40,
            "description": "Optimized for research with larger document view"
        },
        "study": {
            "layout_mode": "split",
            "split_orientation": "vertical",
            "chat_panel_height": 45,
            "description": "Balanced view for active studying"
        },
        "reading": {
            "layout_mode": "document",
            "description": "Full document view for focused reading"
        },
        "chat": {
            "layout_mode": "chat",
            "description": "Full chat interface for conversation"
        },
        "mobile": {
            "layout_mode": "chat",
            "split_orientation": "vertical",
            "chat_panel_height": 60,
            "description": "Mobile-optimized layout"
        }
    }
    
    @staticmethod
    def apply_preset(preset_name: str):
        """Apply a layout preset."""
        if preset_name not in LayoutPresetManager.PRESETS:
            return
        
        preset = LayoutPresetManager.PRESETS[preset_name]
        
        LayoutState.set_layout_mode(preset["layout_mode"])
        
        if "split_orientation" in preset:
            LayoutState.split_orientation = preset["split_orientation"]
        
        if "chat_panel_width" in preset:
            LayoutState.chat_panel_width = preset["chat_panel_width"]
        
        if "chat_panel_height" in preset:
            LayoutState.chat_panel_height = preset["chat_panel_height"]
        
        LayoutState.save_layout_preferences()
    
    @staticmethod
    def get_preset_list() -> List[Dict[str, str]]:
        """Get list of available presets."""
        return [
            {
                "name": name,
                "description": preset["description"],
                "layout_mode": preset["layout_mode"]
            }
            for name, preset in LayoutPresetManager.PRESETS.items()
        ]


def panel_manager() -> rx.Component:
    """Create panel manager component."""
    return CrossPanelCommunication().render()