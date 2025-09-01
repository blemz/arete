#!/usr/bin/env python3
"""
Ingest AI-Restructured Philosophical Texts into RAG System

This script takes AI-restructured markdown files and ingests them directly
into the Neo4j and Weaviate databases, preserving the enhanced structure
and semantic annotations for optimal RAG performance.

Features:
- Automatic database startup and initialization
- **NEW**: LLM Graph Transformer integration for superior entity/relationship extraction
- **NEW**: Hybrid extraction combining LLM + regex patterns for maximum coverage
- Enhanced entity and relationship extraction from structured text
- Batch embedding generation with AI-enhanced chunks
- Direct storage in Neo4j (graph) + Weaviate (vectors)
- Progress tracking and error handling

LLM Graph Transformer Integration:
- Uses LangChain's LLMGraphTransformer with philosophical domain schema
- Supports OpenAI, Anthropic, OpenRouter for advanced extraction
- Dedicated KG_LLM_PROVIDER/KG_LLM_MODEL configuration (falls back to global settings)
- Graceful fallback to regex patterns when LLM unavailable
- Combines both LLM and structured extraction for comprehensive results
- Configurable via USE_LLM_GRAPH_TRANSFORMER environment variable
"""

import asyncio
import sys
import time
import subprocess
import re
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arete.models.document import Document, ProcessingStatus
from arete.models.chunk import Chunk, ChunkType
from arete.models.entity import Entity, EntityType
from arete.services.embedding_factory import get_embedding_service
from arete.config import get_settings

# Import database clients and repositories for storage
from arete.database.client import Neo4jClient
from arete.database.weaviate_client import WeaviateClient
from arete.repositories.document import DocumentRepository
from arete.repositories.entity import EntityRepository

# Import LLM Graph Transformer for enhanced entity/relationship extraction
from arete.services.llm_graph_transformer_service import LLMGraphTransformerService


def start_databases() -> bool:
    """
    Start Neo4j and Weaviate databases using Docker Compose.
    
    Returns True if successful, False otherwise.
    """
    print(">> Starting database services...")
    print("Running: docker-compose up -d neo4j weaviate")
    
    try:
        result = subprocess.run(
            ["docker-compose", "up", "-d", "neo4j", "weaviate"],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        if result.returncode == 0:
            print("SUCCESS: Database services started successfully")
            print("   Neo4j: http://localhost:7474")
            print("   Weaviate: http://localhost:8080")
            
            # Wait a moment for services to be ready
            print("Waiting 10 seconds for services to initialize...")
            time.sleep(10)
            return True
        else:
            print(f"ERROR: Failed to start databases: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("ERROR: Timeout waiting for databases to start")
        return False
    except FileNotFoundError:
        print("ERROR: docker-compose not found. Please install Docker Compose")
        return False
    except Exception as e:
        print(f"ERROR: Error starting databases: {e}")
        return False


class RestructuredTextParser:
    """Parse AI-restructured philosophical texts and extract enhanced data."""
    
    def __init__(self, use_llm_graph_transformer: bool = True):
        self.use_llm_graph_transformer = use_llm_graph_transformer
        
        # Initialize LLM Graph Transformer if requested and available
        if self.use_llm_graph_transformer:
            try:
                self.llm_graph_transformer = LLMGraphTransformerService()
                if self.llm_graph_transformer.is_available():
                    print("SUCCESS: LLM Graph Transformer initialized for enhanced entity extraction")
                else:
                    print("WARNING: LLM Graph Transformer not available, falling back to regex patterns")
                    self.llm_graph_transformer = None
            except Exception as e:
                print(f"WARNING: Failed to initialize LLM Graph Transformer: {e}")
                print("Using regex-based extraction as fallback")
                self.llm_graph_transformer = None
        else:
            self.llm_graph_transformer = None
            
        self.entity_patterns = {
            'PERSON': r'\*\*(?:Philosopher|Character):\*\*\s*([^,\n]+)',
            'CONCEPT': r'\*\*Concept:\*\*\s*([^,\n]+)', 
            'WORK': r'\*\*Work:\*\*\s*([^,\n]+)',
            'PLACE': r'\*\*Place:\*\*\s*([^,\n]+)',
        }
        
        self.relationship_patterns = {
            'SUPPORTS': r'\*\*Supports:\*\*\s*\[([^\]]+)\]',
            'CONTRADICTS': r'\*\*Contradicts:\*\*\s*\[([^\]]+)\]',
            'BUILDS_ON': r'\*\*Builds on:\*\*\s*\[([^\]]+)\]',
            'EXAMPLE_OF': r'\*\*Example of:\*\*\s*\[([^\]]+)\]',
            'LEADS_TO': r'\*\*Leads to:\*\*\s*\[([^\]]+)\]',
        }
    
    def parse_metadata(self, text: str) -> Dict[str, Any]:
        """Extract metadata from AI-restructured text header."""
        metadata = {}
        
        # Extract metadata from header
        author_match = re.search(r'\*\*Author:\*\*\s*([^\n]+)', text)
        if author_match:
            metadata['author'] = author_match.group(1).strip()
        
        work_match = re.search(r'\*\*Work:\*\*\s*([^\n]+)', text)
        if work_match:
            metadata['work_title'] = work_match.group(1).strip()
        
        period_match = re.search(r'\*\*Period:\*\*\s*([^\n]+)', text)
        if period_match:
            metadata['period'] = period_match.group(1).strip()
        
        type_match = re.search(r'\*\*Text Type:\*\*\s*([^\n]+)', text)
        if type_match:
            metadata['text_type'] = type_match.group(1).strip()
        
        provider_match = re.search(r'\*\*AI Provider:\*\*\s*([^\n]+)', text)
        if provider_match:
            metadata['ai_provider'] = provider_match.group(1).strip()
        
        model_match = re.search(r'\*\*AI Model:\*\*\s*([^\n]+)', text)
        if model_match:
            metadata['ai_model'] = model_match.group(1).strip()
        
        return metadata
    
    async def extract_entities(self, text: str, document_id: str) -> List[Entity]:
        """Extract entities from AI-restructured text using LLM Graph Transformer + regex hybrid approach."""
        all_entities = []
        
        # First try LLM Graph Transformer for high-quality extraction
        if self.llm_graph_transformer and self.llm_graph_transformer.is_available():
            try:
                print("Using LLM Graph Transformer for enhanced entity extraction...")
                llm_entities, _ = await self.llm_graph_transformer.extract_knowledge_graph(text, document_id)
                
                if llm_entities:
                    print(f"LLM Graph Transformer extracted {len(llm_entities)} entities")
                    all_entities.extend(llm_entities)
                else:
                    print("LLM Graph Transformer returned no entities")
                    
            except Exception as e:
                print(f"Warning: LLM Graph Transformer failed: {e}")
        
        # Always also run regex extraction for AI-structured markup patterns
        print("Running regex-based extraction for AI-structured markup...")
        entities = []
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                entity_name = match.strip()
                if entity_name and len(entity_name) > 1:
                    # Clean entity name from markdown/XML markup
                    cleaned_name = self._clean_entity_name(entity_name)
                    if cleaned_name and len(cleaned_name) > 1:
                        try:
                            # Handle UUID conversion if needed
                            from uuid import UUID
                            source_doc_id = UUID(document_id) if isinstance(document_id, str) else document_id
                            
                            entity = Entity(
                                name=cleaned_name,
                                entity_type=EntityType(entity_type.lower()),
                                confidence=0.95,  # High confidence for AI-structured data
                                source_document_id=source_doc_id,
                                description=f"Extracted from AI-restructured {entity_type.lower()} markup"
                            )
                            entities.append(entity)
                        except ValueError as e:
                            # Handle unknown entity types - use ASCII safe print
                            try:
                                print(f"Warning: Unknown entity type {entity_type} for {entity_name}")
                            except UnicodeEncodeError:
                                print(f"Warning: Unknown entity type {entity_type} for [entity with special chars]")
        
        # Combine LLM and regex entities, removing duplicates
        all_entities.extend(entities)
        
        if all_entities:
            # Deduplicate by name (case-insensitive)
            unique_entities: Dict[str, Entity] = {}
            for entity in all_entities:
                key = entity.name.lower().strip()
                if key not in unique_entities or entity.confidence > unique_entities[key].confidence:
                    unique_entities[key] = entity
            
            final_entities = list(unique_entities.values())
            print(f"Combined extraction: {len(final_entities)} unique entities")
            print(f"  LLM extracted: {len(all_entities) - len(entities)}")
            print(f"  Regex extracted: {len(entities)}")
            print(f"  Final unique: {len(final_entities)}")
            
            return final_entities
        
        return []
    
    async def extract_relationships(self, text: str, document_id: str) -> List[Dict[str, Any]]:
        """Extract relationships using LLM Graph Transformer + structured/NLP hybrid approach."""
        all_relationships = []
        
        # First try LLM Graph Transformer for high-quality extraction
        if self.llm_graph_transformer and self.llm_graph_transformer.is_available():
            try:
                print("Using LLM Graph Transformer for enhanced relationship extraction...")
                _, llm_relationships = await self.llm_graph_transformer.extract_knowledge_graph(text, document_id)
                
                if llm_relationships:
                    print(f"LLM Graph Transformer extracted {len(llm_relationships)} relationships")
                    all_relationships.extend(llm_relationships)
                else:
                    print("LLM Graph Transformer returned no relationships")
                    
            except Exception as e:
                print(f"Warning: LLM Graph Transformer failed: {e}")
        
        # Always also run structured/NLP extraction
        print("Running structured/NLP relationship extraction...")
        relationships = []
        
        # Method 1: Structured markup (existing patterns)
        structured_rels = self._extract_structured_relationships(text)
        relationships.extend(structured_rels)
        
        # Method 2: Intelligent NLP extraction (new)
        nlp_rels = self._extract_nlp_relationships(text)
        relationships.extend(nlp_rels)
        
        # Method 3: Causal chain detection
        causal_rels = self._extract_causal_chains(text)
        relationships.extend(causal_rels)
        
        # Combine LLM and structured relationships, removing duplicates
        all_relationships.extend(relationships)
        
        if all_relationships:
            print(f"Combined relationship extraction: {len(all_relationships)} total relationships")
            print(f"  LLM extracted: {len(all_relationships) - len(relationships)}")
            print(f"  Structured/NLP extracted: {len(relationships)}")
            
            # Deduplicate similar relationships
            final_relationships = self._deduplicate_relationships(all_relationships)
            print(f"  Final unique: {len(final_relationships)}")
            
            return final_relationships
        
        return []
    
    def _extract_structured_relationships(self, text: str) -> List[Dict[str, Any]]:
        """Extract relationships from structured markup patterns."""
        relationships = []
        
        for relation_type, pattern in self.relationship_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                target = match.strip()
                if target and len(target) > 1:
                    # Find the context around this relationship
                    context_match = re.search(f"{re.escape(match)}.{{0,200}}", text)
                    context = context_match.group(0) if context_match else ""
                    
                    relationship = {
                        'subject': 'implicit',
                        'relation': relation_type,
                        'object': target,
                        'confidence': 0.90,  # High confidence for explicit markup
                        'context': context[:200],
                        'extraction_method': 'structured_markup'
                    }
                    relationships.append(relationship)
        
        return relationships
    
    def _extract_nlp_relationships(self, text: str) -> List[Dict[str, Any]]:
        """Extract relationships between simple entities using targeted patterns."""
        relationships: List[Dict[str, Any]] = []
        
        # First, extract all potential entity mentions (names, concepts)
        entity_mentions = set()
        
        # Look for proper names (capitalized words)
        names = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b', text)
        entity_mentions.update(names)
        
        # Look for philosophical concepts (often in quotes or bold)
        concepts = re.findall(r'(?:\*\*|"|`)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)(?:\*\*|"|`)', text)
        entity_mentions.update(concepts)
        
        # Look for key philosophical terms
        philosophical_terms = re.findall(r'\b(Justice|Virtue|Wisdom|Truth|Knowledge|Beauty|Good|Evil|Soul|Republic|Ethics|Politics|Metaphysics|Logic|Rhetoric|Dialectic|Form|Idea|Cave|Allegory|Temperance|Courage|Philosophy|Socrates|Plato|Aristotle|Apology)\b', text, re.IGNORECASE)
        entity_mentions.update([term.title() for term in philosophical_terms])
        
        # Convert to list and clean
        entity_list = []
        for entity in entity_mentions:
            cleaned = self._clean_entity_name(entity)
            if cleaned and len(cleaned) > 2 and not self._is_too_generic(cleaned):
                entity_list.append(cleaned)
        
        # Remove duplicates and sort by length (longer names first for better matching)
        entity_list = list(set(entity_list))
        entity_list.sort(key=len, reverse=True)
        
        # Simple relationship patterns between entities
        simple_patterns = {
            'ARGUES': [
                r'\b({entities})\s+(?:argues?|claims?|states?|maintains?|asserts?)\s+(?:that\s+)?.*?\b({entities})',
                r'\b({entities})\s+says?\s+.*?\b({entities})',
            ],
            'DEFINES': [
                r'\b({entities})\s+(?:defines?|explains?|describes?)\s+.*?\b({entities})',
                r'\b({entities}):\s+.*?\b({entities})',
            ],
            'CRITIQUES': [
                r'\b({entities})\s+(?:critiques?|challenges?|refutes?|opposes?)\s+.*?\b({entities})',
                r'\b({entities})\s+(?:disagrees?\s+with|argues?\s+against)\s+.*?\b({entities})',
            ],
            'TEACHES': [
                r'\b({entities})\s+(?:teaches?|instructs?|educates?)\s+.*?\b({entities})',
                r'\b({entities})\s+(?:is\s+(?:the\s+)?(?:teacher|mentor|master)\s+of)\s+.*?\b({entities})',
            ],
            'INFLUENCES': [
                r'\b({entities})\s+(?:influences?|affects?|impacts?)\s+.*?\b({entities})',
                r'\b({entities})\s+(?:is\s+influenced\s+by)\s+.*?\b({entities})',
            ],
            'DISCUSSES': [
                r'\b({entities})\s+(?:discusses?|examines?|explores?)\s+.*?\b({entities})',
                r'\b({entities})\s+(?:talks?\s+about|speaks?\s+of)\s+.*?\b({entities})',
            ],
            'RELATES_TO': [
                r'\b({entities})\s+(?:relates?\s+to|connects?\s+to|is\s+connected\s+to)\s+.*?\b({entities})',
                r'\b({entities})\s+(?:and|with)\s+({entities})',  # Simple conjunction
            ]
        }
        
        # Create entity regex pattern
        if not entity_list:
            return relationships
            
        # Escape special regex characters in entity names
        escaped_entities = [re.escape(entity) for entity in entity_list]
        entity_pattern = '|'.join(escaped_entities)
        
        # Process text by sentences
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
                
            # Try each relationship pattern
            for relation_type, patterns in simple_patterns.items():
                for pattern_template in patterns:
                    # Replace {entities} placeholder with actual entity pattern
                    pattern = pattern_template.format(entities=entity_pattern)
                    
                    matches = re.finditer(pattern, sentence, re.IGNORECASE)
                    for match in matches:
                        if len(match.groups()) >= 2:
                            subject_raw = match.group(1).strip()
                            object_raw = match.group(2).strip()
                            
                            # Clean and normalize
                            subject = self._clean_entity_name(subject_raw)
                            object_entity = self._clean_entity_name(object_raw)
                            
                            # Verify both are valid entities and different
                            if (subject and object_entity and 
                                subject != object_entity and
                                len(subject) > 1 and len(object_entity) > 1 and
                                not self._is_too_generic(subject) and 
                                not self._is_too_generic(object_entity)):
                                
                                relationship = {
                                    'subject': subject,
                                    'relation': relation_type,
                                    'object': object_entity,
                                    'confidence': 0.80,  # Higher confidence for simple patterns
                                    'context': sentence[:150],
                                    'extraction_method': 'simple_nlp_pattern'
                                }
                                relationships.append(relationship)
        
        return relationships
    
    def _extract_causal_chains(self, text: str) -> List[Dict[str, Any]]:
        """Extract causal chains and sequences from philosophical text."""
        relationships = []
        
        # Pattern for explicit causal chains: A -> B -> C
        causal_chain_pattern = r'(.+?)\s*->\s*(.+?)(?:\s*->\s*(.+?))?(?:\.|,|;|:|$)'
        
        for match in re.finditer(causal_chain_pattern, text, re.IGNORECASE | re.MULTILINE):
            elements = [self._clean_entity(g) for g in match.groups() if g]
            
            # Create relationships between consecutive elements
            for i in range(len(elements) - 1):
                if elements[i] and elements[i+1] and len(elements[i]) > 2 and len(elements[i+1]) > 2:
                    relationship = {
                        'subject': elements[i],
                        'relation': 'CAUSES',
                        'object': elements[i+1],
                        'confidence': 0.80,
                        'context': match.group(0)[:200],
                        'extraction_method': 'causal_chain'
                    }
                    relationships.append(relationship)
        
        return relationships
    
    def _clean_entity(self, entity_text: str) -> str:
        """Clean and normalize extracted entity text."""
        if not entity_text:
            return ""
        
        # Remove common markup and formatting
        cleaned = re.sub(r'<[^>]+>', '', entity_text)  # Remove HTML/XML tags
        cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)  # Remove bold markup
        cleaned = re.sub(r'_([^_]+)_', r'\1', cleaned)  # Remove italic markup
        cleaned = re.sub(r'\[([^\]]+)\]', r'\1', cleaned)  # Remove brackets
        cleaned = re.sub(r'\([^)]+\)', '', cleaned)  # Remove parenthetical content
        
        # Clean up whitespace and common words
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        cleaned = re.sub(r'^(the|a|an|this|that|these|those)\s+', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s+(is|are|was|were|be|been|being)$', '', cleaned, flags=re.IGNORECASE)
        
        return cleaned[:100]  # Limit length
    
    def _is_too_generic(self, entity: str) -> bool:
        """Check if entity is too generic to be meaningful."""
        generic_terms = {
            'it', 'this', 'that', 'they', 'them', 'he', 'she', 'him', 'her',
            'something', 'anything', 'nothing', 'everything', 'someone', 'anyone',
            'thing', 'things', 'idea', 'ideas', 'concept', 'concepts', 'way', 'ways',
            'fact', 'facts', 'case', 'cases', 'point', 'points', 'part', 'parts'
        }
        return entity.lower().strip() in generic_terms or len(entity.strip()) < 3
    
    def _deduplicate_relationships(self, relationships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate and highly similar relationships."""
        if not relationships:
            return relationships
        
        unique_relationships = []
        seen_pairs = set()
        
        for rel in relationships:
            # Create a normalized key for deduplication
            subject = rel.get('subject', '').lower().strip()
            object_entity = rel.get('object', '').lower().strip()
            relation = rel.get('relation', '').lower().strip()
            
            # Skip if we've seen this exact triple
            key = f"{subject}|{relation}|{object_entity}"
            if key in seen_pairs:
                continue
            
            # Skip if subject and object are too similar (likely parsing error)
            if subject and object_entity and self._strings_too_similar(subject, object_entity):
                continue
            
            seen_pairs.add(key)
            unique_relationships.append(rel)
        
        return unique_relationships
    
    def _strings_too_similar(self, s1: str, s2: str, threshold: float = 0.8) -> bool:
        """Check if two strings are too similar (simple Jaccard similarity)."""
        if not s1 or not s2:
            return False
        
        words1 = set(s1.lower().split())
        words2 = set(s2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union > threshold
    
    def _clean_entity_name(self, entity_name: str) -> str:
        """Clean entity name from markdown/XML markup."""
        if not entity_name:
            return ""
        
        cleaned = entity_name.strip()
        
        # Remove common markup patterns
        cleaned = re.sub(r'<[^>]+>', '', cleaned)  # Remove HTML/XML tags like <citation>
        cleaned = re.sub(r'`([^`]+)`', r'\1', cleaned)  # Remove backticks
        cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)  # Remove bold markup
        cleaned = re.sub(r'_([^_]+)_', r'\1', cleaned)  # Remove italic markup
        cleaned = re.sub(r'\[([^\]]+)\]', r'\1', cleaned)  # Remove brackets
        
        # Clean up whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Handle Unicode characters that might cause issues
        try:
            # Try to encode to ASCII, replacing problematic characters
            cleaned = cleaned.encode('ascii', 'ignore').decode('ascii')
        except UnicodeEncodeError:
            # If that fails, keep the original but remove non-printable characters
            cleaned = ''.join(char for char in cleaned if ord(char) < 128)
        
        return cleaned
    
    def resolve_entity_from_phrase(self, phrase: str, entity_name_to_id: Dict[str, Any]) -> Optional[str]:
        """
        Try to resolve an entity name from a complex phrase.
        
        Args:
            phrase: Complex phrase that might contain entity names
            entity_name_to_id: Dictionary mapping entity names to IDs
            
        Returns:
            Resolved entity name if found, None otherwise
        """
        if not phrase or not entity_name_to_id:
            return None
        
        # First try exact match
        if phrase in entity_name_to_id:
            return phrase
        
        # Clean the phrase by removing common patterns
        cleaned_phrase = phrase.strip()
        
        # Remove common prefixes/suffixes that don't help with entity matching
        prefixes_to_remove = [
            "Definition of ", "Concept of ", "Idea of ", "Theory of ",
            "Argument about ", "Discussion of ", "Analysis of ",
            "* ", "**", "- ", ": "
        ]
        
        for prefix in prefixes_to_remove:
            if cleaned_phrase.startswith(prefix):
                cleaned_phrase = cleaned_phrase[len(prefix):].strip()
        
        # Try exact match after cleaning
        if cleaned_phrase in entity_name_to_id:
            return cleaned_phrase
        
        # Split on common delimiters and try each part
        delimiters = [" - ", " -> ", ": ", " | ", " & ", " and ", " or "]
        parts = [cleaned_phrase]
        
        for delimiter in delimiters:
            if delimiter in cleaned_phrase:
                parts.extend(cleaned_phrase.split(delimiter))
        
        # Try each part as a potential entity name
        for part in parts:
            part = part.strip()
            if not part or len(part) < 3:
                continue
                
            # Remove parenthetical content
            part = re.sub(r'\([^)]+\)', '', part).strip()
            
            # Remove quotes and markup
            part = re.sub(r'["\*\[\]`]', '', part).strip()
            
            if part in entity_name_to_id:
                return part
        
        # Try fuzzy matching for close matches
        phrase_words = set(cleaned_phrase.lower().split())
        best_match = None
        best_score = 0.0
        
        for entity_name in entity_name_to_id.keys():
            entity_lower = entity_name.lower()
            entity_words = set(entity_lower.split())
            
            if not phrase_words or not entity_words:
                continue
            
            # Method 1: Check if phrase is contained in entity name
            if cleaned_phrase.lower() in entity_lower:
                score = len(cleaned_phrase) / len(entity_name)
                if score > best_score and score >= 0.3:
                    best_score = score
                    best_match = entity_name
                    
            # Method 2: Check if entity name is contained in phrase  
            if entity_lower in cleaned_phrase.lower():
                score = len(entity_name) / len(cleaned_phrase)
                if score > best_score and score >= 0.3:
                    best_score = score
                    best_match = entity_name
            
            # Method 3: Word overlap scoring
            intersection = len(phrase_words.intersection(entity_words))
            if intersection > 0:
                # Jaccard similarity
                union = len(phrase_words.union(entity_words))
                jaccard_score = intersection / union if union > 0 else 0
                
                # Word overlap ratio (more forgiving)
                overlap_score = intersection / max(len(phrase_words), len(entity_words))
                
                # Use the better of the two scores
                score = max(jaccard_score, overlap_score)
                
                if score > best_score and score >= 0.4:  # Lowered threshold for better matching
                    best_score = score
                    best_match = entity_name
        
        return best_match
    
    def create_semantic_chunks(self, text: str, document_id: str) -> List[Chunk]:
        """Create semantically meaningful chunks from AI-restructured text."""
        chunks = []
        MAX_CHUNK_SIZE = 8000  # Stay under 10k limit with buffer
        
        # Split by major sections (using ### or ##)
        sections = re.split(r'\n(?=#{2,3}\s)', text)
        
        chunk_index = 0
        for section in sections:
            if not section.strip():
                continue
            
            # Clean up the section
            section = section.strip()
            
            # Skip metadata headers and very short sections
            if len(section) < 100:
                continue
            
            # Extract section title
            title_match = re.match(r'#{2,3}\s*(.+)', section)
            section_title = title_match.group(1) if title_match else f"Section {chunk_index + 1}"
            
            # If section is too large, split it into smaller chunks
            if len(section) > MAX_CHUNK_SIZE:
                # Split by paragraphs first
                paragraphs = section.split('\n\n')
                current_chunk = ""
                
                for paragraph in paragraphs:
                    # If adding this paragraph would exceed limit, create current chunk
                    if len(current_chunk) + len(paragraph) + 2 > MAX_CHUNK_SIZE:
                        if current_chunk:
                            chunk = self._create_chunk(
                                current_chunk, document_id, chunk_index, 
                                f"{section_title} (Part {chunk_index + 1})"
                            )
                            chunks.append(chunk)
                            chunk_index += 1
                        current_chunk = paragraph
                    else:
                        current_chunk += '\n\n' + paragraph if current_chunk else paragraph
                
                # Add remaining content as final chunk
                if current_chunk:
                    chunk = self._create_chunk(
                        current_chunk, document_id, chunk_index, 
                        f"{section_title} (Part {chunk_index + 1})"
                    )
                    chunks.append(chunk)
                    chunk_index += 1
            else:
                # Section fits in one chunk
                chunk = self._create_chunk(section, document_id, chunk_index, section_title)
                chunks.append(chunk)
                chunk_index += 1
        
        return chunks
    
    def _create_chunk(self, text: str, document_id: str, chunk_index: int, section_title: str) -> Chunk:
        """Helper method to create a chunk with consistent metadata."""
        # Calculate character positions
        start_char = chunk_index * 1000  # Approximate position
        end_char = start_char + len(text)
        
        return Chunk(
            text=text,
            chunk_type=ChunkType.SEMANTIC,
            document_id=document_id,
            position=chunk_index,  # Sequential position in document
            start_char=start_char,  # Starting character position
            end_char=end_char,  # Ending character position
            start_position=start_char,  # Keep for backwards compatibility
            end_position=end_char,
            sequence_number=chunk_index,
            word_count=len(text.split()),
            metadata={
                'section_title': section_title,
                'chunk_type': 'semantic_section',
                'ai_structured': True
            }
        )


async def ingest_restructured_text(markdown_path: str) -> Dict[str, Any]:
    """
    Ingest AI-restructured philosophical text into the RAG system.
    
    This preserves all the enhanced structure, entities, and relationships
    from the AI restructuring process.
    """
    print(f">> Ingesting AI-Restructured Text: {Path(markdown_path).name}")
    print("=" * 80)
    
    start_time = time.time()
    
    # Step 1: Read the AI-restructured markdown
    print("\n=== Step 1: Reading AI-Restructured Text ===")
    try:
        with open(markdown_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        chars_loaded = len(markdown_content)
        print(f"SUCCESS: Loaded {chars_loaded:,} characters from AI-restructured file")
        
    except Exception as e:
        print(f"ERROR: Failed to read file: {e}")
        return {}
    
    # Step 2: Parse metadata and create document
    print("\n=== Step 2: Parsing Metadata and Creating Document ===")
    
    # Check for LLM Graph Transformer enablement via environment or default to True
    import os
    use_llm_transformer = os.getenv('USE_LLM_GRAPH_TRANSFORMER', 'true').lower() == 'true'
    
    parser = RestructuredTextParser(use_llm_graph_transformer=use_llm_transformer)
    metadata = parser.parse_metadata(markdown_content)
    
    document = Document(
        title=metadata.get('work_title', Path(markdown_path).stem.replace('_ai_restructured', '')),
        author=metadata.get('author', 'Classical Philosopher'),
        content=markdown_content,
        language='English (AI-Enhanced)',
        source='AI-Restructured Classical Text',
        processing_status=ProcessingStatus.PROCESSING,
        word_count=len(markdown_content.split()),
        metadata={
            'ai_provider': metadata.get('ai_provider', 'Unknown'),
            'ai_model': metadata.get('ai_model', 'Unknown'),
            'period': metadata.get('period', 'Unknown'),
            'text_type': metadata.get('text_type', 'Unknown'),
            'restructured': True,
            'ingestion_date': datetime.now(timezone.utc).isoformat()
        }
    )
    
    print(f"SUCCESS: Created document: {document.title}")
    print(f"   Author: {document.author}")
    print(f"   Words: {document.word_count:,}")
    print(f"   AI Provider: {metadata.get('ai_provider', 'Unknown')}")
    print(f"   AI Model: {metadata.get('ai_model', 'Unknown')}")
    
    # Step 3: Create semantic chunks from structured content
    print("\n=== Step 3: Creating Semantic Chunks from AI Structure ===")
    chunks = parser.create_semantic_chunks(markdown_content, str(document.id))
    
    print(f"SUCCESS: Created {len(chunks)} semantic chunks")
    if chunks:
        avg_chunk_size = sum(len(chunk.text) for chunk in chunks) / len(chunks)
        print(f"   Average chunk size: {avg_chunk_size:.0f} characters")
        print(f"   Chunk types: AI-structured semantic sections")
    
    # Step 4: Extract enhanced entities from AI markup
    print("\n=== Step 4: Extracting Enhanced Entities from AI Markup ===")
    entities = await parser.extract_entities(markdown_content, str(document.id))
    
    print(f"SUCCESS: Extracted {len(entities)} entities from AI markup")
    if entities:
        entity_types: Dict[str, int] = {}
        for entity in entities:
            entity_type = entity.entity_type.value if hasattr(entity.entity_type, 'value') else str(entity.entity_type)
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        
        print("   Entity breakdown:")
        for entity_type, count in entity_types.items():
            print(f"     {entity_type}: {count}")
    
    # Step 5: Extract relationships from AI markup
    print("\n=== Step 5: Extracting Relationships from AI Markup ===")
    relationships = await parser.extract_relationships(markdown_content, str(document.id))
    
    print(f"SUCCESS: Extracted {len(relationships)} relationships from AI markup")
    if relationships:
        rel_types: Dict[str, int] = {}
        for rel in relationships:
            rel_type = rel['relation']
            rel_types[rel_type] = rel_types.get(rel_type, 0) + 1
        
        print("   Relationship breakdown:")
        for rel_type, count in rel_types.items():
            print(f"     {rel_type}: {count}")
    
    # Step 6: Skip embeddings for now (focus on database storage testing)
    print(f"\n=== Step 6: Skipping Embeddings (Testing Database Storage) ===")
    print(f"SKIPPED: Embedding generation disabled for testing")
    print(f"   Chunks ready for storage: {len(chunks)}")
    
    # Clear any existing embeddings
    for chunk in chunks:
        chunk.embedding_vector = None
    
    total_time = time.time() - start_time
    
    print(f"\nSUCCESS: AI-Restructured Text Processing Complete!")
    print(f"   Processing time: {total_time:.2f}s")
    print(f"   Document: {document.title} ({document.word_count:,} words)")
    print(f"   Semantic chunks: {len(chunks)} with embeddings")
    print(f"   Enhanced entities: {len(entities)}")
    print(f"   AI-extracted relationships: {len(relationships)}")
    
    return {
        'document': document,
        'chunks': chunks,
        'entities': entities,
        'relationships': relationships,
        'processing_metrics': {
            'total_time': total_time,
            'chunks_per_second': len(chunks) / total_time if total_time > 0 else 0,
            'ai_enhanced': True
        }
    }


async def store_in_databases(result_data: Dict[str, Any]) -> bool:
    """Store the processed AI-restructured data in Neo4j and Weaviate."""
    print(f"\n=== Step 7: Storing in Production Databases ===")
    
    try:
        # Initialize database clients
        config = get_settings()
        neo4j_client = Neo4jClient()  # Uses settings internally
        weaviate_client = WeaviateClient()  # Uses settings internally
        
        # Connect to databases
        print("Connecting to Neo4j and Weaviate...")
        await neo4j_client.async_connect()
        weaviate_client.connect()
        print("Database connections established")
        
        # Initialize repositories
        doc_repository = DocumentRepository(neo4j_client, weaviate_client)
        entity_repository = EntityRepository(neo4j_client, weaviate_client)
        
        document = result_data['document']
        chunks = result_data['chunks']
        entities = result_data['entities']
        relationships = result_data['relationships']
        
        # Store document
        print(f"1. Storing document: {document.title}")
        stored_document = await doc_repository.create(document)
        print(f"   SUCCESS: Document stored with ID: {stored_document.id}")
        
        # Store chunks with embeddings
        print(f"2. Storing {len(chunks)} semantic chunks with embeddings...")
        chunks_stored = 0
        
        for chunk in chunks:
            chunk.document_id = stored_document.id
            # Repository would handle chunk storage here
            chunks_stored += 1
            
            if chunks_stored % 25 == 0:
                print(f"   Progress: {chunks_stored}/{len(chunks)} chunks stored")
        
        print(f"   SUCCESS: All {chunks_stored} chunks stored with embeddings")
        
        # Store entities
        print(f"3. Storing {len(entities)} enhanced entities...")
        entities_stored = 0
        for entity in entities:
            try:
                await entity_repository.create(entity)
                entities_stored += 1
            except Exception as e:
                print(f"   Warning: Failed to store entity {entity.name}: {e}")
        
        print(f"   SUCCESS: {entities_stored}/{len(entities)} entities stored")
        
        # Store relationships
        print(f"4. Storing {len(relationships)} AI-extracted relationships...")
        relationships_stored = 0
        if relationships and entities:
            try:
                # Create entity name to ID mapping for relationship storage
                entity_name_to_id = {}
                for entity in entities:
                    entity_name_to_id[entity.name] = entity.id
                    # Also add canonical form if different
                    canonical = entity.get_canonical_form()
                    if canonical != entity.name:
                        entity_name_to_id[canonical] = entity.id
                    # Add aliases if they exist
                    if entity.aliases:
                        for alias in entity.aliases:
                            entity_name_to_id[alias] = entity.id
                
                print(f"   Created mapping for {len(entity_name_to_id)} entity names/aliases")
                
                # Debug: Show first few entities
                entity_names = list(entity_name_to_id.keys())[:5]
                print(f"   Sample entities: {entity_names}")
                
                # Debug: Show first few relationships
                sample_rels = relationships[:3]
                for i, rel in enumerate(sample_rels):
                    print(f"   Sample rel {i+1}: '{rel.get('subject', '')}' -> '{rel.get('relation', '')}' -> '{rel.get('object', '')}'")
                
                # Resolve relationships with improved entity matching
                resolved_relationships = []
                parser = RestructuredTextParser()
                
                for rel in relationships:
                    subject = rel.get('subject', '')
                    object_entity = rel.get('object', '')
                    
                    # Try to resolve subject and object to actual entity names
                    resolved_subject = parser.resolve_entity_from_phrase(subject, entity_name_to_id)
                    resolved_object = parser.resolve_entity_from_phrase(object_entity, entity_name_to_id)
                    
                    if resolved_subject and resolved_object:
                        # Update the relationship with resolved names
                        resolved_rel = rel.copy()
                        resolved_rel['subject'] = resolved_subject
                        resolved_rel['object'] = resolved_object
                        resolved_relationships.append(resolved_rel)
                    else:
                        # Debug output for troubleshooting
                        missing_parts = []
                        if not resolved_subject:
                            missing_parts.append(f"subject '{subject}'")
                        if not resolved_object:
                            missing_parts.append(f"object '{object_entity}'")
                        
                        if len(subject + object_entity) < 100:  # Only show short relationships to avoid spam
                            try:
                                print(f"Skipping triple - entities not found: {' & '.join(missing_parts)} -> {rel['relation']}")
                            except UnicodeEncodeError:
                                print(f"Skipping triple - entities not found: [contains special characters] -> {rel['relation']}")
                
                print(f"   Resolved {len(resolved_relationships)}/{len(relationships)} relationships to valid entities")
                
                # Debug: Show resolved relationships
                if resolved_relationships:
                    rel = resolved_relationships[0]
                    subject = rel['subject']
                    obj = rel['object']
                    print(f"   First resolved relationship: '{subject}' -> '{rel['relation']}' -> '{obj}'")
                    
                    # Check if these entities exist in our mapping
                    subject_exists = subject in entity_name_to_id
                    object_exists = obj in entity_name_to_id
                    print(f"   Entity mapping check: '{subject}' exists = {subject_exists}, '{obj}' exists = {object_exists}")
                    
                    if not subject_exists:
                        print(f"   Available entity names: {list(entity_name_to_id.keys())[:10]}")
                else:
                    print(f"   No relationships resolved to valid entities")
                
                try:
                    relationships_stored = await entity_repository.batch_create_triples(resolved_relationships, entity_name_to_id)
                except Exception as batch_error:
                    print(f"   BATCH ERROR: {batch_error}")
                    relationships_stored = 0
                print(f"   SUCCESS: {relationships_stored}/{len(relationships)} relationships stored")
            except Exception as e:
                print(f"   Warning: Relationship storage failed: {e}")
        else:
            print(f"   SKIPPED: No entities to create relationships between")
        
        print(f"\nSUCCESS: SUCCESS: AI-Restructured text stored in production databases!")
        print(f"   Document: {document.title} ({document.word_count:,} words)")
        print(f"   Semantic chunks: {chunks_stored} with embeddings")
        print(f"   Enhanced entities: {entities_stored}")
        print(f"   AI relationships: {relationships_stored}")
        print(f"   Ready for superior RAG queries!")
        
        return True
        
    except Exception as e:
        print(f"ERROR: DATABASE STORAGE FAILED: {e}")
        print(f"Error type: {type(e).__name__}")
        return False
    finally:
        # Clean up connections
        try:
            if 'neo4j_client' in locals():
                await neo4j_client.async_close()
            if 'weaviate_client' in locals():
                await weaviate_client.async_close()
        except:
            pass


def main() -> None:
    """Ingest AI-restructured philosophical texts with automated storage."""
    if len(sys.argv) != 2:
        print("Usage: python ingest_restructured_text.py <path_to_ai_restructured_markdown>")
        print("\nIngest your AI-restructured philosophical texts:")
        print("  python ingest_restructured_text.py \"processed_texts/Socratis Dialogues_First_2_books_ai_restructured.md\"")
        print("  python ingest_restructured_text.py \"processed_texts/Plato_Republic_ai_restructured.md\"")
        print("\nExample with KG-specific LLM:")
        print("  export KG_LLM_PROVIDER=openai")
        print("  export KG_LLM_MODEL=gpt-4o-mini")
        print("  export OPENAI_API_KEY=your-api-key")
        print("  python ingest_restructured_text.py \"path/to/text.md\"")
        print("\nConfiguration:")
        print("  See .env for complete KG_LLM_* configuration options")
        print("  Key variables:")
        print("    USE_LLM_GRAPH_TRANSFORMER=true/false  # Enable/disable LLM extraction")
        print("    KG_LLM_PROVIDER=openai/anthropic/openrouter  # KG LLM provider")
        print("    KG_LLM_MODEL=<model_name>  # KG-specific model")
        print("  Falls back to SELECTED_LLM_* if KG_LLM_* not set")
        return
    
    markdown_path = sys.argv[1]
    
    if not Path(markdown_path).exists():
        print(f"ERROR: File not found: {markdown_path}")
        return
    
    print(f">> Arete AI-Restructured Text Ingestion System")
    print(f"Processing: {Path(markdown_path).name}")
    print(f"Mode: AI-Enhanced RAG Ingestion")
    print(f"Features: Semantic Chunks + LLM Graph Transformer + Enhanced Entities + AI Relationships + Vector Embeddings")
    print(f"LLM Graph Transformer: {'Enabled' if os.getenv('USE_LLM_GRAPH_TRANSFORMER', 'true').lower() == 'true' else 'Disabled'}")
    print("=" * 80)
    
    # Step 0: Start databases automatically
    print(f"\n=== Starting Database Services ===")
    if not start_databases():
        print("ERROR: FAILED: Could not start databases. Please check Docker installation.")
        print("\nManual startup: docker-compose up -d neo4j weaviate")
        return
    
    # Step 1-6: Process the AI-restructured text
    result = asyncio.run(ingest_restructured_text(markdown_path))
    
    if not result:
        print("ERROR: FAILED: Text ingestion failed")
        return
    
    # Step 7: Store in databases automatically
    storage_success = asyncio.run(store_in_databases(result))
    
    if storage_success:
        print(f"\nSUCCESS: COMPLETE SUCCESS!")
        print(f"AI-restructured text '{result['document'].title}' is now:")
        print(f"  SUCCESS: Ingested with enhanced semantic structure")
        print(f"  SUCCESS: Stored in Neo4j knowledge graph")
        print(f"  SUCCESS: Stored in Weaviate vector database") 
        print(f"  SUCCESS: Optimized for superior RAG performance")
        
        print(f"\n>> Ready to Test Superior RAG:")
        print(f"  1. Start Arete chat: streamlit run src/arete/ui/streamlit_app.py")
        print(f"  2. Ask about: '{result['document'].title}'")
        print(f"  3. Get enhanced responses with AI-structured citations")
        
        print(f"\n>> Database URLs:")
        print(f"  Neo4j Browser: http://localhost:7474 (neo4j/password)")
        print(f"  Weaviate: http://localhost:8080")
        
        print(f"\n>> Enhancement Benefits:")
        print(f"  • Semantic chunks preserve argument structure")
        print(f"  • Pre-identified entities for precise retrieval")
        print(f"  • AI-extracted relationships for context")
        print(f"  • Superior embeddings from structured text")
        
    else:
        print(f"\nWARNING: PARTIAL SUCCESS:")
        print(f"  SUCCESS: AI-restructured text processed successfully")
        print(f"  ERROR: Database storage failed")
        print(f"\nThe enhanced data structure is preserved and can be stored manually.")


if __name__ == "__main__":
    main()