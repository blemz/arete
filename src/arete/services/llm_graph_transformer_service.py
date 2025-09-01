"""
Enhanced LLM Graph Transformer Service for Philosophical Text Processing.

This service implements LangChain's LLMGraphTransformer with domain-specific
philosophical entity and relationship schemas for classical philosophical texts.
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID

from langchain_core.documents import Document as LangChainDocument
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from arete.config import get_settings
from arete.models.entity import Entity, EntityType
from arete.services.simple_llm_service import SimpleLLMService


class PhilosophicalLLMGraphTransformer:
    """
    Specialized LLMGraphTransformer for philosophical text extraction.
    
    This class wraps LangChain's LLMGraphTransformer with philosophical domain
    knowledge, optimized prompts, and post-processing for classical texts.
    """
    
    def __init__(self, llm_service: Optional[SimpleLLMService] = None):
        """Initialize the philosophical graph transformer."""
        self.config = get_settings()
        self.llm_service = llm_service or SimpleLLMService()
        
        # Define philosophical entity schema
        self.allowed_nodes = [
            "Philosopher",      # Socrates, Plato, Aristotle
            "Concept",          # justice, virtue, knowledge  
            "Work",            # Republic, Meno, Phaedo
            "Argument",        # Cave Allegory, Theory of Forms
            "School",          # Platonism, Aristotelianism
            "Place",           # Athens, Academy
            "Character",       # Characters in dialogues
            "Definition",      # Specific definitions of concepts
            "Question",        # Philosophical questions posed
            "Method"           # Philosophical methods like dialectic
        ]
        
        # Define philosophical relationship schema
        self.allowed_relationships = [
            # Authorship and Creation
            ("Philosopher", "AUTHORED", "Work"),
            ("Philosopher", "CREATED", "Concept"),
            ("Philosopher", "FORMULATED", "Argument"),
            
            # Influence and Learning  
            ("Philosopher", "INFLUENCED", "Philosopher"),
            ("Philosopher", "TAUGHT", "Philosopher"),
            ("Philosopher", "STUDIED_WITH", "Philosopher"),
            ("Philosopher", "MENTORED", "Philosopher"),
            
            # Intellectual Relationships
            ("Philosopher", "CRITIQUES", "Concept"),
            ("Philosopher", "CRITIQUES", "Argument"),
            ("Philosopher", "DEFENDS", "Concept"),
            ("Philosopher", "DEVELOPS", "Concept"),
            ("Philosopher", "REFUTES", "Argument"),
            ("Philosopher", "AGREES_WITH", "Concept"),
            ("Philosopher", "DISAGREES_WITH", "Concept"),
            
            # Argumentative Structure
            ("Work", "CONTAINS", "Argument"),
            ("Work", "DISCUSSES", "Concept"),
            ("Argument", "PREMISE_OF", "Argument"),
            ("Argument", "OBJECTS_TO", "Argument"),
            ("Argument", "CONCLUDES", "Concept"),
            ("Argument", "SUPPORTS", "Concept"),
            
            # Conceptual Relationships
            ("Concept", "PART_OF", "Concept"),
            ("Concept", "EXAMPLE_OF", "Concept"),
            ("Concept", "TYPE_OF", "Concept"),
            ("Definition", "DEFINES", "Concept"),
            ("Argument", "EXEMPLIFIES", "Concept"),
            
            # Dialogue Structure
            ("Character", "SPEAKS_WITH", "Character"),
            ("Character", "QUESTIONS", "Character"),
            ("Character", "RESPONDS_TO", "Character"),
            ("Character", "CHALLENGES", "Argument"),
            
            # Temporal and Logical
            ("Argument", "PRECEDES", "Argument"),
            ("Argument", "RESULTS_IN", "Concept"),
            ("Argument", "PRESUPPOSES", "Concept"),
            ("Method", "LEADS_TO", "Concept")
        ]
        
        # Initialize the LLMGraphTransformer
        self.transformer = self._create_transformer()
    
    def _create_transformer(self) -> Optional[LLMGraphTransformer]:
        """Create and configure the LLMGraphTransformer."""
        try:
            # Get the appropriate LLM based on current configuration
            llm = self._create_langchain_llm()
            
            # Get the actual KG provider being used
            kg_provider = (self.config.kg_llm_provider or self.config.selected_llm_provider).lower()
            kg_model = self.config.kg_llm_model or self.config.selected_llm_model
            
            # Test the LLM connection first with a simple call
            print("[INFO] Testing LLM connection...")
            try:
                test_response = llm.invoke("Test connection")
                if not test_response or not test_response.content:
                    print(f"[WARN] LLM test failed - no response content")
                    return None
                print(f"[OK] LLM connection test successful")
            except Exception as test_error:
                print(f"[WARN] LLM connection test failed: {test_error}")
                print(f"[INFO] This is likely due to missing API key or network issues")
                return None
            
            # Create philosophical extraction prompt
            philosophical_prompt = self._create_philosophical_prompt()
            
            # Initialize LLMGraphTransformer with philosophical schema
            transformer = LLMGraphTransformer(
                llm=llm,
                allowed_nodes=self.allowed_nodes,
                allowed_relationships=self.allowed_relationships,
                prompt=philosophical_prompt
            )
            
            print(f"[OK] Successfully initialized LLMGraphTransformer with {kg_provider} ({kg_model})")
            return transformer
            
        except ImportError as e:
            print(f"[ERROR] LangChain experimental not available: {e}")
            return None
        except Exception as e:
            print(f"[ERROR] Failed to initialize LLMGraphTransformer: {e}")
            return None
    
    def _create_langchain_llm(self):
        """Create a LangChain LLM instance based on KG-specific configuration."""
        # Use KG-specific LLM settings if available, otherwise fall back to global settings
        provider = (self.config.kg_llm_provider or self.config.selected_llm_provider).lower()
        model = self.config.kg_llm_model or self.config.selected_llm_model
        
        print(f"[INFO] Using KG LLM: provider={provider}, model={model}")
        
        if provider == "openai":
            return ChatOpenAI(
                model=model,
                temperature=0.0,  # Deterministic extraction
                api_key=self.config.openai_api_key
            )
        elif provider == "anthropic":
            return ChatAnthropic(
                model=model,
                temperature=0.0,
                api_key=self.config.anthropic_api_key
            )
        elif provider == "openrouter":
            return ChatOpenAI(
                model=model,
                temperature=0.0,
                base_url="https://openrouter.ai/api/v1",
                api_key=self.config.openrouter_api_key
            )
        else:
            # Fallback to OpenAI with gpt-4o-mini for broad compatibility
            print(f"[WARN] Provider {provider} not supported for LLMGraphTransformer, using OpenAI fallback")
            return ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.0,
                api_key=self.config.openai_api_key
            )
    
    def _create_philosophical_prompt(self):
        """Create a specialized prompt for philosophical text extraction."""
        # For now, we'll use the default prompt and let LLMGraphTransformer handle it
        # Future enhancement: create custom PromptTemplate for philosophical domain
        return None
    
    async def extract_graph_from_text(
        self, 
        text: str, 
        document_id: str,
        chunk_size: int = 2000  # Optimal size for maintaining context in philosophical texts
    ) -> Tuple[List[Entity], List[Dict[str, Any]]]:
        """
        Extract knowledge graph from philosophical text.
        
        Args:
            text: Text to extract knowledge from
            document_id: Document identifier
            chunk_size: Size of text chunks for processing
            
        Returns:
            Tuple of (entities, relationships)
        """
        if not self.transformer:
            print("[WARN] LLMGraphTransformer not available, using fallback extraction")
            return await self._fallback_extraction(text, document_id)
        
        print(f"[DEBUG] LLMGraphTransformer available: {type(self.transformer)}")
        print(f"[DEBUG] Transformer has convert_to_graph_documents: {hasattr(self.transformer, 'convert_to_graph_documents')}")
        
        # Split text into chunks for better processing
        chunks = self._split_text(text, chunk_size)
        print(f"[INFO] Processing {len(chunks)} chunks for knowledge extraction...")
        
        all_entities = []
        all_relationships = []
        
        # Limit processing to first 5 chunks to avoid API rate limits during testing
        max_chunks = min(5, len(chunks))
        print(f"[INFO] Processing first {max_chunks} chunks (rate limiting for testing)")
        
        # Add delay between requests to respect rate limits (500 RPM = ~8.3 requests per second max)
        # We'll be conservative and do 1 request per 2 seconds
        request_delay = 2.0  # seconds between requests
        
        for i, chunk in enumerate(chunks[:max_chunks]):
            print(f"  [INFO] Processing chunk {i+1}/{max_chunks} (size: {len(chunk)} chars)...")
            
            # Add delay between requests (except for the first one)
            if i > 0:
                print(f"  [INFO] Waiting {request_delay}s to respect rate limits...")
                await asyncio.sleep(request_delay)
            
            try:
                # Create LangChain document
                doc = LangChainDocument(
                    page_content=chunk, 
                    metadata={"chunk_id": f"{document_id}_chunk_{i}", "document_id": document_id}
                )
                
                # Transform to graph document with timeout
                try:
                    # Increased timeout for complex graph extraction
                    graph_docs = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None, self.transformer.convert_to_graph_documents, [doc]
                        ),
                        timeout=120.0  # Increased to 120 seconds for gpt-5-mini model
                    )
                except asyncio.TimeoutError:
                    print(f"    [ERROR] LLM transform timed out for chunk {i+1} after 120s")
                    print(f"    [DEBUG] This may be due to rate limits (500 RPM) or API issues")
                    print(f"    [DEBUG] Model: {self.llm_model}, Provider: {self.llm_provider}")
                    continue
                except Exception as transform_error:
                    error_msg = str(transform_error).lower()
                    if "rate" in error_msg or "429" in error_msg or "quota" in error_msg:
                        print(f"    [ERROR] Rate limit hit for chunk {i+1}: {transform_error}")
                        print(f"    [INFO] Waiting 10 seconds before retrying...")
                        await asyncio.sleep(10)
                        # Retry once after rate limit
                        try:
                            graph_docs = await asyncio.wait_for(
                                asyncio.get_event_loop().run_in_executor(
                                    None, self.transformer.convert_to_graph_documents, [doc]
                                ),
                                timeout=120.0
                            )
                        except Exception as retry_error:
                            print(f"    [ERROR] Retry failed: {retry_error}")
                            continue
                    else:
                        print(f"    [ERROR] LLM transform failed for chunk {i+1}: {transform_error}")
                        # For debugging: print the actual chunk content length and first 100 chars
                        print(f"    [DEBUG] Chunk length: {len(chunk)}")
                        print(f"    [DEBUG] Chunk preview: {chunk[:100]}...")
                        continue
                
                # Check if graph_docs is valid
                if graph_docs is None or not isinstance(graph_docs, list):
                    print(f"    [WARN] No valid graph documents returned for chunk {i+1} (got type: {type(graph_docs)})")
                    continue
                
                if len(graph_docs) == 0:
                    print(f"    [WARN] Empty graph documents list for chunk {i+1}")
                    continue
                
                # Extract entities and relationships
                entities, relationships = self._process_graph_documents(graph_docs, document_id)
                
                all_entities.extend(entities)
                all_relationships.extend(relationships)
                
                print(f"    [OK] Found {len(entities)} entities, {len(relationships)} relationships")
                
            except Exception as e:
                print(f"    [ERROR] Error processing chunk {i+1}: {e}")
                print(f"    [DEBUG] Error type: {type(e).__name__}")
                continue
        
        # Post-process results
        merged_entities = self._merge_entities(all_entities)
        validated_relationships = self._validate_relationships(all_relationships)
        
        print(f"[RESULT] Final results: {len(merged_entities)} unique entities, {len(validated_relationships)} validated relationships")
        
        return merged_entities, validated_relationships
    
    def _process_graph_documents(
        self, 
        graph_docs: List, 
        document_id: str
    ) -> Tuple[List[Entity], List[Dict[str, Any]]]:
        """Process LangChain graph documents into our domain models."""
        entities = []
        relationships = []
        
        for graph_doc in graph_docs:
            # Extract entities (nodes)
            for node in graph_doc.nodes:
                # Extract description from node properties if available
                description = None
                if hasattr(node, 'properties') and node.properties:
                    # Convert properties dict to description string
                    if isinstance(node.properties, dict):
                        # Get description if it exists, otherwise format properties as description
                        description = node.properties.get('description')
                        if not description and node.properties:
                            # Format other properties as description
                            prop_strings = [f"{k}: {v}" for k, v in node.properties.items() 
                                          if k != 'description' and v]
                            if prop_strings:
                                description = "; ".join(prop_strings)[:1000]  # Limit to 1000 chars
                
                entity = Entity(
                    name=node.id,
                    entity_type=self._map_node_type_to_entity_type(node.type),
                    source_document_id=UUID(document_id),
                    mentions=[],
                    confidence=0.9,  # High confidence for LLM extraction
                    description=description  # Store properties as description
                )
                entities.append(entity)
            
            # Extract relationships
            for rel in graph_doc.relationships:
                relationship = {
                    "subject": rel.source.id,
                    "relation": rel.type,
                    "object": rel.target.id,
                    "confidence": rel.properties.get("confidence", 0.9),
                    "evidence": rel.properties.get("evidence", ""),
                    "source": "llm_graph_transformer"
                }
                relationships.append(relationship)
        
        return entities, relationships
    
    async def _fallback_extraction(
        self, 
        text: str, 
        document_id: str
    ) -> Tuple[List[Entity], List[Dict[str, Any]]]:
        """Fallback extraction using direct LLM prompting."""
        prompt = f"""
You are an expert in classical philosophy. Extract philosophical entities and relationships from this text.

ENTITIES to identify (with types):
- Philosopher: Socrates, Plato, Aristotle, etc.
- Concept: justice, virtue, knowledge, etc.
- Work: Republic, Meno, Phaedo, etc.
- Argument: Cave Allegory, Theory of Forms, etc.
- School: Platonism, Aristotelianism, etc.
- Place: Athens, Academy, etc.
- Character: Characters in dialogues
- Definition: Specific definitions provided
- Question: Philosophical questions posed
- Method: Dialectic, induction, etc.

RELATIONSHIPS to identify:
{', '.join([f"{r[0]} {r[1]} {r[2]}" for r in self.allowed_relationships[:10]])}
... and others from philosophical context

Return in JSON format:
{{
  "entities": [
    {{"name": "entity_name", "type": "entity_type", "description": "brief_description"}}
  ],
  "relationships": [
    {{"subject": "entity1", "relation": "RELATIONSHIP_TYPE", "object": "entity2", "confidence": 0.8}}
  ]
}}

Text: {text}

Analysis:"""
        
        try:
            from arete.services.llm_provider import LLMMessage, MessageRole
            
            messages = [LLMMessage(role=MessageRole.USER, content=prompt)]
            response = await self.llm_service.generate_response(
                messages=messages,
                max_tokens=2000,
                temperature=0.1,
                timeout=120
            )
            
            return self._parse_json_response(response.content, document_id)
            
        except Exception as e:
            print(f"[ERROR] Fallback extraction failed: {e}")
            return [], []
    
    def _parse_json_response(
        self, 
        response: str, 
        document_id: str
    ) -> Tuple[List[Entity], List[Dict[str, Any]]]:
        """Parse JSON response from fallback extraction."""
        import json
        import re
        
        entities = []
        relationships = []
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                return entities, relationships
            
            data = json.loads(json_match.group())
            
            # Process entities
            for ent_data in data.get("entities", []):
                entity = Entity(
                    name=ent_data["name"],
                    entity_type=self._map_string_to_entity_type(ent_data["type"]),
                    source_document_id=UUID(document_id),
                    mentions=[],
                    confidence=0.8,
                    description=ent_data.get("description", "")  # Use description field directly
                )
                entities.append(entity)
            
            # Process relationships
            for rel_data in data.get("relationships", []):
                if self._is_valid_relationship(rel_data):
                    relationship = {
                        "subject": rel_data["subject"],
                        "relation": rel_data["relation"],
                        "object": rel_data["object"],
                        "confidence": rel_data.get("confidence", 0.8),
                        "source": "fallback_llm"
                    }
                    relationships.append(relationship)
        
        except Exception as e:
            print(f"[ERROR] Failed to parse JSON response: {e}")
        
        return entities, relationships
    
    def _split_text(self, text: str, chunk_size: int) -> List[str]:
        """Split text into chunks preserving sentence boundaries."""
        # Simple sentence-aware chunking
        sentences = text.split('. ')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            if current_size + sentence_size > chunk_size and current_chunk:
                chunks.append('. '.join(current_chunk) + '.')
                current_chunk = [sentence]
                current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size + 2  # Account for '. '
        
        if current_chunk:
            chunks.append('. '.join(current_chunk))
        
        return chunks
    
    def _merge_entities(self, entities: List[Entity]) -> List[Entity]:
        """Merge duplicate entities based on name similarity."""
        merged = {}
        
        for entity in entities:
            # Normalize name for deduplication
            name_key = entity.name.lower().strip()
            
            if name_key in merged:
                # Merge mentions and update confidence
                existing = merged[name_key]
                existing.mentions.extend(entity.mentions)
                existing.confidence = max(existing.confidence, entity.confidence)
                
                # Merge descriptions if both exist
                if entity.description and existing.description:
                    # Combine descriptions if they're different
                    if entity.description not in existing.description:
                        combined = f"{existing.description}; {entity.description}"
                        # Limit to 1000 chars (Entity description field limit)
                        existing.description = combined[:1000]
                elif entity.description and not existing.description:
                    existing.description = entity.description
            else:
                merged[name_key] = entity
        
        return list(merged.values())
    
    def _validate_relationships(self, relationships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and filter relationships."""
        validated = []
        
        for rel in relationships:
            if self._is_valid_relationship(rel):
                validated.append(rel)
        
        return validated
    
    def _is_valid_relationship(self, rel: Dict[str, Any]) -> bool:
        """Check if relationship is valid."""
        required_keys = ["subject", "relation", "object"]
        
        # Check required keys
        if not all(key in rel for key in required_keys):
            return False
        
        # Check confidence threshold
        if rel.get("confidence", 0) < 0.5:
            return False
        
        # Check entity validity
        if not (self._is_valid_entity_name(rel["subject"]) and 
                self._is_valid_entity_name(rel["object"])):
            return False
        
        return True
    
    def _is_valid_entity_name(self, name: str) -> bool:
        """Check if entity name is valid."""
        if not name or len(name) < 2:
            return False
        
        # Skip pronouns and generic terms
        invalid_terms = {
            'it', 'this', 'that', 'he', 'she', 'they', 'we', 'i', 'you',
            'here', 'there', 'now', 'then', 'what', 'which', 'who', 'how'
        }
        
        return name.lower().strip() not in invalid_terms
    
    def _map_node_type_to_entity_type(self, node_type: str) -> EntityType:
        """Map LLMGraphTransformer node type to EntityType."""
        mapping = {
            "Philosopher": EntityType.PERSON,
            "Concept": EntityType.CONCEPT,
            "Work": EntityType.WORK,
            "Argument": EntityType.CONCEPT,  # Arguments are conceptual entities
            "School": EntityType.CONCEPT,   # Philosophical schools are concepts
            "Place": EntityType.PLACE,
            "Character": EntityType.PERSON,
            "Definition": EntityType.CONCEPT,
            "Question": EntityType.CONCEPT,
            "Method": EntityType.CONCEPT
        }
        return mapping.get(node_type, EntityType.CONCEPT)
    
    def _map_string_to_entity_type(self, type_string: str) -> EntityType:
        """Map string to EntityType."""
        type_mapping = {
            "philosopher": EntityType.PERSON,
            "concept": EntityType.CONCEPT,
            "work": EntityType.WORK,
            "argument": EntityType.CONCEPT,  # Arguments are conceptual entities
            "school": EntityType.CONCEPT,   # Philosophical schools are concepts
            "place": EntityType.PLACE,
            "character": EntityType.PERSON,
            "definition": EntityType.CONCEPT,
            "question": EntityType.CONCEPT,
            "method": EntityType.CONCEPT
        }
        return type_mapping.get(type_string.lower(), EntityType.CONCEPT)


class LLMGraphTransformerService:
    """
    Service wrapper for PhilosophicalLLMGraphTransformer.
    
    This service provides a clean interface for the rest of the application
    to use LLMGraphTransformer functionality.
    """
    
    def __init__(self, llm_service: Optional[SimpleLLMService] = None):
        """Initialize the service."""
        self.transformer = PhilosophicalLLMGraphTransformer(llm_service)
    
    async def extract_knowledge_graph(
        self, 
        text: str, 
        document_id: str,
        **kwargs
    ) -> Tuple[List[Entity], List[Dict[str, Any]]]:
        """
        Extract knowledge graph from text.
        
        Args:
            text: Text to process
            document_id: Document identifier
            **kwargs: Additional parameters for extraction
            
        Returns:
            Tuple of (entities, relationships)
        """
        return await self.transformer.extract_graph_from_text(text, document_id, **kwargs)
    
    def get_supported_node_types(self) -> List[str]:
        """Get list of supported node types."""
        return self.transformer.allowed_nodes.copy()
    
    def get_supported_relationships(self) -> List[Tuple[str, str, str]]:
        """Get list of supported relationship types."""
        return self.transformer.allowed_relationships.copy()
    
    def is_available(self) -> bool:
        """Check if LLMGraphTransformer is available."""
        return self.transformer.transformer is not None