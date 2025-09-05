"""
Layout components for the Arete Reflex application.
"""

import reflex as rx


def navbar() -> rx.Component:
    """Main navigation bar component."""
    return rx.div(
        rx.div(
            rx.link(
                rx.hstack(
                    rx.text("🏛️", font_size="1.5rem"),
                    rx.text(
                        "Arete",
                        font_size="1.25rem",
                        font_weight="bold",
                        color="primary"
                    ),
                    spacing="2"
                ),
                href="/",
                class_name="no-underline"
            ),
            rx.div(
                rx.hstack(
                    rx.link(
                        "Home",
                        href="/",
                        class_name="btn btn-ghost btn-sm"
                    ),
                    rx.link(
                        "Chat",
                        href="/chat", 
                        class_name="btn btn-ghost btn-sm"
                    ),
                    rx.link(
                        "Documents",
                        href="/documents",
                        class_name="btn btn-ghost btn-sm"
                    ),
                    rx.link(
                        "Analytics",
                        href="/analytics",
                        class_name="btn btn-ghost btn-sm"
                    ),
                    spacing="2"
                ),
                class_name="hidden md:flex"
            ),
            rx.div(
                rx.button(
                    rx.text("☰", font_size="1.25rem"),
                    class_name="btn btn-ghost btn-sm md:hidden"
                ),
                class_name="dropdown dropdown-end md:hidden"
            ),
            class_name="navbar-start navbar-center navbar-end flex justify-between items-center w-full"
        ),
        class_name="navbar bg-base-100 border-b border-base-200 px-4 py-2"
    )


def sidebar() -> rx.Component:
    """Sidebar component for navigation."""
    return rx.div(
        rx.div(
            rx.text(
                "Navigation",
                font_size="0.875rem",
                font_weight="semibold",
                color="base-content",
                class_name="opacity-60 uppercase tracking-wide mb-4"
            ),
            rx.vstack(
                rx.link(
                    rx.hstack(
                        rx.text("🏠", font_size="1rem"),
                        rx.text("Home"),
                        spacing="3",
                        align="center"
                    ),
                    href="/",
                    class_name="w-full p-3 rounded-lg hover:bg-base-200 text-base-content no-underline"
                ),
                rx.link(
                    rx.hstack(
                        rx.text("💬", font_size="1rem"),
                        rx.text("Chat"),
                        spacing="3",
                        align="center"
                    ),
                    href="/chat",
                    class_name="w-full p-3 rounded-lg hover:bg-base-200 text-base-content no-underline"
                ),
                rx.link(
                    rx.hstack(
                        rx.text("📚", font_size="1rem"),
                        rx.text("Documents"),
                        spacing="3",
                        align="center"
                    ),
                    href="/documents",
                    class_name="w-full p-3 rounded-lg hover:bg-base-200 text-base-content no-underline"
                ),
                rx.link(
                    rx.hstack(
                        rx.text("📊", font_size="1rem"),
                        rx.text("Analytics"),
                        spacing="3",
                        align="center"
                    ),
                    href="/analytics",
                    class_name="w-full p-3 rounded-lg hover:bg-base-200 text-base-content no-underline"
                ),
                spacing="2",
                width="100%"
            ),
            class_name="p-4"
        ),
        class_name="w-64 bg-base-100 border-r border-base-200 h-full"
    )


def base_layout(*children, **props) -> rx.Component:
    """Base layout wrapper for all pages."""
    return rx.div(
        navbar(),
        rx.div(
            *children,
            class_name="flex-1 overflow-auto"
        ),
        class_name="min-h-screen flex flex-col bg-base-200",
        **props
    )