"""
Analytics page for the Arete Reflex application.
"""

import reflex as rx
from ..components.layout import base_layout
from ..components.analytics import analytics_dashboard


def analytics_page() -> rx.Component:
    """Analytics dashboard page component."""
    return base_layout(
        rx.div(
            analytics_dashboard(),
            class_name="h-full p-6"
        ),
        class_name="h-screen"
    )