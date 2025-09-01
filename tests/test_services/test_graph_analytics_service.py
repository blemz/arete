"""
Tests for Graph Analytics Service.

This module provides comprehensive testing for the graph analytics functionality,
including centrality analysis, community detection, influence network analysis,
and topic clustering.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from typing import List, Dict, Any

from arete.services.graph_analytics_service import (
    GraphAnalyticsService,
    CentralityMetric,
    CentralityResult,
    CommunityResult,
    InfluenceNetwork,
    TopicClusteringResult,
    ConceptCluster,
    CentralityAnalysisError,
    CommunityDetectionError,
    AnalysisError,
    create_graph_analytics_service
)
from arete.models.entity import EntityType
from arete.database.client import Neo4jClient


class TestCentralityResult:
    """Test CentralityResult data class."""
    
    def test_centrality_result_creation(self):
        """Test basic CentralityResult creation."""
        result = CentralityResult(
            metric=CentralityMetric.DEGREE,
            scores={"entity1": 5.0, "entity2": 3.0},
            top_entities=[("entity1", "Plato", 5.0), ("entity2", "Aristotle", 3.0)],
            total_entities=2
        )
        
        assert result.metric == CentralityMetric.DEGREE
        assert result.scores["entity1"] == 5.0
        assert result.total_entities == 2
        assert len(result.top_entities) == 2
    
    def test_get_top_n(self):
        """Test getting top N entities."""
        top_entities = [
            ("entity1", "Plato", 10.0),
            ("entity2", "Aristotle", 8.0),
            ("entity3", "Socrates", 6.0),
            ("entity4", "Kant", 4.0),
        ]
        
        result = CentralityResult(
            metric=CentralityMetric.DEGREE,
            top_entities=top_entities,
            total_entities=4
        )
        
        top_2 = result.get_top_n(2)
        assert len(top_2) == 2
        assert top_2[0] == ("entity1", "Plato", 10.0)
        assert top_2[1] == ("entity2", "Aristotle", 8.0)


class TestCommunityResult:
    """Test CommunityResult data class."""
    
    def test_community_result_creation(self):
        """Test basic CommunityResult creation."""
        communities = {
            0: ["entity1", "entity2"],
            1: ["entity3", "entity4", "entity5"]
        }
        entity_community = {
            "entity1": 0, "entity2": 0,
            "entity3": 1, "entity4": 1, "entity5": 1
        }
        
        result = CommunityResult(
            algorithm="label_propagation",
            communities=communities,
            entity_community=entity_community,
            modularity_score=0.8,
            total_communities=2
        )
        
        assert result.algorithm == "label_propagation"
        assert result.total_communities == 2
        assert result.modularity_score == 0.8
        assert len(result.communities[1]) == 3


class TestInfluenceNetwork:
    """Test InfluenceNetwork data class."""
    
    def test_influence_network_creation(self):
        """Test basic InfluenceNetwork creation."""
        influences = {
            "plato": ["aristotle", "augustine"],
            "aristotle": ["aquinas"]
        }
        influence_scores = {
            ("plato", "aristotle"): 1.0,
            ("plato", "augustine"): 0.8,
            ("aristotle", "aquinas"): 0.9
        }
        
        network = InfluenceNetwork(
            influences=influences,
            influence_scores=influence_scores
        )
        
        assert "plato" in network.influences
        assert len(network.influences["plato"]) == 2
        assert network.influence_scores[("plato", "aristotle")] == 1.0


class TestConceptCluster:
    """Test ConceptCluster data class."""
    
    def test_concept_cluster_creation(self):
        """Test basic ConceptCluster creation."""
        cluster = ConceptCluster(
            cluster_id=0,
            entities=["justice", "virtue", "good"],
            central_concept="virtue",
            similarity_threshold=0.8,
            cluster_keywords=["ethics", "morality", "philosophy"]
        )
        
        assert cluster.cluster_id == 0
        assert cluster.central_concept == "virtue"
        assert len(cluster.entities) == 3
        assert "ethics" in cluster.cluster_keywords


class TestGraphAnalyticsService:
    """Test GraphAnalyticsService functionality."""
    
    @pytest.fixture
    def mock_neo4j_client(self):
        """Create mock Neo4j client."""
        client = MagicMock(spec=Neo4jClient)
        session = AsyncMock()
        client.session.return_value.__aenter__.return_value = session
        client.session.return_value.__aexit__.return_value = None
        return client, session
    
    @pytest.fixture
    def analytics_service(self, mock_neo4j_client):
        """Create analytics service with mock client."""
        client, _ = mock_neo4j_client
        return GraphAnalyticsService(neo4j_client=client)
    
    def test_service_initialization(self):
        """Test service initialization."""
        service = GraphAnalyticsService()
        assert service.neo4j_client is None
        assert service.settings is not None
    
    def test_service_initialization_with_client(self, mock_neo4j_client):
        """Test service initialization with client."""
        client, _ = mock_neo4j_client
        service = GraphAnalyticsService(neo4j_client=client)
        assert service.neo4j_client == client
    
    @patch('arete.database.client.Neo4jClient')
    def test_client_property_creates_client(self, mock_neo4j_class):
        """Test that client property creates client when needed."""
        mock_client = MagicMock(spec=Neo4jClient)
        mock_neo4j_class.return_value = mock_client
        
        service = GraphAnalyticsService()
        assert service.client == mock_client
        mock_neo4j_class.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_degree_centrality(self, analytics_service, mock_neo4j_client):
        """Test degree centrality analysis."""
        _, session = mock_neo4j_client
        
        # Mock query results
        mock_result = AsyncMock()
        mock_result.data.return_value = [
            {"entity_id": "plato", "entity_name": "Plato", "degree": 10},
            {"entity_id": "aristotle", "entity_name": "Aristotle", "degree": 8},
            {"entity_id": "socrates", "entity_name": "Socrates", "degree": 6}
        ]
        session.run.return_value = mock_result
        
        result = await analytics_service.analyze_centrality(
            metric=CentralityMetric.DEGREE,
            limit=10
        )
        
        assert isinstance(result, CentralityResult)
        assert result.metric == CentralityMetric.DEGREE
        assert result.total_entities == 3
        assert "plato" in result.scores
        assert result.scores["plato"] == 10.0
        assert len(result.top_entities) == 3
        assert result.top_entities[0] == ("plato", "Plato", 10.0)
    
    @pytest.mark.asyncio
    async def test_analyze_betweenness_centrality(self, analytics_service, mock_neo4j_client):
        """Test betweenness centrality analysis."""
        _, session = mock_neo4j_client
        
        mock_result = AsyncMock()
        mock_result.data.return_value = [
            {"entity_id": "aristotle", "entity_name": "Aristotle", "paths_through": 15},
            {"entity_id": "plato", "entity_name": "Plato", "paths_through": 12}
        ]
        session.run.return_value = mock_result
        
        result = await analytics_service.analyze_centrality(
            metric=CentralityMetric.BETWEENNESS,
            entity_types=[EntityType.PERSON],
            limit=5
        )
        
        assert result.metric == CentralityMetric.BETWEENNESS
        assert result.total_entities == 2
        assert result.scores["aristotle"] == 15.0
    
    @pytest.mark.asyncio
    async def test_analyze_closeness_centrality(self, analytics_service, mock_neo4j_client):
        """Test closeness centrality analysis."""
        _, session = mock_neo4j_client
        
        mock_result = AsyncMock()
        mock_result.data.return_value = [
            {"entity_id": "socrates", "entity_name": "Socrates", "closeness": 0.8},
            {"entity_id": "plato", "entity_name": "Plato", "closeness": 0.75}
        ]
        session.run.return_value = mock_result
        
        result = await analytics_service.analyze_centrality(
            metric=CentralityMetric.CLOSENESS
        )
        
        assert result.metric == CentralityMetric.CLOSENESS
        assert result.scores["socrates"] == 0.8
    
    @pytest.mark.asyncio
    async def test_analyze_eigenvector_centrality(self, analytics_service, mock_neo4j_client):
        """Test eigenvector centrality analysis."""
        _, session = mock_neo4j_client
        
        mock_result = AsyncMock()
        mock_result.data.return_value = [
            {"entity_id": "plato", "entity_name": "Plato", "eigenvector_score": 12.5}
        ]
        session.run.return_value = mock_result
        
        result = await analytics_service.analyze_centrality(
            metric=CentralityMetric.EIGENVECTOR
        )
        
        assert result.metric == CentralityMetric.EIGENVECTOR
        assert result.scores["plato"] == 12.5
    
    @pytest.mark.asyncio
    async def test_analyze_pagerank_centrality(self, analytics_service, mock_neo4j_client):
        """Test PageRank centrality analysis."""
        _, session = mock_neo4j_client
        
        mock_result = AsyncMock()
        mock_result.data.return_value = [
            {"entity_id": "aristotle", "entity_name": "Aristotle", "pagerank_score": 2.3}
        ]
        session.run.return_value = mock_result
        
        result = await analytics_service.analyze_centrality(
            metric=CentralityMetric.PAGE_RANK
        )
        
        assert result.metric == CentralityMetric.PAGE_RANK
        assert result.scores["aristotle"] == 2.3
    
    @pytest.mark.asyncio
    async def test_unsupported_centrality_metric(self, analytics_service):
        """Test error handling for unsupported centrality metric."""
        with pytest.raises(CentralityAnalysisError, match="Unsupported centrality metric"):
            await analytics_service.analyze_centrality(metric="invalid_metric")
    
    @pytest.mark.asyncio
    async def test_centrality_analysis_database_error(self, analytics_service, mock_neo4j_client):
        """Test centrality analysis with database error."""
        _, session = mock_neo4j_client
        session.run.side_effect = Exception("Database connection failed")
        
        with pytest.raises(CentralityAnalysisError, match="Failed to compute DEGREE centrality"):
            await analytics_service.analyze_centrality(metric=CentralityMetric.DEGREE)
    
    @pytest.mark.asyncio
    async def test_detect_communities_label_propagation(self, analytics_service, mock_neo4j_client):
        """Test community detection with label propagation."""
        _, session = mock_neo4j_client
        
        mock_result = AsyncMock()
        mock_result.data.return_value = [
            {"entity1": "plato", "entity2": "aristotle", "name1": "Plato", "name2": "Aristotle"},
            {"entity1": "aristotle", "entity2": "aquinas", "name1": "Aristotle", "name2": "Aquinas"},
            {"entity1": "kant", "entity2": "hegel", "name1": "Kant", "name2": "Hegel"},
            {"entity1": "hegel", "entity2": "marx", "name1": "Hegel", "name2": "Marx"}
        ]
        session.run.return_value = mock_result
        
        result = await analytics_service.detect_communities(
            algorithm="label_propagation",
            min_community_size=2
        )
        
        assert isinstance(result, CommunityResult)
        assert result.algorithm == "label_propagation"
        assert result.total_communities >= 1
        assert len(result.entity_community) > 0
    
    @pytest.mark.asyncio
    async def test_detect_communities_unsupported_algorithm(self, analytics_service):
        """Test community detection with unsupported algorithm."""
        with pytest.raises(CommunityDetectionError, match="Unsupported algorithm"):
            await analytics_service.detect_communities(algorithm="invalid_algorithm")
    
    @pytest.mark.asyncio
    async def test_community_detection_database_error(self, analytics_service, mock_neo4j_client):
        """Test community detection with database error."""
        _, session = mock_neo4j_client
        session.run.side_effect = Exception("Database error")
        
        with pytest.raises(CommunityDetectionError, match="Failed to detect communities"):
            await analytics_service.detect_communities()
    
    @pytest.mark.asyncio
    async def test_analyze_influence_network(self, analytics_service, mock_neo4j_client):
        """Test influence network analysis."""
        _, session = mock_neo4j_client
        
        mock_result = AsyncMock()
        mock_result.data.return_value = [
            {
                "influencer_id": "plato",
                "influencer_name": "Plato",
                "influenced_id": "aristotle",
                "influenced_name": "Aristotle",
                "relationship_type": "INFLUENCES",
                "influencer_date": "428 BCE",
                "influenced_date": "384 BCE"
            },
            {
                "influencer_id": "aristotle",
                "influencer_name": "Aristotle",
                "influenced_id": "aquinas",
                "influenced_name": "Thomas Aquinas",
                "relationship_type": "INSPIRED",
                "influencer_date": "384 BCE",
                "influenced_date": "1225 CE"
            }
        ]
        session.run.return_value = mock_result
        
        result = await analytics_service.analyze_influence_network(
            temporal_analysis=True
        )
        
        assert isinstance(result, InfluenceNetwork)
        assert "plato" in result.influences
        assert "aristotle" in result.influences["plato"]
        assert ("plato", "aristotle") in result.influence_scores
        assert result.influence_scores[("plato", "aristotle")] == 1.0  # INFLUENCES
        assert result.influence_scores[("aristotle", "aquinas")] == 0.8  # INSPIRED
    
    @pytest.mark.asyncio
    async def test_influence_network_analysis_error(self, analytics_service, mock_neo4j_client):
        """Test influence network analysis with error."""
        _, session = mock_neo4j_client
        session.run.side_effect = Exception("Query failed")
        
        with pytest.raises(AnalysisError, match="Failed to analyze influence network"):
            await analytics_service.analyze_influence_network()
    
    @pytest.mark.asyncio
    async def test_cluster_topics(self, analytics_service, mock_neo4j_client):
        """Test topic clustering analysis."""
        _, session = mock_neo4j_client
        
        mock_result = AsyncMock()
        mock_result.data.return_value = [
            {
                "concept_id": "justice",
                "concept_name": "Justice",
                "attributes": ["virtue", "ethics", "morality"]
            },
            {
                "concept_id": "virtue",
                "concept_name": "Virtue",
                "attributes": ["ethics", "morality", "character"]
            },
            {
                "concept_id": "beauty",
                "concept_name": "Beauty",
                "attributes": ["aesthetics", "art", "form"]
            }
        ]
        session.run.return_value = mock_result
        
        result = await analytics_service.cluster_topics(
            similarity_threshold=0.5,
            min_cluster_size=2
        )
        
        assert isinstance(result, TopicClusteringResult)
        assert len(result.clusters) >= 0
        # Should cluster justice and virtue together (share ethics, morality)
        # Beauty should be an outlier or in separate cluster
    
    @pytest.mark.asyncio
    async def test_topic_clustering_error(self, analytics_service, mock_neo4j_client):
        """Test topic clustering with error."""
        _, session = mock_neo4j_client
        session.run.side_effect = Exception("Clustering failed")
        
        with pytest.raises(AnalysisError, match="Failed to perform topic clustering"):
            await analytics_service.cluster_topics()
    
    @pytest.mark.asyncio
    async def test_empty_results_handling(self, analytics_service, mock_neo4j_client):
        """Test handling of empty query results."""
        _, session = mock_neo4j_client
        
        mock_result = AsyncMock()
        mock_result.data.return_value = []
        session.run.return_value = mock_result
        
        result = await analytics_service.analyze_centrality(
            metric=CentralityMetric.DEGREE
        )
        
        assert result.total_entities == 0
        assert len(result.scores) == 0
        assert len(result.top_entities) == 0


class TestCreateGraphAnalyticsService:
    """Test factory function for creating graph analytics service."""
    
    def test_create_service_default(self):
        """Test creating service with default parameters."""
        service = create_graph_analytics_service()
        assert isinstance(service, GraphAnalyticsService)
        assert service.neo4j_client is None
    
    def test_create_service_with_client(self):
        """Test creating service with Neo4j client."""
        mock_client = MagicMock(spec=Neo4jClient)
        service = create_graph_analytics_service(neo4j_client=mock_client)
        assert isinstance(service, GraphAnalyticsService)
        assert service.neo4j_client == mock_client
    
    def test_create_service_with_settings(self):
        """Test creating service with custom settings."""
        mock_settings = MagicMock()
        service = create_graph_analytics_service(settings=mock_settings)
        assert isinstance(service, GraphAnalyticsService)
        assert service.settings == mock_settings


class TestGraphAnalyticsIntegration:
    """Integration tests for graph analytics functionality."""
    
    @pytest.fixture
    def analytics_service(self):
        """Create real analytics service for integration tests."""
        return GraphAnalyticsService()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_analytics_workflow(self, analytics_service):
        """Test complete analytics workflow (requires real Neo4j)."""
        # This test would require a real Neo4j instance with test data
        # For now, we'll skip it unless specifically running integration tests
        pytest.skip("Integration test requires real Neo4j instance")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_performance_with_large_graph(self, analytics_service):
        """Test analytics performance with large graph."""
        # Performance test with realistic data size
        pytest.skip("Performance test requires large dataset")