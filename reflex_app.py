import reflex as rx
from pages.chat import chat_page, chat_settings_page

class State(rx.State):
    """The app state."""
    pass

def index() -> rx.Component:
    """Landing page with navigation to chat interface"""
    return rx.container(
        rx.color_mode.button(position="top-right"),
        rx.vstack(
            rx.heading("Arete - Classical Philosophy Tutor", size="9", color="blue.500"),
            rx.text(
                "Your AI-powered guide to classical philosophical texts",
                size="5",
                color="gray.600",
                text_align="center"
            ),
            rx.vstack(
                rx.text(
                    "Arete combines advanced RAG (Retrieval-Augmented Generation) with knowledge graphs to provide accurate, well-cited responses from classical philosophical texts.",
                    size="4",
                    color="gray.700",
                    text_align="center",
                    max_width="600px"
                ),
                rx.text(
                    "Currently featuring works by Plato including the Apology and Charmides, with comprehensive citation tracking and entity relationship mapping.",
                    size="3",
                    color="gray.600",
                    text_align="center",
                    max_width="500px"
                ),
                spacing="3",
                align="center"
            ),
            
            # Feature highlights
            rx.hstack(
                rx.vstack(
                    rx.icon("search", size="2rem", color="blue.500"),
                    rx.text("Semantic Search", font_weight="bold"),
                    rx.text("Advanced vector similarity search across classical texts", size="2", text_align="center"),
                    align="center",
                    spacing="2",
                    max_width="200px"
                ),
                rx.vstack(
                    rx.icon("brain", size="2rem", color="green.500"),
                    rx.text("Knowledge Graph", font_weight="bold"),
                    rx.text("Entity relationships and concept mapping from Neo4j", size="2", text_align="center"),
                    align="center",
                    spacing="2",
                    max_width="200px"
                ),
                rx.vstack(
                    rx.icon("quote", size="2rem", color="purple.500"),
                    rx.text("Accurate Citations", font_weight="bold"),
                    rx.text("Precise source attribution with relevance scoring", size="2", text_align="center"),
                    align="center",
                    spacing="2",
                    max_width="200px"
                ),
                spacing="8",
                justify="center",
                wrap="wrap"
            ),
            
            # Action buttons
            rx.vstack(
                rx.link(
                    rx.button(
                        rx.icon("message-circle", margin_right="0.5rem"),
                        "Start Philosophical Discussion",
                        size="lg",
                        color_scheme="blue"
                    ),
                    href="/chat"
                ),
                rx.hstack(
                    rx.text("Or try a quick question:", size="3", color="gray.600"),
                    rx.link(
                        rx.button("What is virtue?", variant="outline", size="sm"),
                        href="/chat?q=What is virtue?"
                    ),
                    rx.link(
                        rx.button("Tell me about Socrates", variant="outline", size="sm"),
                        href="/chat?q=Tell me about Socrates"
                    ),
                    spacing="3",
                    align="center",
                    wrap="wrap"
                ),
                spacing="4",
                align="center"
            ),
            
            # System status
            rx.box(
                rx.vstack(
                    rx.text("System Status", font_weight="bold", size="3"),
                    rx.hstack(
                        rx.badge("RAG Pipeline", color_scheme="green", variant="solid"),
                        rx.badge("227 Chunks", color_scheme="blue", variant="outline"),
                        rx.badge("83 Entities", color_scheme="purple", variant="outline"),
                        rx.badge("GPT-5-mini", color_scheme="orange", variant="outline"),
                        spacing="2",
                        wrap="wrap",
                        justify="center"
                    ),
                    rx.text(
                        "Production RAG system operational with OpenAI GPT-5-mini reasoning model",
                        size="2",
                        color="gray.600",
                        text_align="center"
                    ),
                    spacing="2",
                    align="center"
                ),
                bg="gray.50",
                p="4",
                border_radius="md",
                border="1px solid gray.200"
            ),
            
            spacing="8",
            justify="center",
            align="center",
            min_height="85vh",
            py="8"
        ),
        max_width="1200px",
        px="4"
    )

# Create the app
app = rx.App(
    theme=rx.theme(
        appearance="dark",
        has_background=True,
        radius="medium",
        scaling="100%"
    )
)

# Add pages
app.add_page(index, route="/")
app.add_page(chat_page, route="/chat")
app.add_page(chat_settings_page, route="/chat/settings")

# Add global styles for chat interface
app.add_custom_head_code("""
<style>
    /* Global chat interface styles */
    .chat-container {
        height: 100vh;
        overflow: hidden;
    }
    
    .messages-container {
        flex: 1;
        overflow-y: auto;
        scroll-behavior: smooth;
    }
    
    .message-bubble {
        animation: slideIn 0.3s ease-out;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .citation-preview {
        transition: all 0.2s ease;
    }
    
    .citation-preview:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* Typing indicator animation */
    @keyframes typing {
        0%, 60%, 100% {
            transform: translateY(0);
        }
        30% {
            transform: translateY(-10px);
        }
    }
    
    .typing-dot {
        animation: typing 1.4s infinite;
        animation-delay: 0s;
    }
    
    .typing-dot:nth-child(2) {
        animation-delay: 0.2s;
    }
    
    .typing-dot:nth-child(3) {
        animation-delay: 0.4s;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .message-bubble {
            max-width: 95%;
        }
        
        .chat-header {
            flex-direction: column;
            gap: 0.5rem;
        }
        
        .chat-controls {
            justify-content: center;
        }
    }
    
    /* Accessibility enhancements */
    .message-bubble:focus-within {
        outline: 2px solid #3b82f6;
        outline-offset: 2px;
    }
    
    .citation-preview:focus {
        outline: 2px solid #8b5cf6;
        outline-offset: 2px;
    }
    
    /* Dark theme optimizations */
    @media (prefers-color-scheme: dark) {
        .message-bubble {
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .citation-preview {
            border: 1px solid rgba(255,255,255,0.1);
        }
    }
</style>
""")