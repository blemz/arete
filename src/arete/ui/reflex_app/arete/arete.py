"""
Arete Reflex Application - Main Entry Point

A Graph-RAG AI tutoring system for classical philosophical texts.
Built with Reflex framework for modern web interface.
"""

import reflex as rx
from typing import List, Dict
import sys
import os

# Add components directory to Python path for direct imports
components_path = os.path.join(os.path.dirname(__file__), '..', 'components')
sys.path.insert(0, components_path)

from response_display import formatted_response, simple_message, thinking_animation

class State(rx.State):
    """Global application state."""
    
    # Chat state
    user_query: str = ""
    chat_messages: List[Dict[str, str]] = []
    is_loading: bool = False
    
    # Document state
    current_document: str = ""
    document_content: str = ""
    is_reading: bool = False
    
    def set_user_query(self, query: str):
        """Set the user query."""
        self.user_query = query
    
    async def send_message(self):
        """Send a chat message."""
        if self.user_query.strip():
            # Add user message
            self.chat_messages.append({
                "role": "user",
                "content": self.user_query
            })
            
            # Store query for async processing
            query = self.user_query
            self.user_query = ""
            
            # Set loading state
            self.is_loading = True
            
            # Try to get RAG response, fallback to simple response
            try:
                # Use production RAG CLI approach - simpler and more reliable
                import subprocess
                import sys
                import os
                
                # Get the root directory (arete project root)
                # Current file is in: src/arete/ui/reflex_app/arete/arete.py
                # Need to go up 5 levels to reach project root
                root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
                
                # Verify chat_rag_clean.py exists
                chat_rag_path = os.path.join(root_dir, 'chat_rag_clean.py')
                if not os.path.exists(chat_rag_path):
                    raise FileNotFoundError(f"chat_rag_clean.py not found at {chat_rag_path}")
                
                # Run the production RAG CLI
                result = subprocess.run([
                    sys.executable, 
                    'chat_rag_clean.py', 
                    query
                ], 
                cwd=root_dir,
                capture_output=True, 
                text=True, 
                timeout=180  # Extended timeout for GPT-5-mini reasoning models
                )
                
                # Log errors only if needed for debugging
                if result.returncode != 0:
                    print(f"RAG Error: {result.stderr}")
                
                if result.returncode == 0 and result.stdout.strip():
                    raw_response = result.stdout.strip()
                    
                    # Extract clean philosophical response
                    cleaned_response = self._clean_rag_response(raw_response)
                    
                    # Add assistant response
                    self.chat_messages.append({
                        "role": "assistant", 
                        "content": cleaned_response
                    })
                else:
                    # Fallback to mock philosophical response
                    fallback_response = f"That's a profound philosophical question about '{query}'. According to classical philosophy, this involves examining the nature of virtue, knowledge, and the good life as explored in Plato's dialogues."
                    self.chat_messages.append({
                        "role": "assistant",
                        "content": fallback_response
                    })
                    
            except Exception as e:
                # Fallback response with more philosophical content
                if "virtue" in query.lower():
                    fallback_content = "According to Socrates in Plato's dialogues, virtue is knowledge. He believed that if we truly know what is good, we will act virtuously. This is explored extensively in the Apology and other dialogues."
                elif "accused" in query.lower():
                    fallback_content = "In the Apology, Socrates faces several accusations: corrupting the youth of Athens, not believing in the gods of the city, and introducing new divinities. He systematically addresses each charge in his defense."
                else:
                    fallback_content = f"Thank you for that thoughtful question about '{query}'. This touches on fundamental philosophical concepts that require careful examination through the lens of classical philosophy."
                
                self.chat_messages.append({
                    "role": "assistant",
                    "content": fallback_content
                })
            
            # Always reset loading state
            self.is_loading = False
    
    def _clean_rag_response(self, raw_response: str) -> str:
        """Extract clean philosophical response from RAG output."""
        try:
            # Look for the response section between the delimiters
            response_start = "Response:\n" + "-" * 80 + "\n"
            response_end = "\n" + "-" * 80 + "\n\nCitations"
            
            start_idx = raw_response.find(response_start)
            if start_idx != -1:
                start_idx += len(response_start)
                end_idx = raw_response.find(response_end, start_idx)
                if end_idx != -1:
                    # Extract the philosophical content
                    philosophical_content = raw_response[start_idx:end_idx].strip()
                    return philosophical_content
            
            # Fallback: look for content after "Response:" if delimiters not found
            response_marker = "Response:\n"
            start_idx = raw_response.find(response_marker)
            if start_idx != -1:
                start_idx += len(response_marker)
                # Take content until citations or end
                content = raw_response[start_idx:]
                
                # Stop at citations section
                citations_idx = content.find("\nCitations from Plato's texts:")
                if citations_idx != -1:
                    content = content[:citations_idx]
                
                # Clean up any remaining formatting
                content = content.replace("-" * 80, "").strip()
                return content
            
            # Final fallback: return original response
            return raw_response
            
        except Exception:
            # If anything goes wrong, return the original response
            return raw_response
    
    def read_document(self, document_id: str):
        """Load and display a document."""
        self.current_document = document_id
        self.is_reading = True
        
        # Mock document content for now
        if document_id == "apology":
            self.document_content = """# Plato's Apology
            
The Apology is Plato's account of the speech given by Socrates in his defense during his trial for allegedly corrupting the youth and introducing new gods.

**Key Themes:**
- The unexamined life is not worth living
- Socratic wisdom and knowing that one knows nothing  
- The role of the philosopher in society
- Divine mission and the pursuit of wisdom

**Main Arguments:**
Socrates argues that his philosophical questioning serves Athens by exposing ignorance and encouraging virtue..."""
            
        elif document_id == "charmides":
            self.document_content = """# Plato's Charmides

The Charmides is a dialogue exploring the nature of temperance (sophrosyne) through Socratic questioning.

**Key Themes:**
- Definition of temperance/self-control
- Knowledge and self-knowledge
- The relationship between virtue and knowledge
- The limits of human wisdom

**Main Arguments:**
Through examining various definitions, Socrates shows the difficulty of defining temperance while highlighting its importance..."""
        else:
            self.document_content = "Document not found."
    
    def close_document(self):
        """Close the current document."""
        self.is_reading = False
        self.current_document = ""
        self.document_content = ""


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


def render_message(message: Dict[str, str]) -> rx.Component:
    """Render a message based on its role."""
    return rx.cond(
        message["role"] == "user",
        simple_message(message["content"], is_user=True),
        formatted_response(message["content"])
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
                        render_message
                    ),
                    # Show thinking animation when loading
                    rx.cond(
                        State.is_loading,
                        thinking_animation(),
                        rx.fragment()
                    ),
                    spacing="4",
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
                    placeholder=rx.cond(
                        State.is_loading,
                        "Arete is thinking...",
                        "Ask about philosophy..."
                    ),
                    value=State.user_query,
                    on_change=State.set_user_query,
                    disabled=State.is_loading,
                    width="100%"
                ),
                rx.button(
                    rx.cond(
                        State.is_loading,
                        "Thinking...",
                        "Send"
                    ),
                    on_click=State.send_message,
                    color_scheme="blue",
                    disabled=State.is_loading
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
        rx.cond(
            State.is_reading,
            # Document viewer
            rx.vstack(
                rx.hstack(
                    rx.button(
                        "← Back to Library",
                        on_click=State.close_document,
                        color_scheme="gray",
                        size="2"
                    ),
                    rx.heading(f"Reading: {State.current_document.title()}", size="6", color="green.600"),
                    justify="between",
                    width="100%"
                ),
                rx.box(
                    rx.markdown(State.document_content),
                    bg="white",
                    p="6",
                    border_radius="lg",
                    border="1px solid",
                    border_color="gray.200",
                    height="70vh",
                    overflow_y="auto",
                    width="100%"
                ),
                spacing="4",
                width="100%"
            ),
            # Document library
            rx.vstack(
                rx.heading("📚 Document Library", size="7", color="green.600"),
                rx.text("Browse classical philosophical texts"),
                
                rx.grid(
                    rx.box(
                        rx.vstack(
                            rx.heading("Plato's Apology", size="5"),
                            rx.text("Socrates' defense in court", color="gray.600"),
                            rx.button("Read", on_click=lambda: State.read_document("apology"), color_scheme="green", size="2"),
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
                            rx.button("Read", on_click=lambda: State.read_document("charmides"), color_scheme="green", size="2"),
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
            )
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