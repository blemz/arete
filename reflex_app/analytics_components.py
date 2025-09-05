"""Advanced analytics components for Reflex dashboard"""

import reflex as rx
from typing import Dict, List, Any, Optional
import json


class NetworkVisualization(rx.Component):
    """Interactive network visualization component"""
    
    library = "plotly.js"
    tag = "Plot"
    
    # Props
    data: rx.Var[Dict[str, Any]]
    layout_algorithm: rx.Var[str] = "spring"
    node_size_metric: rx.Var[str] = "degree"
    color_scheme: rx.Var[str] = "viridis"
    width: rx.Var[str] = "100%"
    height: rx.Var[str] = "400px"
    
    def _get_custom_code(self) -> str:
        return """
        const NetworkVisualization = ({data, layoutAlgorithm, nodeSizeMetric, colorScheme, width, height}) => {
            const [plotData, setPlotData] = React.useState([]);
            const [plotLayout, setPlotLayout] = React.useState({});
            
            React.useEffect(() => {
                if (!data || !data.nodes || !data.edges) return;
                
                // Process network data for Plotly
                const nodes = data.nodes;
                const edges = data.edges;
                
                // Create edge traces
                const edgeTrace = {
                    x: [],
                    y: [],
                    mode: 'lines',
                    line: {color: 'rgba(125,125,125,0.3)', width: 1},
                    hoverinfo: 'none',
                    type: 'scatter'
                };
                
                // Add edge coordinates (would need layout calculation)
                edges.forEach(edge => {
                    const source = nodes.find(n => n.id === edge.source);
                    const target = nodes.find(n => n.id === edge.target);
                    if (source && target) {
                        edgeTrace.x.push(source.x, target.x, null);
                        edgeTrace.y.push(source.y, target.y, null);
                    }
                });
                
                // Create node trace
                const nodeTrace = {
                    x: nodes.map(n => n.x),
                    y: nodes.map(n => n.y),
                    mode: 'markers+text',
                    marker: {
                        size: nodes.map(n => n[nodeSizeMetric] || 10),
                        color: nodes.map(n => n[nodeSizeMetric] || 0),
                        colorscale: colorScheme,
                        line: {width: 1, color: 'white'}
                    },
                    text: nodes.map(n => n.label || n.id),
                    textposition: 'middle center',
                    hovertemplate: '<b>%{text}</b><br>' +
                                 'Centrality: %{marker.color}<br>' +
                                 '<extra></extra>',
                    type: 'scatter'
                };
                
                setPlotData([edgeTrace, nodeTrace]);
                setPlotLayout({
                    title: 'Knowledge Graph Network',
                    showlegend: false,
                    hovermode: 'closest',
                    margin: {b: 20, l: 5, r: 5, t: 40},
                    annotations: [{
                        text: "Interactive network visualization",
                        showarrow: false,
                        xref: "paper", yref: "paper",
                        x: 0.005, y: -0.002,
                        font: {color: "grey", size: 12}
                    }],
                    xaxis: {showgrid: false, zeroline: false, showticklabels: false},
                    yaxis: {showgrid: false, zeroline: false, showticklabels: false},
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    paper_bgcolor: 'rgba(0,0,0,0)'
                });
                
            }, [data, layoutAlgorithm, nodeSizeMetric, colorScheme]);
            
            return React.createElement(Plotly.Plot, {
                data: plotData,
                layout: plotLayout,
                style: {width, height},
                config: {responsive: true, displayModeBar: false}
            });
        };
        """


def network_graph(
    data: rx.Var[Dict[str, Any]],
    layout_algorithm: rx.Var[str] = "spring",
    node_size_metric: rx.Var[str] = "degree",
    color_scheme: rx.Var[str] = "viridis",
    width: str = "100%",
    height: str = "400px"
) -> rx.Component:
    """Create interactive network graph component"""
    return NetworkVisualization.create(
        data=data,
        layout_algorithm=layout_algorithm,
        node_size_metric=node_size_metric,
        color_scheme=color_scheme,
        width=width,
        height=height
    )


def centrality_metrics_table(centrality_data: rx.Var[Dict[str, Any]]) -> rx.Component:
    """Create centrality metrics comparison table"""
    return rx.cond(
        centrality_data,
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Node"),
                        rx.table.column_header_cell("Degree"),
                        rx.table.column_header_cell("Betweenness"),
                        rx.table.column_header_cell("Closeness"),
                        rx.table.column_header_cell("Eigenvector"),
                        rx.table.column_header_cell("PageRank"),
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        centrality_data["nodes"],
                        lambda node: rx.table.row(
                            rx.table.row_header_cell(node["name"]),
                            rx.table.cell(f"{node['degree']:.3f}"),
                            rx.table.cell(f"{node['betweenness']:.3f}"),
                            rx.table.cell(f"{node['closeness']:.3f}"),
                            rx.table.cell(f"{node['eigenvector']:.3f}"),
                            rx.table.cell(f"{node['pagerank']:.3f}"),
                        )
                    )
                ),
                size="2",
                variant="surface"
            ),
            overflow_x="auto"
        ),
        rx.text("No centrality data available", color="gray.500")
    )


def community_summary_card(community_data: rx.Var[Dict[str, Any]]) -> rx.Component:
    """Create community detection summary card"""
    return rx.cond(
        community_data,
        rx.card(
            rx.vstack(
                rx.heading("Community Detection Results", size="3"),
                rx.hstack(
                    rx.vstack(
                        rx.text("Communities", font_weight="bold", color="gray.600"),
                        rx.text(
                            community_data["community_count"],
                            font_size="2xl",
                            font_weight="bold",
                            color="blue.600"
                        ),
                        align="center",
                        spacing="1"
                    ),
                    rx.vstack(
                        rx.text("Modularity", font_weight="bold", color="gray.600"),
                        rx.text(
                            f"{community_data['modularity']:.3f}",
                            font_size="2xl",
                            font_weight="bold",
                            color="green.600"
                        ),
                        align="center",
                        spacing="1"
                    ),
                    rx.vstack(
                        rx.text("Avg Size", font_weight="bold", color="gray.600"),
                        rx.text(
                            f"{community_data.get('avg_size', 0):.1f}",
                            font_size="2xl",
                            font_weight="bold",
                            color="purple.600"
                        ),
                        align="center",
                        spacing="1"
                    ),
                    spacing="6",
                    width="100%",
                    justify="around"
                ),
                spacing="4"
            ),
            width="100%"
        ),
        rx.card(
            rx.text("Community analysis not available", color="gray.500"),
            width="100%"
        )
    )


def influence_timeline(influence_data: rx.Var[Dict[str, Any]]) -> rx.Component:
    """Create influence network timeline visualization"""
    return rx.cond(
        influence_data,
        rx.box(
            # Custom timeline component would go here
            rx.vstack(
                rx.text("Influence Network Timeline", font_weight="bold"),
                rx.text("Interactive timeline showing philosophical influence over time"),
                # Placeholder for actual timeline implementation
                rx.box(
                    height="200px",
                    width="100%",
                    bg="gray.50",
                    border_radius="md",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    children=[
                        rx.text("Timeline visualization", color="gray.500")
                    ]
                ),
                spacing="3"
            ),
            width="100%"
        ),
        rx.text("No influence data available", color="gray.500")
    )


def topic_cluster_heatmap(topic_data: rx.Var[List[Dict[str, Any]]]) -> rx.Component:
    """Create topic clustering heatmap"""
    return rx.cond(
        topic_data,
        rx.box(
            # Heatmap visualization for topic similarities
            rx.vstack(
                rx.text("Topic Similarity Heatmap", font_weight="bold"),
                rx.box(
                    id="topic-heatmap",
                    height="300px",
                    width="100%",
                    border="1px solid",
                    border_color="gray.200",
                    border_radius="md"
                ),
                spacing="3"
            ),
            width="100%"
        ),
        rx.text("No topic clustering data available", color="gray.500")
    )


def export_controls() -> rx.Component:
    """Create data export controls"""
    return rx.hstack(
        rx.button(
            rx.icon("download"),
            "Export PNG",
            color_scheme="blue",
            variant="soft",
            size="2"
        ),
        rx.button(
            rx.icon("file-text"),
            "Export CSV",
            color_scheme="green",
            variant="soft",
            size="2"
        ),
        rx.button(
            rx.icon("share"),
            "Share Link",
            color_scheme="purple",
            variant="soft",
            size="2"
        ),
        spacing="2"
    )


def performance_indicator(loading_state: rx.Var[bool], data_count: rx.Var[int]) -> rx.Component:
    """Create performance indicator component"""
    return rx.hstack(
        rx.cond(
            loading_state,
            rx.hstack(
                rx.spinner(size="1"),
                rx.text("Loading...", color="gray.500", font_size="sm"),
                spacing="2"
            ),
            rx.hstack(
                rx.icon("check-circle", color="green.500", size=16),
                rx.text(f"Loaded {data_count} items", color="green.600", font_size="sm"),
                spacing="2"
            )
        ),
        align="center"
    )


def filter_panel(state) -> rx.Component:
    """Advanced filter panel with real-time updates"""
    return rx.vstack(
        rx.heading("Filters & Controls", size="4", margin_bottom="4"),
        
        # Quick actions
        rx.hstack(
            rx.button(
                rx.icon("refresh-cw"),
                "Refresh",
                on_click=state.load_all_data,
                color_scheme="blue",
                variant="soft",
                size="2"
            ),
            rx.button(
                rx.icon("settings"),
                "Settings",
                color_scheme="gray",
                variant="soft",
                size="2"
            ),
            spacing="2",
            width="100%"
        ),
        
        # Philosopher selection with search
        rx.vstack(
            rx.text("Philosopher", font_weight="bold", font_size="sm"),
            rx.select(
                state.available_philosophers,
                value=state.selected_philosopher,
                on_change=state.set_philosopher,
                placeholder="Select philosopher...",
                size="2",
                width="100%"
            ),
            spacing="1"
        ),
        
        # Time period with custom range
        rx.vstack(
            rx.text("Time Period", font_weight="bold", font_size="sm"),
            rx.select(
                state.available_periods,
                value=state.selected_time_period,
                on_change=state.set_time_period,
                placeholder="Select period...",
                size="2",
                width="100%"
            ),
            spacing="1"
        ),
        
        # Visualization settings
        rx.vstack(
            rx.text("Visualization", font_weight="bold", font_size="sm"),
            rx.vstack(
                rx.hstack(
                    rx.text("Layout:", font_size="xs", color="gray.600"),
                    rx.select(
                        state.available_layouts,
                        value=state.selected_layout,
                        on_change=state.set_layout,
                        size="1",
                        width="120px"
                    ),
                    spacing="2",
                    align="center",
                    width="100%"
                ),
                rx.hstack(
                    rx.text("Node Size:", font_size="xs", color="gray.600"),
                    rx.select(
                        ["degree", "betweenness", "closeness"],
                        value=state.node_size_metric,
                        on_change=state.set_node_size_metric,
                        size="1",
                        width="120px"
                    ),
                    spacing="2",
                    align="center",
                    width="100%"
                ),
                rx.hstack(
                    rx.text("Colors:", font_size="xs", color="gray.600"),
                    rx.select(
                        ["viridis", "plasma", "inferno"],
                        value=state.color_scheme,
                        on_change=state.set_color_scheme,
                        size="1",
                        width="120px"
                    ),
                    spacing="2",
                    align="center",
                    width="100%"
                ),
                spacing="2"
            ),
            spacing="1"
        ),
        
        # Performance info
        rx.separator(),
        performance_indicator(
            state.is_loading_centrality,
            len(state.available_philosophers)
        ),
        
        spacing="4",
        width="280px",
        padding="4",
        bg="gray.50",
        border_radius="lg"
    )