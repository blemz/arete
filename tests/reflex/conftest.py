"""Pytest configuration for Reflex component testing."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
import reflex as rx
from typing import Any, Dict, List, Optional
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from arete.state import NavigationState, ChatState, DocumentState


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_navigation_state():
    """Mock NavigationState for testing."""
    state = NavigationState()
    state.current_route = "/"
    state.is_mobile_menu_open = False
    state.is_sidebar_collapsed = False
    state.theme_mode = "light"
    state.layout_mode = "split"
    return state


@pytest.fixture
def mock_chat_state():
    """Mock ChatState for testing."""
    state = ChatState()
    state.messages = []
    state.current_message = ""
    state.is_loading = False
    return state


@pytest.fixture
def mock_document_state():
    """Mock DocumentState for testing."""
    state = DocumentState()
    state.current_document = None
    state.document_content = ""
    state.highlighted_passages = []
    state.search_query = ""
    state.search_results = []
    return state


@pytest.fixture
def mock_rag_service():
    """Mock RAG service for testing."""
    mock = AsyncMock()
    mock.query.return_value = {
        "response": "This is a test philosophical response about virtue.",
        "citations": [
            {
                "source": "Plato's Republic",
                "content": "Test citation content",
                "relevance_score": 0.85,
                "position": 42.0
            }
        ],
        "entities": ["virtue", "Plato", "justice"],
        "processing_time": 1.23
    }
    return mock


@pytest.fixture
def sample_conversation():
    """Sample conversation data for testing."""
    return [
        {
            "role": "user",
            "content": "What is virtue according to Plato?",
            "timestamp": "2025-09-05T10:00:00Z"
        },
        {
            "role": "assistant",
            "content": "According to Plato, virtue is knowledge...",
            "timestamp": "2025-09-05T10:00:05Z",
            "citations": [
                {
                    "source": "Republic",
                    "content": "Virtue is knowledge passage",
                    "position": 123.0
                }
            ]
        }
    ]


@pytest.fixture
def sample_documents():
    """Sample document data for testing."""
    return [
        {
            "id": "doc1",
            "title": "Plato's Republic",
            "type": "dialogue",
            "content": "Sample content from Republic...",
            "word_count": 120000
        },
        {
            "id": "doc2", 
            "title": "Nicomachean Ethics",
            "type": "treatise",
            "content": "Sample content from Ethics...",
            "word_count": 95000
        }
    ]


class MockReflex:
    """Mock Reflex components for testing without full rendering."""
    
    @staticmethod
    def component(*args, **kwargs) -> Mock:
        """Create a mock Reflex component."""
        mock = Mock()
        mock.args = args
        mock.kwargs = kwargs
        mock.children = kwargs.get('children', [])
        mock.props = kwargs
        return mock
    
    @staticmethod
    def box(*args, **kwargs) -> Mock:
        """Mock rx.box component."""
        return MockReflex.component('box', *args, **kwargs)
    
    @staticmethod
    def text(*args, **kwargs) -> Mock:
        """Mock rx.text component."""
        return MockReflex.component('text', *args, **kwargs)
    
    @staticmethod
    def button(*args, **kwargs) -> Mock:
        """Mock rx.button component."""
        return MockReflex.component('button', *args, **kwargs)
    
    @staticmethod
    def input(*args, **kwargs) -> Mock:
        """Mock rx.input component."""
        return MockReflex.component('input', *args, **kwargs)


@pytest.fixture
def mock_reflex():
    """Provide mock Reflex components."""
    return MockReflex()


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables."""
    os.environ.setdefault('TESTING', 'true')
    os.environ.setdefault('REFLEX_ENV', 'test')
    yield
    # Cleanup
    if 'TESTING' in os.environ:
        del os.environ['TESTING']
    if 'REFLEX_ENV' in os.environ:
        del os.environ['REFLEX_ENV']


class ComponentTestHelper:
    """Helper class for testing Reflex components."""
    
    @staticmethod
    def extract_props(component: Any) -> Dict[str, Any]:
        """Extract props from a component for testing."""
        if hasattr(component, 'props'):
            return component.props
        if hasattr(component, 'kwargs'):
            return component.kwargs
        return {}
    
    @staticmethod
    def find_child_by_type(component: Any, child_type: str) -> Optional[Any]:
        """Find child component by type."""
        if hasattr(component, 'children'):
            for child in component.children:
                if hasattr(child, 'tag') and child.tag == child_type:
                    return child
                # Recursive search
                found = ComponentTestHelper.find_child_by_type(child, child_type)
                if found:
                    return found
        return None
    
    @staticmethod
    def count_children(component: Any) -> int:
        """Count child components."""
        if hasattr(component, 'children'):
            return len(component.children)
        return 0


@pytest.fixture
def component_helper():
    """Provide component testing helper."""
    return ComponentTestHelper()


# Performance testing fixtures
@pytest.fixture
def performance_thresholds():
    """Performance testing thresholds."""
    return {
        'component_render_time': 0.1,  # 100ms max
        'state_update_time': 0.05,     # 50ms max
        'page_load_time': 2.0,         # 2s max
        'api_response_time': 5.0,      # 5s max
        'memory_usage_mb': 100,        # 100MB max
    }


@pytest.fixture
def accessibility_rules():
    """Accessibility testing rules."""
    return {
        'color_contrast_ratio': 4.5,  # WCAG AA standard
        'font_size_minimum': 16,      # 16px minimum
        'focus_indicator_required': True,
        'alt_text_required': True,
        'keyboard_navigation': True,
    }