# Arete Reflex Components

Enhanced layout and navigation components for the Arete Reflex application, featuring responsive design, accessibility support, and multiple view modes.

## Component Structure

### Navigation (`arete/components/navigation.py`)
- **Responsive navigation bar** with mobile hamburger menu
- **Active route highlighting** for current page indication  
- **User profile dropdown** with avatar and settings options
- **Theme toggle** for light/dark mode switching
- **Layout mode selector** for split/chat/document views
- Mobile-optimized collapsible menu

### Sidebar (`arete/components/sidebar.py`)  
- **Collapsible sidebar** with icon-only collapsed state
- **Recent conversations** with truncated titles and dates
- **Recent documents** with type indicators (dialogue/treatise)
- **Quick actions** for new chat, search, bookmarks
- **Philosophical tools** for analysis and exploration
- Smooth width transitions and mobile responsiveness

### Footer (`arete/components/footer.py`)
- **Comprehensive project information** and status
- **Academic attribution** and methodology explanation
- **Multi-column link sections** (navigation, resources, community)
- **Social links** with GitHub, Twitter, email, RSS
- **Technology badges** showing RAG pipeline components
- Legal and privacy policy links

### Layout (`arete/components/layout.py`)
- **Multiple layout modes**:
  - Split-view (chat + document side by side)
  - Chat-only mode for focused conversations  
  - Document-only mode for reading
  - Mobile-optimized responsive layout
- **Base layout wrapper** with navigation, sidebar, footer
- **Mobile bottom navigation** for touch interfaces
- **Content area management** with proper spacing

### Accessibility (`arete/components/accessibility.py`)
- **Keyboard navigation support** with Alt+key shortcuts:
  - Alt+H: Home, Alt+C: Chat, Alt+L: Library, Alt+A: Analytics
  - Alt+T: Theme toggle, Alt+S: Sidebar toggle
  - Escape: Close modals, Tab/Shift+Tab: Navigate
- **Screen reader support** with ARIA labels and live regions
- **Skip to content** links for keyboard users
- **High contrast** and **reduced motion** support
- **Keyboard shortcuts modal** for help

## State Management (`arete/state.py`)

### NavigationState
- Route tracking and mobile menu state
- Sidebar collapse and user dropdown management  
- Theme and layout mode switching
- Recent conversations and documents data

### ChatState  
- Message history with user/assistant roles
- Input handling and loading states
- Mock conversation simulation

### DocumentState
- Current document tracking and content
- Search functionality with highlighted results
- Passage highlighting and annotations

## Theming (`arete/styles.py`)
- **Classical philosophy-inspired** color palette
- **Typography scale** with Inter font family
- **Spacing and sizing** systems for consistency
- **Component-specific styles** for buttons, cards, inputs
- **Accessibility styles** with focus indicators
- **Dark theme overrides** for night mode

## Usage

### Basic Setup
```python
import reflex as rx
from arete.components import base_layout

def my_page():
    return base_layout(
        rx.box("Your page content here")
    )
```

### Layout Modes
```python 
# Split view (default)
NavigationState.set_layout_mode("split")

# Chat only
NavigationState.set_layout_mode("chat")  

# Document only
NavigationState.set_layout_mode("document")
```

### Theme Toggle
```python
# In any component
theme_toggle_button()

# Programmatic toggle
NavigationState.toggle_theme()
```

## Features

### ✅ Responsive Design
- Desktop, tablet, and mobile breakpoints
- Collapsible sidebar and mobile hamburger menu
- Touch-friendly bottom navigation on mobile
- Flexible grid layouts with proper wrapping

### ✅ Accessibility (WCAG 2.1 AA)
- Semantic HTML structure with proper ARIA landmarks
- Keyboard navigation with logical tab order
- Screen reader support with descriptive labels
- Focus indicators and high contrast mode
- Skip links and keyboard shortcuts

### ✅ Multiple View Modes
- **Split View**: Chat and document side by side
- **Chat Only**: Full-width conversation interface  
- **Document Only**: Focused reading experience
- **Mobile**: Optimized single-column layout

### ✅ Theme Support
- Light and dark themes with smooth transitions
- Classical philosophy color palette (accent oranges)
- Automatic theme detection based on system preferences
- CSS custom properties for easy customization

### ✅ Production Ready
- Type-safe with comprehensive TypeScript-style hints
- Performance optimized with minimal re-renders
- Error boundaries and loading states
- Comprehensive component testing support

## Integration with Existing Arete System

The Reflex components are designed to integrate seamlessly with the existing Arete RAG pipeline:

- **Chat Interface** connects to `ChatState` for RAG conversations
- **Document Viewer** integrates with document loading and citation display
- **Navigation** supports existing routes (/chat, /library, /analytics) 
- **Footer** displays current system status (227 chunks, 83 entities)
- **Theme** matches Arete branding and philosophical aesthetic

## Launch Instructions

1. **Install Reflex**: `pip install reflex`
2. **Initialize**: `reflex init` (if needed)
3. **Run**: `reflex run` or `python reflex_app.py`  
4. **Build**: `reflex export` for production deployment

## File Structure
```
arete/
├── components/
│   ├── __init__.py
│   ├── navigation.py      # Nav bar with mobile menu
│   ├── sidebar.py         # Collapsible sidebar  
│   ├── footer.py          # Comprehensive footer
│   ├── layout.py          # Layout modes and wrapper
│   └── accessibility.py   # Keyboard nav and a11y
├── pages/
│   ├── __init__.py
│   ├── home.py           # Landing page
│   └── chat.py           # Chat interface page
├── state.py              # Global state management
├── styles.py             # Theme and styling
└── arete.py             # Main app with routing
```

The enhanced Reflex components provide a production-ready, accessible, and responsive foundation for the Arete philosophical AI tutoring system.