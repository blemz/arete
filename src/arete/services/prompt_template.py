"""
Prompt template system for philosophical tutoring.

This module provides a comprehensive prompt template system designed specifically
for Graph-RAG philosophical tutoring, with provider-specific optimizations and
citation-aware prompt construction.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Union
import re

# Setup logger
logger = logging.getLogger(__name__)


class PromptType(Enum):
    """Types of philosophical prompts supported."""
    TUTORING = "tutoring"
    EXPLANATION = "explanation"
    ANALYSIS = "analysis"
    COMPARISON = "comparison"
    CRITIQUE = "critique"
    CONTEXTUALIZATION = "contextualization"


class PhilosophicalContext(Enum):
    """Philosophical contexts for prompt optimization."""
    ANCIENT = "ancient"
    MEDIEVAL = "medieval"
    MODERN = "modern"
    CONTEMPORARY = "contemporary"
    CROSS_TRADITIONAL = "cross_traditional"


@dataclass
class Citation:
    """Represents a source citation for philosophical content."""
    text: str
    source: str
    author: Optional[str] = None
    work: Optional[str] = None
    reference: Optional[str] = None  # e.g., "Republic 514a"
    confidence: float = 1.0
    context: Optional[str] = None


@dataclass
class PromptContext:
    """Context information for prompt generation."""
    query: str
    retrieved_passages: List[str] = field(default_factory=list)
    citations: List[Citation] = field(default_factory=list)
    philosophical_context: Optional[PhilosophicalContext] = None
    student_level: str = "undergraduate"  # undergraduate, graduate, advanced
    learning_objective: Optional[str] = None
    previous_context: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PromptResult:
    """Result from prompt template generation."""
    system_prompt: str
    user_prompt: str
    prompt_type: PromptType
    provider: str
    citations_included: List[Citation]
    token_estimate: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class BasePromptTemplate(ABC):
    """
    Abstract base class for prompt templates.
    
    All prompt templates must implement the generate method to create
    provider-specific prompts for philosophical tutoring scenarios.
    """
    
    def __init__(self, provider: str, prompt_type: PromptType):
        """
        Initialize prompt template.
        
        Args:
            provider: LLM provider name (ollama, anthropic, etc.)
            prompt_type: Type of philosophical prompt
        """
        self.provider = provider
        self.prompt_type = prompt_type
        self._template_cache: Dict[str, str] = {}
    
    @abstractmethod
    def generate(self, context: PromptContext) -> PromptResult:
        """
        Generate provider-specific prompt from context.
        
        Args:
            context: Prompt generation context
            
        Returns:
            Generated prompt result
        """
        pass
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        # Simple estimation: ~4 characters per token
        return len(text) // 4
    
    def _format_citations(self, citations: List[Citation]) -> str:
        """
        Format citations for inclusion in prompts.
        
        Args:
            citations: List of citations to format
            
        Returns:
            Formatted citation text
        """
        if not citations:
            return ""
        
        formatted = []
        for i, citation in enumerate(citations, 1):
            ref = citation.reference or f"{citation.author}, {citation.work}"
            formatted.append(f"[{i}] {citation.text}\n    — {ref}")
        
        return "\n\n".join(formatted)
    
    def _build_context_section(self, context: PromptContext) -> str:
        """
        Build context section from retrieved passages.
        
        Args:
            context: Prompt generation context
            
        Returns:
            Formatted context section
        """
        if not context.retrieved_passages:
            return ""
        
        context_parts = []
        for i, passage in enumerate(context.retrieved_passages, 1):
            context_parts.append(f"Context {i}:\n{passage}")
        
        return "\n\n".join(context_parts)


class PhilosophicalTutoringTemplate(BasePromptTemplate):
    """
    Template for philosophical tutoring prompts.
    
    Optimized for educational scenarios where the AI acts as a philosophy tutor
    guiding students through classical philosophical texts and concepts.
    """
    
    def __init__(self, provider: str):
        """Initialize tutoring template."""
        super().__init__(provider, PromptType.TUTORING)
        self._provider_configs = self._load_provider_configs()
    
    def generate(self, context: PromptContext) -> PromptResult:
        """Generate tutoring prompt for specified provider."""
        config = self._provider_configs.get(self.provider, self._provider_configs["default"])
        
        # Build system prompt
        system_prompt = self._build_system_prompt(context, config)
        
        # Build user prompt with context and citations
        user_prompt = self._build_user_prompt(context)
        
        # Prepare citations
        citations_included = context.citations.copy()
        
        # Estimate tokens
        total_text = system_prompt + user_prompt
        token_estimate = self._estimate_tokens(total_text)
        
        return PromptResult(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            prompt_type=self.prompt_type,
            provider=self.provider,
            citations_included=citations_included,
            token_estimate=token_estimate,
            metadata={
                "student_level": context.student_level,
                "philosophical_context": context.philosophical_context,
                "learning_objective": context.learning_objective
            }
        )
    
    def _build_system_prompt(self, context: PromptContext, config: Dict[str, Any]) -> str:
        """Build provider-specific system prompt."""
        base_role = config["base_role"]
        
        # Add philosophical context specialization
        context_specialization = ""
        if context.philosophical_context:
            context_specialization = config["context_specializations"].get(
                context.philosophical_context.value, ""
            )
        
        # Add student level adaptation
        level_adaptation = config["level_adaptations"].get(
            context.student_level, ""
        )
        
        # Combine components
        system_parts = [
            base_role,
            context_specialization,
            level_adaptation,
            config["citation_requirements"],
            config["response_guidelines"]
        ]
        
        return "\n\n".join(filter(None, system_parts))
    
    def _build_user_prompt(self, context: PromptContext) -> str:
        """Build user prompt with context and query."""
        prompt_parts = []
        
        # Add retrieved context if available
        if context.retrieved_passages:
            context_section = self._build_context_section(context)
            prompt_parts.append(f"**Relevant Sources:**\n{context_section}")
        
        # Add citations if available
        if context.citations:
            citations_section = self._format_citations(context.citations)
            prompt_parts.append(f"**Source Citations:**\n{citations_section}")
        
        # Add learning objective if specified
        if context.learning_objective:
            prompt_parts.append(f"**Learning Objective:** {context.learning_objective}")
        
        # Add the actual query
        prompt_parts.append(f"**Question:** {context.query}")
        
        return "\n\n".join(prompt_parts)
    
    def _load_provider_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load provider-specific configuration templates."""
        return {
            "default": {
                "base_role": (
                    "You are a knowledgeable philosophy tutor specializing in classical texts. "
                    "Your role is to guide students through philosophical concepts with clarity, "
                    "accuracy, and pedagogical insight. Always ground your responses in the "
                    "provided source materials and cite them appropriately."
                ),
                "context_specializations": {
                    "ancient": (
                        "Focus on the historical context of ancient philosophy, including "
                        "cultural background and the development of key concepts in their "
                        "original settings."
                    ),
                    "medieval": (
                        "Emphasize the synthesis of classical philosophy with religious thought "
                        "and the unique contributions of medieval philosophers."
                    ),
                    "modern": (
                        "Highlight the revolutionary changes in philosophical method and "
                        "the emergence of new epistemological approaches."
                    ),
                    "contemporary": (
                        "Connect historical philosophical concepts to current debates and "
                        "show their relevance to modern philosophical problems."
                    )
                },
                "level_adaptations": {
                    "undergraduate": (
                        "Present concepts clearly with accessible explanations. Use analogies "
                        "and examples to illustrate abstract ideas. Encourage critical thinking "
                        "while building foundational understanding."
                    ),
                    "graduate": (
                        "Engage with sophisticated philosophical distinctions and debates. "
                        "Encourage original analysis and connection of ideas across texts "
                        "and traditions."
                    ),
                    "advanced": (
                        "Assume familiarity with major philosophical concepts and engage "
                        "in nuanced analysis of textual interpretations and scholarly debates."
                    )
                },
                "citation_requirements": (
                    "IMPORTANT: Always cite your sources using the provided references. "
                    "Include specific textual references (e.g., 'Republic 514a') when available. "
                    "Distinguish between direct quotes, paraphrases, and your interpretative "
                    "commentary."
                ),
                "response_guidelines": (
                    "Structure your response with clear sections. Begin with a brief overview, "
                    "develop your explanation with supporting evidence from sources, and "
                    "conclude with questions or suggestions for further exploration."
                )
            },
            
            "anthropic": {
                "base_role": (
                    "You are Claude, an AI assistant specialized in philosophical education. "
                    "As a philosophy tutor, you combine deep textual knowledge with pedagogical "
                    "sensitivity to guide students through classical philosophical works. "
                    "Your responses should be thorough, well-reasoned, and carefully cited."
                ),
                "context_specializations": {
                    "ancient": (
                        "Pay special attention to the oral tradition background of ancient "
                        "philosophy and the cultural contexts that shaped these foundational "
                        "works. Consider the dialogical nature of much ancient philosophical writing."
                    ),
                    "modern": (
                        "Emphasize the methodological innovations of modern philosophers and "
                        "their departure from scholastic approaches. Connect ideas to the "
                        "broader intellectual transformations of their eras."
                    )
                },
                "level_adaptations": {
                    "undergraduate": (
                        "Provide comprehensive explanations that build understanding step by step. "
                        "Use structured responses with clear headings and logical progression."
                    ),
                    "graduate": (
                        "Engage with complex philosophical arguments and their implications. "
                        "Encourage critical analysis of different interpretative approaches "
                        "and scholarly debates."
                    ),
                    "advanced": (
                        "Assume sophisticated philosophical background and engage with "
                        "nuanced interpretative questions. Focus on cutting-edge scholarly "
                        "discussions and methodological considerations."
                    )
                },
                "citation_requirements": (
                    "Citations are crucial for philosophical accuracy. Always indicate which "
                    "parts of your response come from the provided sources versus your own "
                    "analysis. Use numbered references that correspond to the source materials."
                ),
                "response_guidelines": (
                    "Aim for responses that are both informative and thought-provoking. "
                    "Include follow-up questions that encourage deeper engagement with the material."
                )
            },
            
            "ollama": {
                "base_role": (
                    "You are a philosophy tutor helping students understand classical texts. "
                    "Provide clear, accurate explanations based on the source materials provided. "
                    "Keep responses focused and well-organized."
                ),
                "context_specializations": {
                    "ancient": "Focus on the key ideas and arguments from ancient philosophical texts.",
                    "medieval": "Explain how medieval thinkers built upon and modified ancient ideas.",
                    "modern": "Highlight the new approaches and methods of modern philosophy."
                },
                "level_adaptations": {
                    "undergraduate": "Explain concepts clearly with helpful examples.",
                    "graduate": "Engage with complex ideas and scholarly interpretations.",
                    "advanced": "Assume familiarity with major concepts and focus on nuanced analysis."
                },
                "citation_requirements": (
                    "Always cite the sources provided. Use specific references when available."
                ),
                "response_guidelines": (
                    "Keep responses well-structured and focused. Include the most important "
                    "points first, then supporting details."
                )
            }
        }


class ExplanationTemplate(BasePromptTemplate):
    """Template for philosophical explanation prompts."""
    
    def __init__(self, provider: str):
        """Initialize explanation template."""
        super().__init__(provider, PromptType.EXPLANATION)
    
    def generate(self, context: PromptContext) -> PromptResult:
        """Generate explanation prompt."""
        system_prompt = (
            "You are a philosophy expert providing clear explanations of philosophical "
            "concepts. Use the provided sources to give accurate, well-cited explanations. "
            "Structure your response logically and include relevant examples."
        )
        
        user_prompt_parts = []
        
        # Add context if available
        if context.retrieved_passages:
            context_section = self._build_context_section(context)
            user_prompt_parts.append(f"**Source Material:**\n{context_section}")
        
        # Add citations
        if context.citations:
            citations_section = self._format_citations(context.citations)
            user_prompt_parts.append(f"**Citations:**\n{citations_section}")
        
        # Add query
        user_prompt_parts.append(f"**Explain:** {context.query}")
        
        user_prompt = "\n\n".join(user_prompt_parts)
        
        return PromptResult(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            prompt_type=self.prompt_type,
            provider=self.provider,
            citations_included=context.citations.copy(),
            token_estimate=self._estimate_tokens(system_prompt + user_prompt),
            metadata={"explanation_focus": True}
        )