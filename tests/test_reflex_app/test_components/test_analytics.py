"""Tests for analytics component."""
import pytest
from unittest.mock import Mock, patch
import reflex as rx
from src.arete.ui.reflex_app.components.analytics import AnalyticsComponent


class TestAnalyticsComponent:
    """Test cases for AnalyticsComponent."""

    @pytest.fixture
    def analytics_component(self):
        """AnalyticsComponent instance for testing."""
        return AnalyticsComponent()

    @pytest.fixture
    def sample_analytics_data(self):
        """Sample analytics data for testing."""
        return {
            "centrality_scores": {
                "virtue": {"degree": 15, "betweenness": 0.65, "closeness": 0.82},
                "justice": {"degree": 12, "betweenness": 0.45, "closeness": 0.73},
                "wisdom": {"degree": 10, "betweenness": 0.38, "closeness": 0.68}
            },
            "communities": [
                {"id": 0, "nodes": ["virtue", "justice", "courage"], "modularity": 0.75},
                {"id": 1, "nodes": ["wisdom", "knowledge", "truth"], "modularity": 0.68}
            ],
            "network_metrics": {
                "total_nodes": 150,
                "total_edges": 300,
                "density": 0.027,
                "clustering_coefficient": 0.65
            }
        }

    def test_analytics_component_initialization(self, analytics_component):
        """Test analytics component initialization."""
        assert analytics_component is not None
        assert hasattr(analytics_component, 'render')

    def test_render_analytics_dashboard(self, analytics_component, sample_analytics_data):
        """Test rendering analytics dashboard."""
        with patch('src.arete.ui.reflex_app.state.analytics_state.AnalyticsState') as mock_state:
            mock_state.analytics_data = sample_analytics_data
            mock_state.is_loading = False
            
            rendered = analytics_component.render()
            
            assert rendered is not None

    def test_render_loading_state(self, analytics_component):
        """Test rendering analytics in loading state."""
        with patch('src.arete.ui.reflex_app.state.analytics_state.AnalyticsState') as mock_state:
            mock_state.is_loading = True
            mock_state.analytics_data = None
            
            rendered = analytics_component.render()
            
            assert rendered is not None

    def test_centrality_scores_chart(self, analytics_component):
        """Test centrality scores chart component."""
        centrality_data = {
            "virtue": {"degree": 15, "betweenness": 0.65},
            "justice": {"degree": 12, "betweenness": 0.45},
            "wisdom": {"degree": 10, "betweenness": 0.38}
        }
        
        chart = analytics_component.create_centrality_chart(centrality_data)
        
        assert chart is not None

    def test_network_graph_visualization(self, analytics_component):
        """Test network graph visualization."""
        network_data = {
            "nodes": [
                {"id": "virtue", "label": "Virtue", "size": 15},
                {"id": "justice", "label": "Justice", "size": 12}
            ],
            "edges": [
                {"source": "virtue", "target": "justice", "weight": 0.8}
            ]
        }
        
        graph = analytics_component.create_network_graph(network_data)
        
        assert graph is not None

    def test_community_detection_visualization(self, analytics_component):
        """Test community detection visualization."""
        communities = [
            {"id": 0, "nodes": ["virtue", "justice"], "modularity": 0.75, "color": "#ff6b6b"},
            {"id": 1, "nodes": ["wisdom", "knowledge"], "modularity": 0.68, "color": "#4ecdc4"}
        ]
        
        community_viz = analytics_component.create_community_visualization(communities)
        
        assert community_viz is not None

    def test_influence_network_chart(self, analytics_component):
        """Test influence network chart."""
        influence_data = {
            "socrates": {"influence_score": 0.95, "connections": 25},
            "plato": {"influence_score": 0.88, "connections": 22},
            "aristotle": {"influence_score": 0.92, "connections": 28}
        }
        
        influence_chart = analytics_component.create_influence_chart(influence_data)
        
        assert influence_chart is not None

    def test_timeline_visualization(self, analytics_component):
        """Test philosophical timeline visualization."""
        timeline_data = [
            {"period": "Pre-Socratic", "start": -600, "end": -400, "concepts": ["cosmos", "logos"]},
            {"period": "Classical", "start": -400, "end": -300, "concepts": ["virtue", "justice"]},
            {"period": "Hellenistic", "start": -300, "end": 300, "concepts": ["ataraxia", "apatheia"]}
        ]
        
        timeline = analytics_component.create_timeline_visualization(timeline_data)
        
        assert timeline is not None

    def test_concept_evolution_chart(self, analytics_component):
        """Test concept evolution chart."""
        evolution_data = {
            "concept": "virtue",
            "timeline": [
                {"period": "Homer", "definition": "Excellence in general", "frequency": 0.3},
                {"period": "Socratic", "definition": "Knowledge of good", "frequency": 0.7},
                {"period": "Aristotelian", "definition": "Disposition to excellence", "frequency": 0.9}
            ]
        }
        
        evolution_chart = analytics_component.create_concept_evolution_chart(evolution_data)
        
        assert evolution_chart is not None

    def test_metrics_dashboard(self, analytics_component):
        """Test metrics dashboard component."""
        metrics = {
            "total_concepts": 150,
            "total_relationships": 300,
            "network_density": 0.027,
            "average_clustering": 0.65,
            "most_central_concept": "virtue",
            "largest_community_size": 25
        }
        
        dashboard = analytics_component.create_metrics_dashboard(metrics)
        
        assert dashboard is not None

    def test_interactive_filters(self, analytics_component):
        """Test interactive filters component."""
        filter_options = {
            "time_periods": ["Classical", "Hellenistic", "Medieval", "Modern"],
            "philosophers": ["Socrates", "Plato", "Aristotle", "Augustine"],
            "concept_types": ["Virtue", "Knowledge", "Justice", "Truth"]
        }
        
        filters = analytics_component.create_interactive_filters(filter_options)
        
        assert filters is not None

    def test_comparison_charts(self, analytics_component):
        """Test concept comparison charts."""
        comparison_data = [
            {"concept": "virtue", "aristotle_score": 0.9, "plato_score": 0.85},
            {"concept": "justice", "aristotle_score": 0.8, "plato_score": 0.95},
            {"concept": "wisdom", "aristotle_score": 0.85, "plato_score": 0.88}
        ]
        
        comparison_chart = analytics_component.create_comparison_chart(comparison_data)
        
        assert comparison_chart is not None

    def test_heatmap_visualization(self, analytics_component):
        """Test concept relationship heatmap."""
        relationship_matrix = {
            "virtue": {"justice": 0.8, "wisdom": 0.7, "courage": 0.9},
            "justice": {"virtue": 0.8, "wisdom": 0.6, "temperance": 0.7},
            "wisdom": {"virtue": 0.7, "justice": 0.6, "knowledge": 0.95}
        }
        
        heatmap = analytics_component.create_relationship_heatmap(relationship_matrix)
        
        assert heatmap is not None

    def test_usage_statistics_charts(self, analytics_component):
        """Test usage statistics charts."""
        usage_stats = {
            "daily_queries": [45, 52, 38, 67, 71, 49, 55],
            "top_concepts": [
                {"concept": "virtue", "query_count": 156},
                {"concept": "justice", "query_count": 142},
                {"concept": "wisdom", "query_count": 128}
            ],
            "user_engagement": {"avg_session": 12.5, "bounce_rate": 0.15}
        }
        
        usage_charts = analytics_component.create_usage_statistics(usage_stats)
        
        assert usage_charts is not None

    def test_export_analytics_functionality(self, analytics_component, sample_analytics_data):
        """Test analytics export functionality."""
        export_menu = analytics_component.create_export_menu(sample_analytics_data)
        
        assert export_menu is not None

    def test_real_time_updates(self, analytics_component):
        """Test real-time analytics updates."""
        with patch.object(analytics_component, 'setup_websocket_updates') as mock_setup:
            analytics_component.enable_real_time_updates()
            
            mock_setup.assert_called_once()

    def test_drill_down_functionality(self, analytics_component):
        """Test drill-down functionality for detailed analysis."""
        with patch.object(analytics_component, 'show_detailed_view') as mock_detail:
            analytics_component.handle_concept_click("virtue")
            
            mock_detail.assert_called_once_with("virtue")

    def test_color_scheme_customization(self, analytics_component):
        """Test color scheme customization."""
        color_schemes = {
            "default": ["#1f77b4", "#ff7f0e", "#2ca02c"],
            "dark": ["#8c564b", "#e377c2", "#7f7f7f"],
            "colorblind": ["#d62728", "#9467bd", "#8c564b"]
        }
        
        analytics_component.set_color_scheme("dark")
        
        assert analytics_component.current_color_scheme == "dark"

    def test_responsive_chart_design(self, analytics_component):
        """Test responsive chart design."""
        with patch.object(analytics_component, 'is_mobile_view', return_value=True):
            mobile_chart = analytics_component.create_responsive_chart({}, chart_type="bar")
            assert mobile_chart is not None
        
        with patch.object(analytics_component, 'is_mobile_view', return_value=False):
            desktop_chart = analytics_component.create_responsive_chart({}, chart_type="bar")
            assert desktop_chart is not None

    def test_animation_and_transitions(self, analytics_component):
        """Test chart animations and transitions."""
        with patch.object(analytics_component, 'animate_chart_update') as mock_animate:
            new_data = {"virtue": 0.9, "justice": 0.8}
            analytics_component.update_chart_data("centrality", new_data)
            
            mock_animate.assert_called_once()

    def test_tooltip_functionality(self, analytics_component):
        """Test chart tooltip functionality."""
        tooltip_config = analytics_component.create_tooltip_config()
        
        assert "enabled" in tooltip_config
        assert "format" in tooltip_config
        assert tooltip_config["enabled"] == True

    def test_legend_customization(self, analytics_component):
        """Test chart legend customization."""
        legend_config = {
            "position": "right",
            "show_values": True,
            "interactive": True
        }
        
        legend = analytics_component.create_legend(legend_config)
        
        assert legend is not None

    def test_data_quality_indicators(self, analytics_component):
        """Test data quality indicators."""
        quality_metrics = {
            "completeness": 0.95,
            "accuracy": 0.88,
            "consistency": 0.92,
            "timeliness": 0.85
        }
        
        quality_display = analytics_component.create_quality_indicators(quality_metrics)
        
        assert quality_display is not None

    def test_statistical_summaries(self, analytics_component):
        """Test statistical summaries."""
        stats_data = {
            "mean": 0.75,
            "median": 0.78,
            "std_dev": 0.12,
            "min": 0.45,
            "max": 0.95
        }
        
        summary = analytics_component.create_statistical_summary(stats_data)
        
        assert summary is not None

    def test_trend_analysis(self, analytics_component):
        """Test trend analysis visualization."""
        trend_data = {
            "virtue": [0.5, 0.6, 0.7, 0.8, 0.85, 0.9],
            "justice": [0.4, 0.5, 0.6, 0.65, 0.7, 0.75],
            "time_labels": ["2020", "2021", "2022", "2023", "2024", "2025"]
        }
        
        trend_chart = analytics_component.create_trend_analysis(trend_data)
        
        assert trend_chart is not None

    def test_accessibility_features(self, analytics_component):
        """Test accessibility features for charts."""
        with patch.object(analytics_component, 'add_alt_text') as mock_alt_text:
            with patch.object(analytics_component, 'add_keyboard_navigation') as mock_keyboard:
                analytics_component.ensure_chart_accessibility()
                
                mock_alt_text.assert_called_once()
                mock_keyboard.assert_called_once()

    def test_performance_optimization(self, analytics_component):
        """Test performance optimization for large datasets."""
        large_dataset = {"concepts": list(range(1000)), "relationships": list(range(5000))}
        
        with patch.object(analytics_component, 'use_data_sampling') as mock_sampling:
            analytics_component.render_large_dataset(large_dataset)
            
            mock_sampling.assert_called_once()

    def test_error_handling_in_visualizations(self, analytics_component):
        """Test error handling in visualizations."""
        invalid_data = {"malformed": "data"}
        
        error_display = analytics_component.handle_visualization_error(invalid_data)
        
        assert error_display is not None

    def test_custom_chart_types(self, analytics_component):
        """Test custom chart type creation."""
        custom_config = {
            "type": "philosophical_network",
            "layout": "force_directed",
            "node_styling": "by_importance",
            "edge_styling": "by_relationship_type"
        }
        
        custom_chart = analytics_component.create_custom_chart(custom_config)
        
        assert custom_chart is not None

    def test_data_refresh_controls(self, analytics_component):
        """Test data refresh controls."""
        refresh_controls = analytics_component.create_refresh_controls()
        
        assert refresh_controls is not None

    def test_fullscreen_chart_mode(self, analytics_component):
        """Test fullscreen chart mode."""
        fullscreen_button = analytics_component.create_fullscreen_button()
        
        assert fullscreen_button is not None

    def test_chart_interaction_handlers(self, analytics_component):
        """Test chart interaction handlers."""
        with patch.object(analytics_component, 'handle_node_click') as mock_node_click:
            with patch.object(analytics_component, 'handle_edge_hover') as mock_edge_hover:
                analytics_component.setup_interaction_handlers()
                
                # Simulate interactions
                analytics_component.on_node_click({"id": "virtue"})
                analytics_component.on_edge_hover({"source": "virtue", "target": "justice"})
                
                mock_node_click.assert_called_once()
                mock_edge_hover.assert_called_once()

    def test_analytics_presets(self, analytics_component):
        """Test analytics view presets."""
        presets = {
            "overview": {"charts": ["network", "metrics", "top_concepts"]},
            "detailed": {"charts": ["centrality", "communities", "evolution"]},
            "comparison": {"charts": ["heatmap", "comparison", "trends"]}
        }
        
        preset_selector = analytics_component.create_preset_selector(presets)
        
        assert preset_selector is not None

    def test_annotation_system(self, analytics_component):
        """Test chart annotation system."""
        annotations = [
            {"x": 0.5, "y": 0.8, "text": "Peak virtue discussions", "type": "peak"},
            {"x": 0.3, "y": 0.6, "text": "Concept introduction", "type": "milestone"}
        ]
        
        annotated_chart = analytics_component.add_annotations(annotations)
        
        assert annotated_chart is not None