"""Split-view layout system for Reflex app with resizable panels and mode management."""

import reflex as rx
from typing import Dict, Any, Optional, Literal
from ...state.layout_state import LayoutState


class SplitViewComponent(rx.Component):
    """Resizable split-view layout with chat and document panels."""
    
    def render(self) -> rx.Component:
        return rx.box(
            # Main split container
            rx.box(
                # Chat panel
                rx.box(
                    rx.cond(
                        LayoutState.layout_mode == "chat",
                        self._render_chat_only(),
                        rx.cond(
                            LayoutState.layout_mode == "split",
                            self._render_chat_split(),
                            rx.box()  # Hidden in document-only mode
                        )
                    ),
                    id="chat-panel",
                    class_name=rx.cond(
                        LayoutState.layout_mode == "chat",
                        "w-full h-full",
                        rx.cond(
                            LayoutState.layout_mode == "split",
                            rx.cond(
                                LayoutState.split_orientation == "horizontal",
                                f"w-[{LayoutState.chat_panel_width}%] h-full",
                                f"w-full h-[{LayoutState.chat_panel_height}%]"
                            ),
                            "hidden"
                        )
                    ),
                    style={
                        "transition": "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                        "overflow": "hidden",
                        "border_right": rx.cond(
                            (LayoutState.layout_mode == "split") & (LayoutState.split_orientation == "horizontal"),
                            "1px solid var(--color-border)",
                            "none"
                        ),
                        "border_bottom": rx.cond(
                            (LayoutState.layout_mode == "split") & (LayoutState.split_orientation == "vertical"),
                            "1px solid var(--color-border)",
                            "none"
                        )
                    }
                ),
                
                # Resizable divider
                rx.cond(
                    LayoutState.layout_mode == "split",
                    rx.box(
                        rx.box(
                            class_name=rx.cond(
                                LayoutState.split_orientation == "horizontal",
                                "w-1 h-full bg-gray-200 hover:bg-gray-300 cursor-col-resize",
                                "w-full h-1 bg-gray-200 hover:bg-gray-300 cursor-row-resize"
                            ),
                            style={
                                "transition": "background-color 0.2s ease",
                                "user_select": "none"
                            }
                        ),
                        on_mouse_down=LayoutState.start_resize,
                        class_name=rx.cond(
                            LayoutState.split_orientation == "horizontal",
                            "flex items-center justify-center w-1 h-full",
                            "flex items-center justify-center w-full h-1"
                        )
                    ),
                    rx.box()
                ),
                
                # Document panel
                rx.box(
                    rx.cond(
                        LayoutState.layout_mode == "document",
                        self._render_document_only(),
                        rx.cond(
                            LayoutState.layout_mode == "split",
                            self._render_document_split(),
                            rx.box()  # Hidden in chat-only mode
                        )
                    ),
                    id="document-panel",
                    class_name=rx.cond(
                        LayoutState.layout_mode == "document",
                        "w-full h-full",
                        rx.cond(
                            LayoutState.layout_mode == "split",
                            rx.cond(
                                LayoutState.split_orientation == "horizontal",
                                f"w-[{100 - LayoutState.chat_panel_width}%] h-full",
                                f"w-full h-[{100 - LayoutState.chat_panel_height}%]"
                            ),
                            "hidden"
                        )
                    ),
                    style={
                        "transition": "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                        "overflow": "hidden"
                    }
                ),
                
                class_name=rx.cond(
                    LayoutState.split_orientation == "horizontal",
                    "flex flex-row h-full",
                    "flex flex-col h-full"
                ),
                style={
                    "width": "100%",
                    "height": "100vh",
                    "position": "relative"
                }
            ),
            
            # Layout mode controls
            self._render_layout_controls(),
            
            # Mobile responsive overlay
            rx.cond(
                LayoutState.is_mobile & (LayoutState.layout_mode == "split"),
                self._render_mobile_overlay(),
                rx.box()
            ),
            
            class_name="relative w-full h-screen overflow-hidden",
            on_window_resize=LayoutState.handle_window_resize,
            on_mouse_move=LayoutState.handle_resize,
            on_mouse_up=LayoutState.end_resize
        )
    
    def _render_chat_only(self) -> rx.Component:
        """Render chat interface in full-width mode."""
        from ..chat.chat_interface import ChatInterface
        
        return rx.box(
            ChatInterface(),
            class_name="w-full h-full",
            style={
                "padding": "1rem",
                "display": "flex",
                "flex_direction": "column"
            }
        )
    
    def _render_chat_split(self) -> rx.Component:
        """Render chat interface in split-view mode."""
        from ..chat.chat_interface import ChatInterface
        
        return rx.box(
            # Split-view chat header
            rx.box(
                rx.heading(
                    "Chat",
                    size="sm",
                    class_name="text-gray-700 dark:text-gray-300"
                ),
                rx.button_group(
                    rx.button(
                        rx.icon("maximize-2"),
                        on_click=LayoutState.toggle_chat_expanded,
                        variant="ghost",
                        size="sm",
                        aria_label="Expand chat panel"
                    ),
                    rx.button(
                        rx.icon("x"),
                        on_click=lambda: LayoutState.set_layout_mode("document"),
                        variant="ghost",
                        size="sm",
                        aria_label="Close chat panel"
                    ),
                    class_name="flex gap-1"
                ),
                class_name="flex justify-between items-center p-2 border-b border-gray-200 dark:border-gray-700",
                style={"min_height": "3rem"}
            ),
            
            # Chat content
            rx.box(
                ChatInterface(compact_mode=True),
                class_name="flex-1 overflow-hidden"
            ),
            
            class_name="flex flex-col h-full bg-white dark:bg-gray-900"
        )
    
    def _render_document_only(self) -> rx.Component:
        """Render document viewer in full-width mode."""
        from ..document.document_viewer import DocumentViewer
        
        return rx.box(
            DocumentViewer(),
            class_name="w-full h-full"
        )
    
    def _render_document_split(self) -> rx.Component:
        """Render document viewer in split-view mode."""
        from ..document.document_viewer import DocumentViewer
        
        return rx.box(
            # Split-view document header
            rx.box(
                rx.heading(
                    "Document",
                    size="sm",
                    class_name="text-gray-700 dark:text-gray-300"
                ),
                rx.button_group(
                    rx.button(
                        rx.icon("maximize-2"),
                        on_click=LayoutState.toggle_document_expanded,
                        variant="ghost",
                        size="sm",
                        aria_label="Expand document panel"
                    ),
                    rx.button(
                        rx.icon("x"),
                        on_click=lambda: LayoutState.set_layout_mode("chat"),
                        variant="ghost",
                        size="sm",
                        aria_label="Close document panel"
                    ),
                    class_name="flex gap-1"
                ),
                class_name="flex justify-between items-center p-2 border-b border-gray-200 dark:border-gray-700",
                style={"min_height": "3rem"}
            ),
            
            # Document content
            rx.box(
                DocumentViewer(compact_mode=True),
                class_name="flex-1 overflow-hidden"
            ),
            
            class_name="flex flex-col h-full bg-white dark:bg-gray-900"
        )
    
    def _render_layout_controls(self) -> rx.Component:
        """Render layout mode controls."""
        return rx.box(
            rx.button_group(
                rx.button(
                    rx.icon("message-square"),
                    rx.text("Chat", class_name="hidden md:inline ml-1"),
                    on_click=lambda: LayoutState.set_layout_mode("chat"),
                    variant=rx.cond(
                        LayoutState.layout_mode == "chat",
                        "solid",
                        "outline"
                    ),
                    size="sm",
                    class_name="flex items-center"
                ),
                rx.button(
                    rx.icon("columns"),
                    rx.text("Split", class_name="hidden md:inline ml-1"),
                    on_click=lambda: LayoutState.set_layout_mode("split"),
                    variant=rx.cond(
                        LayoutState.layout_mode == "split",
                        "solid",
                        "outline"
                    ),
                    size="sm",
                    class_name="flex items-center"
                ),
                rx.button(
                    rx.icon("file-text"),
                    rx.text("Document", class_name="hidden md:inline ml-1"),
                    on_click=lambda: LayoutState.set_layout_mode("document"),
                    variant=rx.cond(
                        LayoutState.layout_mode == "document",
                        "solid",
                        "outline"
                    ),
                    size="sm",
                    class_name="flex items-center"
                ),
                rx.cond(
                    LayoutState.layout_mode == "split",
                    rx.button(
                        rx.icon(
                            rx.cond(
                                LayoutState.split_orientation == "horizontal",
                                "split-square-horizontal",
                                "split-square-vertical"
                            )
                        ),
                        on_click=LayoutState.toggle_split_orientation,
                        variant="outline",
                        size="sm",
                        aria_label="Toggle split orientation"
                    ),
                    rx.box()
                ),
                class_name="flex gap-1"
            ),
            class_name="absolute top-4 right-4 z-10 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-2 border border-gray-200 dark:border-gray-700"
        )
    
    def _render_mobile_overlay(self) -> rx.Component:
        """Render mobile responsive overlay."""
        return rx.box(
            rx.box(
                rx.text(
                    "Split view is not available on mobile devices. Switch to single panel mode.",
                    class_name="text-center text-gray-600 dark:text-gray-400 mb-4"
                ),
                rx.button_group(
                    rx.button(
                        "Chat Mode",
                        on_click=lambda: LayoutState.set_layout_mode("chat"),
                        class_name="flex-1"
                    ),
                    rx.button(
                        "Document Mode",
                        on_click=lambda: LayoutState.set_layout_mode("document"),
                        class_name="flex-1"
                    ),
                    class_name="flex gap-2 w-full"
                ),
                class_name="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-xl max-w-sm w-full"
            ),
            class_name="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
        )


def split_view() -> rx.Component:
    """Create split-view layout component."""
    return SplitViewComponent().render()