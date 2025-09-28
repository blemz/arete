"""State management for Arete Reflex application."""

try:
    from .chat_state import RAGChatState as ChatState
except ImportError:
    # Create a basic fallback state
    import reflex as rx
    class ChatState(rx.State):
        messages: list = []
        current_input: str = ""

try:
    from .document_state import DocumentState
except ImportError:
    import reflex as rx
    class DocumentState(rx.State):
        current_document: str = ""

try:
    from .layout_state import LayoutState
except ImportError:
    import reflex as rx
    class LayoutState(rx.State):
        layout_mode: str = "split"

try:
    from .ui_state import UIState
except ImportError:
    import reflex as rx
    class UIState(rx.State):
        theme_mode: str = "light"

__all__ = [
    "ChatState",
    "DocumentState",
    "LayoutState",
    "UIState"
]