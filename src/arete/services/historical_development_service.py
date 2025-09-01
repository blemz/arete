"""
Historical Development Tracking Service for Arete Graph-RAG System.

This service provides comprehensive tracking and analysis of historical development
patterns in philosophical thought, including:
- Timeline construction for concepts and thinkers
- Evolutionary tracking of ideas across time periods
- Historical influence pattern analysis
- Chronological relationship mapping
- Period-based clustering and analysis

The service integrates with Neo4j to analyze temporal patterns in the
philosophical knowledge graph, providing insights for educational content
and research analysis.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from collections import defaultdict, Counter
import re

from neo4j import AsyncSession
from pydantic import BaseModel, Field, ConfigDict

from arete.config import get_settings
from arete.database.client import Neo4jClient
from arete.models.entity import Entity, EntityType

logger = logging.getLogger(__name__)

class TimePeriod(str, Enum):
    """Historical time periods for philosophical analysis."""
    ANCIENT = "ancient"  # Before 500 CE
    MEDIEVAL = "medieval"  # 500-1500 CE
    RENAISSANCE = "renaissance"  # 1500-1650 CE
    MODERN = "modern"  # 1650-1800 CE
    CONTEMPORARY = "contemporary"  # 1800-1950 CE
    CURRENT = "current"  # 1950-present

class HistoricalAnalysisError(Exception):
    """Base exception for historical analysis errors."""
    pass

class TimelineConstructionError(HistoricalAnalysisError):
    """Exception raised during timeline construction."""
    pass

@dataclass
class HistoricalEvent:
    """Represents a historical event in philosophical development."""
    entity_id: str
    entity_name: str
    entity_type: EntityType
    date: Optional[datetime] = None
    date_string: Optional[str] = None  # Original date string
    period: Optional[TimePeriod] = None
    description: Optional[str] = None
    related_entities: List[str] = field(default_factory=list)
    confidence_score: float = 1.0  # Confidence in date accuracy

@dataclass
class ConceptEvolution:
    """Tracks the evolution of a philosophical concept over time."""
    concept_id: str
    concept_name: str
    timeline: List[HistoricalEvent] = field(default_factory=list)
    key_developments: List[Tuple[datetime, str, str]] = field(default_factory=list)  # (date, entity, development)
    evolution_periods: Dict[TimePeriod, List[str]] = field(default_factory=dict)  # period -> contributors
    influence_chain: List[Tuple[str, str, datetime]] = field(default_factory=list)  # (from, to, date)

@dataclass
class HistoricalTimeline:
    """Complete historical timeline for philosophical development."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    events: List[HistoricalEvent] = field(default_factory=list)
    periods: Dict[TimePeriod, List[HistoricalEvent]] = field(default_factory=dict)
    concept_evolutions: Dict[str, ConceptEvolution] = field(default_factory=dict)
    total_events: int = 0

@dataclass
class PeriodAnalysis:
    """Analysis of a specific historical period."""
    period: TimePeriod
    start_year: int
    end_year: int
    key_figures: List[Tuple[str, str]] = field(default_factory=list)  # (id, name)
    dominant_concepts: List[Tuple[str, str]] = field(default_factory=list)  # (id, name)
    influential_works: List[str] = field(default_factory=list)
    schools_of_thought: List[str] = field(default_factory=list)
    period_characteristics: List[str] = field(default_factory=list)

class HistoricalDevelopmentService:
    """Service for tracking historical development in philosophical thought."""
    
    def __init__(
        self,
        neo4j_client: Optional[Neo4jClient] = None,
        settings: Optional[Any] = None
    ):
        """Initialize historical development service."""
        self.settings = settings or get_settings()
        self.neo4j_client = neo4j_client
        self.logger = logging.getLogger(__name__)
        
        # Date parsing patterns
        self.date_patterns = [
            r"(\d{1,4})\s*(BCE?|CE?|AD)",  # 384 BCE, 428 BC, 1225 CE, 1596 AD
            r"(\d{1,4})-(\d{1,4})\s*(BCE?|CE?|AD)",  # 384-322 BCE
            r"(\d{1,4})",  # Just year (assume CE if > 500, BCE otherwise)
        ]
        
    @property
    def client(self) -> Neo4jClient:
        """Get or create Neo4j client."""
        if self.neo4j_client is None:
            from arete.database.client import Neo4jClient
            self.neo4j_client = Neo4jClient()
        return self.neo4j_client
    
    def _parse_date(self, date_string: str) -> Tuple[Optional[datetime], float]:
        """
        Parse date string and return datetime with confidence score.
        
        Args:
            date_string: String representation of date
            
        Returns:
            Tuple of (parsed_datetime, confidence_score)
        """
        if not date_string:
            return None, 0.0
        
        date_string = date_string.strip()
        
        # Try each pattern
        for pattern in self.date_patterns:
            match = re.search(pattern, date_string, re.IGNORECASE)
            if match:
                try:
                    if "BCE" in date_string.upper() or "BC" in date_string.upper():
                        year = -int(match.group(1))
                        confidence = 0.8
                    else:
                        year = int(match.group(1))
                        if year < 500 and "CE" not in date_string.upper() and "AD" not in date_string.upper():
                            year = -year  # Assume BCE for early years
                            confidence = 0.6
                        else:
                            confidence = 0.9
                    
                    # Create datetime (using January 1st as default)
                    if year < 0:
                        # Handle BCE dates
                        return datetime(abs(year), 1, 1), confidence
                    else:
                        return datetime(year, 1, 1), confidence
                        
                except ValueError:
                    continue
        
        return None, 0.0
    
    def _determine_period(self, date: datetime) -> TimePeriod:
        """Determine historical period from date."""
        year = date.year
        if date.year < 0:  # BCE
            return TimePeriod.ANCIENT
        
        if year <= 500:
            return TimePeriod.ANCIENT
        elif year <= 1500:
            return TimePeriod.MEDIEVAL
        elif year <= 1650:
            return TimePeriod.RENAISSANCE
        elif year <= 1800:
            return TimePeriod.MODERN
        elif year <= 1950:
            return TimePeriod.CONTEMPORARY
        else:
            return TimePeriod.CURRENT
    
    async def construct_historical_timeline(
        self,
        entity_types: Optional[List[EntityType]] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> HistoricalTimeline:
        """
        Construct comprehensive historical timeline of philosophical development.
        
        Args:
            entity_types: Optional list to filter by entity types
            start_year: Optional start year filter
            end_year: Optional end year filter
            
        Returns:
            HistoricalTimeline with events and analysis
        """
        self.logger.info("Constructing historical timeline")
        
        try:
            async with self.client.session() as session:
                events = await self._extract_historical_events(session, entity_types)
                
                # Filter by date range if specified
                if start_year or end_year:
                    events = self._filter_events_by_date_range(events, start_year, end_year)
                
                # Sort events chronologically
                events.sort(key=lambda e: e.date or datetime(1, 1, 1))
                
                # Group by periods
                periods = defaultdict(list)
                for event in events:
                    if event.period:
                        periods[event.period].append(event)
                
                # Analyze concept evolutions
                concept_evolutions = await self._analyze_concept_evolutions(session, events)
                
                return HistoricalTimeline(
                    start_date=events[0].date if events else None,
                    end_date=events[-1].date if events else None,
                    events=events,
                    periods=dict(periods),
                    concept_evolutions=concept_evolutions,
                    total_events=len(events)
                )
                
        except Exception as e:
            self.logger.error(f"Timeline construction failed: {e}")
            raise TimelineConstructionError(f"Failed to construct timeline: {str(e)}")
    
    async def _extract_historical_events(
        self,
        session: AsyncSession,
        entity_types: Optional[List[EntityType]]
    ) -> List[HistoricalEvent]:
        """Extract historical events from the knowledge graph."""
        type_filter = ""
        if entity_types:
            type_labels = [f"'{et.value}'" for et in entity_types]
            type_filter = f"AND e.type IN [{','.join(type_labels)}]"
        
        query = f"""
        MATCH (e:Entity)
        WHERE e.id IS NOT NULL {type_filter}
        OPTIONAL MATCH (e)-[:HAS_ATTRIBUTE]->(date_attr:Entity {{type: 'DATE'}})
        OPTIONAL MATCH (e)-[:HAS_ATTRIBUTE]->(birth_attr:Entity {{name: 'birth_date'}})
        OPTIONAL MATCH (e)-[:HAS_ATTRIBUTE]->(death_attr:Entity {{name: 'death_date'}})
        OPTIONAL MATCH (e)-[:HAS_ATTRIBUTE]->(period_attr:Entity {{type: 'PERIOD'}})
        OPTIONAL MATCH (e)-[r]-(related:Entity)
        WHERE related.id IS NOT NULL
        RETURN e.id as entity_id, e.name as entity_name, e.type as entity_type,
               COALESCE(date_attr.value, birth_attr.value) as date_string,
               period_attr.value as period_string,
               e.description as description,
               collect(DISTINCT related.id) as related_entities
        """
        
        result = await session.run(query)
        records = await result.data()
        
        events = []
        for record in records:
            entity_id = record["entity_id"]
            entity_name = record["entity_name"] or entity_id
            entity_type_str = record["entity_type"]
            date_string = record["date_string"]
            description = record["description"]
            related_entities = record["related_entities"] or []
            
            # Parse entity type
            try:
                entity_type = EntityType(entity_type_str) if entity_type_str else EntityType.OTHER
            except ValueError:
                entity_type = EntityType.OTHER
            
            # Parse date
            date, confidence = self._parse_date(date_string) if date_string else (None, 0.0)
            
            # Determine period
            period = self._determine_period(date) if date else None
            
            event = HistoricalEvent(
                entity_id=entity_id,
                entity_name=entity_name,
                entity_type=entity_type,
                date=date,
                date_string=date_string,
                period=period,
                description=description,
                related_entities=related_entities,
                confidence_score=confidence
            )
            
            events.append(event)
        
        return events
    
    def _filter_events_by_date_range(
        self,
        events: List[HistoricalEvent],
        start_year: Optional[int],
        end_year: Optional[int]
    ) -> List[HistoricalEvent]:
        """Filter events by date range."""
        filtered_events = []
        
        for event in events:
            if not event.date:
                continue  # Skip events without dates
            
            event_year = event.date.year
            if event.date.year < 0:  # BCE dates
                event_year = -event_year
            
            if start_year and event_year < start_year:
                continue
            if end_year and event_year > end_year:
                continue
            
            filtered_events.append(event)
        
        return filtered_events
    
    async def _analyze_concept_evolutions(
        self,
        session: AsyncSession,
        events: List[HistoricalEvent]
    ) -> Dict[str, ConceptEvolution]:
        """Analyze how concepts evolved over time."""
        concept_evolutions = {}
        
        # Group events by concept
        concept_events = defaultdict(list)
        for event in events:
            if event.entity_type == EntityType.CONCEPT:
                concept_events[event.entity_id].append(event)
        
        for concept_id, concept_event_list in concept_events.items():
            if not concept_event_list:
                continue
            
            # Sort by date
            concept_event_list.sort(key=lambda e: e.date or datetime(1, 1, 1))
            concept_name = concept_event_list[0].entity_name
            
            # Analyze periods
            evolution_periods = defaultdict(list)
            for event in concept_event_list:
                if event.period:
                    evolution_periods[event.period].extend(event.related_entities)
            
            # Build influence chain (simplified)
            influence_chain = []
            for i in range(len(concept_event_list) - 1):
                current = concept_event_list[i]
                next_event = concept_event_list[i + 1]
                if current.date and next_event.date:
                    influence_chain.append((current.entity_id, next_event.entity_id, current.date))
            
            evolution = ConceptEvolution(
                concept_id=concept_id,
                concept_name=concept_name,
                timeline=concept_event_list,
                evolution_periods=dict(evolution_periods),
                influence_chain=influence_chain
            )
            
            concept_evolutions[concept_id] = evolution
        
        return concept_evolutions
    
    async def analyze_period(self, period: TimePeriod) -> PeriodAnalysis:
        """
        Analyze a specific historical period in detail.
        
        Args:
            period: The historical period to analyze
            
        Returns:
            PeriodAnalysis with detailed period information
        """
        self.logger.info(f"Analyzing period: {period}")
        
        try:
            async with self.client.session() as session:
                # Get period boundaries
                period_years = self._get_period_boundaries(period)
                
                # Query entities from this period
                query = """
                MATCH (e:Entity)
                WHERE e.id IS NOT NULL
                OPTIONAL MATCH (e)-[:HAS_ATTRIBUTE]->(date_attr:Entity {type: 'DATE'})
                OPTIONAL MATCH (e)-[:HAS_ATTRIBUTE]->(birth_attr:Entity {name: 'birth_date'})
                RETURN e.id as entity_id, e.name as entity_name, e.type as entity_type,
                       COALESCE(date_attr.value, birth_attr.value) as date_string,
                       e.description as description
                """
                
                result = await session.run(query)
                records = await result.data()
                
                # Filter and categorize entities by period
                key_figures = []
                dominant_concepts = []
                
                for record in records:
                    date_string = record["date_string"]
                    if date_string:
                        date, _ = self._parse_date(date_string)
                        if date and self._determine_period(date) == period:
                            entity_type = record["entity_type"]
                            entity_id = record["entity_id"]
                            entity_name = record["entity_name"] or entity_id
                            
                            if entity_type == EntityType.PERSON.value:
                                key_figures.append((entity_id, entity_name))
                            elif entity_type == EntityType.CONCEPT.value:
                                dominant_concepts.append((entity_id, entity_name))
                
                return PeriodAnalysis(
                    period=period,
                    start_year=period_years[0],
                    end_year=period_years[1],
                    key_figures=key_figures[:20],  # Top 20
                    dominant_concepts=dominant_concepts[:15],  # Top 15
                    period_characteristics=self._get_period_characteristics(period)
                )
                
        except Exception as e:
            self.logger.error(f"Period analysis failed: {e}")
            raise HistoricalAnalysisError(f"Failed to analyze period {period}: {str(e)}")
    
    def _get_period_boundaries(self, period: TimePeriod) -> Tuple[int, int]:
        """Get start and end years for a historical period."""
        boundaries = {
            TimePeriod.ANCIENT: (-3000, 500),
            TimePeriod.MEDIEVAL: (500, 1500),
            TimePeriod.RENAISSANCE: (1500, 1650),
            TimePeriod.MODERN: (1650, 1800),
            TimePeriod.CONTEMPORARY: (1800, 1950),
            TimePeriod.CURRENT: (1950, 2024)
        }
        return boundaries.get(period, (0, 2024))
    
    def _get_period_characteristics(self, period: TimePeriod) -> List[str]:
        """Get characteristic features of a historical period."""
        characteristics = {
            TimePeriod.ANCIENT: [
                "Foundation of Western philosophy",
                "Socratic method development",
                "Platonic idealism",
                "Aristotelian logic and metaphysics",
                "Stoicism and Epicureanism"
            ],
            TimePeriod.MEDIEVAL: [
                "Synthesis of faith and reason",
                "Scholastic method",
                "Islamic and Jewish philosophy",
                "University system development",
                "Commentaries on Aristotle"
            ],
            TimePeriod.RENAISSANCE: [
                "Humanistic philosophy",
                "Revival of ancient texts",
                "Scientific revolution beginnings",
                "Political philosophy development",
                "Religious reformation impact"
            ],
            TimePeriod.MODERN: [
                "Rationalism vs. empiricism",
                "Systematic philosophy",
                "Enlightenment ideals",
                "Scientific method formalization",
                "Social contract theory"
            ],
            TimePeriod.CONTEMPORARY: [
                "German idealism",
                "Utilitarianism development",
                "Existentialism emergence",
                "Analytic philosophy beginnings",
                "Marxist philosophy"
            ],
            TimePeriod.CURRENT: [
                "Analytic vs. continental divide",
                "Logical positivism",
                "Phenomenology and hermeneutics",
                "Philosophy of mind emergence",
                "Applied ethics development"
            ]
        }
        return characteristics.get(period, [])
    
    async def trace_concept_development(
        self,
        concept_id: str,
        include_influences: bool = True
    ) -> ConceptEvolution:
        """
        Trace the historical development of a specific concept.
        
        Args:
            concept_id: The concept to trace
            include_influences: Whether to include influence relationships
            
        Returns:
            ConceptEvolution with detailed development history
        """
        self.logger.info(f"Tracing development of concept: {concept_id}")
        
        try:
            async with self.client.session() as session:
                # Get concept and related historical information
                query = """
                MATCH (concept:Entity {id: $concept_id})
                OPTIONAL MATCH (concept)-[r]-(related:Entity)
                WHERE related.id IS NOT NULL
                OPTIONAL MATCH (related)-[:HAS_ATTRIBUTE]->(date_attr:Entity {type: 'DATE'})
                RETURN concept.name as concept_name,
                       related.id as related_id, related.name as related_name,
                       related.type as related_type,
                       date_attr.value as date_string,
                       type(r) as relationship_type
                """
                
                result = await session.run(query, concept_id=concept_id)
                records = await result.data()
                
                if not records:
                    raise HistoricalAnalysisError(f"Concept {concept_id} not found")
                
                concept_name = records[0]["concept_name"] or concept_id
                
                # Build timeline events
                timeline_events = []
                for record in records:
                    if record["related_id"] and record["date_string"]:
                        date, confidence = self._parse_date(record["date_string"])
                        if date:
                            event = HistoricalEvent(
                                entity_id=record["related_id"],
                                entity_name=record["related_name"] or record["related_id"],
                                entity_type=EntityType(record["related_type"]) if record["related_type"] else EntityType.OTHER,
                                date=date,
                                date_string=record["date_string"],
                                period=self._determine_period(date),
                                confidence_score=confidence
                            )
                            timeline_events.append(event)
                
                # Sort chronologically
                timeline_events.sort(key=lambda e: e.date or datetime(1, 1, 1))
                
                # Analyze evolution periods
                evolution_periods = defaultdict(list)
                for event in timeline_events:
                    if event.period and event.entity_type == EntityType.PERSON:
                        evolution_periods[event.period].append(event.entity_id)
                
                return ConceptEvolution(
                    concept_id=concept_id,
                    concept_name=concept_name,
                    timeline=timeline_events,
                    evolution_periods=dict(evolution_periods)
                )
                
        except Exception as e:
            self.logger.error(f"Concept development tracing failed: {e}")
            raise HistoricalAnalysisError(f"Failed to trace concept {concept_id}: {str(e)}")


def create_historical_development_service(
    neo4j_client: Optional[Neo4jClient] = None,
    settings: Optional[Any] = None
) -> HistoricalDevelopmentService:
    """Create a HistoricalDevelopmentService instance."""
    return HistoricalDevelopmentService(neo4j_client=neo4j_client, settings=settings)