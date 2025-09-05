# Arete Reflex UI

A modern web interface for the Arete Graph-RAG AI philosophy tutoring system, built with [Reflex](https://reflex.dev/).

## Features

- **Interactive Chat Interface**: Conversational AI tutoring with real-time responses
- **Document Viewer**: Browse and search classical philosophical texts
- **Analytics Dashboard**: Visualize knowledge graph insights and usage statistics
- **Responsive Design**: Mobile-friendly interface with DaisyUI components
- **RAG Integration**: Seamless integration with existing Arete RAG pipeline
- **Multi-Provider Support**: Compatible with OpenAI, Claude, Gemini, and local models

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Existing Arete project setup with Neo4j and Weaviate

### Installation

1. **Install Reflex**:
```bash
pip install reflex
```

2. **Install Frontend Dependencies**:
```bash
cd src/arete/ui/reflex_app
npm install
```

3. **Configure Environment**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Initialize Reflex App**:
```bash
reflex init
```

### Development

1. **Start the Development Server**:
```bash
reflex run
```

2. **Access the Application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

## Project Structure

```
reflex_app/
├── reflex_app.py          # Main application module
├── rxconfig.py            # Reflex configuration
├── package.json           # Frontend dependencies
├── tailwind.config.js     # Tailwind CSS configuration
├── pages/                 # Page components
│   ├── index.py           # Home page
│   ├── chat.py            # Chat interface
│   ├── documents.py       # Document viewer
│   └── analytics.py       # Analytics dashboard
├── components/            # Reusable UI components
│   ├── layout.py          # Base layout and navigation
│   ├── hero.py            # Hero section
│   ├── features.py        # Features showcase
│   ├── chat.py            # Chat components
│   ├── document_viewer.py # Document viewing components
│   └── analytics.py       # Analytics components
├── services/              # Backend integration services
│   ├── rag_service.py     # RAG pipeline integration
│   ├── chat_service.py    # Chat message handling
│   ├── document_service.py # Document management
│   └── analytics_service.py # Analytics data
└── assets/                # Static assets
    └── styles/
        └── global.css     # Custom CSS styles
```

## Configuration

### Reflex Configuration (`rxconfig.py`)

- **App Settings**: Port configuration, module paths
- **Frontend Packages**: DaisyUI, Tailwind CSS plugins
- **Tailwind Theme**: Custom Arete color scheme
- **Database**: SQLite for session storage
- **CORS**: Development server origins

### Tailwind Configuration (`tailwind.config.js`)

- **DaisyUI Integration**: Multiple theme support
- **Custom Colors**: Arete brand colors
- **Typography**: Inter font family
- **Responsive Design**: Mobile-first approach
- **Accessibility**: WCAG-compliant styling

### Environment Variables (`.env`)

```env
# Core Application
REFLEX_ENV=development
REFLEX_PORT=3000
REFLEX_BACKEND_PORT=8000

# Database Integration (from main Arete project)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
WEAVIATE_URL=http://localhost:8080

# LLM Providers
KG_LLM_PROVIDER=openai
OPENAI_API_KEY=your_key
EMBEDDING_PROVIDER=openai

# Security
SECRET_KEY=your_secret_key
```

## Integration with Arete RAG System

The Reflex UI integrates seamlessly with the existing Arete RAG pipeline:

### RAG Service Integration

```python
from services.rag_service import get_rag_service

# Process queries through RAG pipeline
rag_service = get_rag_service()
result = await rag_service.process_query("What is virtue?")
```

### Services Architecture

- **RAGService**: Vector search, entity retrieval, LLM generation
- **ChatService**: Conversation management, context handling
- **DocumentService**: Text corpus access, search functionality
- **AnalyticsService**: Knowledge graph metrics, visualizations

## Development Workflow

### Adding New Pages

1. Create page component in `pages/`
2. Add route in `reflex_app.py`
3. Update navigation in `components/layout.py`

### Adding New Components

1. Create component in `components/`
2. Export from `components/__init__.py`
3. Import and use in pages

### Styling Guidelines

- Use DaisyUI component classes for consistency
- Custom styles in `assets/styles/global.css`
- Follow Tailwind utility-first approach
- Maintain accessibility standards

## Deployment

### Production Build

```bash
reflex export
```

### Environment Variables

Ensure production environment variables are configured:
- Database connections
- API keys
- CORS origins
- Security settings

### Docker Deployment (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install reflex
RUN reflex init
RUN reflex export

EXPOSE 3000 8000

CMD ["reflex", "run", "--env", "prod"]
```

## Contributing

1. Follow existing code patterns
2. Add tests for new functionality
3. Update documentation
4. Ensure accessibility compliance

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure Python path includes Arete project root
2. **Database Connection**: Verify Neo4j and Weaviate are running
3. **Missing Dependencies**: Run `npm install` and `pip install reflex`
4. **Port Conflicts**: Check REFLEX_PORT and REFLEX_BACKEND_PORT

### Development Tips

- Use `reflex run --debug` for detailed error messages
- Check browser console for frontend errors
- Monitor backend logs for RAG integration issues
- Test with different screen sizes and themes

## License

This project is part of the Arete Graph-RAG system and follows the same license terms.