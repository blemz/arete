"""
Philosophical Text Restructuring Service for RAG Optimization

This service uses LLM-powered processing to transform unstructured philosophical texts
into semantically organized, RAG-friendly formats using KG_LLM_PROVIDER and KG_LLM_MODEL
configuration from environment variables.

Features:
- Multi-pass LLM processing for different transformation tasks
- Dialogue speaker separation for Platonic dialogues
- Argument structure extraction and markup
- Entity identification and relationship mapping
- Citation-ready chunk formatting
- Cross-reference network creation
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

from arete.services.simple_llm_service import SimpleLLMService
from arete.services.llm_provider import LLMMessage, MessageRole, LLMResponse
from arete.config import get_settings

# Setup logger
logger = logging.getLogger(__name__)


class ProcessingMode(Enum):
    """Different processing modes for philosophical texts."""
    DIALOGUE_SEPARATION = "dialogue_separation"
    ARGUMENT_EXTRACTION = "argument_extraction" 
    ENTITY_MARKUP = "entity_markup"
    CITATION_FORMATTING = "citation_formatting"
    FULL_RESTRUCTURE = "full_restructure"


@dataclass
class PhilosophicalContext:
    """Context information for philosophical text processing."""
    author: Optional[str] = None
    work_title: Optional[str] = None
    philosophical_period: Optional[str] = None  # Ancient, Medieval, Modern, Contemporary
    text_type: Optional[str] = None  # dialogue, treatise, commentary, letter
    key_concepts: List[str] = field(default_factory=list)
    major_themes: List[str] = field(default_factory=list)


@dataclass
class RestructuringResult:
    """Result of philosophical text restructuring."""
    restructured_text: str
    processing_mode: ProcessingMode
    context: PhilosophicalContext
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_stats: Dict[str, Any] = field(default_factory=dict)


class PhilosophicalTextRestructurer:
    """
    LLM-powered service for restructuring philosophical texts for optimal RAG processing.
    
    Uses KG_LLM_PROVIDER and KG_LLM_MODEL environment variables for consistent
    knowledge graph extraction quality.
    """
    
    def __init__(self, settings=None):
        """
        Initialize the restructuring service.
        
        Args:
            settings: Configuration settings (uses default if None)
        """
        self.settings = settings or get_settings()
        self.llm_service = SimpleLLMService(self.settings)
        
        # Get KG-specific LLM configuration
        self.kg_provider = os.getenv("KG_LLM_PROVIDER", "openrouter")
        self.kg_model = os.getenv("KG_LLM_MODEL", "deepseek/deepseek-chat-v3.1:free")
        
        logger.info(f"Initialized PhilosophicalTextRestructurer with {self.kg_provider}:{self.kg_model}")
        
        # Processing prompts
        self._init_prompts()
    
    def _init_prompts(self):
        """Initialize specialized prompts for different processing modes."""
        
        self.prompts = {
            ProcessingMode.DIALOGUE_SEPARATION: """
You are a classical philosophy expert specializing in Platonic dialogues. Transform the following unstructured philosophical text into properly formatted dialogue with clear speaker attributions.

INSTRUCTIONS:
1. Identify speakers based on context clues and dialogue markers
2. Format each statement with **Speaker:** prefix
3. Preserve the exact philosophical content
4. Identify main speakers: Socrates, and dialogue partners
5. Use context to determine when speakers change
6. Keep original philosophical arguments intact

INPUT TEXT:
{text}

OUTPUT FORMAT:
**Speaker:** [exact dialogue content]
**Speaker:** [continuing dialogue]

Focus on accuracy - it's better to use **Speaker:** for unclear attributions than to guess incorrectly.
""",

            ProcessingMode.ARGUMENT_EXTRACTION: """
You are a philosophical scholar expert at analyzing argument structures. Extract and clearly structure the philosophical arguments from this text.

INSTRUCTIONS:
1. Identify main thesis/claims
2. Extract supporting premises
3. Note examples or analogies used
4. Mark logical connections
5. Identify counter-arguments
6. Preserve exact quotes for key points

INPUT TEXT:
{text}

OUTPUT FORMAT:
### Main Argument: [Title]

**Thesis:** [main claim]

**Supporting Premises:**
- [premise 1]
- [premise 2]

**Examples/Analogies:**
- [example with context]

**Counter-arguments Addressed:**
- [opposing view and response]

**Key Quote:** "[exact quote]" - [significance]

**Logical Structure:** [how premises connect to conclusion]
""",

            ProcessingMode.ENTITY_MARKUP: """
You are a philosophical knowledge extraction expert. Identify and mark all philosophical entities in this text for knowledge graph construction.

INSTRUCTIONS:
1. Mark philosophers, concepts, works, places, and characters
2. Use consistent entity type labels
3. Focus on philosophically significant entities
4. Include confidence levels where relevant
5. Note relationships between entities

INPUT TEXT:
{text}

OUTPUT FORMAT:
**Philosophers:** Name1, Name2
**Concepts:** concept1, concept2, concept3
**Works:** "Work Title 1", "Work Title 2"  
**Places:** Location1, Location2
**Characters:** character1, character2

**Key Relationships:**
- [Entity1] → [relationship] → [Entity2]
- [Entity3] → [relationship] → [Entity4]

Mark entities with **Entity Type:** formatting throughout the text where they appear.
""",

            ProcessingMode.CITATION_FORMATTING: """
You are a scholarly editor specializing in classical philosophical citations. Create citation-ready chunks from this philosophical text.

INSTRUCTIONS:
1. Break text into coherent semantic chunks (500-1000 characters)
2. Add proper headers with context
3. Include citation information
4. Mark philosophical significance
5. Note connections to other concepts
6. Preserve scholarly accuracy

INPUT TEXT:
{text}

OUTPUT FORMAT:
### [Topic/Argument Title] ([Classical Reference if available])

**Context:** [where this appears in the work and its significance]

**Text:**
[coherent chunk of original text]

**Philosophical Significance:** [why this passage is important]

**Key Concepts:** [main ideas in this chunk]

**Connects to:** [related philosophical ideas or passages]

**Citation Notes:** [any special attribution or reference formatting needed]
""",

            ProcessingMode.FULL_RESTRUCTURE: """
You are a philosophical text processing expert. Transform this unstructured philosophical text into a completely RAG-optimized format with dialogue separation, argument structure, entity markup, and citation formatting.

INSTRUCTIONS:
1. First identify the text type (dialogue, treatise, etc.)
2. Separate speakers if it's a dialogue
3. Extract and structure philosophical arguments
4. Mark all philosophical entities
5. Create citation-ready sections
6. Add cross-references and relationships
7. Preserve all original philosophical content

INPUT TEXT:
{text}

CONTEXT: {context}

OUTPUT: Comprehensive restructured text with all optimizations applied.
"""
        }
    
    async def restructure_text(
        self,
        text: str,
        mode: ProcessingMode = ProcessingMode.FULL_RESTRUCTURE,
        context: Optional[PhilosophicalContext] = None,
        chunk_size: int = 4000
    ) -> RestructuringResult:
        """
        Restructure philosophical text using specified processing mode.
        
        Args:
            text: Original philosophical text to restructure
            mode: Processing mode to use
            context: Optional context information about the text
            chunk_size: Maximum size of text chunks for processing
            
        Returns:
            RestructuringResult with restructured text and metadata
        """
        logger.info(f"Starting {mode.value} processing for {len(text)} characters")
        
        context = context or PhilosophicalContext()
        
        # Handle large texts by chunking
        if len(text) > chunk_size:
            chunks = self._chunk_text(text, chunk_size)
            processed_chunks = []
            
            for i, chunk in enumerate(chunks):
                logger.info(f"Processing chunk {i+1}/{len(chunks)}")
                processed_chunk = await self._process_chunk(chunk, mode, context)
                processed_chunks.append(processed_chunk)
            
            # Combine processed chunks
            restructured_text = self._combine_chunks(processed_chunks, mode)
        else:
            restructured_text = await self._process_chunk(text, mode, context)
        
        # Compile processing statistics
        processing_stats = {
            "original_length": len(text),
            "restructured_length": len(restructured_text),
            "mode": mode.value,
            "provider": self.kg_provider,
            "model": self.kg_model,
            "chunks_processed": len(chunks) if len(text) > chunk_size else 1
        }
        
        result = RestructuringResult(
            restructured_text=restructured_text,
            processing_mode=mode,
            context=context,
            processing_stats=processing_stats
        )
        
        logger.info(f"Restructuring complete: {len(text)} → {len(restructured_text)} characters")
        return result
    
    async def _process_chunk(
        self, 
        chunk: str, 
        mode: ProcessingMode, 
        context: PhilosophicalContext
    ) -> str:
        """Process a single text chunk with the specified mode."""
        
        # Get the appropriate prompt
        prompt_template = self.prompts[mode]
        
        # Format prompt with context if needed
        if mode == ProcessingMode.FULL_RESTRUCTURE:
            context_info = f"""
Author: {context.author or 'Unknown'}
Work: {context.work_title or 'Unknown'}
Period: {context.philosophical_period or 'Unknown'}
Type: {context.text_type or 'Unknown'}
Key Concepts: {', '.join(context.key_concepts) if context.key_concepts else 'None specified'}
Major Themes: {', '.join(context.major_themes) if context.major_themes else 'None specified'}
"""
            prompt = prompt_template.format(text=chunk, context=context_info)
        else:
            prompt = prompt_template.format(text=chunk)
        
        # Create message for LLM
        messages = [LLMMessage(
            role=MessageRole.USER,
            content=prompt
        )]
        
        try:
            # Generate response using KG-specific provider and model
            response = await self.llm_service.generate_response(
                messages=messages,
                provider=self.kg_provider,
                model=self.kg_model,
                temperature=0.3,  # Lower temperature for more consistent formatting
                max_tokens=6000   # Ensure enough tokens for restructured output
            )
            
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"Error processing chunk with {self.kg_provider}: {e}")
            # Return original chunk if processing fails
            return chunk
    
    def _chunk_text(self, text: str, chunk_size: int) -> List[str]:
        """Split text into chunks while preserving paragraph boundaries."""
        chunks = []
        current_chunk = ""
        
        # Split by paragraphs to preserve structure
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size
            if len(current_chunk) + len(paragraph) + 2 > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = paragraph
                else:
                    # Paragraph itself is too large, split by sentences
                    sentences = paragraph.split('. ')
                    temp_chunk = ""
                    for sentence in sentences:
                        if len(temp_chunk) + len(sentence) + 2 > chunk_size:
                            if temp_chunk:
                                chunks.append(temp_chunk.strip() + '.')
                            temp_chunk = sentence
                        else:
                            temp_chunk += sentence + '. ' if not temp_chunk else sentence + '. '
                    current_chunk = temp_chunk.rstrip('. ')
            else:
                current_chunk += '\n\n' + paragraph if current_chunk else paragraph
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _combine_chunks(self, processed_chunks: List[str], mode: ProcessingMode) -> str:
        """Combine processed chunks back into coherent text."""
        
        if mode == ProcessingMode.DIALOGUE_SEPARATION:
            # Join dialogues with clear separators
            return '\n\n'.join(processed_chunks)
        
        elif mode == ProcessingMode.ARGUMENT_EXTRACTION:
            # Combine arguments with section separators
            combined = ""
            for i, chunk in enumerate(processed_chunks):
                combined += f"\n\n## Section {i+1}\n\n{chunk}"
            return combined.strip()
        
        elif mode == ProcessingMode.ENTITY_MARKUP:
            # Combine entity markups, merging duplicates
            return '\n\n---\n\n'.join(processed_chunks)
        
        elif mode == ProcessingMode.CITATION_FORMATTING:
            # Join citation chunks with clear divisions
            return '\n\n---\n\n'.join(processed_chunks)
        
        else:  # FULL_RESTRUCTURE
            # Smart combination preserving structure
            return '\n\n'.join(processed_chunks)
    
    async def restructure_file(
        self,
        input_file: Path,
        output_file: Optional[Path] = None,
        mode: ProcessingMode = ProcessingMode.FULL_RESTRUCTURE,
        context: Optional[PhilosophicalContext] = None
    ) -> Path:
        """
        Restructure a philosophical text file.
        
        Args:
            input_file: Path to input text file
            output_file: Path for output (generated if None)
            mode: Processing mode to use
            context: Optional context information
            
        Returns:
            Path to the restructured output file
        """
        # Read input file
        with open(input_file, 'r', encoding='utf-8') as f:
            original_text = f.read()
        
        # Process the text
        result = await self.restructure_text(original_text, mode, context)
        
        # Generate output filename if not provided
        if output_file is None:
            suffix = f"_{mode.value}"
            output_file = input_file.parent / f"{input_file.stem}{suffix}_restructured.md"
        
        # Write restructured text
        with open(output_file, 'w', encoding='utf-8') as f:
            # Add metadata header
            f.write(f"# Restructured Philosophical Text\n\n")
            f.write(f"**Original:** {input_file.name}\n")
            f.write(f"**Processing Mode:** {mode.value}\n")
            f.write(f"**Provider:** {self.kg_provider}\n")
            f.write(f"**Model:** {self.kg_model}\n")
            if context.author:
                f.write(f"**Author:** {context.author}\n")
            if context.work_title:
                f.write(f"**Work:** {context.work_title}\n")
            f.write(f"**Processing Date:** {result.processing_stats}\n\n")
            f.write("---\n\n")
            f.write(result.restructured_text)
        
        logger.info(f"Restructured text saved to: {output_file}")
        return output_file


# Convenience functions for common use cases

async def restructure_socratic_dialogue(
    text: str,
    author: str = "Plato",
    work_title: Optional[str] = None
) -> RestructuringResult:
    """
    Convenience function for restructuring Socratic dialogues.
    
    Args:
        text: Original dialogue text
        author: Author name (default: Plato)
        work_title: Title of the work
        
    Returns:
        RestructuringResult with dialogue formatting
    """
    context = PhilosophicalContext(
        author=author,
        work_title=work_title,
        philosophical_period="Ancient",
        text_type="dialogue",
        key_concepts=["wisdom", "virtue", "knowledge", "justice"],
        major_themes=["epistemology", "ethics", "metaphysics"]
    )
    
    restructurer = PhilosophicalTextRestructurer()
    return await restructurer.restructure_text(
        text, 
        mode=ProcessingMode.DIALOGUE_SEPARATION,
        context=context
    )


async def extract_philosophical_arguments(
    text: str,
    context: Optional[PhilosophicalContext] = None
) -> RestructuringResult:
    """
    Convenience function for extracting philosophical argument structures.
    
    Args:
        text: Original philosophical text
        context: Optional context information
        
    Returns:
        RestructuringResult with argument structure
    """
    restructurer = PhilosophicalTextRestructurer()
    return await restructurer.restructure_text(
        text,
        mode=ProcessingMode.ARGUMENT_EXTRACTION,
        context=context
    )