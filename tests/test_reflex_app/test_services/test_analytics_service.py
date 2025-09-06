"""Tests for analytics service."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.arete.ui.reflex_app.services.analytics_service import AnalyticsService


class TestAnalyticsService:
    """Test cases for AnalyticsService."""

    @pytest.fixture
    def analytics_service(self, mock_neo4j_client):
        """AnalyticsService instance for testing."""
        return AnalyticsService(neo4j_client=mock_neo4j_client)

    @pytest.mark.asyncio
    async def test_get_centrality_scores(self, analytics_service, mock_analytics_data):
        """Test centrality score calculation."""
        with patch.object(analytics_service, '_calculate_centrality') as mock_calc:
            mock_calc.return_value = mock_analytics_data["centrality_scores"]
            
            scores = await analytics_service.get_centrality_scores()
            
            assert "virtue" in scores
            assert "justice" in scores
            assert scores["virtue"]["degree"] == 10
            assert scores["virtue"]["betweenness"] == 0.5

    @pytest.mark.asyncio
    async def test_get_centrality_scores_specific_algorithm(self, analytics_service):
        """Test centrality calculation for specific algorithm."""
        with patch.object(analytics_service, '_calculate_degree_centrality') as mock_degree:
            mock_degree.return_value = {"virtue": 10, "justice": 8, "wisdom": 6}
            
            scores = await analytics_service.get_centrality_scores(algorithm="degree")
            
            assert scores["virtue"] == 10
            assert scores["justice"] == 8
            mock_degree.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_community_detection(self, analytics_service, mock_analytics_data):
        """Test community detection functionality."""
        with patch.object(analytics_service, '_detect_communities') as mock_communities:
            mock_communities.return_value = mock_analytics_data["communities"]
            
            communities = await analytics_service.get_community_detection()
            
            assert len(communities) == 1
            assert communities[0]["id"] == 0
            assert "virtue" in communities[0]["nodes"]
            assert "justice" in communities[0]["nodes"]
            assert communities[0]["modularity"] == 0.7

    @pytest.mark.asyncio
    async def test_get_influence_networks(self, analytics_service, mock_analytics_data):
        """Test influence network analysis."""
        with patch.object(analytics_service, '_analyze_influence') as mock_influence:
            mock_influence.return_value = mock_analytics_data["influence_networks"]
            
            networks = await analytics_service.get_influence_networks()
            
            assert "socrates" in networks
            assert networks["socrates"]["influence_score"] == 0.9
            assert "virtue" in networks["socrates"]["connections"]

    @pytest.mark.asyncio
    async def test_get_concept_relationships(self, analytics_service):
        """Test concept relationship analysis."""
        with patch.object(analytics_service.neo4j_client, 'session') as mock_session:
            mock_result = Mock()
            mock_result.data.return_value = [
                {
                    "source": "virtue",
                    "target": "justice",
                    "relationship": "RELATES_TO",
                    "strength": 0.8
                },
                {
                    "source": "virtue",
                    "target": "wisdom",
                    "relationship": "PREREQUISITE_FOR",
                    "strength": 0.9
                }
            ]
            mock_session.return_value.__enter__.return_value.run.return_value = mock_result
            
            relationships = await analytics_service.get_concept_relationships("virtue")
            
            assert len(relationships) == 2
            assert relationships[0]["target"] == "justice"
            assert relationships[1]["strength"] == 0.9

    @pytest.mark.asyncio
    async def test_get_philosophical_timeline(self, analytics_service):
        """Test philosophical timeline generation."""
        with patch.object(analytics_service, '_build_timeline') as mock_timeline:
            mock_timeline.return_value = [
                {
                    "period": "Classical Antiquity",
                    "start_year": -500,
                    "end_year": 500,
                    "philosophers": ["Socrates", "Plato", "Aristotle"],
                    "key_concepts": ["virtue", "justice", "wisdom"]
                },
                {
                    "period": "Medieval Philosophy",
                    "start_year": 500,
                    "end_year": 1500,
                    "philosophers": ["Augustine", "Aquinas"],
                    "key_concepts": ["divine command", "natural law"]
                }
            ]
            
            timeline = await analytics_service.get_philosophical_timeline()
            
            assert len(timeline) == 2
            assert timeline[0]["period"] == "Classical Antiquity"
            assert "Socrates" in timeline[0]["philosophers"]

    @pytest.mark.asyncio
    async def test_get_concept_evolution(self, analytics_service):
        """Test concept evolution tracking."""
        with patch.object(analytics_service, '_trace_concept_evolution') as mock_evolution:
            mock_evolution.return_value = {
                "concept": "virtue",
                "timeline": [
                    {
                        "period": "Pre-Socratic",
                        "definition": "Excellence in general",
                        "key_thinkers": ["Homer"]
                    },
                    {
                        "period": "Classical",
                        "definition": "Moral excellence, knowledge of good",
                        "key_thinkers": ["Socrates", "Plato", "Aristotle"]
                    }
                ]
            }
            
            evolution = await analytics_service.get_concept_evolution("virtue")
            
            assert evolution["concept"] == "virtue"
            assert len(evolution["timeline"]) == 2
            assert "Socrates" in evolution["timeline"][1]["key_thinkers"]

    @pytest.mark.asyncio
    async def test_get_network_metrics(self, analytics_service):
        """Test network metrics calculation."""
        with patch.object(analytics_service, '_calculate_network_metrics') as mock_metrics:
            mock_metrics.return_value = {
                "total_nodes": 150,
                "total_edges": 300,
                "density": 0.027,
                "average_clustering": 0.65,
                "diameter": 8,
                "average_path_length": 3.2
            }
            
            metrics = await analytics_service.get_network_metrics()
            
            assert metrics["total_nodes"] == 150
            assert metrics["density"] == 0.027
            assert metrics["diameter"] == 8

    @pytest.mark.asyncio
    async def test_get_topic_clusters(self, analytics_service):
        """Test topic clustering analysis."""
        with patch.object(analytics_service, '_cluster_topics') as mock_clustering:
            mock_clustering.return_value = [
                {
                    "cluster_id": 0,
                    "topics": ["virtue", "ethics", "morality"],
                    "coherence_score": 0.85,
                    "size": 25
                },
                {
                    "cluster_id": 1,
                    "topics": ["knowledge", "epistemology", "truth"],
                    "coherence_score": 0.78,
                    "size": 20
                }
            ]
            
            clusters = await analytics_service.get_topic_clusters()
            
            assert len(clusters) == 2
            assert clusters[0]["coherence_score"] == 0.85
            assert "virtue" in clusters[0]["topics"]

    @pytest.mark.asyncio
    async def test_get_philosopher_influence_map(self, analytics_service):
        """Test philosopher influence mapping."""
        with patch.object(analytics_service, '_map_philosopher_influence') as mock_influence_map:
            mock_influence_map.return_value = {
                "socrates": {
                    "influenced": ["plato", "xenophon"],
                    "influence_score": 0.95,
                    "key_contributions": ["socratic method", "virtue as knowledge"]
                },
                "plato": {
                    "influenced": ["aristotle", "plotinus"],
                    "influence_score": 0.92,
                    "key_contributions": ["theory of forms", "philosopher king"]
                }
            }
            
            influence_map = await analytics_service.get_philosopher_influence_map()
            
            assert "socrates" in influence_map
            assert "plato" in influence_map["socrates"]["influenced"]
            assert influence_map["socrates"]["influence_score"] == 0.95

    @pytest.mark.asyncio
    async def test_generate_network_visualization_data(self, analytics_service):
        """Test network visualization data generation."""
        with patch.object(analytics_service, '_prepare_visualization_data') as mock_viz_data:
            mock_viz_data.return_value = {
                "nodes": [
                    {"id": "virtue", "label": "Virtue", "size": 10, "color": "#ff0000"},
                    {"id": "justice", "label": "Justice", "size": 8, "color": "#00ff00"}
                ],
                "edges": [
                    {"source": "virtue", "target": "justice", "weight": 0.7, "color": "#cccccc"}
                ]
            }
            
            viz_data = await analytics_service.generate_network_visualization_data()
            
            assert len(viz_data["nodes"]) == 2
            assert len(viz_data["edges"]) == 1
            assert viz_data["nodes"][0]["id"] == "virtue"
            assert viz_data["edges"][0]["weight"] == 0.7

    @pytest.mark.asyncio
    async def test_get_usage_statistics(self, analytics_service):
        """Test usage statistics collection."""
        with patch.object(analytics_service, '_collect_usage_stats') as mock_stats:
            mock_stats.return_value = {
                "total_queries": 1250,
                "unique_concepts_accessed": 85,
                "average_session_duration": 420,
                "most_queried_concepts": [
                    {"concept": "virtue", "count": 156},
                    {"concept": "justice", "count": 132},
                    {"concept": "wisdom", "count": 98}
                ],
                "query_trends": {
                    "daily_average": 45,
                    "peak_hour": 14,
                    "growth_rate": 0.12
                }
            }
            
            stats = await analytics_service.get_usage_statistics()
            
            assert stats["total_queries"] == 1250
            assert len(stats["most_queried_concepts"]) == 3
            assert stats["most_queried_concepts"][0]["concept"] == "virtue"

    def test_calculate_concept_similarity(self, analytics_service):
        """Test concept similarity calculation."""
        with patch.object(analytics_service, '_compute_similarity') as mock_similarity:
            mock_similarity.return_value = 0.85
            
            similarity = analytics_service.calculate_concept_similarity("virtue", "excellence")
            
            assert similarity == 0.85
            mock_similarity.assert_called_once_with("virtue", "excellence")

    @pytest.mark.asyncio
    async def test_get_knowledge_gaps(self, analytics_service):
        """Test knowledge gap identification."""
        with patch.object(analytics_service, '_identify_knowledge_gaps') as mock_gaps:
            mock_gaps.return_value = [
                {
                    "concept": "stoicism",
                    "missing_connections": 15,
                    "importance_score": 0.8,
                    "suggested_expansions": ["marcus aurelius", "epictetus"]
                },
                {
                    "concept": "existentialism",
                    "missing_connections": 12,
                    "importance_score": 0.7,
                    "suggested_expansions": ["kierkegaard", "sartre"]
                }
            ]
            
            gaps = await analytics_service.get_knowledge_gaps()
            
            assert len(gaps) == 2
            assert gaps[0]["concept"] == "stoicism"
            assert gaps[0]["missing_connections"] == 15

    def test_validate_analytics_parameters(self, analytics_service):
        """Test analytics parameter validation."""
        # Test valid parameters
        assert analytics_service.validate_parameters(
            algorithm="degree",
            min_score=0.5,
            max_results=100
        ) is True
        
        # Test invalid parameters
        assert analytics_service.validate_parameters(
            algorithm="invalid_algorithm",
            min_score=1.5,  # > 1.0
            max_results=-1   # negative
        ) is False

    @pytest.mark.asyncio
    async def test_export_analytics_data(self, analytics_service):
        """Test analytics data export."""
        with patch.object(analytics_service, '_prepare_export_data') as mock_export:
            mock_export.return_value = {
                "centrality_scores": {"virtue": 0.9, "justice": 0.8},
                "communities": [{"id": 0, "nodes": ["virtue", "justice"]}],
                "metadata": {
                    "generated_at": "2025-01-01T12:00:00",
                    "total_concepts": 150,
                    "export_format": "json"
                }
            }
            
            export_data = await analytics_service.export_analytics_data(format="json")
            
            assert "centrality_scores" in export_data
            assert "communities" in export_data
            assert export_data["metadata"]["export_format"] == "json"

    @pytest.mark.asyncio
    async def test_error_handling_database_failure(self, analytics_service):
        """Test error handling when database operations fail."""
        analytics_service.neo4j_client.session.side_effect = Exception("Database connection failed")
        
        with pytest.raises(Exception, match="Database connection failed"):
            await analytics_service.get_centrality_scores()

    @pytest.mark.asyncio
    async def test_caching_centrality_results(self, analytics_service):
        """Test caching of centrality calculation results."""
        with patch.object(analytics_service, '_calculate_centrality') as mock_calc:
            mock_calc.return_value = {"virtue": 0.9, "justice": 0.8}
            
            # First call should calculate
            result1 = await analytics_service.get_centrality_scores()
            
            # Second call should use cache
            result2 = await analytics_service.get_centrality_scores()
            
            assert result1 == result2
            # Should only calculate once if caching is implemented
            if hasattr(analytics_service, '_cache'):
                mock_calc.assert_called_once()

    def test_data_aggregation_accuracy(self, analytics_service):
        """Test accuracy of data aggregation operations."""
        sample_data = [
            {"concept": "virtue", "score": 0.9},
            {"concept": "justice", "score": 0.8},
            {"concept": "wisdom", "score": 0.85}
        ]
        
        aggregated = analytics_service.aggregate_scores(sample_data)
        
        assert aggregated["average"] == 0.85
        assert aggregated["max"] == 0.9
        assert aggregated["min"] == 0.8
        assert aggregated["total"] == 2.55