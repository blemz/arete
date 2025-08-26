"""
Tests for Citation Tracking Service.

This test suite validates the citation tracking and provenance functionality including:
- Citation event recording and provenance tracking
- Citation relationship creation and management
- Citation network building and analysis
- Usage statistics tracking and impact analysis
- Automatic relationship detection
- Network metrics calculation
"""

import pytest
from unittest.mock import Mock, patch
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from src.arete.services.citation_tracking_service import (
    CitationTrackingService,
    CitationTrackingConfig,
    ProvenanceRecord,
    CitationRelationship,
    CitationNetwork,
    CitationUsageStats,
    TrackingEventType,
    CitationSource,
    CitationTrackingError,
    ProvenanceError
)
from src.arete.models.citation import Citation, CitationType, CitationContext


class TestCitationTrackingService:
    """Test suite for CitationTrackingService."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return CitationTrackingConfig(
            enable_provenance_tracking=True,
            enable_relationship_tracking=True,
            enable_usage_analytics=True,
            max_provenance_records=100,
            similarity_threshold_for_relationships=0.7
        )
    
    @pytest.fixture
    def tracking_service(self, config):
        """Create citation tracking service instance."""
        return CitationTrackingService(config)
    
    @pytest.fixture
    def sample_citation(self):
        """Create sample citation for testing."""
        return Citation(
            id=uuid4(),
            text="The unexamined life is not worth living",
            citation_type=CitationType.DIRECT_QUOTE,
            context=CitationContext.ARGUMENT,
            document_id=uuid4(),
            source_title="Apology",
            source_author="Plato",
            source_reference="Apology 38a",
            confidence=0.9
        )
    
    @pytest.fixture
    def related_citation(self):
        """Create related citation for testing relationships."""
        return Citation(
            id=uuid4(),
            text="Know thyself",
            citation_type=CitationType.DIRECT_QUOTE,
            context=CitationContext.DEFINITION,
            document_id=uuid4(),
            source_title="Phaedrus",
            source_author="Plato",
            source_reference="Phaedrus 229e",
            confidence=0.8
        )
    
    def test_service_initialization(self, config):
        """Test service initialization with configuration."""
        service = CitationTrackingService(config)
        
        assert service.config == config
        assert isinstance(service._provenance_records, dict)
        assert isinstance(service._relationships, dict)
        assert isinstance(service._usage_stats, dict)
        assert isinstance(service._networks, dict)
    
    def test_service_initialization_default_config(self):
        """Test service initialization with default configuration."""
        service = CitationTrackingService()
        
        assert isinstance(service.config, CitationTrackingConfig)
        assert service.config.enable_provenance_tracking == True
        assert service.config.max_provenance_records == 1000
    
    def test_record_citation_event(self, tracking_service, sample_citation):
        """Test recording citation events."""
        record = tracking_service.record_citation_event(
            citation=sample_citation,
            event_type=TrackingEventType.CREATED,
            source_type=CitationSource.ORIGINAL_TEXT,
            processor="test_processor",
            context={"test": "context"}
        )
        
        assert isinstance(record, ProvenanceRecord)
        assert record.citation_id == sample_citation.id
        assert record.event_type == TrackingEventType.CREATED
        assert record.source_type == CitationSource.ORIGINAL_TEXT
        assert record.processor == "test_processor"
        assert record.context == {"test": "context"}
        assert record.confidence_score == sample_citation.confidence
    
    def test_provenance_record_storage(self, tracking_service, sample_citation):
        """Test that provenance records are stored correctly."""
        # Record multiple events
        tracking_service.record_citation_event(
            sample_citation, TrackingEventType.CREATED, CitationSource.ORIGINAL_TEXT
        )
        tracking_service.record_citation_event(
            sample_citation, TrackingEventType.VALIDATED, CitationSource.SYSTEM_GENERATED
        )
        
        # Retrieve records
        records = tracking_service.get_citation_provenance(sample_citation.id)
        
        assert len(records) == 2
        assert records[0].event_type in [TrackingEventType.CREATED, TrackingEventType.VALIDATED]
        assert records[1].event_type in [TrackingEventType.CREATED, TrackingEventType.VALIDATED]
        
        # Should be sorted by timestamp (newest first)
        assert records[0].timestamp >= records[1].timestamp
    
    def test_provenance_record_limit(self, tracking_service, sample_citation):
        """Test provenance record limit enforcement."""
        # Set low limit for testing
        tracking_service.config.max_provenance_records = 3
        
        # Record more events than the limit
        for i in range(5):
            tracking_service.record_citation_event(
                sample_citation, TrackingEventType.REFERENCED, CitationSource.LLM_RESPONSE
            )
        
        records = tracking_service.get_citation_provenance(sample_citation.id)
        
        # Should not exceed the limit
        assert len(records) <= 3
    
    def test_change_detection(self, tracking_service, sample_citation):
        """Test detection of changes between citation versions."""
        # Create modified citation
        modified_citation = Citation(
            id=sample_citation.id,
            text="Modified text",  # Changed
            citation_type=sample_citation.citation_type,
            context=sample_citation.context,
            document_id=sample_citation.document_id,
            source_title=sample_citation.source_title,
            source_author=sample_citation.source_author,
            source_reference="Modified reference",  # Changed
            confidence=0.8  # Changed
        )
        
        record = tracking_service.record_citation_event(
            citation=modified_citation,
            event_type=TrackingEventType.MODIFIED,
            previous_state=sample_citation
        )
        
        assert record.previous_state is not None
        assert len(record.changes) > 0
        assert "text" in record.changes
        assert "source_reference" in record.changes
        assert "confidence" in record.changes
    
    def test_usage_stats_tracking(self, tracking_service, sample_citation):
        """Test usage statistics tracking."""
        # Record usage events
        tracking_service.record_citation_event(
            sample_citation, TrackingEventType.REFERENCED, CitationSource.LLM_RESPONSE
        )
        tracking_service.record_citation_event(
            sample_citation, TrackingEventType.REFERENCED, CitationSource.USER_INPUT
        )
        
        stats = tracking_service.get_citation_usage_stats(sample_citation.id)
        
        assert isinstance(stats, CitationUsageStats)
        assert stats.citation_id == sample_citation.id
        assert stats.reference_count == 2
        assert stats.first_used is not None
        assert stats.last_used is not None
    
    def test_citation_relationship_creation(self, tracking_service, sample_citation, related_citation):
        """Test creation of citation relationships."""
        relationship = tracking_service.create_citation_relationship(
            source_citation=sample_citation,
            target_citation=related_citation,
            relationship_type="supports",
            strength=0.8,
            confidence=0.9,
            created_by="test_user"
        )
        
        assert isinstance(relationship, CitationRelationship)
        assert relationship.source_citation_id == sample_citation.id
        assert relationship.target_citation_id == related_citation.id
        assert relationship.relationship_type == "supports"
        assert relationship.strength == 0.8
        assert relationship.confidence == 0.9
        assert relationship.created_by == "test_user"
    
    def test_relationship_storage_and_retrieval(self, tracking_service, sample_citation, related_citation):
        """Test relationship storage and retrieval."""
        # Create relationship
        tracking_service.create_citation_relationship(
            sample_citation, related_citation, "elaborates"
        )
        
        # Retrieve relationships for source citation
        relationships = tracking_service.get_citation_relationships(sample_citation.id)
        
        assert len(relationships) > 0
        found_relationship = False
        for rel in relationships:
            if (rel.source_citation_id == sample_citation.id and
                rel.target_citation_id == related_citation.id and
                rel.relationship_type == "elaborates"):
                found_relationship = True
                break
        
        assert found_relationship
    
    def test_relationship_filtering(self, tracking_service, sample_citation, related_citation):
        """Test filtering relationships by type."""
        # Create different relationship types
        tracking_service.create_citation_relationship(
            sample_citation, related_citation, "supports"
        )
        tracking_service.create_citation_relationship(
            sample_citation, related_citation, "contradicts"
        )
        
        # Filter by type
        support_rels = tracking_service.get_citation_relationships(
            sample_citation.id, "supports"
        )
        contradict_rels = tracking_service.get_citation_relationships(
            sample_citation.id, "contradicts"
        )
        
        assert len(support_rels) >= 1
        assert len(contradict_rels) >= 1
        assert all(rel.relationship_type == "supports" for rel in support_rels)
        assert all(rel.relationship_type == "contradicts" for rel in contradict_rels)
    
    def test_citation_network_building(self, tracking_service, sample_citation, related_citation):
        """Test building citation networks."""
        citations = [sample_citation, related_citation]
        
        # Create some relationships first
        tracking_service.create_citation_relationship(
            sample_citation, related_citation, "supports"
        )
        
        network = tracking_service.build_citation_network(citations)
        
        assert isinstance(network, CitationNetwork)
        assert len(network.citations) == 2
        assert len(network.relationships) >= 1
        assert network.total_citations == 2
        assert network.total_relationships >= 1
        assert 0.0 <= network.density <= 1.0
    
    def test_automatic_relationship_detection(self, tracking_service):
        """Test automatic relationship detection."""
        # Create similar citations
        citation1 = Citation(
            id=uuid4(),
            text="Justice is giving each their due",
            citation_type=CitationType.PARAPHRASE,
            context=CitationContext.DEFINITION,
            document_id=uuid4(),
            source_title="Republic",
            source_author="Plato",
            source_reference="Republic 433e",
            confidence=0.8
        )
        
        citation2 = Citation(
            id=uuid4(),
            text="Justice consists in giving each person their due",
            citation_type=CitationType.PARAPHRASE,
            context=CitationContext.DEFINITION,
            document_id=uuid4(),
            source_title="Republic",
            source_author="Plato",
            source_reference="Republic 434a",
            confidence=0.8
        )
        
        network = tracking_service.build_citation_network(
            [citation1, citation2],
            include_automatic_relationships=True
        )
        
        # Should detect similarity and create automatic relationships
        if tracking_service.config.enable_automatic_relationship_detection:
            assert len(network.relationships) > 0
            auto_rels = [rel for rel in network.relationships if rel.created_by == "automatic_detection"]
            assert len(auto_rels) > 0
    
    def test_network_metrics_calculation(self, tracking_service, sample_citation, related_citation):
        """Test network metrics calculation."""
        # Create third citation for more interesting network
        third_citation = Citation(
            id=uuid4(),
            text="Virtue is knowledge",
            citation_type=CitationType.REFERENCE,
            context=CitationContext.ARGUMENT,
            document_id=uuid4(),
            source_title="Meno",
            source_author="Plato",
            source_reference="Meno 87c",
            confidence=0.8
        )
        
        citations = [sample_citation, related_citation, third_citation]
        
        # Create relationships
        tracking_service.create_citation_relationship(
            sample_citation, related_citation, "supports"
        )
        tracking_service.create_citation_relationship(
            related_citation, third_citation, "elaborates"
        )
        
        network = tracking_service.build_citation_network(citations)
        
        # Check metrics
        assert network.total_citations == 3
        assert network.total_relationships >= 2
        assert network.density > 0.0
        assert len(network.centrality_scores) == 3
        
        # All centrality scores should be between 0 and 1
        for score in network.centrality_scores.values():
            assert 0.0 <= score <= 1.0
    
    def test_citation_impact_analysis(self, tracking_service, sample_citation):
        """Test citation impact analysis."""
        # Create usage history
        for _ in range(5):
            tracking_service.record_citation_event(
                sample_citation, TrackingEventType.REFERENCED, CitationSource.LLM_RESPONSE
            )
        
        # Create relationships
        related_citation = Citation(
            id=uuid4(),
            text="Related quote",
            citation_type=CitationType.REFERENCE,
            context=CitationContext.ARGUMENT,
            document_id=uuid4(),
            source_title="Test",
            source_author="Test",
            confidence=0.8
        )
        
        tracking_service.create_citation_relationship(
            sample_citation, related_citation, "supports"
        )
        
        analysis = tracking_service.analyze_citation_impact(sample_citation.id)
        
        assert isinstance(analysis, dict)
        assert "citation_id" in analysis
        assert "impact_score" in analysis
        assert "influence_score" in analysis
        assert "total_references" in analysis
        assert "relationship_count" in analysis
        
        # Scores should be between 0 and 1
        assert 0.0 <= analysis["impact_score"] <= 1.0
        assert 0.0 <= analysis["influence_score"] <= 1.0
        
        # Should reflect usage
        assert analysis["total_references"] == 5
        assert analysis["relationship_count"] >= 1
    
    def test_recent_usage_calculation(self, tracking_service, sample_citation):
        """Test recent usage calculation in impact analysis."""
        # Record recent and old usage
        tracking_service.record_citation_event(
            sample_citation, TrackingEventType.REFERENCED, CitationSource.LLM_RESPONSE
        )
        
        # Analyze with short time window
        analysis = tracking_service.analyze_citation_impact(
            sample_citation.id, time_window_days=1
        )
        
        assert "recent_usage" in analysis
        assert analysis["recent_usage"] >= 1
    
    def test_citation_similarity_calculation(self, tracking_service):
        """Test citation similarity calculation."""
        citation1 = Citation(
            id=uuid4(),
            text="The good life requires virtue",
            citation_type=CitationType.PARAPHRASE,
            context=CitationContext.ARGUMENT,
            document_id=uuid4(),
            source_title="Ethics",
            source_author="Aristotle",
            confidence=0.8
        )
        
        citation2 = Citation(
            id=uuid4(),
            text="A virtuous life is the good life",
            citation_type=CitationType.PARAPHRASE,
            context=CitationContext.ARGUMENT,
            document_id=uuid4(),
            source_title="Ethics",
            source_author="Aristotle",
            confidence=0.8
        )
        
        similarity = tracking_service._calculate_citation_similarity(citation1, citation2)
        
        # Should be high similarity due to similar text and same source
        assert 0.0 <= similarity <= 1.0
        assert similarity > 0.5  # Should be reasonably similar
    
    def test_relationship_type_determination(self, tracking_service):
        """Test automatic relationship type determination."""
        same_author_citation1 = Citation(
            id=uuid4(),
            text="Text 1",
            citation_type=CitationType.REFERENCE,
            context=CitationContext.ARGUMENT,
            document_id=uuid4(),
            source_title="Work A",
            source_author="Plato",
            confidence=0.8
        )
        
        same_author_citation2 = Citation(
            id=uuid4(),
            text="Text 2",
            citation_type=CitationType.REFERENCE,
            context=CitationContext.ARGUMENT,
            document_id=uuid4(),
            source_title="Work B",
            source_author="Plato",
            confidence=0.8
        )
        
        rel_type = tracking_service._determine_relationship_type(
            same_author_citation1, same_author_citation2
        )
        
        assert rel_type == "supports"  # Same author, different works
    
    def test_impact_score_calculation(self, tracking_service, sample_citation):
        """Test impact score calculation components."""
        # Create usage stats
        stats = CitationUsageStats(
            citation_id=sample_citation.id,
            reference_count=10,
            average_confidence=0.9,
            validation_rate=0.8
        )
        
        # Create relationships
        relationships = [
            CitationRelationship(
                source_citation_id=sample_citation.id,
                target_citation_id=uuid4(),
                relationship_type="supports",
                strength=0.8,
                confidence=0.9
            )
        ]
        
        impact_score = tracking_service._calculate_impact_score(
            sample_citation.id, stats, relationships
        )
        
        assert 0.0 <= impact_score <= 1.0
    
    def test_influence_score_calculation(self, tracking_service, sample_citation):
        """Test influence score calculation."""
        relationships = [
            CitationRelationship(
                source_citation_id=sample_citation.id,
                target_citation_id=uuid4(),
                relationship_type="supports",
                strength=0.9,
                confidence=0.8
            ),
            CitationRelationship(
                source_citation_id=sample_citation.id,
                target_citation_id=uuid4(),
                relationship_type="elaborates",
                strength=0.7,
                confidence=0.9
            )
        ]
        
        influence_score = tracking_service._calculate_influence_score(
            sample_citation.id, relationships
        )
        
        assert 0.0 <= influence_score <= 1.0
        assert influence_score > 0.0  # Should have some influence with relationships
    
    def test_empty_citation_list_network(self, tracking_service):
        """Test network building with empty citation list."""
        network = tracking_service.build_citation_network([])
        
        assert isinstance(network, CitationNetwork)
        assert len(network.citations) == 0
        assert len(network.relationships) == 0
        assert network.total_citations == 0
        assert network.total_relationships == 0
        assert network.density == 0.0
    
    def test_single_citation_network(self, tracking_service, sample_citation):
        """Test network building with single citation."""
        network = tracking_service.build_citation_network([sample_citation])
        
        assert len(network.citations) == 1
        assert network.total_citations == 1
        assert network.density == 0.0  # No possible edges with single node
        assert sample_citation.id in network.centrality_scores
        assert network.centrality_scores[sample_citation.id] == 0.0


class TestCitationTrackingConfig:
    """Test suite for CitationTrackingConfig."""
    
    def test_default_configuration(self):
        """Test default configuration values."""
        config = CitationTrackingConfig()
        
        assert config.enable_provenance_tracking == True
        assert config.enable_relationship_tracking == True
        assert config.enable_usage_analytics == True
        assert config.max_provenance_records == 1000
        assert config.provenance_retention_days == 365
        assert config.similarity_threshold_for_relationships == 0.7
    
    def test_custom_configuration(self):
        """Test custom configuration values."""
        config = CitationTrackingConfig(
            max_provenance_records=500,
            similarity_threshold_for_relationships=0.8,
            enable_automatic_relationship_detection=False
        )
        
        assert config.max_provenance_records == 500
        assert config.similarity_threshold_for_relationships == 0.8
        assert config.enable_automatic_relationship_detection == False


class TestProvenanceRecord:
    """Test suite for ProvenanceRecord dataclass."""
    
    def test_provenance_record_creation(self):
        """Test creation of ProvenanceRecord objects."""
        citation_id = uuid4()
        record = ProvenanceRecord(
            citation_id=citation_id,
            event_type=TrackingEventType.CREATED,
            source_type=CitationSource.ORIGINAL_TEXT,
            processor="test_processor",
            confidence_score=0.9
        )
        
        assert record.citation_id == citation_id
        assert record.event_type == TrackingEventType.CREATED
        assert record.source_type == CitationSource.ORIGINAL_TEXT
        assert record.processor == "test_processor"
        assert record.confidence_score == 0.9
        assert isinstance(record.timestamp, datetime)
        assert len(record.changes) == 0


class TestCitationRelationship:
    """Test suite for CitationRelationship dataclass."""
    
    def test_citation_relationship_creation(self):
        """Test creation of CitationRelationship objects."""
        source_id = uuid4()
        target_id = uuid4()
        
        relationship = CitationRelationship(
            source_citation_id=source_id,
            target_citation_id=target_id,
            relationship_type="supports",
            strength=0.8,
            confidence=0.9,
            created_by="test_user"
        )
        
        assert relationship.source_citation_id == source_id
        assert relationship.target_citation_id == target_id
        assert relationship.relationship_type == "supports"
        assert relationship.strength == 0.8
        assert relationship.confidence == 0.9
        assert relationship.created_by == "test_user"
        assert relationship.is_validated == False


class TestCitationUsageStats:
    """Test suite for CitationUsageStats dataclass."""
    
    def test_usage_stats_creation(self):
        """Test creation of CitationUsageStats objects."""
        citation_id = uuid4()
        stats = CitationUsageStats(
            citation_id=citation_id,
            reference_count=5,
            direct_quotes=2,
            paraphrases=3,
            average_confidence=0.85
        )
        
        assert stats.citation_id == citation_id
        assert stats.reference_count == 5
        assert stats.direct_quotes == 2
        assert stats.paraphrases == 3
        assert stats.average_confidence == 0.85
        assert stats.first_used is None  # Default
        assert len(stats.contexts_used) == 0  # Default empty


class TestTrackingErrors:
    """Test suite for citation tracking error handling."""
    
    def test_citation_tracking_error(self):
        """Test CitationTrackingError exception."""
        with pytest.raises(CitationTrackingError):
            raise CitationTrackingError("Test tracking error")
    
    def test_provenance_error(self):
        """Test ProvenanceError exception."""
        with pytest.raises(ProvenanceError):
            raise ProvenanceError("Test provenance error")
    
    def test_error_handling_in_tracking(self, tracking_service):
        """Test error handling during tracking operations."""
        # Create citation with potential issues
        problematic_citation = Citation(
            id=uuid4(),
            text="Test",
            citation_type=CitationType.REFERENCE,
            context=CitationContext.EXPLANATION,
            document_id=uuid4(),
            source_title="Test",
            source_author="Test",
            confidence=0.5
        )
        
        # Should not raise exception
        record = tracking_service.record_citation_event(
            problematic_citation, TrackingEventType.CREATED
        )
        
        assert isinstance(record, ProvenanceRecord)
        assert record.citation_id == problematic_citation.id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])