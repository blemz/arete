"""
Document viewer page for the Arete Reflex application.
"""

import reflex as rx
from ..components.layout import base_layout
from ..components.document_viewer import document_viewer


def document_page() -> rx.Component:
    """Document viewer page component."""
    return base_layout(
        rx.div(
            document_viewer(),
            class_name="h-full"
        ),
        class_name="h-screen"
    )