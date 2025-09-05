"""Chat page for philosophical conversations."""

import reflex as rx
from ..components.layout import base_layout
from ..state import NavigationState


def chat_page() -> rx.Component:
    """Chat page with full interface."""
    return base_layout(
        rx.box(
            # Set layout to chat mode on page load
            rx.script(
                NavigationState.set_layout_mode("chat")
            ),
            padding="0",  # Let the layout component handle padding
            height="100%"
        )
    )