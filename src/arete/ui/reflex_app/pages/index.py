"""
Index/Home page for the Arete Reflex application.
"""

import reflex as rx

from ..components.features import features_section
from ..components.hero import hero_section
from ..components.layout import base_layout


def index_page() -> rx.Component:
    """Home page component."""
    return base_layout(
        rx.vstack(
            hero_section(),
            features_section(),
            spacing="8",
            class_name="min-h-screen"
        )
    )
