#!/usr/bin/env python3
"""
Enhanced Prompt Templates for Arete RAG System

Provides intelligent, dynamic, and structured prompts that:
1. Adapt to any philosophical text/author dynamically 
2. Structure responses in clear sections
3. Use beginner-friendly language
4. Include error guards against hallucination
5. Maintain scholarly accuracy with proper citations
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum


class PromptStyle(Enum):
    """Different prompt styles for different use cases."""
    EDUCATIONAL = "educational"  # For beginners, accessible language
    SCHOLARLY = "scholarly"      # For advanced users, technical language
    CONVERSATIONAL = "conversational"  # For casual exploration


@dataclass
class ContextMetadata:
    """Metadata about the retrieved context."""
    authors: Set[str]
    works: Set[str] 
    total_chunks: int
    primary_source: Optional[str] = None
    citations: Dict[str, str] = None  # work -> citation format mapping
    
    def __post_init__(self):
        if self.citations is None:
            self.citations = {}
    
    def get_context_description(self) -> str:
        """Generate dynamic context description with explicit work titles."""
        if len(self.authors) == 1 and len(self.works) == 1:
            author = list(self.authors)[0]
            work = list(self.works)[0]
            return f"{author}'s {work}"
        elif len(self.authors) == 1:
            author = list(self.authors)[0]
            works_list = ", ".join(sorted(self.works))
            return f"{author}'s {works_list}"
        elif len(self.works) == 1:
            work = list(self.works)[0]
            authors_list = " and ".join(sorted(self.authors))
            return f"{work} by {authors_list}"
        else:
            # Multiple authors and works - be explicit about what's included
            if len(self.authors) <= 3 and len(self.works) <= 3:
                works_list = ", ".join(sorted(self.works))
                return f"the following texts: {works_list}"
            else:
                return "multiple classical philosophical texts"
    
    def get_detailed_source_list(self) -> str:
        """Generate detailed list of sources for context header."""
        if not self.works:
            return "classical philosophical texts"
            
        # Group works by author when possible
        author_works = {}
        for work in self.works:
            # Try to match work to author based on common knowledge
            matched_author = None
            for author in self.authors:
                if self._work_belongs_to_author(work, author):
                    matched_author = author
                    break
            
            if matched_author:
                if matched_author not in author_works:
                    author_works[matched_author] = []
                author_works[matched_author].append(work)
        
        # Format the source list
        source_parts = []
        for author, works in author_works.items():
            if len(works) == 1:
                source_parts.append(f"{author}'s {works[0]}")
            else:
                works_str = ", ".join(sorted(works))
                source_parts.append(f"{author}'s {works_str}")
        
        # Add any unmatched works
        unmatched_works = self.works - {work for works in author_works.values() for work in works}
        if unmatched_works:
            source_parts.extend(sorted(unmatched_works))
        
        return ", ".join(source_parts)
    
    def _work_belongs_to_author(self, work: str, author: str) -> bool:
        """Determine if a work belongs to a specific author."""
        # Simple heuristic matching - could be enhanced with a lookup table
        work_lower = work.lower()
        author_lower = author.lower()
        
        plato_works = {'apology', 'charmides', 'republic', 'meno', 'phaedo', 'symposium', 'timaeus'}
        aristotle_works = {'nicomachean ethics', 'politics', 'metaphysics', 'poetics'}
        
        if author_lower == 'plato' and any(pw in work_lower for pw in plato_works):
            return True
        elif author_lower == 'aristotle' and any(aw in work_lower for aw in aristotle_works):
            return True
        
        return False


class PromptTemplate:
    """Enhanced prompt template system for Arete RAG responses."""
    
    @staticmethod
    def extract_context_metadata(search_results: List[Dict[str, Any]]) -> ContextMetadata:
        """
        Extract metadata from search results to build dynamic context.
        
        This analyzes the retrieved chunks to identify:
        - Which authors are represented
        - Which works are cited
        - Citation formats for references (Stephanus numbers, Book/Chapter)
        - The primary source if clear
        """
        authors = set()
        works = set()
        citations = {}
        
        # Enhanced extraction from content and metadata
        for result in search_results:
            # Check both content and metadata for source information
            content = result.get('properties', {}).get('content', '').lower()
            metadata = result.get('properties', {})
            
            # Try to extract from metadata first (more reliable)
            if 'source' in metadata:
                source = metadata['source']
                if 'apology' in source.lower():
                    works.add('Apology')
                    authors.add('Plato')
                    citations['Apology'] = 'Stephanus'
                elif 'charmides' in source.lower():
                    works.add('Charmides')
                    authors.add('Plato')
                    citations['Charmides'] = 'Stephanus'
                elif 'republic' in source.lower():
                    works.add('Republic')
                    authors.add('Plato')
                    citations['Republic'] = 'Stephanus'
                elif 'nicomachean' in source.lower():
                    works.add('Nicomachean Ethics')
                    authors.add('Aristotle')
                    citations['Nicomachean Ethics'] = 'Bekker'
            
            # Fallback to content-based detection
            # Detect common authors from content patterns
            if any(term in content for term in ['plato', 'platonic']):
                authors.add('Plato')
            if any(term in content for term in ['aristotle', 'aristotelian']):
                authors.add('Aristotle')
            if any(term in content for term in ['socrates', 'socratic']):
                authors.add('Socrates')
                
            # Detect works from content patterns
            if any(term in content for term in ['apology', 'defense']):
                works.add('Apology')
                if 'Apology' not in citations:
                    citations['Apology'] = 'Stephanus'
            if any(term in content for term in ['charmides', 'temperance']):
                works.add('Charmides')
                if 'Charmides' not in citations:
                    citations['Charmides'] = 'Stephanus'
            if any(term in content for term in ['republic']):
                works.add('Republic')
                if 'Republic' not in citations:
                    citations['Republic'] = 'Stephanus'
            if any(term in content for term in ['nicomachean ethics']):
                works.add('Nicomachean Ethics')
                if 'Nicomachean Ethics' not in citations:
                    citations['Nicomachean Ethics'] = 'Bekker'
            if any(term in content for term in ['meno']):
                works.add('Meno')
                if 'Meno' not in citations:
                    citations['Meno'] = 'Stephanus'
            if any(term in content for term in ['phaedo']):
                works.add('Phaedo')
                if 'Phaedo' not in citations:
                    citations['Phaedo'] = 'Stephanus'
        
        # Default fallback if no specific detection
        if not authors:
            authors.add('Classical Philosophers')
        if not works:
            works.add('Classical Texts')
            
        return ContextMetadata(
            authors=authors,
            works=works,
            total_chunks=len(search_results),
            citations=citations
        )
    
    @staticmethod
    def build_educational_prompt(
        query: str,
        context_chunks: List[str],
        entities: List[Dict[str, Any]],
        search_results: List[Dict[str, Any]],
        style: PromptStyle = PromptStyle.EDUCATIONAL
    ) -> str:
        """
        Build an enhanced educational prompt with dynamic context and structured response format.
        """
        
        # Extract dynamic context metadata
        metadata = PromptTemplate.extract_context_metadata(search_results)
        context_description = metadata.get_context_description()
        detailed_sources = metadata.get_detailed_source_list()
        
        # Build entity context
        entity_names = [e['name'] for e in entities[:5]]
        entity_context = f"Key related concepts: {', '.join(entity_names)}" if entity_names else ""
        
        # Combine context chunks with source headers
        if context_chunks:
            context_header = f"Context from {detailed_sources}:"
            combined_context = f"{context_header}\n\n" + "\n\n".join(context_chunks)
        else:
            combined_context = ""
        
        # Build citation format instructions
        citation_formats = []
        for work, format_type in metadata.citations.items():
            if format_type == 'Stephanus':
                citation_formats.append(f"{work}: Use Stephanus numbers (e.g., Apology 38a)")
            elif format_type == 'Bekker':
                citation_formats.append(f"{work}: Use Bekker numbers (e.g., Ethics 1103a)")
        
        citation_instructions = "\n".join(citation_formats) if citation_formats else "Reference by work title and general location"
        
        # Select language style based on prompt style
        if style == PromptStyle.EDUCATIONAL:
            expertise_level = "You are a philosophy teacher who excels at making complex ideas accessible to beginners."
            language_instruction = """
- Explain philosophical terms in simple, everyday language
- Use analogies and examples when helpful to illustrate abstract concepts
- Define any technical vocabulary the first time you use it
- Write as if teaching a curious student with no prior philosophy background"""
        elif style == PromptStyle.SCHOLARLY:
            expertise_level = "You are a classical philosophy scholar with deep expertise in ancient texts."
            language_instruction = """
- Use precise philosophical terminology appropriately
- Reference scholarly conventions and interpretations
- Maintain academic rigor while remaining accessible"""
        else:  # CONVERSATIONAL
            expertise_level = "You are a knowledgeable philosophy guide for casual exploration."
            language_instruction = """
- Use natural, conversational language
- Balance accuracy with approachability
- Encourage further exploration and questions"""
        
        # Build the structured prompt
        prompt = f"""<instructions>
{expertise_level}

Answer this philosophical question using the provided context from {context_description}.

<question>
{query}
</question>

<context>
{combined_context}
</context>

<entities>
{entity_context}
</entities>

<response_format>
Structure your response in exactly these four sections with XML tags for programmatic parsing:

<direct_answer>
Provide a clear, one-sentence direct response to the question.
</direct_answer>

<detailed_explanation>
Give a thorough philosophical analysis that:
{language_instruction}
- Explains the relevant concepts and their significance
- References specific passages from the provided context
- Shows the logical development of the philosophical argument
</detailed_explanation>

<broader_connections>
Connect this topic to broader themes in the author's work and classical philosophy:
- How does this relate to other key ideas by the same author(s)?
- What is the historical or philosophical significance?
- How does this concept influence later philosophical thought?
</broader_connections>

<references>
List specific passages from the context that support your answer:
- Use proper citation format: {citation_instructions}
- Quote brief key phrases that directly address the question
- Note any particularly important or illuminating passages
- Only reference what is explicitly provided in the context above
</references>
</response_format>

<critical_guidelines>
- If the provided context does not contain enough information to answer the question accurately, clearly state this limitation in your <direct_answer> and avoid speculation
- Only reference information that is explicitly supported by the provided context
- When unsure about a specific detail, acknowledge the uncertainty explicitly
- Focus on what can be confidently derived from the available sources
- If context is missing for key aspects of the question, state: "The available context from {detailed_sources} does not provide sufficient information about [specific aspect]"
</critical_guidelines>
</instructions>"""

        return prompt
    
    @staticmethod
    def build_comparison_prompt(
        query: str,
        context_chunks: List[str],
        entities: List[Dict[str, Any]],
        search_results: List[Dict[str, Any]]
    ) -> str:
        """Build a specialized prompt for comparative philosophical questions."""
        
        metadata = PromptTemplate.extract_context_metadata(search_results)
        context_description = metadata.get_context_description()
        detailed_sources = metadata.get_detailed_source_list()
        
        # Detect if this is a comparison question
        comparison_indicators = ['differ', 'compare', 'contrast', 'versus', 'vs', 'different', 'similar']
        is_comparison = any(indicator in query.lower() for indicator in comparison_indicators)
        
        if not is_comparison:
            # Fall back to standard educational prompt
            return PromptTemplate.build_educational_prompt(query, context_chunks, entities, search_results)
        
        entity_names = [e['name'] for e in entities[:5]]
        entity_context = f"Key related concepts: {', '.join(entity_names)}" if entity_names else ""
        
        # Combine context chunks with source headers
        if context_chunks:
            context_header = f"Context from {detailed_sources}:"
            combined_context = f"{context_header}\n\n" + "\n\n".join(context_chunks)
        else:
            combined_context = ""
        
        # Build citation format instructions
        citation_formats = []
        for work, format_type in metadata.citations.items():
            if format_type == 'Stephanus':
                citation_formats.append(f"{work}: Use Stephanus numbers (e.g., Apology 38a)")
            elif format_type == 'Bekker':
                citation_formats.append(f"{work}: Use Bekker numbers (e.g., Ethics 1103a)")
        
        citation_instructions = "\n".join(citation_formats) if citation_formats else "Reference by work title and general location"
        
        # Check if comparison is possible with available sources
        authors_in_context = len(metadata.authors)
        works_in_context = len(metadata.works)
        
        prompt = f"""<instructions>
You are a philosophy teacher specializing in comparative analysis of classical philosophical ideas.

Answer this comparative question using the provided context from {context_description}.

<question>
{query}
</question>

<context>
{combined_context}
</context>

<entities>
{entity_context}
</entities>

<response_format>
Structure your comparative analysis in these sections with XML tags:

<direct_comparison>
Summarize the key differences or similarities in one clear sentence. 
If comparing multiple philosophers/works but context only covers one, explicitly state the limitation.
</direct_comparison>

<detailed_analysis>
Break down the comparison systematically:
- What are the main points of agreement or disagreement that can be determined from the available context?
- What different approaches are evident in the provided texts?
- What underlying assumptions can be identified from the sources?
- Use simple language and explain technical terms
- IMPORTANT: Only analyze what is explicitly supported by the context from {detailed_sources}
</detailed_analysis>

<philosophical_significance>
Explain why these differences or similarities matter based on the available evidence:
- What broader philosophical questions do they address according to the sources?
- How do these positions influence later thought (only if mentioned in context)?
- What are the practical implications visible in the provided texts?
</philosophical_significance>

<textual_evidence>
Provide specific quotes and references from the context:
- Use proper citation format: {citation_instructions}
- Quote passages that directly support your comparative analysis
- Only reference what is explicitly provided in the context above
</textual_evidence>
</response_format>

<critical_guidelines>
- STRICT EVIDENCE REQUIREMENT: Only compare what is explicitly discussed in the provided context from {detailed_sources}
- MISSING EVIDENCE PROTOCOL: If the context only covers one side of a comparison (e.g., only Plato when asked about "Plato vs. Aristotle"), state clearly: "The available context only includes material from [covered sources]. No information about [missing philosopher/work] is provided, so a complete comparison cannot be made."
- LIMITED EVIDENCE ACKNOWLEDGMENT: When evidence is limited or positions are unclear, explicitly acknowledge: "Based on the available passages from {detailed_sources}, [specific limitation]"
- NO SPECULATION RULE: Never attempt to infer or describe positions that are not explicitly supported by the provided context
- COVERAGE CHECK: Before making any comparative claim, verify that both sides of the comparison are actually represented in the context
</critical_guidelines>
</instructions>"""

        return prompt
    
    @staticmethod
    def select_best_prompt_type(query: str) -> str:
        """
        Analyze the query to select the most appropriate prompt template.
        """
        query_lower = query.lower()
        
        # Comparison questions
        comparison_indicators = ['differ', 'compare', 'contrast', 'versus', 'vs', 'different', 'similar', 'both']
        if any(indicator in query_lower for indicator in comparison_indicators):
            return 'comparison'
        
        # Definition questions
        definition_indicators = ['what is', 'define', 'meaning of', 'definition']
        if any(indicator in query_lower for indicator in definition_indicators):
            return 'educational'
            
        # Complex analysis questions
        analysis_indicators = ['why', 'how', 'analyze', 'explain', 'relationship', 'significance']
        if any(indicator in query_lower for indicator in analysis_indicators):
            return 'educational'
            
        # Default to educational
        return 'educational'


def build_enhanced_prompt(
    query: str,
    context_chunks: List[str],
    entities: List[Dict[str, Any]],
    search_results: List[Dict[str, Any]],
    style: PromptStyle = PromptStyle.EDUCATIONAL
) -> str:
    """
    Main function to build the best prompt for a given query and context.
    
    This function:
    1. Analyzes the query type
    2. Extracts dynamic context metadata
    3. Selects the appropriate prompt template
    4. Returns a structured, intelligent prompt
    """
    
    # Determine the best prompt type
    prompt_type = PromptTemplate.select_best_prompt_type(query)
    
    if prompt_type == 'comparison':
        return PromptTemplate.build_comparison_prompt(query, context_chunks, entities, search_results)
    else:
        return PromptTemplate.build_educational_prompt(query, context_chunks, entities, search_results, style)