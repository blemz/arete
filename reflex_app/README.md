# Arete Graph Analytics Dashboard - Reflex Implementation

This is a Reflex-based web application that provides an interactive analytics dashboard for the Arete classical philosophy AI tutoring system. It integrates with the existing GraphAnalyticsService and provides advanced visualizations for philosophical knowledge graphs.

## Features

### Analytics Dashboard Core
- **Centrality Analysis**: Interactive visualization of degree, betweenness, closeness, eigenvector, and PageRank centrality metrics
- **Community Detection**: Community visualization with modularity scoring and cluster analysis  
- **Influence Networks**: Temporal tracking of philosophical influence relationships
- **Topic Clustering**: Jaccard similarity-based concept grouping with heatmap visualization
- **Historical Timeline**: BCE/CE timeline construction with period analysis

### Interactive Visualizations
- **Network Graphs**: Plotly-powered knowledge graph visualization with interactive node exploration
- **Centrality Charts**: Bar charts and scatter plots showing centrality distributions
- **Community Diagrams**: Network diagrams with community highlighting and metrics
- **Timeline Visualizations**: Historical development tracking with period markers
- **Topic Heatmaps**: Similarity matrices for philosophical concept relationships

### Advanced Controls
- **Dynamic Filtering**: Filter by time periods, philosophers, and concepts
- **Algorithm Selection**: Choose from multiple centrality and layout algorithms
- **Visualization Settings**: Customizable node sizes, colors, and layouts
- **Real-time Updates**: Live updates based on user interactions
- **Export Functionality**: Export charts and data in multiple formats

### Chat Integration
- **RAG-Powered Chat**: Integration with existing chat_rag_clean.py system
- **Contextual Analytics**: Link chat conversations to graph visualizations
- **Citation Highlighting**: Connect graph nodes to document sources
- **Interactive Responses**: Enhanced responses with visual context

## Installation

1. **Install Reflex and Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Initialize Reflex Project**:
```bash
reflex init
```

3. **Set Up Environment**: 
   - Copy `.env` file from parent Arete directory
   - Ensure Neo4j, Weaviate, and LLM services are configured

## Usage

### Running the Dashboard

```bash
# Start the Reflex development server
reflex run

# Or run in production mode
reflex run --env prod
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

### Navigation

- **Home** (`/`): Landing page with navigation options
- **Analytics Dashboard** (`/analytics`): Full analytics interface with interactive visualizations
- **Chat Interface** (`/chat`): AI-powered philosophical discussions with RAG integration

### Key Components

#### AnalyticsDashboardState
Central state management for all analytics functionality:
- Data loading and caching
- Filter state management  
- Service initialization
- Real-time updates

#### NetworkVisualization
Custom Plotly.js integration for interactive network graphs:
- Dynamic layout algorithms (spring, circular, Kamada-Kawai)
- Configurable node sizing and coloring
- Interactive click handling
- Responsive design

#### Advanced Filter Panel
Comprehensive filtering and control system:
- Philosopher selection with search
- Time period filtering (classical, hellenistic, etc.)
- Visualization parameter controls
- Performance monitoring

## Integration with Existing Arete System

### Service Integration
The dashboard directly integrates with existing Arete services:
- `GraphAnalyticsService`: Core analytics calculations
- `HistoricalDevelopmentService`: Timeline and period analysis
- `Neo4jClient`: Direct database connectivity
- `chat_rag_clean`: RAG pipeline integration

### Data Flow
1. **Initialization**: Services connect to Neo4j and Weaviate
2. **Data Loading**: Analytics services compute centrality and community metrics
3. **Visualization**: Plotly renders interactive network graphs
4. **User Interaction**: Filter changes trigger real-time updates
5. **Export**: Charts and data can be exported in multiple formats

### Performance Optimization
- **Lazy Loading**: Large network visualizations load progressively
- **Caching**: Expensive graph calculations are cached
- **Batch Processing**: Multiple analytics operations run concurrently
- **Responsive Rendering**: Charts adapt to different screen sizes

## Architecture

### State Management
```
AnalyticsDashboardState
├── centrality_data: Dict[str, Any]
├── community_data: Dict[str, Any]  
├── influence_data: Dict[str, Any]
├── topic_clusters: List[Dict[str, Any]]
├── historical_timeline: List[Dict[str, Any]]
└── UI filters and settings
```

### Component Hierarchy
```
analytics_dashboard()
├── filter_panel()
├── network_graph()
├── centrality_metrics_table()
├── community_summary_card()
├── influence_timeline()
├── topic_cluster_heatmap()
└── export_controls()
```

### Custom JavaScript Integration
Advanced Plotly.js integration enables:
- Real-time chart updates
- Interactive node selection
- Custom visualization layouts
- Export functionality

## Development

### Adding New Analytics
1. Extend `AnalyticsDashboardState` with new data fields
2. Create corresponding visualization components
3. Add loading and update methods
4. Integrate with filter panel

### Custom Visualizations
1. Create new component in `analytics_components.py`
2. Add JavaScript integration for Plotly
3. Connect to state management system
4. Add to main dashboard layout

### Testing
The dashboard includes comprehensive error handling and fallback systems:
- Service initialization failures are gracefully handled
- Missing data shows appropriate placeholders
- Loading states provide user feedback
- Export functions validate data before processing

## Performance Considerations

### Large Datasets
- Progressive loading for networks with >1000 nodes
- Sampling strategies for complex visualizations
- Client-side caching of computed layouts
- Optimized rendering pipelines

### Real-time Updates
- Debounced filter updates prevent excessive re-rendering
- Incremental data updates rather than full reloads
- Efficient state management with minimal re-renders
- Background data loading with user feedback

## Future Enhancements

### Planned Features
- **3D Network Visualization**: Three-dimensional knowledge graphs
- **Collaborative Analysis**: Multi-user analytics sessions
- **Advanced Export Options**: PDF reports, interactive HTML exports
- **Machine Learning Integration**: Predictive analytics and trend detection
- **Mobile Optimization**: Touch-friendly interface for tablets and phones

### Integration Opportunities
- **Jupyter Notebook Export**: Generate analytical notebooks
- **API Integration**: RESTful API for external analytics tools
- **Plugin System**: Extensible architecture for custom analytics
- **Data Pipeline**: Automated analytics updates as corpus grows

## Dependencies

### Core Dependencies
- `reflex>=0.6.0`: Modern web framework
- `plotly>=5.17.0`: Interactive visualizations
- `pandas>=2.0.0`: Data manipulation
- `numpy>=1.24.0`: Numerical computing

### Arete Integration
- Existing GraphAnalyticsService components
- Neo4j and Weaviate database connectivity
- Multi-provider LLM integration
- RAG pipeline components

## License

Part of the Arete Classical Philosophy AI Tutoring System. See main project license for details.