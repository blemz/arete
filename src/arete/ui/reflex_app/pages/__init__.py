"""
Page components for the Arete Reflex application.
"""

from .analytics import analytics_page
from .chat import chat_page
from .documents import document_page
from .index import index_page

__all__ = [
    "index_page",
    "chat_page",
    "document_page",
    "analytics_page"
]
