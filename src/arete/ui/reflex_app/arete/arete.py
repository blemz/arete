"""
Arete Reflex Application - Main Entry Point

A Graph-RAG AI tutoring system for classical philosophical texts.
Built with Reflex framework for modern web interface.
"""

import reflex as rx
from typing import List

class State(rx.State):
    """Global application state."""
    
    # Chat state
    user_query: str = ""
    chat_messages: List[str] = []
    
    def set_user_query(self, query: str):
        """Set the user query."""
        self.user_query = query
    
    def send_message(self):
        """Send a chat message."""
        if self.user_query.strip():
            self.chat_messages.append(f"You: {self.user_query}")
            self.chat_messages.append(f"Arete: Thanks for asking about '{self.user_query}'. I'm a philosophy tutor!")
            self.user_query = ""


def index() -> rx.Component:
    """Home page."""
    return rx.container(
        rx.vstack(
            rx.heading("🏛️ Welcome to Arete", size="9", color="blue.600"),
            rx.text(
                "AI Philosophy Tutor powered by Graph-RAG", 
                size="5", 
                color="gray.600"
            ),
            rx.hstack(
                rx.button(
                    "Start Learning", 
                    on_click=rx.redirect("/chat"),
                    color_scheme="blue",
                    size="3"
                ),
                rx.button(
                    "Browse Texts",
                    on_click=rx.redirect("/documents"), 
                    color_scheme="green",
                    size="3"
                ),
                rx.button(
                    "View Analytics",
                    on_click=rx.redirect("/analytics"),
                    color_scheme="purple", 
                    size="3"
                ),
                spacing="4"
            ),
            spacing="6",
            align="center",
            min_height="80vh",
            justify="center"
        ),
        size="4"
    )


def chat() -> rx.Component:
    """Chat interface."""
    return rx.container(
        rx.vstack(
            rx.heading("💬 Chat with Arete", size="7", color="blue.600"),
            
            # Messages area
            rx.box(
                rx.vstack(
                    rx.foreach(
                        State.chat_messages,
                        lambda msg: rx.text(msg, padding="2")
                    ),
                    spacing="2",
                    width="100%"
                ),
                bg="gray.50",
                p="4", 
                border_radius="lg",
                height="400px",
                overflow_y="auto",
                width="100%"
            ),
            
            # Input area
            rx.hstack(
                rx.input(
                    placeholder="Ask about philosophy...",
                    value=State.user_query,
                    on_change=State.set_user_query,
                    width="100%"
                ),
                rx.button(
                    "Send",
                    on_click=State.send_message,
                    color_scheme="blue"
                ),
                width="100%"
            ),
            
            spacing="4",
            width="100%"
        ),
        size="4"
    )


def documents() -> rx.Component:
    """Document library."""
    return rx.container(
        rx.vstack(
            rx.heading("📚 Document Library", size="7", color="green.600"),
            rx.text("Browse classical philosophical texts"),
            
            rx.grid(
                rx.box(
                    rx.vstack(
                        rx.heading("Plato's Apology", size="5"),
                        rx.text("Socrates' defense in court", color="gray.600"),
                        rx.button("Read", color_scheme="green", size="2"),
                        spacing="2"
                    ),
                    bg="white",
                    p="4",
                    border_radius="lg",
                    border="1px solid",
                    border_color="gray.200",
                    _hover={"shadow": "lg"}
                ),
                rx.box(
                    rx.vstack(
                        rx.heading("Charmides", size="5"),
                        rx.text("On temperance and self-knowledge", color="gray.600"),
                        rx.button("Read", color_scheme="green", size="2"),
                        spacing="2"
                    ),
                    bg="white",
                    p="4", 
                    border_radius="lg",
                    border="1px solid",
                    border_color="gray.200",
                    _hover={"shadow": "lg"}
                ),
                columns="2",
                spacing="4",
                width="100%"
            ),
            
            spacing="4",
            align="center"
        ),
        size="4"
    )


def analytics() -> rx.Component:
    """Analytics dashboard."""
    return rx.container(
        rx.vstack(
            rx.heading("📊 Knowledge Graph Analytics", size="7", color="purple.600"),
            rx.text("Explore philosophical concepts and relationships"),
            
            rx.grid(
                rx.box(
                    rx.vstack(
                        rx.text("Documents", font_weight="bold"),
                        rx.text("2", font_size="3xl", color="blue.500"),
                        rx.text("Classical texts", color="gray.600"),
                        spacing="1"
                    ),
                    bg="blue.50",
                    p="4",
                    border_radius="lg",
                    text_align="center"
                ),
                rx.box(
                    rx.vstack(
                        rx.text("Concepts", font_weight="bold"),
                        rx.text("83", font_size="3xl", color="green.500"),
                        rx.text("Philosophical entities", color="gray.600"),
                        spacing="1"
                    ),
                    bg="green.50",
                    p="4",
                    border_radius="lg", 
                    text_align="center"
                ),
                rx.box(
                    rx.vstack(
                        rx.text("Relationships", font_weight="bold"),
                        rx.text("109", font_size="3xl", color="purple.500"),
                        rx.text("Concept connections", color="gray.600"),
                        spacing="1"
                    ),
                    bg="purple.50",
                    p="4",
                    border_radius="lg",
                    text_align="center"
                ),
                columns="3",
                spacing="4",
                width="100%"
            ),
            
            spacing="4",
            align="center"
        ),
        size="4"
    )


def navbar() -> rx.Component:
    """Navigation bar."""
    return rx.box(
        rx.hstack(
            rx.hstack(
                rx.text("🏛️", font_size="2xl"),
                rx.text("Arete", font_size="xl", font_weight="bold", color="blue.600"),
                spacing="2"
            ),
            rx.spacer(),
            rx.hstack(
                rx.link("Home", href="/", color="gray.600", _hover={"color": "blue.600"}),
                rx.link("Chat", href="/chat", color="gray.600", _hover={"color": "blue.600"}),
                rx.link("Documents", href="/documents", color="gray.600", _hover={"color": "green.600"}), 
                rx.link("Analytics", href="/analytics", color="gray.600", _hover={"color": "purple.600"}),
                spacing="6"
            ),
            justify="between",
            align="center",
            width="100%"
        ),
        bg="white",
        border_bottom="1px solid",
        border_color="gray.200",
        px="6",
        py="4",
        width="100%"
    )


def footer() -> rx.Component:
    """Footer."""
    return rx.box(
        rx.hstack(
            rx.text("© 2024 Arete - AI Philosophy Tutor", color="gray.500"),
            rx.spacer(),
            rx.text("Powered by Reflex & Graph-RAG", color="gray.400"),
            justify="between",
            align="center",
            width="100%"
        ),
        bg="gray.50",
        border_top="1px solid",
        border_color="gray.200", 
        px="6",
        py="4",
        width="100%"
    )


def base_layout(content: rx.Component) -> rx.Component:
    """Base layout for all pages."""
    return rx.vstack(
        navbar(),
        rx.box(content, flex="1", width="100%"),
        footer(),
        spacing="0",
        min_height="100vh",
        width="100%"
    )


# Page functions
def index_page() -> rx.Component:
    return base_layout(index())

def chat_page() -> rx.Component:
    return base_layout(chat())

def documents_page() -> rx.Component:
    return base_layout(documents())

def analytics_page() -> rx.Component:
    return base_layout(analytics())


# Create the app
app = rx.App()

# Add pages
app.add_page(index_page, route="/", title="Arete - Home")
app.add_page(chat_page, route="/chat", title="Arete - Chat")
app.add_page(documents_page, route="/documents", title="Arete - Documents")
app.add_page(analytics_page, route="/analytics", title="Arete - Analytics")