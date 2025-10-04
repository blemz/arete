# Arete UI Redesign Plan: Classical Aesthetic + Knowledge Chat Template

## Overview
Transform the current Reflex UI to match the classical philosophical aesthetic shown in the color palette (warm beiges, deep blues, golds) and adopt the knowledge-chat template architecture pattern.

## Classical Color Palette (Extracted from Arete Colors.png)

### Primary Colors
- **Deep Navy Blue**: `#2C3E50` - Primary philosophical color (from figure's robe)
- **Warm Gold/Mustard**: `#D4A574` - Secondary accent (from toga drape)
- **Golden Accent**: `#C9A961` - Highlights and borders

### Background Colors
- **Cream/Parchment**: `#E8DCC8` - Base background (main parchment)
- **Light Beige**: `#F5F0E8` - Lighter background variant
- **Warm White**: `#FAF8F5` - Brightest background

### Text Colors
- **Dark Brown**: `#3D3028` - Primary text (from ARETE title)
- **Soft Gray**: `#9B8B7E` - Secondary text (from subtitle)
- **Medium Gray**: `#6B625A` - Tertiary text

### Accent Colors
- **Success/Info**: `#7B9E87` - Muted sage green (classical)
- **Warning**: `#C9A961` - Golden (reuse)
- **Error**: `#A85B52` - Muted terracotta

## Phase 1: Classical Color Theme Implementation

### 1.1 Extract Colors from Palette ✅
- Identified 11 classical colors from the image
- Categorized by usage (primary, background, text, accent)
- Ensured WCAG AA contrast compliance

### 1.2 Update Tailwind Configuration
**File**: `src/arete/ui/reflex_app/tailwind.config.js`
- Replace current blue/purple theme with classical palette
- Create "classical" DaisyUI theme matching the image
- Add custom color variables for philosophical UI elements
- Update typography to match classical aesthetic (serif for content)

**Changes Required**:
```javascript
colors: {
  arete: {
    // Classical palette
    primary: '#2C3E50',           // Deep navy blue
    'primary-focus': '#1a252f',   // Darker navy
    'primary-content': '#FAF8F5', // Warm white text
    secondary: '#D4A574',         // Warm gold
    'secondary-focus': '#C9A961',  // Golden accent
    'secondary-content': '#3D3028', // Dark brown text
    accent: '#C9A961',            // Golden highlight
    'accent-focus': '#B89751',    // Darker gold
    'accent-content': '#3D3028',  // Dark brown text
    neutral: '#6B625A',           // Medium gray
    'neutral-focus': '#3D3028',   // Dark brown
    'neutral-content': '#FAF8F5', // Warm white
    'base-100': '#FAF8F5',        // Warm white (brightest)
    'base-200': '#F5F0E8',        // Light beige
    'base-300': '#E8DCC8',        // Cream parchment
    'base-content': '#3D3028',    // Dark brown text
    info: '#7B9E87',              // Sage green
    success: '#7B9E87',           // Sage green
    warning: '#C9A961',           // Golden
    error: '#A85B52'              // Terracotta
  }
}
```

### 1.3 Update Global CSS
**File**: `src/arete/ui/reflex_app/assets/styles/global.css`
- Add classical background textures/patterns (subtle parchment effect)
- Update citation styles with classical borders (Greek key pattern optional)
- Enhance philosophical text with classical typography
- Add warm color transitions and shadows

**Changes Required**:
- Parchment texture background
- Classical border treatments
- Warm shadow effects
- Greek text styling enhancements

## Phase 2: Knowledge Chat Template Architecture

### 2.1 Chat Interface Modernization
**File**: `src/arete/ui/reflex_app/components/chat.py`

**Template Features to Implement**:
- ✅ Sidebar conversation history (left panel)
- ✅ Context-aware search with document preview
- ✅ Collapsible source citations panel (right panel)
- ✅ Smart document summaries in chat responses
- ✅ Conversation branching/threading

**Current Implementation Status**:
- Basic chat interface with message bubbles
- Loading indicators
- Clear chat functionality
- Missing: Conversation history, citations panel, search

### 2.2 Enhanced State Management
**File**: `src/arete/ui/reflex_app/state/chat_state.py`

**New State Variables Needed**:
```python
# Conversation history
conversations: list[dict] = []
active_conversation_id: str = ""

# Source tracking
message_sources: dict[str, list[dict]] = {}
selected_citation_id: str = ""

# Search context
search_query: str = ""
search_results: list[dict] = []
```

### 2.3 Document Integration
**Files**:
- `src/arete/ui/reflex_app/components/document_viewer.py`
- `src/arete/ui/reflex_app/pages/documents.py`

**Features**:
- Unified knowledge search across texts
- Inline document preview in chat interface
- Citation click-through to full document view
- Document context awareness in responses

## Phase 3: Layout & Component Updates

### 3.1 Hero Section Redesign
**File**: `src/arete/ui/reflex_app/components/hero.py`

**Changes**:
- Replace emoji with classical Greek column icon/illustration
- Update typography to classical serif headings
- Add subtle parchment background gradient
- Implement classical border treatments

### 3.2 Navigation Enhancement
**File**: `src/arete/ui/reflex_app/components/layout.py`

**Changes**:
- Add classical styling to navbar (subtle borders, warm colors)
- Implement theme toggle (light classical / dark classical)
- Add breadcrumb navigation for context
- Classical icon set for navigation items

### 3.3 New Components to Create

#### A. Conversation History Sidebar
**File**: `src/arete/ui/reflex_app/components/conversation_sidebar.py`
- List of past conversations with timestamps
- Quick search through conversation history
- New conversation button
- Delete/archive conversations

#### B. Source Citation Panel
**File**: `src/arete/ui/reflex_app/components/citation_panel.py`
- Display sources for current message
- Click to expand full citation
- Link to full document view
- Show relevance scores

#### C. Document Preview Card
**File**: `src/arete/ui/reflex_app/components/document_preview.py`
- Compact document summary
- Key passages highlighted
- Metadata (author, date, dialogue)
- Quick actions (read, bookmark)

#### D. Smart Summary Display
**File**: `src/arete/ui/reflex_app/components/summary_display.py`
- AI-generated summaries
- Key concepts extracted
- Related passages
- Argument structure visualization

## Phase 4: Typography & Font Updates

### 4.1 Classical Font Stack

**Fonts to Add**:
```css
/* Headings - Classical Inscriptional */
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&display=swap');

/* Body - Classical Book Serif */
@import url('https://fonts.googleapis.com/css2?family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');
@import url('https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400&display=swap');

/* UI Elements - Modern Sans (keep Inter) */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Greek Text - Specialized */
@import url('https://fonts.googleapis.com/css2?family=GFS+Didot&display=swap');
```

**Font Usage**:
- **Headings**: Cinzel (classical inscriptional)
- **Philosophical Text**: EB Garamond (classical book serif)
- **UI Elements**: Inter (maintain legibility)
- **Greek Terms**: GFS Didot + italic styling

### 4.2 Typography Scale
- Increase base font size to 16px (improve readability)
- Line-height: 1.8 for philosophical text
- Letter-spacing: slight increase for classical feel
- Drop caps for major sections (optional enhancement)

## Phase 5: Enhanced Features from Template

### 5.1 Unified Search
- Implement cross-document semantic search
- Add search filters (author, dialogue, concept)
- Display search results with context snippets
- Integrate with existing Weaviate vector search

### 5.2 Smart Summaries
- Generate dialogue summaries on demand
- Create concept relationship visualizations
- Add "key arguments" extraction per dialogue

### 5.3 Collaborative Features (Future)
- Add annotation/highlighting capability
- Implement note-taking with citation linking
- Create shareable conversation permalinks

## Implementation Order (Following TDD)

### Sprint 1: Classical Theme (Phases 1 & 4)
1. Extract color palette from image ✅
2. Update tailwind.config.js with classical colors
3. Update global.css with classical styling
4. Add classical font imports
5. Test: Visual regression and accessibility

**Estimated**: 3-4 hours

### Sprint 2: Chat Architecture (Phase 2)
1. Create conversation sidebar component
2. Implement conversation history state
3. Add citation panel component
4. Update chat state for source tracking
5. Test: State management and UI rendering

**Estimated**: 5-6 hours

### Sprint 3: Layout & Components (Phase 3)
1. Redesign hero section with classical aesthetic
2. Update navigation with classical styling
3. Create document preview component
4. Create smart summary component
5. Test: Responsive behavior and integration

**Estimated**: 4-5 hours

### Sprint 4: Advanced Features (Phase 5)
1. Implement unified search
2. Add smart summaries
3. Integrate with RAG pipeline
4. Test: Search accuracy and performance

**Estimated**: 4-5 hours

## Success Criteria

- ✅ Classical color palette fully applied matching the image
- ✅ Knowledge chat template architecture implemented
- ✅ Conversation history with context tracking
- ✅ Source citation panel with document preview
- ✅ Classical typography enhancing philosophical content
- ✅ WCAG AA accessibility maintained (4.5:1 contrast ratio)
- ✅ All existing RAG functionality preserved
- ✅ >80% test coverage for new components
- ✅ Responsive design (mobile, tablet, desktop)
- ✅ Performance: <3s initial load, <500ms interactions

## Estimated Total Effort

- Sprint 1 (Theme): 3-4 hours
- Sprint 2 (Chat): 5-6 hours
- Sprint 3 (Layout): 4-5 hours
- Sprint 4 (Features): 4-5 hours

**Total**: 16-20 hours of development

## Technical Notes

### Accessibility Considerations
- Maintain WCAG AA contrast ratios (4.5:1 for text)
- Test with screen readers
- Keyboard navigation support
- Reduced motion support
- High contrast mode support

### Performance Considerations
- Lazy load conversation history
- Virtual scrolling for long chat histories
- Optimize font loading (subset fonts)
- Cache document previews
- Debounce search queries

### Browser Compatibility
- Chrome/Edge (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Mobile browsers (iOS Safari, Chrome Mobile)

### Testing Strategy
- Unit tests for new components
- Integration tests for state management
- E2E tests for user flows
- Visual regression tests for theme
- Accessibility testing (axe-core)
- Performance testing (Lighthouse)

## References

- **Design Inspiration**: Arete Colors.png (classical palette)
- **Template Reference**: https://reflex.dev/templates/knowledge-chat/
- **Current Implementation**: src/arete/ui/reflex_app/
- **Project Context**: CLAUDE.md (Phase 8.0 - Reflex UI Complete)

---

**Created**: 2025-10-04
**Status**: Planning Complete - Ready for Implementation
**Next Step**: Begin Sprint 1 - Classical Theme Implementation
