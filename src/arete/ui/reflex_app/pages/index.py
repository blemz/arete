"""
Index/Home page for the Arete Reflex application.
"""

import reflex as rx
from ..components.layout import base_layout
from ..components.hero import hero_section
from ..components.features import features_section


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