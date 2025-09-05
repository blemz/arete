"""
Chat page for the Arete Reflex application.
"""

import reflex as rx
from ..components.layout import base_layout
from ..components.chat import chat_interface


def chat_page() -> rx.Component:
    """Chat page component."""
    return base_layout(
        rx.div(
            chat_interface(),
            class_name="h-full"
        ),
        class_name="h-screen"
    )