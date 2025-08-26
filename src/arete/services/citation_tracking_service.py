"""
Citation Tracking and Provenance Service for Arete Graph-RAG system.

This service provides comprehensive citation tracking and provenance management:
- Track citation lineage and provenance through the processing pipeline
- Manage citation relationships and cross-references
- Maintain citation history and version tracking
- Provide citation network analysis and visualization data
- Support citation impact and usage analytics
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4
import json

from ..models.citation import Citation, CitationType, CitationContext
from ..models.document import Document
from ..models.chunk import Chunk
from .base import ServiceError

logger = logging.getLogger(__name__)


class CitationTrackingError(ServiceError):
    """Base exception for citation tracking service errors."""
    pass


class ProvenanceError(CitationTrackingError):
    """Exception for provenance tracking failures."""
    pass


class TrackingEventType(str, Enum):
    """Types of citation tracking events."""
    
    CREATED = "created"
    EXTRACTED = "extracted"
    VALIDATED = "validated"
    REFERENCED = "referenced"
    MODIFIED = "modified"
    LINKED = "linked"
    UNLINKED = "unlinked"


class CitationSource(str, Enum):
    """Sources from which citations can originate."""
    
    ORIGINAL_TEXT = "original_text"
    LLM_RESPONSE = "llm_response"
    USER_INPUT = "user_input"
    SYSTEM_GENERATED = "system_generated"
    CROSS_REFERENCE = "cross_reference"


@dataclass
class ProvenanceRecord:
    """A record of citation provenance and history."""
    
    id: UUID = field(default_factory=uuid4)
    citation_id: UUID = field(default_factory=uuid4)
    
    # Event information
    event_type: TrackingEventType = TrackingEventType.CREATED
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Source information
    source_type: CitationSource = CitationSource.ORIGINAL_TEXT
    source_id: Optional[UUID] = None
    source_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Processing information
    processor: str = ""  # Service or component that created/modified citation
    processing_version: str = ""
    confidence_score: float = 0.0
    
    # Change information
    previous_state: Optional[Dict[str, Any]] = None
    current_state: Dict[str, Any] = field(default_factory=dict)
    changes: List[str] = field(default_factory=list)
    
    # Context
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CitationRelationship:
    """A relationship between two citations."""
    
    id: UUID = field(default_factory=uuid4)
    source_citation_id: UUID = field(default_factory=uuid4)
    target_citation_id: UUID = field(default_factory=uuid4)
    
    # Relationship information
    relationship_type: str = ""  # supports, contradicts, elaborates, references, etc.
    strength: float = 1.0  # Relationship strength (0.0 to 1.0)
    confidence: float = 0.8  # Confidence in relationship accuracy
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = ""  # Service or user that created relationship
    
    # Validation
    is_validated: bool = False
    validation_source: str = ""


@dataclass
class CitationNetwork:
    """A network of related citations."""
    
    # Network nodes and edges
    citations: List[Citation] = field(default_factory=list)
    relationships: List[CitationRelationship] = field(default_factory=list)
    
    # Network metadata
    network_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Analysis results
    centrality_scores: Dict[UUID, float] = field(default_factory=dict)
    community_clusters: Dict[UUID, int] = field(default_factory=dict)
    
    # Statistics
    total_citations: int = 0
    total_relationships: int = 0
    density: float = 0.0


@dataclass
class CitationUsageStats:
    """Statistics about citation usage and impact."""
    
    citation_id: UUID = field(default_factory=uuid4)
    
    # Usage metrics
    reference_count: int = 0
    direct_quotes: int = 0
    paraphrases: int = 0
    
    # Quality metrics
    average_confidence: float = 0.0
    validation_rate: float = 0.0
    
    # Temporal data
    first_used: Optional[datetime] = None
    last_used: Optional[datetime] = None
    usage_frequency: Dict[str, int] = field(default_factory=dict)  # by time period
    
    # Context analysis
    contexts_used: Dict[CitationContext, int] = field(default_factory=dict)
    citation_types: Dict[CitationType, int] = field(default_factory=dict)


@dataclass
class CitationTrackingConfig:
    """Configuration for citation tracking operations."""
    
    # Tracking settings
    enable_provenance_tracking: bool = True
    enable_relationship_tracking: bool = True
    enable_usage_analytics: bool = True
    
    # Storage settings
    max_provenance_records: int = 1000
    provenance_retention_days: int = 365
    
    # Relationship detection
    enable_automatic_relationship_detection: bool = True
    similarity_threshold_for_relationships: float = 0.7
    max_relationships_per_citation: int = 50
    
    # Performance settings
    batch_size: int = 100
    enable_caching: bool = True
    cache_ttl: int = 3600


class CitationTrackingService:
    """
    Citation Tracking and Provenance Service for scholarly integrity.
    
    Maintains comprehensive tracking of citation origins, modifications, 
    relationships, and usage patterns to ensure scholarly accuracy and
    provide analytical insights.
    """
    
    def __init__(
        self,
        config: Optional[CitationTrackingConfig] = None
    ):
        """
        Initialize citation tracking service.
        
        Args:
            config: Tracking configuration
        """
        self.config = config or CitationTrackingConfig()
        
        # Storage for tracking data
        self._provenance_records: Dict[UUID, List[ProvenanceRecord]] = {}
        self._relationships: Dict[UUID, List[CitationRelationship]] = {}
        self._usage_stats: Dict[UUID, CitationUsageStats] = {}
        self._networks: Dict[UUID, CitationNetwork] = {}
        
        # Caching
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        
        logger.info("Initialized CitationTrackingService")
    
    def record_citation_event(
        self,
        citation: Citation,
        event_type: TrackingEventType,
        source_type: CitationSource = CitationSource.SYSTEM_GENERATED,
        processor: str = "",
        context: Optional[Dict[str, Any]] = None,
        previous_state: Optional[Citation] = None
    ) -> ProvenanceRecord:
        """
        Record a citation tracking event.
        
        Args:
            citation: Citation being tracked
            event_type: Type of event
            source_type: Source of the citation
            processor: Component that processed the citation
            context: Additional context information
            previous_state: Previous state of citation (for modifications)
            
        Returns:
            Created provenance record
        """
        try:
            # Create provenance record
            record = ProvenanceRecord(
                citation_id=citation.id,
                event_type=event_type,
                source_type=source_type,
                processor=processor,
                confidence_score=citation.confidence,
                current_state=citation.model_dump(),
                context=context or {}
            )
            
            # Add previous state if provided
            if previous_state:
                record.previous_state = previous_state.model_dump()
                record.changes = self._detect_changes(previous_state, citation)
            
            # Store record
            if citation.id not in self._provenance_records:
                self._provenance_records[citation.id] = []
            
            self._provenance_records[citation.id].append(record)
            
            # Maintain record limit
            if len(self._provenance_records[citation.id]) > self.config.max_provenance_records:
                self._provenance_records[citation.id] = \
                    self._provenance_records[citation.id][-self.config.max_provenance_records:]
            
            # Update usage stats
            self._update_usage_stats(citation, event_type)
            
            logger.debug(f"Recorded {event_type.value} event for citation {citation.id}")
            return record
            
        except Exception as e:
            logger.error(f"Failed to record citation event: {e}")
            raise CitationTrackingError(f"Event recording failed: {e}") from e
    
    def create_citation_relationship(
        self,
        source_citation: Citation,
        target_citation: Citation,
        relationship_type: str,
        strength: float = 1.0,
        confidence: float = 0.8,
        created_by: str = ""
    ) -> CitationRelationship:
        """
        Create a relationship between two citations.
        
        Args:
            source_citation: Source citation
            target_citation: Target citation
            relationship_type: Type of relationship
            strength: Relationship strength (0.0 to 1.0)
            confidence: Confidence in relationship
            created_by: Creator identifier
            
        Returns:
            Created relationship
        """
        try:
            relationship = CitationRelationship(
                source_citation_id=source_citation.id,
                target_citation_id=target_citation.id,
                relationship_type=relationship_type,
                strength=strength,
                confidence=confidence,
                created_by=created_by
            )
            
            # Store relationship for both citations
            for citation_id in [source_citation.id, target_citation.id]:
                if citation_id not in self._relationships:
                    self._relationships[citation_id] = []
                
                # Check if relationship already exists
                existing = any(
                    rel.source_citation_id == relationship.source_citation_id and
                    rel.target_citation_id == relationship.target_citation_id and
                    rel.relationship_type == relationship.relationship_type
                    for rel in self._relationships[citation_id]
                )
                
                if not existing:
                    self._relationships[citation_id].append(relationship)
            
            # Record tracking events
            self.record_citation_event(
                source_citation,
                TrackingEventType.LINKED,
                context={
                    "target_citation": str(target_citation.id),
                    "relationship_type": relationship_type
                }
            )
            
            logger.debug(
                f"Created {relationship_type} relationship between "
                f"{source_citation.id} and {target_citation.id}"
            )
            
            return relationship
            
        except Exception as e:
            logger.error(f"Failed to create citation relationship: {e}")
            raise CitationTrackingError(f"Relationship creation failed: {e}") from e
    
    def get_citation_provenance(
        self,
        citation_id: UUID,
        limit: Optional[int] = None
    ) -> List[ProvenanceRecord]:
        """
        Get provenance records for a citation.
        
        Args:
            citation_id: Citation ID
            limit: Maximum number of records to return
            
        Returns:
            List of provenance records, newest first
        """
        records = self._provenance_records.get(citation_id, [])
        
        # Sort by timestamp (newest first)
        records = sorted(records, key=lambda r: r.timestamp, reverse=True)
        
        if limit:
            records = records[:limit]
        
        return records
    
    def get_citation_relationships(
        self,
        citation_id: UUID,
        relationship_type: Optional[str] = None
    ) -> List[CitationRelationship]:
        """
        Get relationships for a citation.
        
        Args:
            citation_id: Citation ID
            relationship_type: Filter by relationship type
            
        Returns:
            List of citation relationships
        """
        relationships = self._relationships.get(citation_id, [])
        
        if relationship_type:
            relationships = [
                rel for rel in relationships
                if rel.relationship_type == relationship_type
            ]
        
        return relationships
    
    def build_citation_network(
        self,
        citations: List[Citation],
        include_automatic_relationships: bool = True
    ) -> CitationNetwork:
        """
        Build a citation network from a list of citations.
        
        Args:
            citations: Citations to include in network
            include_automatic_relationships: Whether to detect relationships automatically
            
        Returns:
            Citation network with relationships
        """
        try:
            network = CitationNetwork(citations=citations)
            
            # Collect all relationships for these citations
            citation_ids = {c.id for c in citations}
            all_relationships = []
            
            for citation_id in citation_ids:
                relationships = self.get_citation_relationships(citation_id)
                for rel in relationships:
                    # Include relationship if both citations are in the network
                    if (rel.source_citation_id in citation_ids and 
                        rel.target_citation_id in citation_ids):
                        all_relationships.append(rel)
            
            # Remove duplicates
            unique_relationships = []
            seen = set()
            for rel in all_relationships:
                key = (rel.source_citation_id, rel.target_citation_id, rel.relationship_type)
                if key not in seen:
                    seen.add(key)
                    unique_relationships.append(rel)
            
            network.relationships = unique_relationships
            
            # Detect additional relationships if enabled
            if include_automatic_relationships and self.config.enable_automatic_relationship_detection:
                auto_relationships = self._detect_automatic_relationships(citations)
                network.relationships.extend(auto_relationships)
            
            # Calculate network metrics
            network = self._calculate_network_metrics(network)
            
            # Store network
            self._networks[network.network_id] = network
            
            logger.info(
                f"Built citation network: {len(citations)} citations, "
                f"{len(network.relationships)} relationships"
            )
            
            return network
            
        except Exception as e:
            logger.error(f"Failed to build citation network: {e}")
            raise CitationTrackingError(f"Network building failed: {e}") from e
    
    def get_citation_usage_stats(self, citation_id: UUID) -> CitationUsageStats:
        """
        Get usage statistics for a citation.
        
        Args:
            citation_id: Citation ID
            
        Returns:
            Citation usage statistics
        """
        return self._usage_stats.get(citation_id, CitationUsageStats(citation_id=citation_id))
    
    def analyze_citation_impact(
        self,
        citation_id: UUID,
        time_window_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze the impact and influence of a citation.
        
        Args:
            citation_id: Citation ID
            time_window_days: Time window for analysis
            
        Returns:
            Impact analysis results
        """
        try:
            stats = self.get_citation_usage_stats(citation_id)
            relationships = self.get_citation_relationships(citation_id)
            
            # Calculate impact metrics
            impact_score = self._calculate_impact_score(citation_id, stats, relationships)
            influence_score = self._calculate_influence_score(citation_id, relationships)
            
            # Recent usage analysis
            recent_cutoff = datetime.now(timezone.utc) - timedelta(days=time_window_days)
            recent_usage = self._calculate_recent_usage(citation_id, recent_cutoff)
            
            analysis = {
                "citation_id": str(citation_id),
                "impact_score": impact_score,
                "influence_score": influence_score,
                "total_references": stats.reference_count,
                "relationship_count": len(relationships),
                "recent_usage": recent_usage,
                "quality_metrics": {
                    "average_confidence": stats.average_confidence,
                    "validation_rate": stats.validation_rate
                },
                "usage_distribution": {
                    "direct_quotes": stats.direct_quotes,
                    "paraphrases": stats.paraphrases,
                    "contexts": dict(stats.contexts_used)
                }
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze citation impact: {e}")
            raise CitationTrackingError(f"Impact analysis failed: {e}") from e
    
    def _detect_changes(self, old_citation: Citation, new_citation: Citation) -> List[str]:
        """Detect changes between citation versions."""
        changes = []
        
        # Compare key fields
        if old_citation.text != new_citation.text:
            changes.append("text")
        if old_citation.citation_type != new_citation.citation_type:
            changes.append("citation_type")
        if old_citation.context != new_citation.context:
            changes.append("context")
        if old_citation.source_reference != new_citation.source_reference:
            changes.append("source_reference")
        if old_citation.confidence != new_citation.confidence:
            changes.append("confidence")
        
        return changes
    
    def _update_usage_stats(self, citation: Citation, event_type: TrackingEventType) -> None:
        """Update usage statistics for a citation."""
        if citation.id not in self._usage_stats:
            self._usage_stats[citation.id] = CitationUsageStats(citation_id=citation.id)
        
        stats = self._usage_stats[citation.id]
        now = datetime.now(timezone.utc)
        
        # Update based on event type
        if event_type == TrackingEventType.REFERENCED:
            stats.reference_count += 1
            if not stats.first_used:
                stats.first_used = now
            stats.last_used = now
            
            # Count by citation type
            if citation.citation_type == CitationType.DIRECT_QUOTE:
                stats.direct_quotes += 1
            elif citation.citation_type == CitationType.PARAPHRASE:
                stats.paraphrases += 1
            
            # Count by context
            if citation.context not in stats.contexts_used:
                stats.contexts_used[citation.context] = 0
            stats.contexts_used[citation.context] += 1
            
            # Count by type
            if citation.citation_type not in stats.citation_types:
                stats.citation_types[citation.citation_type] = 0
            stats.citation_types[citation.citation_type] += 1
        
        # Update average confidence
        total_events = sum(stats.citation_types.values()) or 1
        stats.average_confidence = (
            (stats.average_confidence * (total_events - 1) + citation.confidence) / total_events
        )
    
    def _detect_automatic_relationships(
        self,
        citations: List[Citation]
    ) -> List[CitationRelationship]:
        """Detect automatic relationships between citations."""
        relationships = []
        
        # Compare all citation pairs
        for i, citation1 in enumerate(citations):
            for citation2 in citations[i+1:]:
                # Check for potential relationships
                similarity = self._calculate_citation_similarity(citation1, citation2)
                
                if similarity >= self.config.similarity_threshold_for_relationships:
                    # Determine relationship type
                    rel_type = self._determine_relationship_type(citation1, citation2)
                    
                    relationship = CitationRelationship(
                        source_citation_id=citation1.id,
                        target_citation_id=citation2.id,
                        relationship_type=rel_type,
                        strength=similarity,
                        confidence=0.7,  # Lower confidence for automatic detection
                        created_by="automatic_detection"
                    )
                    
                    relationships.append(relationship)
        
        return relationships
    
    def _calculate_citation_similarity(self, citation1: Citation, citation2: Citation) -> float:
        """Calculate similarity between two citations."""
        import difflib
        
        # Text similarity
        text_sim = difflib.SequenceMatcher(
            None, citation1.text.lower(), citation2.text.lower()
        ).ratio()
        
        # Source similarity
        source_sim = 0.0
        if (citation1.source_author == citation2.source_author and
            citation1.source_title == citation2.source_title):
            source_sim = 1.0
        
        # Combined similarity
        return (text_sim + source_sim) / 2
    
    def _determine_relationship_type(self, citation1: Citation, citation2: Citation) -> str:
        """Determine relationship type between citations."""
        # Simple heuristics for relationship type
        if citation1.source_author == citation2.source_author:
            if citation1.source_title == citation2.source_title:
                return "elaborates"
            else:
                return "supports"
        else:
            # Different authors - could be supporting or contrasting
            return "references"
    
    def _calculate_network_metrics(self, network: CitationNetwork) -> CitationNetwork:
        """Calculate network analysis metrics."""
        network.total_citations = len(network.citations)
        network.total_relationships = len(network.relationships)
        
        # Calculate density (actual edges / possible edges)
        if network.total_citations > 1:
            possible_edges = network.total_citations * (network.total_citations - 1)
            network.density = (network.total_relationships * 2) / possible_edges
        
        # Calculate centrality scores (simplified degree centrality)
        centrality = {}
        for citation in network.citations:
            degree = sum(
                1 for rel in network.relationships
                if rel.source_citation_id == citation.id or rel.target_citation_id == citation.id
            )
            centrality[citation.id] = degree / max(network.total_citations - 1, 1)
        
        network.centrality_scores = centrality
        
        return network
    
    def _calculate_impact_score(
        self,
        citation_id: UUID,
        stats: CitationUsageStats,
        relationships: List[CitationRelationship]
    ) -> float:
        """Calculate impact score for a citation."""
        # Base score from usage
        usage_score = min(stats.reference_count / 10.0, 1.0)
        
        # Boost from relationships
        relationship_score = min(len(relationships) / 5.0, 1.0)
        
        # Quality multiplier
        quality_multiplier = (stats.average_confidence + stats.validation_rate) / 2
        
        return (usage_score + relationship_score) / 2 * quality_multiplier
    
    def _calculate_influence_score(
        self,
        citation_id: UUID,
        relationships: List[CitationRelationship]
    ) -> float:
        """Calculate influence score based on relationships."""
        if not relationships:
            return 0.0
        
        # Weight different relationship types
        type_weights = {
            "supports": 1.0,
            "elaborates": 0.8,
            "references": 0.6,
            "contradicts": 0.4
        }
        
        total_influence = 0.0
        for rel in relationships:
            weight = type_weights.get(rel.relationship_type, 0.5)
            total_influence += weight * rel.strength * rel.confidence
        
        return min(total_influence / len(relationships), 1.0)
    
    def _calculate_recent_usage(
        self,
        citation_id: UUID,
        cutoff_date: datetime
    ) -> int:
        """Calculate recent usage count."""
        records = self.get_citation_provenance(citation_id)
        return sum(
            1 for record in records
            if record.timestamp >= cutoff_date and 
               record.event_type == TrackingEventType.REFERENCED
        )


# Factory function following established pattern
def create_citation_tracking_service(
    config: Optional[CitationTrackingConfig] = None
) -> CitationTrackingService:
    """
    Create citation tracking service with configuration.
    
    Args:
        config: Optional configuration
        
    Returns:
        Configured CitationTrackingService instance
    """
    return CitationTrackingService(config=config)