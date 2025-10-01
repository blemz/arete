"""
Interactive Graph Analytics Visualization for Arete.

This module provides Streamlit-based interactive visualizations for graph analytics
results, including centrality analysis, community detection, influence networks,
and topic clustering visualizations.
"""

import logging

import networkx as nx
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from arete.models.entity import EntityType
from arete.services.graph_analytics_service import (
    CentralityMetric,
    CentralityResult,
    CommunityResult,
    GraphAnalyticsService,
    InfluenceNetwork,
    TopicClusteringResult,
    create_graph_analytics_service,
)

logger = logging.getLogger(__name__)

class GraphAnalyticsVisualizer:
    """Streamlit-based visualizer for graph analytics results."""

    def __init__(self, analytics_service: GraphAnalyticsService | None = None):
        """Initialize the visualizer."""
        self.analytics_service = analytics_service or create_graph_analytics_service()

    def render_analytics_dashboard(self):
        """Render the main analytics dashboard."""
        st.title("📊 Graph Analytics Dashboard")
        st.markdown("*Analyze philosophical knowledge graph structure and relationships*")

        # Sidebar controls
        with st.sidebar:
            st.header("Analytics Controls")

            analysis_type = st.selectbox(
                "Select Analysis Type",
                ["Centrality Analysis", "Community Detection", "Influence Networks", "Topic Clustering"],
                help="Choose the type of graph analysis to perform"
            )

        # Main content area
        if analysis_type == "Centrality Analysis":
            self._render_centrality_analysis()
        elif analysis_type == "Community Detection":
            self._render_community_detection()
        elif analysis_type == "Influence Networks":
            self._render_influence_networks()
        elif analysis_type == "Topic Clustering":
            self._render_topic_clustering()

    def _render_centrality_analysis(self):
        """Render centrality analysis section."""
        st.header("🎯 Centrality Analysis")
        st.markdown("Identify the most important concepts and thinkers in the knowledge graph")

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            centrality_metric = st.selectbox(
                "Centrality Metric",
                [metric.value for metric in CentralityMetric],
                help="Different metrics highlight different aspects of importance"
            )

        with col2:
            entity_types = st.multiselect(
                "Entity Types",
                [et.value for et in EntityType],
                default=[EntityType.PERSON.value, EntityType.CONCEPT.value],
                help="Filter analysis by entity types"
            )

        with col3:
            top_n = st.number_input("Top N Results", min_value=5, max_value=100, value=20)

        if st.button("🔍 Run Centrality Analysis", type="primary"):
            with st.spinner("Analyzing graph centrality..."):
                try:
                    # Convert string values back to enums
                    metric_enum = CentralityMetric(centrality_metric)
                    [EntityType(et) for et in entity_types] if entity_types else None

                    # This would be async in real implementation
                    # For demo, we'll create mock results
                    result = self._create_mock_centrality_result(metric_enum, top_n)

                    self._display_centrality_results(result)

                except Exception as e:
                    st.error(f"Analysis failed: {str(e)}")
                    logger.error(f"Centrality analysis error: {e}")

    def _render_community_detection(self):
        """Render community detection section."""
        st.header("🏘️ Community Detection")
        st.markdown("Discover philosophical schools and conceptual clusters")

        col1, col2 = st.columns(2)

        with col1:
            st.selectbox(
                "Detection Algorithm",
                ["label_propagation", "louvain", "leiden"],
                help="Algorithm for detecting communities"
            )

        with col2:
            st.number_input("Minimum Community Size", min_value=2, max_value=20, value=3)

        if st.button("🔍 Detect Communities", type="primary"):
            with st.spinner("Detecting communities..."):
                try:
                    result = self._create_mock_community_result()
                    self._display_community_results(result)

                except Exception as e:
                    st.error(f"Community detection failed: {str(e)}")
                    logger.error(f"Community detection error: {e}")

    def _render_influence_networks(self):
        """Render influence network analysis section."""
        st.header("🌐 Influence Networks")
        st.markdown("Trace intellectual influence and historical connections")

        col1, col2 = st.columns(2)

        with col1:
            st.checkbox("Include Temporal Analysis", value=True)

        with col2:
            focus_entity = st.text_input("Focus on Entity (optional)", placeholder="e.g., Plato")

        if st.button("🔍 Analyze Influence Networks", type="primary"):
            with st.spinner("Analyzing influence networks..."):
                try:
                    result = self._create_mock_influence_network()
                    self._display_influence_network(result, focus_entity)

                except Exception as e:
                    st.error(f"Influence analysis failed: {str(e)}")
                    logger.error(f"Influence analysis error: {e}")

    def _render_topic_clustering(self):
        """Render topic clustering section."""
        st.header("🧩 Topic Clustering")
        st.markdown("Group related philosophical concepts and themes")

        col1, col2 = st.columns(2)

        with col1:
            st.slider("Similarity Threshold", 0.3, 0.9, 0.7)

        with col2:
            st.number_input("Min Cluster Size", min_value=2, max_value=10, value=3)

        if st.button("🔍 Cluster Topics", type="primary"):
            with st.spinner("Clustering topics..."):
                try:
                    result = self._create_mock_topic_clustering_result()
                    self._display_topic_clusters(result)

                except Exception as e:
                    st.error(f"Topic clustering failed: {str(e)}")
                    logger.error(f"Topic clustering error: {e}")

    def _display_centrality_results(self, result: CentralityResult):
        """Display centrality analysis results."""
        st.success(f"✅ Centrality analysis completed! Found {result.total_entities} entities.")

        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Entities", result.total_entities)
        with col2:
            st.metric("Analysis Type", result.metric.value.title())
        with col3:
            if result.top_entities:
                st.metric("Top Score", f"{result.top_entities[0][2]:.2f}")

        # Top entities table
        st.subheader("🏆 Top Entities by Centrality")
        if result.top_entities:
            df = pd.DataFrame(
                result.top_entities[:20],
                columns=["Entity ID", "Name", "Score"]
            )
            st.dataframe(df, use_container_width=True)

        # Centrality distribution chart
        st.subheader("📊 Centrality Score Distribution")
        if result.scores:
            scores_df = pd.DataFrame(
                list(result.scores.items()),
                columns=["Entity", "Score"]
            )
            fig = px.histogram(
                scores_df,
                x="Score",
                nbins=30,
                title=f"{result.metric.value.title()} Centrality Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)

        # Interactive bar chart of top entities
        if result.top_entities:
            st.subheader("📈 Top Entities Ranking")
            top_df = pd.DataFrame(
                result.top_entities[:15],
                columns=["Entity ID", "Name", "Score"]
            )
            fig = px.bar(
                top_df,
                x="Name",
                y="Score",
                title=f"Top 15 Entities by {result.metric.value.title()} Centrality",
                hover_data=["Entity ID"]
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

    def _display_community_results(self, result: CommunityResult):
        """Display community detection results."""
        st.success(f"✅ Found {result.total_communities} communities!")

        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Communities Found", result.total_communities)
        with col2:
            st.metric("Algorithm Used", result.algorithm.title())
        with col3:
            if result.modularity_score > 0:
                st.metric("Modularity Score", f"{result.modularity_score:.3f}")

        # Community details
        st.subheader("🏘️ Community Breakdown")
        for community_id, entities in result.communities.items():
            with st.expander(f"Community {community_id + 1} ({len(entities)} entities)"):
                st.write("**Members:**")
                for entity in entities[:10]:  # Show first 10
                    st.write(f"• {entity}")
                if len(entities) > 10:
                    st.write(f"*...and {len(entities) - 10} more*")

        # Community size distribution
        if result.communities:
            st.subheader("📊 Community Size Distribution")
            sizes = [len(entities) for entities in result.communities.values()]
            sizes_df = pd.DataFrame({"Community Size": sizes})
            fig = px.histogram(
                sizes_df,
                x="Community Size",
                nbins=min(20, len(sizes)),
                title="Distribution of Community Sizes"
            )
            st.plotly_chart(fig, use_container_width=True)

    def _display_influence_network(self, result: InfluenceNetwork, focus_entity: str | None = None):
        """Display influence network visualization."""
        st.success("✅ Influence network analysis completed!")

        # Summary metrics
        total_influences = len(result.influences)
        total_connections = sum(len(influenced) for influenced in result.influences.values())

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Influencers", total_influences)
        with col2:
            st.metric("Total Connections", total_connections)
        with col3:
            if result.influence_scores:
                avg_score = np.mean(list(result.influence_scores.values()))
                st.metric("Avg. Influence Score", f"{avg_score:.2f}")

        # Network visualization
        st.subheader("🌐 Influence Network Graph")
        if result.influences:
            fig = self._create_influence_network_plot(result, focus_entity)
            st.plotly_chart(fig, use_container_width=True)

        # Top influencers table
        st.subheader("👑 Most Influential Entities")
        influencer_counts = {
            influencer: len(influenced)
            for influencer, influenced in result.influences.items()
        }
        if influencer_counts:
            sorted_influencers = sorted(
                influencer_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )
            df = pd.DataFrame(
                sorted_influencers[:15],
                columns=["Entity", "Influences Count"]
            )
            st.dataframe(df, use_container_width=True)

    def _display_topic_clusters(self, result: TopicClusteringResult):
        """Display topic clustering results."""
        st.success(f"✅ Found {len(result.clusters)} topic clusters!")

        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Topic Clusters", len(result.clusters))
        with col2:
            st.metric("Outliers", len(result.outliers))
        with col3:
            if result.silhouette_score > 0:
                st.metric("Silhouette Score", f"{result.silhouette_score:.3f}")

        # Cluster details
        st.subheader("🧩 Topic Clusters")
        for cluster in result.clusters:
            with st.expander(f"Cluster {cluster.cluster_id + 1}: {cluster.central_concept}"):
                st.write(f"**Central Concept:** {cluster.central_concept}")
                st.write(f"**Similarity Threshold:** {cluster.similarity_threshold}")
                st.write(f"**Entities ({len(cluster.entities)}):**")
                for entity in cluster.entities:
                    st.write(f"• {entity}")

                if cluster.cluster_keywords:
                    st.write("**Keywords:**")
                    st.write(", ".join(cluster.cluster_keywords))

        # Outliers
        if result.outliers:
            with st.expander(f"Outliers ({len(result.outliers)} entities)"):
                for outlier in result.outliers:
                    st.write(f"• {outlier}")

    def _create_influence_network_plot(self, result: InfluenceNetwork, focus_entity: str | None = None):
        """Create interactive influence network plot."""
        # Create NetworkX graph
        G = nx.DiGraph()

        # Add nodes and edges
        for influencer, influenced_list in result.influences.items():
            G.add_node(influencer)
            for influenced in influenced_list:
                G.add_node(influenced)
                weight = result.influence_scores.get((influencer, influenced), 1.0)
                G.add_edge(influencer, influenced, weight=weight)

        # Layout
        if focus_entity and focus_entity in G:
            pos = nx.spring_layout(G, k=2, iterations=50, center=[0, 0])
        else:
            pos = nx.spring_layout(G, k=1, iterations=50)

        # Create Plotly figure
        edge_x = []
        edge_y = []
        edge_info = []

        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            weight = G[edge[0]][edge[1]]["weight"]
            edge_info.append(f"{edge[0]} → {edge[1]} (strength: {weight:.2f})")

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line={"width": 1, "color": "rgba(125,125,125,0.3)"},
            hoverinfo="none",
            mode="lines"
        )

        node_x = []
        node_y = []
        node_text = []
        node_info = []
        node_size = []

        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)

            # Node size based on influence (out-degree + in-degree)
            out_degree = G.out_degree(node)
            in_degree = G.in_degree(node)
            size = 10 + (out_degree + in_degree) * 2
            node_size.append(size)

            node_info.append(f"{node}<br>Influences: {out_degree}<br>Influenced by: {in_degree}")

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode="markers+text",
            hoverinfo="text",
            text=node_text,
            hovertext=node_info,
            textposition="middle center",
            marker={
                "size": node_size,
                "color": "lightblue",
                "line": {"width": 2, "color": "darkblue"}
            }
        )

        # Highlight focus entity if specified
        if focus_entity and focus_entity in pos:
            focus_trace = go.Scatter(
                x=[pos[focus_entity][0]],
                y=[pos[focus_entity][1]],
                mode="markers",
                marker={"size": 30, "color": "red", "opacity": 0.7},
                hoverinfo="none",
                showlegend=False
            )
            data = [edge_trace, node_trace, focus_trace]
        else:
            data = [edge_trace, node_trace]

        fig = go.Figure(
            data=data,
            layout=go.Layout(
                title="Philosophical Influence Network",
                titlefont_size=16,
                showlegend=False,
                hovermode="closest",
                margin={"b": 20,"l": 5,"r": 5,"t": 40},
                annotations=[{
                    "text": "Node size represents total influence connections",
                    "showarrow": False,
                    "xref": "paper", "yref": "paper",
                    "x": 0.005, "y": -0.002,
                    "xanchor": "left", "yanchor": "bottom",
                    "font": {"size": 12}
                }],
                xaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
                yaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
                height=600
            )
        )

        return fig

    # Mock data creation methods for demonstration
    def _create_mock_centrality_result(self, metric: CentralityMetric, limit: int) -> CentralityResult:
        """Create mock centrality result for demonstration."""
        philosophers = [
            ("plato", "Plato", 10.5),
            ("aristotle", "Aristotle", 9.8),
            ("socrates", "Socrates", 8.2),
            ("kant", "Immanuel Kant", 7.9),
            ("aquinas", "Thomas Aquinas", 7.1),
            ("augustine", "Augustine of Hippo", 6.8),
            ("hume", "David Hume", 6.5),
            ("descartes", "René Descartes", 6.2),
            ("spinoza", "Baruch Spinoza", 5.9),
            ("leibniz", "Gottfried Leibniz", 5.7)
        ]

        top_entities = philosophers[:limit]
        scores = {entity_id: score for entity_id, _, score in top_entities}

        return CentralityResult(
            metric=metric,
            scores=scores,
            top_entities=top_entities,
            total_entities=len(philosophers)
        )

    def _create_mock_community_result(self) -> CommunityResult:
        """Create mock community result for demonstration."""
        communities = {
            0: ["plato", "aristotle", "socrates"],
            1: ["kant", "hegel", "fichte"],
            2: ["aquinas", "augustine", "anselm"],
            3: ["hume", "locke", "berkeley"]
        }

        entity_community = {}
        for comm_id, entities in communities.items():
            for entity in entities:
                entity_community[entity] = comm_id

        return CommunityResult(
            algorithm="label_propagation",
            communities=communities,
            entity_community=entity_community,
            modularity_score=0.742,
            total_communities=len(communities)
        )

    def _create_mock_influence_network(self) -> InfluenceNetwork:
        """Create mock influence network for demonstration."""
        influences = {
            "socrates": ["plato"],
            "plato": ["aristotle", "augustine"],
            "aristotle": ["aquinas"],
            "kant": ["hegel", "fichte"],
            "augustine": ["aquinas", "anselm"]
        }

        influence_scores = {
            ("socrates", "plato"): 1.0,
            ("plato", "aristotle"): 0.95,
            ("plato", "augustine"): 0.8,
            ("aristotle", "aquinas"): 0.85,
            ("kant", "hegel"): 0.9,
            ("kant", "fichte"): 0.7,
            ("augustine", "aquinas"): 0.75,
            ("augustine", "anselm"): 0.6
        }

        return InfluenceNetwork(
            influences=influences,
            influence_scores=influence_scores
        )

    def _create_mock_topic_clustering_result(self) -> TopicClusteringResult:
        """Create mock topic clustering result for demonstration."""
        from arete.services.graph_analytics_service import ConceptCluster  # noqa: PLC0415

        clusters = [
            ConceptCluster(
                cluster_id=0,
                entities=["justice", "virtue", "good"],
                central_concept="virtue",
                similarity_threshold=0.7,
                cluster_keywords=["ethics", "morality", "character"]
            ),
            ConceptCluster(
                cluster_id=1,
                entities=["knowledge", "truth", "belief"],
                central_concept="knowledge",
                similarity_threshold=0.7,
                cluster_keywords=["epistemology", "certainty", "skepticism"]
            ),
            ConceptCluster(
                cluster_id=2,
                entities=["soul", "mind", "consciousness"],
                central_concept="soul",
                similarity_threshold=0.7,
                cluster_keywords=["metaphysics", "identity", "dualism"]
            )
        ]

        outliers = ["beauty", "art", "rhetoric"]

        return TopicClusteringResult(
            clusters=clusters,
            outliers=outliers,
            silhouette_score=0.68
        )


def render_graph_analytics():
    """Main function to render the graph analytics interface."""
    try:
        visualizer = GraphAnalyticsVisualizer()
        visualizer.render_analytics_dashboard()
    except Exception as e:
        st.error(f"Error loading graph analytics: {str(e)}")
        logger.error(f"Graph analytics visualization error: {e}")


if __name__ == "__main__":
    render_graph_analytics()
