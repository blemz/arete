"""
Chat page for the Arete Reflex application.
"""

import reflex as rx

from ..components.chat import chat_interface
from ..components.layout import base_layout


def chat_page() -> rx.Component:
    """Chat page component."""
    return base_layout(
        rx.div(
            chat_interface(),
            class_name="h-full"
        ),
        class_name="h-screen"
    )
