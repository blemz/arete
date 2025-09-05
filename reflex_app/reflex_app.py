"""Arete Graph Analytics Dashboard - Reflex Implementation"""

import reflex as rx
from typing import List, Dict, Any, Optional
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import asyncio

# Import existing Arete services
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from arete.services.graph_analytics.graph_analytics_service import GraphAnalyticsService
from arete.services.graph_analytics.historical_development_service import HistoricalDevelopmentService
from arete.core.database.neo4j_client import Neo4jClient
from arete.core.config.settings import get_settings

# Import custom components and chat interface
from analytics_components import (
    network_graph, centrality_metrics_table, community_summary_card,
    influence_timeline, topic_cluster_heatmap, export_controls, filter_panel
)
from chat_interface import chat_interface, ChatInterfaceState


class AnalyticsDashboardState(rx.State):
    """State management for the analytics dashboard"""
    
    # Core data
    centrality_data: Dict[str, Any] = {}
    community_data: Dict[str, Any] = {}
    influence_data: Dict[str, Any] = {}
    topic_clusters: List[Dict[str, Any]] = []
    historical_timeline: List[Dict[str, Any]] = []
    
    # UI state
    selected_algorithm: str = "degree"
    selected_philosopher: str = "all"
    selected_time_period: str = "all"
    selected_layout: str = "spring"
    node_size_metric: str = "degree"
    color_scheme: str = "viridis"
    
    # Loading states
    is_loading_centrality: bool = False
    is_loading_communities: bool = False
    is_loading_influence: bool = False
    is_loading_topics: bool = False
    is_loading_timeline: bool = False
    
    # Filter options
    available_philosophers: List[str] = []
    available_algorithms: List[str] = ["degree", "betweenness", "closeness", "eigenvector", "pagerank"]
    available_layouts: List[str] = ["spring", "circular", "kamada_kawai", "random"]
    available_periods: List[str] = ["all", "classical", "hellenistic", "medieval", "renaissance", "modern"]
    
    # Services (initialized in constructor)
    graph_service: Optional[GraphAnalyticsService] = None
    historical_service: Optional[HistoricalDevelopmentService] = None
    
    def __init__(self):
        super().__init__()
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize analytics services"""
        try:
            settings = get_settings()
            neo4j_client = Neo4jClient(settings)
            self.graph_service = GraphAnalyticsService(neo4j_client)
            self.historical_service = HistoricalDevelopmentService(neo4j_client)
        except Exception as e:
            print(f"Error initializing services: {e}")
    
    async def load_centrality_analysis(self):
        """Load centrality analysis data"""
        if not self.graph_service:
            return
            
        self.is_loading_centrality = True
        try:
            # Get centrality metrics
            centrality_results = {}
            for algorithm in self.available_algorithms:
                if algorithm == "degree":
                    centrality_results[algorithm] = await self.graph_service.calculate_degree_centrality()
                elif algorithm == "betweenness":
                    centrality_results[algorithm] = await self.graph_service.calculate_betweenness_centrality()
                elif algorithm == "closeness":
                    centrality_results[algorithm] = await self.graph_service.calculate_closeness_centrality()
                elif algorithm == "eigenvector":
                    centrality_results[algorithm] = await self.graph_service.calculate_eigenvector_centrality()
                elif algorithm == "pagerank":
                    centrality_results[algorithm] = await self.graph_service.calculate_pagerank()
            
            self.centrality_data = centrality_results
            
            # Extract available philosophers
            all_nodes = set()
            for results in centrality_results.values():
                all_nodes.update(results.keys())
            self.available_philosophers = ["all"] + sorted(list(all_nodes))
            
        except Exception as e:
            print(f"Error loading centrality analysis: {e}")
        finally:
            self.is_loading_centrality = False
    
    async def load_community_detection(self):
        """Load community detection data"""
        if not self.graph_service:
            return
            
        self.is_loading_communities = True
        try:
            communities = await self.graph_service.detect_communities()
            modularity = await self.graph_service.calculate_modularity(communities)
            
            self.community_data = {
                "communities": communities,
                "modularity": modularity,
                "community_count": len(set(communities.values()))
            }
        except Exception as e:
            print(f"Error loading community detection: {e}")
        finally:
            self.is_loading_communities = False
    
    async def load_influence_networks(self):
        """Load influence network analysis"""
        if not self.graph_service:
            return
            
        self.is_loading_influence = True
        try:
            influence_data = await self.graph_service.analyze_influence_networks()
            self.influence_data = influence_data
        except Exception as e:
            print(f"Error loading influence networks: {e}")
        finally:
            self.is_loading_influence = False
    
    async def load_topic_clustering(self):
        """Load topic clustering analysis"""
        if not self.graph_service:
            return
            
        self.is_loading_topics = True
        try:
            clusters = await self.graph_service.cluster_topics()
            self.topic_clusters = clusters
        except Exception as e:
            print(f"Error loading topic clustering: {e}")
        finally:
            self.is_loading_topics = False
    
    async def load_historical_timeline(self):
        """Load historical development timeline"""
        if not self.historical_service:
            return
            
        self.is_loading_timeline = True
        try:
            timeline = await self.historical_service.build_timeline()
            periods = await self.historical_service.analyze_periods()
            
            self.historical_timeline = {
                "timeline": timeline,
                "periods": periods
            }
        except Exception as e:
            print(f"Error loading historical timeline: {e}")
        finally:
            self.is_loading_timeline = False
    
    async def load_all_data(self):
        """Load all analytics data"""
        await asyncio.gather(
            self.load_centrality_analysis(),
            self.load_community_detection(),
            self.load_influence_networks(),
            self.load_topic_clustering(),
            self.load_historical_timeline()
        )
    
    def set_algorithm(self, algorithm: str):
        """Set selected centrality algorithm"""
        self.selected_algorithm = algorithm
    
    def set_philosopher(self, philosopher: str):
        """Set selected philosopher filter"""
        self.selected_philosopher = philosopher
    
    def set_time_period(self, period: str):
        """Set selected time period filter"""
        self.selected_time_period = period
    
    def set_layout(self, layout: str):
        """Set network layout algorithm"""
        self.selected_layout = layout
    
    def set_node_size_metric(self, metric: str):
        """Set node size metric"""
        self.node_size_metric = metric
    
    def set_color_scheme(self, scheme: str):
        """Set visualization color scheme"""
        self.color_scheme = scheme


def create_centrality_chart() -> rx.Component:
    """Create centrality analysis chart"""
    return rx.box(
        rx.cond(
            AnalyticsDashboardState.is_loading_centrality,
            rx.spinner(size="lg"),
            rx.cond(
                AnalyticsDashboardState.centrality_data,
                rx.html(
                    id="centrality-chart",
                    # Plotly chart will be rendered here via JavaScript
                ),
                rx.text("No centrality data available", color="gray.500")
            )
        ),
        width="100%",
        height="400px",
        border="1px solid",
        border_color="gray.200",
        border_radius="md",
        padding="4"
    )


def create_community_chart() -> rx.Component:
    """Create community detection chart"""
    return rx.box(
        rx.cond(
            AnalyticsDashboardState.is_loading_communities,
            rx.spinner(size="lg"),
            rx.cond(
                AnalyticsDashboardState.community_data,
                rx.vstack(
                    rx.text(
                        f"Communities: {AnalyticsDashboardState.community_data.get('community_count', 0)}",
                        font_weight="bold"
                    ),
                    rx.text(
                        f"Modularity: {AnalyticsDashboardState.community_data.get('modularity', 0):.3f}",
                        color="blue.600"
                    ),
                    rx.html(
                        id="community-chart",
                        # Plotly chart will be rendered here
                    ),
                    spacing="2"
                ),
                rx.text("No community data available", color="gray.500")
            )
        ),
        width="100%",
        height="400px",
        border="1px solid",
        border_color="gray.200",
        border_radius="md",
        padding="4"
    )


def create_influence_chart() -> rx.Component:
    """Create influence network chart"""
    return rx.box(
        rx.cond(
            AnalyticsDashboardState.is_loading_influence,
            rx.spinner(size="lg"),
            rx.cond(
                AnalyticsDashboardState.influence_data,
                rx.html(
                    id="influence-chart",
                    # Plotly chart will be rendered here
                ),
                rx.text("No influence data available", color="gray.500")
            )
        ),
        width="100%",
        height="400px",
        border="1px solid",
        border_color="gray.200",
        border_radius="md",
        padding="4"
    )


def create_timeline_chart() -> rx.Component:
    """Create historical timeline chart"""
    return rx.box(
        rx.cond(
            AnalyticsDashboardState.is_loading_timeline,
            rx.spinner(size="lg"),
            rx.cond(
                AnalyticsDashboardState.historical_timeline,
                rx.html(
                    id="timeline-chart",
                    # Timeline visualization will be rendered here
                ),
                rx.text("No timeline data available", color="gray.500")
            )
        ),
        width="100%",
        height="300px",
        border="1px solid",
        border_color="gray.200",
        border_radius="md",
        padding="4"
    )


def create_topic_clusters_chart() -> rx.Component:
    """Create topic clustering chart"""
    return rx.box(
        rx.cond(
            AnalyticsDashboardState.is_loading_topics,
            rx.spinner(size="lg"),
            rx.cond(
                AnalyticsDashboardState.topic_clusters,
                rx.html(
                    id="topic-clusters-chart",
                    # Topic clusters visualization
                ),
                rx.text("No topic clustering data available", color="gray.500")
            )
        ),
        width="100%",
        height="400px",
        border="1px solid",
        border_color="gray.200",
        border_radius="md",
        padding="4"
    )


def create_control_panel() -> rx.Component:
    """Create analytics control panel"""
    return rx.vstack(
        rx.heading("Analytics Controls", size="md", margin_bottom="4"),
        
        # Algorithm Selection
        rx.vstack(
            rx.text("Centrality Algorithm:", font_weight="bold"),
            rx.select(
                AnalyticsDashboardState.available_algorithms,
                value=AnalyticsDashboardState.selected_algorithm,
                on_change=AnalyticsDashboardState.set_algorithm,
                width="100%"
            ),
            spacing="2"
        ),
        
        # Philosopher Filter
        rx.vstack(
            rx.text("Philosopher Filter:", font_weight="bold"),
            rx.select(
                AnalyticsDashboardState.available_philosophers,
                value=AnalyticsDashboardState.selected_philosopher,
                on_change=AnalyticsDashboardState.set_philosopher,
                width="100%"
            ),
            spacing="2"
        ),
        
        # Time Period Filter
        rx.vstack(
            rx.text("Time Period:", font_weight="bold"),
            rx.select(
                AnalyticsDashboardState.available_periods,
                value=AnalyticsDashboardState.selected_time_period,
                on_change=AnalyticsDashboardState.set_time_period,
                width="100%"
            ),
            spacing="2"
        ),
        
        # Layout Selection
        rx.vstack(
            rx.text("Network Layout:", font_weight="bold"),
            rx.select(
                AnalyticsDashboardState.available_layouts,
                value=AnalyticsDashboardState.selected_layout,
                on_change=AnalyticsDashboardState.set_layout,
                width="100%"
            ),
            spacing="2"
        ),
        
        # Node Size Metric
        rx.vstack(
            rx.text("Node Size Metric:", font_weight="bold"),
            rx.select(
                ["degree", "betweenness", "closeness", "eigenvector", "pagerank"],
                value=AnalyticsDashboardState.node_size_metric,
                on_change=AnalyticsDashboardState.set_node_size_metric,
                width="100%"
            ),
            spacing="2"
        ),
        
        # Color Scheme
        rx.vstack(
            rx.text("Color Scheme:", font_weight="bold"),
            rx.select(
                ["viridis", "plasma", "inferno", "magma", "cividis"],
                value=AnalyticsDashboardState.color_scheme,
                on_change=AnalyticsDashboardState.set_color_scheme,
                width="100%"
            ),
            spacing="2"
        ),
        
        # Actions
        rx.vstack(
            rx.button(
                "Refresh All Data",
                on_click=AnalyticsDashboardState.load_all_data,
                color_scheme="blue",
                width="100%"
            ),
            rx.button(
                "Export Data",
                color_scheme="green",
                width="100%"
            ),
            spacing="2"
        ),
        
        width="300px",
        padding="4",
        border="1px solid",
        border_color="gray.200",
        border_radius="md",
        spacing="4"
    )


def analytics_dashboard() -> rx.Component:
    """Main analytics dashboard page with enhanced components"""
    return rx.vstack(
        # Header with export controls
        rx.hstack(
            rx.vstack(
                rx.heading("Arete Graph Analytics Dashboard", size="6"),
                rx.text(
                    "Interactive visualization and analysis of philosophical knowledge graphs",
                    color="gray.600"
                ),
                align="start",
                spacing="2"
            ),
            rx.spacer(),
            export_controls(),
            width="100%",
            align="center"
        ),
        
        # Main content area with enhanced layout
        rx.hstack(
            # Advanced filter panel (left side)
            filter_panel(AnalyticsDashboardState),
            
            # Analytics grid (right side)
            rx.vstack(
                # Network visualization with metrics
                rx.card(
                    rx.vstack(
                        rx.hstack(
                            rx.heading("Network Visualization", size="4"),
                            rx.spacer(),
                            rx.badge("Interactive", color_scheme="blue"),
                            width="100%",
                            align="center"
                        ),
                        network_graph(
                            data=AnalyticsDashboardState.centrality_data,
                            layout_algorithm=AnalyticsDashboardState.selected_layout,
                            node_size_metric=AnalyticsDashboardState.node_size_metric,
                            color_scheme=AnalyticsDashboardState.color_scheme
                        ),
                        spacing="3"
                    ),
                    width="100%"
                ),
                
                # Centrality metrics table
                rx.card(
                    rx.vstack(
                        rx.heading("Centrality Metrics", size="4"),
                        centrality_metrics_table(AnalyticsDashboardState.centrality_data),
                        spacing="3"
                    ),
                    width="100%"
                ),
                
                # Community analysis row
                rx.hstack(
                    rx.vstack(
                        community_summary_card(AnalyticsDashboardState.community_data),
                        create_community_chart(),
                        spacing="4",
                        width="100%"
                    ),
                    rx.vstack(
                        rx.card(
                            rx.vstack(
                                rx.heading("Influence Networks", size="4"),
                                influence_timeline(AnalyticsDashboardState.influence_data),
                                spacing="3"
                            )
                        ),
                        spacing="4",
                        width="100%"
                    ),
                    spacing="4",
                    width="100%"
                ),
                
                # Topic clustering and timeline
                rx.hstack(
                    rx.card(
                        rx.vstack(
                            rx.heading("Topic Clustering", size="4"),
                            topic_cluster_heatmap(AnalyticsDashboardState.topic_clusters),
                            spacing="3"
                        ),
                        width="50%"
                    ),
                    rx.card(
                        rx.vstack(
                            rx.heading("Historical Timeline", size="4"),
                            create_timeline_chart(),
                            spacing="3"
                        ),
                        width="50%"
                    ),
                    spacing="4",
                    width="100%"
                ),
                
                spacing="6",
                width="100%",
                flex="1"
            ),
            
            spacing="6",
            width="100%",
            align="start"
        ),
        
        width="100%",
        max_width="1600px",
        margin="0 auto",
        padding="6",
        min_height="100vh",
        spacing="6"
    )


def index() -> rx.Component:
    """Index page with navigation to analytics dashboard"""
    return rx.vstack(
        rx.heading("Arete - Classical Philosophy AI Tutor", size="xl"),
        rx.text("Graph-RAG AI tutoring system for classical philosophical texts"),
        
        rx.hstack(
            rx.link(
                rx.button("Analytics Dashboard", color_scheme="blue"),
                href="/analytics"
            ),
            rx.link(
                rx.button("Chat Interface", color_scheme="green"),
                href="/chat"
            ),
            spacing="4"
        ),
        
        spacing="6",
        align="center",
        min_height="100vh",
        justify="center"
    )


# App configuration
app = rx.App(
    state=AnalyticsDashboardState,
    theme=rx.theme(
        appearance="light",
        has_background=True,
        radius="medium",
        scaling="100%",
    )
)

# Add pages
app.add_page(index, route="/")
app.add_page(analytics_dashboard, route="/analytics")
app.add_page(chat_interface, route="/chat")


# Custom JavaScript for Plotly integration
plotly_script = """
// Plotly integration functions for Reflex
window.renderCentralityChart = function(data) {
    const centralityData = data.centrality_data || {};
    const selectedAlgorithm = data.selected_algorithm || 'degree';
    
    if (!centralityData[selectedAlgorithm]) return;
    
    const values = Object.values(centralityData[selectedAlgorithm]);
    const labels = Object.keys(centralityData[selectedAlgorithm]);
    
    const trace = {
        x: labels,
        y: values,
        type: 'bar',
        marker: {
            color: values,
            colorscale: 'Viridis'
        }
    };
    
    const layout = {
        title: `${selectedAlgorithm.charAt(0).toUpperCase() + selectedAlgorithm.slice(1)} Centrality`,
        xaxis: { title: 'Nodes' },
        yaxis: { title: 'Centrality Score' },
        margin: { t: 40, r: 10, b: 80, l: 60 }
    };
    
    Plotly.newPlot('centrality-chart', [trace], layout, {responsive: true});
};

window.renderCommunityChart = function(data) {
    const communityData = data.community_data || {};
    
    if (!communityData.communities) return;
    
    // Create network visualization for communities
    // This would require more complex Plotly.js network graph implementation
    const communities = communityData.communities;
    const nodes = Object.keys(communities);
    const communityIds = [...new Set(Object.values(communities))];
    
    // Simple community bar chart as placeholder
    const communitySizes = {};
    Object.values(communities).forEach(community => {
        communitySizes[community] = (communitySizes[community] || 0) + 1;
    });
    
    const trace = {
        x: Object.keys(communitySizes),
        y: Object.values(communitySizes),
        type: 'bar',
        marker: { color: 'rgba(55, 128, 191, 0.7)' }
    };
    
    const layout = {
        title: 'Community Sizes',
        xaxis: { title: 'Community ID' },
        yaxis: { title: 'Number of Nodes' },
        margin: { t: 40, r: 10, b: 60, l: 60 }
    };
    
    Plotly.newPlot('community-chart', [trace], layout, {responsive: true});
};

// Add event listener for state changes
document.addEventListener('DOMContentLoaded', function() {
    // Listen for state updates and re-render charts
    setInterval(() => {
        const state = window.reflex_state || {};
        if (state.centrality_data) {
            renderCentralityChart(state);
        }
        if (state.community_data) {
            renderCommunityChart(state);
        }
    }, 1000);
});
"""

# Add the custom script to the app
app.add_custom_loading_script(plotly_script)