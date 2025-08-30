"""
Enhanced Knowledge Graph Service using LLMGraphTransformer.

Based on recommendations from philosophical GraphRAG research for improved
relationship extraction in classical philosophical texts.
"""

from typing import List, Dict, Any, Optional, Tuple
import asyncio
import re
from uuid import UUID

from langchain_core.documents import Document as LangChainDocument
from langchain_experimental.graph_transformers import LLMGraphTransformer

from arete.models.entity import Entity, EntityType
from arete.services.simple_llm_service import SimpleLLMService
from arete.config import get_settings


class EnhancedKnowledgeGraphService:
    """
    Enhanced Knowledge Graph extraction service using LLMGraphTransformer.
    
    Implements best practices from philosophical GraphRAG research:
    - Domain-specific entity and relationship schemas
    - Proper philosophical concept recognition
    - LLM-based extraction with philosophical prompts
    - Quality validation and filtering
    """
    
    def __init__(self, llm_service: Optional[SimpleLLMService] = None):
        """Initialize the enhanced KG service."""
        self.config = get_settings()
        
        # Use dedicated KG LLM service if configured, otherwise fall back to general LLM service
        if self.config.kg_llm_provider and self.config.kg_llm_model:
            print(f"INFO: Using dedicated KG LLM: {self.config.kg_llm_provider}/{self.config.kg_llm_model}")
            # Create specialized LLM service for knowledge extraction
            self.llm_service = self._create_kg_llm_service()
        else:
            print(f"INFO: Using general LLM for KG extraction: {self.config.selected_llm_provider}/{self.config.selected_llm_model}")
            self.llm_service = llm_service or SimpleLLMService()
        
        # Define philosophical entity schema
        self.allowed_nodes = [
            "Philosopher",      # Sócrates, Platão, Aristóteles
            "Concept",          # justiça, virtude, conhecimento
            "Work",            # República, Mênon, Fédon
            "Argument",        # Argumento da Caverna, Teoria das Formas
            "School",          # Platonismo, Aristotelismo
            "Place",           # Athens, Academia
            "Character"        # Characters in dialogues
        ]
        
        # Define philosophical relationship schema (English)
        self.allowed_relationships = [
            # Authorship and Creation
            "AUTHORED",           # Plato AUTHORED Republic
            "CREATED",           # Plato CREATED Theory of Forms
            
            # Influence and Learning  
            "INFLUENCED_BY",     # Aristotle INFLUENCED_BY Plato
            "TAUGHT",           # Socrates TAUGHT Plato
            "STUDIED_WITH",     # Plato STUDIED_WITH Socrates
            "MENTORED",         # Socrates MENTORED Plato
            
            # Intellectual Relationships
            "CRITIQUES",        # Aristotle CRITIQUES Theory of Forms
            "DEFENDS",          # Plato DEFENDS Theory of Forms
            "DEVELOPS",         # Aristotle DEVELOPS Plato's concepts
            "REFUTES",          # Socrates REFUTES sophists
            "AGREES_WITH",      # philosopher AGREES_WITH concept
            "DISAGREES_WITH",   # philosopher DISAGREES_WITH concept
            
            # Argumentative Structure
            "CONTAINS_ARGUMENT", # Republic CONTAINS_ARGUMENT Cave Allegory
            "PREMISE_OF",       # premise PREMISE_OF conclusion
            "OBJECTS_TO",       # argument OBJECTS_TO another argument
            "CONCLUDES",        # argument CONCLUDES position
            "SUPPORTS",         # evidence SUPPORTS argument
            
            # Conceptual Relationships
            "PART_OF",          # courage PART_OF virtue
            "EXAMPLE_OF",       # specific case EXAMPLE_OF general concept
            "DEFINES",          # Socrates DEFINES justice
            "EXEMPLIFIES",      # story EXEMPLIFIES concept
            "TYPE_OF",          # subconcept TYPE_OF concept
            
            # Dialogue Structure
            "SPEAKS_WITH",      # Socrates SPEAKS_WITH Meno
            "QUESTIONS",        # Socrates QUESTIONS Meno
            "RESPONDS_TO",      # Meno RESPONDS_TO Socrates
            "CHALLENGES",       # character CHALLENGES argument
            
            # Temporal and Logical
            "PRECEDES",         # event PRECEDES another event
            "RESULTS_IN",       # action RESULTS_IN consequence
            "PRESUPPOSES",      # argument PRESUPPOSES premise
            "LEADS_TO"          # reasoning LEADS_TO conclusion
        ]
        
        # Initialize LLMGraphTransformer
        self.llm_transformer = None
        self._initialize_transformer()
    
    def _initialize_transformer(self):
        """Initialize the LLMGraphTransformer with philosophical schema."""
        try:
            from arete.services.llm_graph_transformer_service import LLMGraphTransformerService
            
            # Use the new LLMGraphTransformerService
            self.llm_transformer = LLMGraphTransformerService(self.llm_service)
            
            if self.llm_transformer.is_available():
                print("✅ Successfully initialized LLMGraphTransformerService with philosophical schema")
            else:
                print("⚠️  LLMGraphTransformerService initialized but LangChain transformer not available - will use fallback")
            
        except ImportError as e:
            print(f"❌ Failed to import LLMGraphTransformerService: {e}")
            print("Falling back to basic extraction.")
            self.llm_transformer = None
        except Exception as e:
            print(f"❌ Could not initialize LLMGraphTransformerService: {e}")
            print("Falling back to basic extraction.")
            self.llm_transformer = None
    
    def _create_kg_llm_service(self) -> SimpleLLMService:
        """Create a specialized LLM service for knowledge graph extraction."""
        from arete.services.simple_llm_service import SimpleLLMService
        
        print(f"DEBUG: Creating KG LLM service with {self.config.kg_llm_provider}/{self.config.kg_llm_model}")
        
        # Create SimpleLLMService
        kg_llm_service = SimpleLLMService()
        
        # Use the correct methods to set provider and model
        kg_llm_service.set_provider(self.config.kg_llm_provider)
        kg_llm_service.set_model(self.config.kg_llm_model)
        
        print(f"DEBUG: Configured KG service - Provider: {kg_llm_service.get_active_provider_name()}, Model: {kg_llm_service.get_active_model_name()}")
        
        return kg_llm_service
    
    async def extract_knowledge_graph(
        self, 
        text: str, 
        document_id: str,
        chunk_size: int = 2000,  # Optimal size for philosophical context preservation
        max_chunks: int = None   # Process all chunks with powerful KG model
    ) -> Tuple[List[Entity], List[Dict[str, Any]]]:
        """
        Extract knowledge graph from text using enhanced philosophical extraction.
        
        Args:
            text: Text to extract knowledge from
            document_id: Document identifier  
            chunk_size: Size of text chunks for processing (larger preserves context)
            max_chunks: Maximum number of chunks to process (None = all chunks)
            
        Returns:
            Tuple of (entities, relationships)
        """
        # Split text into manageable chunks
        chunks = self._split_text(text, chunk_size)
        
        # Optionally limit chunks if max_chunks is specified
        if max_chunks is not None and len(chunks) > max_chunks:
            print(f"INFO: Limiting processing to first {max_chunks} chunks out of {len(chunks)} total chunks")
            chunks = chunks[:max_chunks]
        else:
            print(f"INFO: Processing all {len(chunks)} chunks with dedicated KG model")
        
        all_entities = []
        all_relationships = []
        
        print(f"Processing {len(chunks)} chunks for knowledge extraction...")
        
        for i, chunk in enumerate(chunks):
            print(f"  Processing chunk {i+1}/{len(chunks)}...")
            try:
                # Extract from chunk using LLMGraphTransformer with timeout handling
                entities, relationships = await self._extract_from_chunk(
                    chunk, f"{document_id}_chunk_{i}"
                )
                all_entities.extend(entities)
                all_relationships.extend(relationships)
                print(f"    Found {len(entities)} entities, {len(relationships)} relationships")
                
            except Exception as e:
                print(f"    WARNING: Error processing chunk {i+1}: {e}")
                print(f"    Continuing with remaining chunks...")
                continue
        
        # Deduplicate and merge entities
        merged_entities = self._merge_entities(all_entities)
        
        # Filter and validate relationships
        validated_relationships = self._validate_relationships(all_relationships)
        
        return merged_entities, validated_relationships
    
    async def _extract_from_chunk(
        self, 
        text: str, 
        chunk_id: str
    ) -> Tuple[List[Entity], List[Dict[str, Any]]]:
        """Extract entities and relationships from a text chunk."""
        if not self.llm_transformer:
            # Fallback to basic extraction
            return await self._fallback_extraction(text, chunk_id)
        
        try:
            # Extract document ID from chunk ID
            document_id = self._extract_document_id_from_chunk_id(chunk_id)
            
            # Use the LLMGraphTransformerService for extraction
            entities, relationships = await self.llm_transformer.extract_knowledge_graph(
                text=text,
                document_id=document_id,
                chunk_size=len(text)  # Process the chunk as-is
            )
            
            print(f"    ✅ LLMGraphTransformer extracted {len(entities)} entities, {len(relationships)} relationships")
            return entities, relationships
            
        except Exception as e:
            print(f"❌ LLMGraphTransformerService extraction failed: {e}")
            return await self._fallback_extraction(text, chunk_id)
    
    async def _fallback_extraction(
        self, 
        text: str, 
        chunk_id: str
    ) -> Tuple[List[Entity], List[Dict[str, Any]]]:
        """Fallback extraction method using enhanced prompts."""
        prompt = f"""
        You are an expert in classical philosophy. Extract philosophical entities and relationships from this text.

        ENTITIES to identify:
        - Philosophers (Sócrates, Platão, Aristóteles, etc.)
        - Philosophical Concepts (justiça, virtude, conhecimento, etc.)
        - Works (República, Mênon, Fédon, etc.)
        - Arguments (specific philosophical positions or arguments)

        RELATIONSHIPS to identify:
        {', '.join(self.allowed_relationships)}

        Return in this format:
        ENTITIES:
        Name | Type | Description

        RELATIONSHIPS:
        Subject | Relationship | Object | Confidence

        Text: {text}

        Analysis:
        """
        
        try:
            from arete.services.llm_provider import LLMMessage, MessageRole
            
            messages = [LLMMessage(role=MessageRole.USER, content=prompt)]
            response = await self.llm_service.generate_response(
                messages=messages,
                max_tokens=1000,  # Increased for detailed philosophical analysis
                temperature=0.1,  # Low temperature for consistent extraction
                timeout=120       # Generous timeout for powerful models
            )
            
            response_text = response.content
            
            return self._parse_fallback_response(response_text, chunk_id)
            
        except Exception as e:
            print(f"Fallback extraction failed: {e}")
            return [], []
    
    def _extract_document_id_from_chunk_id(self, chunk_id: str) -> str:
        """Extract document ID from chunk ID format 'doc_id_chunk_N'."""
        if '_chunk_' in chunk_id:
            return chunk_id.split('_chunk_')[0]
        return chunk_id
    
    def _parse_fallback_response(
        self, 
        response: str, 
        chunk_id: str
    ) -> Tuple[List[Entity], List[Dict[str, Any]]]:
        """Parse the fallback LLM response into entities and relationships."""
        entities = []
        relationships = []
        
        lines = response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if 'ENTITIES:' in line:
                current_section = 'entities'
                continue
            elif 'RELATIONSHIPS:' in line:
                current_section = 'relationships'
                continue
            
            if not line or line.startswith('#'):
                continue
                
            if current_section == 'entities' and '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 2:
                    name, entity_type = parts[0], parts[1]
                    description = parts[2] if len(parts) > 2 else ""
                    
                    # Extract document ID from chunk ID and convert to UUID
                    document_id = self._extract_document_id_from_chunk_id(chunk_id)
                    
                    entity = Entity(
                        name=name,
                        entity_type=self._map_string_to_entity_type(entity_type),
                        source_document_id=UUID(document_id),
                        mentions=[],
                        confidence=0.7,
                        properties={"description": description} if description else {}
                    )
                    entities.append(entity)
            
            elif current_section == 'relationships' and '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3:
                    subject, relation, obj = parts[0], parts[1], parts[2]
                    confidence = float(parts[3]) if len(parts) > 3 and parts[3].replace('.', '').isdigit() else 0.7
                    
                    if self._is_valid_philosophical_entity(subject) and self._is_valid_philosophical_entity(obj):
                        relationship = {
                            "subject": subject,
                            "relation": relation,
                            "object": obj,
                            "confidence": confidence,
                            "source": "fallback_llm"
                        }
                        relationships.append(relationship)
        
        return entities, relationships
    
    def _split_text(self, text: str, chunk_size: int) -> List[str]:
        """Split text into chunks for processing."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            if current_size + len(word) > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_size = len(word)
            else:
                current_chunk.append(word)
                current_size += len(word) + 1
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _merge_entities(self, entities: List[Entity]) -> List[Entity]:
        """Merge duplicate entities based on name similarity."""
        merged = {}
        
        for entity in entities:
            name_key = entity.name.lower().strip()
            if name_key in merged:
                # Merge mentions and update confidence
                existing = merged[name_key]
                existing.mentions.extend(entity.mentions)
                existing.confidence = max(existing.confidence, entity.confidence)
            else:
                merged[name_key] = entity
        
        return list(merged.values())
    
    def _validate_relationships(self, relationships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and filter relationships based on quality criteria."""
        validated = []
        
        for rel in relationships:
            # Check if entities are valid philosophical terms
            if (self._is_valid_philosophical_entity(rel["subject"]) and 
                self._is_valid_philosophical_entity(rel["object"]) and
                rel["confidence"] >= 0.5):
                validated.append(rel)
        
        return validated
    
    def _is_valid_philosophical_entity(self, entity: str) -> bool:
        """Check if entity is a valid philosophical entity."""
        if not entity or len(entity) < 2:
            return False
            
        entity_lower = entity.lower().strip()
        
        # Skip pronouns and generic terms
        invalid_terms = {
            'it', 'this', 'that', 'he', 'she', 'they', 'we', 'i', 'you',
            'here', 'there', 'now', 'then', 'what', 'which', 'who', 'how',
            'many', 'some', 'all', 'any', 'each', 'every', 'quickly', 'slowly'
        }
        
        return entity_lower not in invalid_terms and len(entity) >= 3
    
    def _map_node_type_to_entity_type(self, node_type: str) -> EntityType:
        """Map LLMGraphTransformer node type to EntityType."""
        mapping = {
            "Philosopher": EntityType.PERSON,
            "Concept": EntityType.CONCEPT,
            "Work": EntityType.WORK,
            "Argument": EntityType.ARGUMENT,
            "School": EntityType.ORGANIZATION,
            "Place": EntityType.LOCATION,
            "Character": EntityType.PERSON
        }
        return mapping.get(node_type, EntityType.CONCEPT)
    
    def _map_string_to_entity_type(self, type_string: str) -> EntityType:
        """Map string to EntityType."""
        type_mapping = {
            "philosopher": EntityType.PERSON,
            "concept": EntityType.CONCEPT,
            "work": EntityType.WORK,
            "argument": EntityType.ARGUMENT,
            "school": EntityType.ORGANIZATION,
            "place": EntityType.LOCATION,
            "character": EntityType.PERSON
        }
        return type_mapping.get(type_string.lower(), EntityType.CONCEPT)