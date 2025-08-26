"""
Comprehensive tests for prompt template system.

Tests cover all prompt template types, provider-specific optimizations,
and citation-aware prompt construction for philosophical tutoring.
"""

import pytest
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from arete.services.prompt_template import (
    BasePromptTemplate,
    PhilosophicalTutoringTemplate,
    ExplanationTemplate,
    PromptType,
    PromptContext,
    PromptResult,
    PhilosophicalContext,
    Citation
)


class TestCitation:
    """Test Citation data class."""
    
    def test_citation_creation(self):
        """Test basic citation creation."""
        citation = Citation(
            text="The cave allegory illustrates the journey from ignorance to knowledge.",
            source="plato_republic",
            author="Plato",
            work="Republic",
            reference="Republic 514a-517c",
            confidence=0.95
        )
        
        assert citation.text == "The cave allegory illustrates the journey from ignorance to knowledge."
        assert citation.source == "plato_republic"
        assert citation.author == "Plato"
        assert citation.work == "Republic"
        assert citation.reference == "Republic 514a-517c"
        assert citation.confidence == 0.95
    
    def test_citation_minimal(self):
        """Test citation with minimal required fields."""
        citation = Citation(
            text="Knowledge is virtue.",
            source="socrates_maxim"
        )
        
        assert citation.text == "Knowledge is virtue."
        assert citation.source == "socrates_maxim"
        assert citation.author is None
        assert citation.work is None
        assert citation.reference is None
        assert citation.confidence == 1.0


class TestPromptContext:
    """Test PromptContext data class."""
    
    def test_context_creation_minimal(self):
        """Test minimal context creation."""
        context = PromptContext(query="What is virtue?")
        
        assert context.query == "What is virtue?"
        assert context.retrieved_passages == []
        assert context.citations == []
        assert context.philosophical_context is None
        assert context.student_level == "undergraduate"
        assert context.learning_objective is None
        assert context.previous_context is None
        assert context.metadata == {}
    
    def test_context_creation_full(self):
        """Test full context creation with all fields."""
        citations = [Citation(text="Virtue is knowledge", source="socrates")]
        passages = ["Socratic dialogue on virtue and knowledge"]
        
        context = PromptContext(
            query="Explain Socratic intellectualism",
            retrieved_passages=passages,
            citations=citations,
            philosophical_context=PhilosophicalContext.ANCIENT,
            student_level="graduate",
            learning_objective="Understand the relationship between virtue and knowledge",
            previous_context="Previous discussion on Plato's Forms",
            metadata={"topic": "ethics", "complexity": "high"}
        )
        
        assert context.query == "Explain Socratic intellectualism"
        assert context.retrieved_passages == passages
        assert context.citations == citations
        assert context.philosophical_context == PhilosophicalContext.ANCIENT
        assert context.student_level == "graduate"
        assert context.learning_objective == "Understand the relationship between virtue and knowledge"
        assert context.previous_context == "Previous discussion on Plato's Forms"
        assert context.metadata == {"topic": "ethics", "complexity": "high"}


class MockPromptTemplate(BasePromptTemplate):
    """Mock template for testing abstract base class."""
    
    def generate(self, context: PromptContext) -> PromptResult:
        """Mock generate method."""
        return PromptResult(
            system_prompt="Mock system prompt",
            user_prompt=f"Mock user prompt: {context.query}",
            prompt_type=self.prompt_type,
            provider=self.provider,
            citations_included=context.citations,
            token_estimate=self._estimate_tokens("Mock system prompt" + context.query),
            metadata={"mock": True}
        )


class TestBasePromptTemplate:
    """Test base prompt template functionality."""
    
    def test_template_initialization(self):
        """Test template initialization."""
        template = MockPromptTemplate("anthropic", PromptType.TUTORING)
        
        assert template.provider == "anthropic"
        assert template.prompt_type == PromptType.TUTORING
        assert template._template_cache == {}
    
    def test_estimate_tokens(self):
        """Test token estimation."""
        template = MockPromptTemplate("anthropic", PromptType.TUTORING)
        
        # Test various text lengths
        assert template._estimate_tokens("") == 0
        assert template._estimate_tokens("test") == 1
        assert template._estimate_tokens("this is a longer test") == 5
        assert template._estimate_tokens("a" * 100) == 25
    
    def test_format_citations(self):
        """Test citation formatting."""
        template = MockPromptTemplate("anthropic", PromptType.TUTORING)
        
        citations = [
            Citation(
                text="Knowledge is virtue",
                source="socrates",
                author="Socrates",
                work="Meno",
                reference="Meno 87c"
            ),
            Citation(
                text="The unexamined life is not worth living",
                source="socrates_apology",
                author="Socrates",
                work="Apology",
                reference="Apology 38a"
            )
        ]
        
        formatted = template._format_citations(citations)
        
        assert "[1]" in formatted
        assert "[2]" in formatted
        assert "Knowledge is virtue" in formatted
        assert "Meno 87c" in formatted
        assert "The unexamined life is not worth living" in formatted
        assert "Apology 38a" in formatted
    
    def test_format_citations_empty(self):
        """Test formatting empty citations list."""
        template = MockPromptTemplate("anthropic", PromptType.TUTORING)
        assert template._format_citations([]) == ""
    
    def test_build_context_section(self):
        """Test context section building."""
        template = MockPromptTemplate("anthropic", PromptType.TUTORING)
        
        context = PromptContext(
            query="Test query",
            retrieved_passages=[
                "First relevant passage about virtue",
                "Second passage about knowledge"
            ]
        )
        
        context_section = template._build_context_section(context)
        
        assert "Context 1:" in context_section
        assert "Context 2:" in context_section
        assert "First relevant passage about virtue" in context_section
        assert "Second passage about knowledge" in context_section
    
    def test_build_context_section_empty(self):
        """Test building context section with no passages."""
        template = MockPromptTemplate("anthropic", PromptType.TUTORING)
        
        context = PromptContext(query="Test query")
        context_section = template._build_context_section(context)
        
        assert context_section == ""


class TestPhilosophicalTutoringTemplate:
    """Test philosophical tutoring template."""
    
    @pytest.fixture
    def tutoring_template(self):
        """Create tutoring template for testing."""
        return PhilosophicalTutoringTemplate("anthropic")
    
    @pytest.fixture
    def basic_context(self):
        """Create basic prompt context for testing."""
        return PromptContext(
            query="What is Plato's theory of Forms?",
            student_level="undergraduate",
            philosophical_context=PhilosophicalContext.ANCIENT
        )
    
    def test_template_initialization(self, tutoring_template):
        """Test tutoring template initialization."""
        assert tutoring_template.provider == "anthropic"
        assert tutoring_template.prompt_type == PromptType.TUTORING
        assert tutoring_template._provider_configs is not None
    
    def test_generate_basic_prompt(self, tutoring_template, basic_context):
        """Test basic prompt generation."""
        result = tutoring_template.generate(basic_context)
        
        assert isinstance(result, PromptResult)
        assert result.provider == "anthropic"
        assert result.prompt_type == PromptType.TUTORING
        assert result.system_prompt != ""
        assert result.user_prompt != ""
        assert "What is Plato's theory of Forms?" in result.user_prompt
        assert result.token_estimate > 0
        assert result.metadata["student_level"] == "undergraduate"
        assert result.metadata["philosophical_context"] == PhilosophicalContext.ANCIENT
    
    def test_generate_with_citations(self, tutoring_template):
        """Test prompt generation with citations."""
        citations = [
            Citation(
                text="The Forms are eternal and unchanging essences",
                source="plato_republic",
                author="Plato",
                work="Republic",
                reference="Republic 507b"
            )
        ]
        
        context = PromptContext(
            query="Explain the theory of Forms",
            citations=citations,
            student_level="graduate"
        )
        
        result = tutoring_template.generate(context)
        
        assert len(result.citations_included) == 1
        assert "Source Citations:" in result.user_prompt
        assert "Republic 507b" in result.user_prompt
        assert "The Forms are eternal and unchanging essences" in result.user_prompt
    
    def test_generate_with_context_passages(self, tutoring_template):
        """Test prompt generation with retrieved passages."""
        context = PromptContext(
            query="What is the cave allegory?",
            retrieved_passages=[
                "The cave allegory in Republic Book VII illustrates the philosopher's journey from ignorance to knowledge.",
                "Prisoners in the cave mistake shadows for reality until one escapes and sees the true world."
            ],
            student_level="undergraduate"
        )
        
        result = tutoring_template.generate(context)
        
        assert "**Relevant Sources:**" in result.user_prompt
        assert "Context 1:" in result.user_prompt
        assert "Context 2:" in result.user_prompt
        assert "cave allegory" in result.user_prompt
    
    def test_provider_specific_configs(self):
        """Test different provider configurations."""
        anthropic_template = PhilosophicalTutoringTemplate("anthropic")
        ollama_template = PhilosophicalTutoringTemplate("ollama")
        default_template = PhilosophicalTutoringTemplate("unknown_provider")
        
        context = PromptContext(query="Test question")
        
        anthropic_result = anthropic_template.generate(context)
        ollama_result = ollama_template.generate(context)
        default_result = default_template.generate(context)
        
        # Check that different providers produce different system prompts
        assert anthropic_result.system_prompt != ollama_result.system_prompt
        assert ollama_result.system_prompt != default_result.system_prompt
        
        # Anthropic should mention "Claude"
        assert "Claude" in anthropic_result.system_prompt
        
        # All should contain citation requirements
        for result in [anthropic_result, ollama_result, default_result]:
            assert "cite" in result.system_prompt.lower()
    
    def test_student_level_adaptations(self, tutoring_template):
        """Test student level adaptations."""
        base_context = PromptContext(query="What is virtue?")
        
        # Test different student levels
        undergrad_context = PromptContext(query="What is virtue?", student_level="undergraduate")
        graduate_context = PromptContext(query="What is virtue?", student_level="graduate")
        advanced_context = PromptContext(query="What is virtue?", student_level="advanced")
        
        undergrad_result = tutoring_template.generate(undergrad_context)
        graduate_result = tutoring_template.generate(graduate_context)
        advanced_result = tutoring_template.generate(advanced_context)
        
        # Different levels should produce different system prompts
        assert undergrad_result.system_prompt != graduate_result.system_prompt
        assert graduate_result.system_prompt != advanced_result.system_prompt
        
        # Undergraduate should mention accessibility
        assert any(word in undergrad_result.system_prompt.lower() 
                  for word in ["clear", "accessible", "examples"])
    
    def test_philosophical_context_specialization(self, tutoring_template):
        """Test philosophical context specializations."""
        ancient_context = PromptContext(
            query="What is virtue?",
            philosophical_context=PhilosophicalContext.ANCIENT
        )
        modern_context = PromptContext(
            query="What is virtue?",
            philosophical_context=PhilosophicalContext.MODERN
        )
        
        ancient_result = tutoring_template.generate(ancient_context)
        modern_result = tutoring_template.generate(modern_context)
        
        # Different contexts should produce different prompts
        assert ancient_result.system_prompt != modern_result.system_prompt
        
        # Ancient should mention cultural contexts
        assert "cultural contexts" in ancient_result.system_prompt.lower()
    
    def test_learning_objective_inclusion(self, tutoring_template):
        """Test inclusion of learning objectives."""
        context = PromptContext(
            query="Explain virtue ethics",
            learning_objective="Understand the relationship between virtue and happiness in Aristotelian ethics"
        )
        
        result = tutoring_template.generate(context)
        
        assert "**Learning Objective:**" in result.user_prompt
        assert "virtue and happiness" in result.user_prompt
        assert result.metadata["learning_objective"] == context.learning_objective


class TestExplanationTemplate:
    """Test explanation template."""
    
    @pytest.fixture
    def explanation_template(self):
        """Create explanation template for testing."""
        return ExplanationTemplate("ollama")
    
    def test_template_initialization(self, explanation_template):
        """Test explanation template initialization."""
        assert explanation_template.provider == "ollama"
        assert explanation_template.prompt_type == PromptType.EXPLANATION
    
    def test_generate_explanation_prompt(self, explanation_template):
        """Test explanation prompt generation."""
        context = PromptContext(
            query="What is epistemology?",
            retrieved_passages=["Epistemology is the study of knowledge and justified belief."]
        )
        
        result = explanation_template.generate(context)
        
        assert isinstance(result, PromptResult)
        assert result.prompt_type == PromptType.EXPLANATION
        assert result.provider == "ollama"
        assert "**Explain:**" in result.user_prompt
        assert "What is epistemology?" in result.user_prompt
        assert "**Source Material:**" in result.user_prompt
        assert result.metadata["explanation_focus"] is True
    
    def test_explanation_with_citations(self, explanation_template):
        """Test explanation generation with citations."""
        citations = [Citation(text="Knowledge is justified true belief", source="plato_theaetetus")]
        context = PromptContext(query="What is knowledge?", citations=citations)
        
        result = explanation_template.generate(context)
        
        assert "**Citations:**" in result.user_prompt
        assert "Knowledge is justified true belief" in result.user_prompt


class TestPromptResult:
    """Test PromptResult data class."""
    
    def test_prompt_result_creation(self):
        """Test prompt result creation."""
        citations = [Citation(text="Test citation", source="test")]
        
        result = PromptResult(
            system_prompt="System prompt content",
            user_prompt="User prompt content",
            prompt_type=PromptType.TUTORING,
            provider="anthropic",
            citations_included=citations,
            token_estimate=150,
            metadata={"test": "metadata"}
        )
        
        assert result.system_prompt == "System prompt content"
        assert result.user_prompt == "User prompt content"
        assert result.prompt_type == PromptType.TUTORING
        assert result.provider == "anthropic"
        assert len(result.citations_included) == 1
        assert result.token_estimate == 150
        assert result.metadata["test"] == "metadata"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])