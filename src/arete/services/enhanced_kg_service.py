"""
Enhanced Knowledge Graph Service using LLMGraphTransformer.

Based on recommendations from philosophical GraphRAG research for improved
relationship extraction in classical philosophical texts.
"""

from typing import List, Dict, Any, Optional, Tuple
import asyncio
import re

from langchain_core.documents import Document as LangChainDocument
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_core.graph_documents import GraphDocument

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
        self.llm_service = llm_service or SimpleLLMService()
        self.config = get_settings()
        
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
            # Create a proper LangChain LLM wrapper for SimpleLLMService
            class SimpleLLMAdapter:
                """Adapter to make SimpleLLMService compatible with LangChain."""
                
                def __init__(self, llm_service: SimpleLLMService):
                    self.llm_service = llm_service
                
                async def ainvoke(self, prompt: str) -> str:
                    """Async invoke for LangChain compatibility."""
                    from arete.models.llm import LLMMessage
                    
                    messages = [LLMMessage(role="user", content=prompt)]
                    response = await self.llm_service.generate_response(
                        messages=messages,
                        max_tokens=1000,
                        temperature=0.1
                    )
                    return response.content
                
                def invoke(self, prompt: str) -> str:
                    """Sync invoke for LangChain compatibility.""" 
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        return loop.run_until_complete(self.ainvoke(prompt))
                    except RuntimeError:
                        # Create new event loop if none exists
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            return loop.run_until_complete(self.ainvoke(prompt))
                        finally:
                            loop.close()
            
            llm_adapter = SimpleLLMAdapter(self.llm_service)
            
            # Try to initialize LLMGraphTransformer with our existing LLM service
            self.llm_transformer = LLMGraphTransformer(
                llm=llm_adapter,
                allowed_nodes=self.allowed_nodes,
                allowed_relationships=self.allowed_relationships,
                node_properties=["description", "type", "importance"],
                relationship_properties=["confidence", "evidence", "context"]
            )
            
        except ImportError:
            print("Warning: LangChain experimental not available. Using fallback extraction.")
            self.llm_transformer = None
        except Exception as e:
            print(f"Warning: Could not initialize LLMGraphTransformer: {e}")
            print("Falling back to direct LLM-based extraction.")
            self.llm_transformer = None
    
    async def extract_knowledge_graph(
        self, 
        text: str, 
        document_id: str,
        chunk_size: int = 1000
    ) -> Tuple[List[Entity], List[Dict[str, Any]]]:
        """
        Extract knowledge graph from text using enhanced philosophical extraction.
        
        Args:
            text: Text to extract knowledge from
            document_id: Source document ID
            chunk_size: Size of text chunks for processing
            
        Returns:
            Tuple of (entities, relationships)
        """
        # Split text into manageable chunks
        chunks = self._split_text(text, chunk_size)
        
        all_entities = []
        all_relationships = []
        
        for i, chunk in enumerate(chunks):
            try:
                # Extract from chunk using LLMGraphTransformer
                entities, relationships = await self._extract_from_chunk(
                    chunk, f"{document_id}_chunk_{i}"
                )
                all_entities.extend(entities)
                all_relationships.extend(relationships)
                
            except Exception as e:
                print(f"Error processing chunk {i}: {e}")
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
            # Create LangChain document
            doc = LangChainDocument(page_content=text, metadata={"chunk_id": chunk_id})
            
            # Transform to graph document
            graph_docs = self.llm_transformer.convert_to_graph_documents([doc])
            
            entities = []
            relationships = []
            
            for graph_doc in graph_docs:
                # Extract entities (nodes)
                for node in graph_doc.nodes:
                    entity = Entity(
                        name=node.id,
                        entity_type=self._map_node_type_to_entity_type(node.type),
                        source_document_id=chunk_id,
                        mentions=[],  # Would be populated in full implementation
                        confidence=0.8
                    )
                    entities.append(entity)
                
                # Extract relationships
                for rel in graph_doc.relationships:
                    relationship = {
                        "subject": rel.source.id,
                        "relation": rel.type,
                        "object": rel.target.id,
                        "confidence": rel.properties.get("confidence", 0.8),
                        "evidence": rel.properties.get("evidence", text[:200]),
                        "source": "llm_graph_transformer"
                    }
                    relationships.append(relationship)
            
            return entities, relationships
            
        except Exception as e:
            print(f"LLMGraphTransformer extraction failed: {e}")
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
            response = self.llm_service.generate_text(
                prompt=prompt,
                max_tokens=800,
                temperature=0.1
            )
            
            return self._parse_fallback_response(response, chunk_id)
            
        except Exception as e:
            print(f"Fallback extraction failed: {e}")
            return [], []
    
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
                    
                    entity = Entity(
                        name=name,
                        entity_type=self._map_string_to_entity_type(entity_type),
                        source_document_id=chunk_id,
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