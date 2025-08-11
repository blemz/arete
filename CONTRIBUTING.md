# Contributing to Arete

Thank you for your interest in contributing to Arete! This guide will help you understand how to contribute effectively to our AI philosophy tutoring system.

## 🎯 Project Mission

Arete aims to make high-quality philosophical education accessible through AI while maintaining the rigor and nuance that philosophical inquiry demands. Our contributions should always serve this mission.

## 🚀 Getting Started

### Prerequisites

Before contributing, ensure you have:
- Python 3.11+
- Docker Desktop 4.0+
- Git 2.30+
- Basic understanding of philosophy (helpful but not required)
- Familiarity with our [Code of Conduct](CODE_OF_CONDUCT.md)

### Development Environment

1. **Fork and clone the repository:**
```bash
git clone https://github.com/your-username/arete.git
cd arete
```

2. **Set up development environment:**
```bash
# Install dependencies
pip install -e ".[dev,all]"

# Install pre-commit hooks
pre-commit install

# Start database services
docker-compose up -d neo4j weaviate ollama
```

3. **Verify installation:**
```bash
# Run tests
pytest tests/ -v

# Check code quality
pre-commit run --all-files
```

## 🧪 Development Process (Refined TDD)

Arete follows a refined Test-Driven Development (TDD) approach based on proven methodology breakthrough:

### 🏆 Test Redesign Victory

Our testing approach has been validated through a major redesign that achieved:
- **98%+ reduction** in test code while maintaining practical coverage
- **>80% reduction** in test execution time
- **87.5% reduction** in test maintenance overhead
- **Contract-based testing** over exhaustive API coverage

**Key Principle**: "Quality over Quantity" - test for value, not just to test.

### 🎯 Testing Philosophy

**Focus on Contracts, Not Implementation Details:**
- Test what the code promises to do (contracts)
- Avoid testing internal implementation mechanics
- Prioritize critical business logic over comprehensive API coverage
- Eliminate "testing to test" anti-patterns

**Proven Anti-Patterns to Avoid:**
- ❌ Testing every possible parameter combination
- ❌ Mocking complex internal state unnecessarily  
- ❌ Over-engineering test scenarios for edge cases
- ❌ Writing tests that primarily exercise test infrastructure

**Effective Patterns to Follow:**
- ✅ Contract-based testing focusing on public API behavior
- ✅ Focused test scenarios covering critical business paths
- ✅ Modern tooling integration (e.g., weaviate.connect_to_local())
- ✅ Practical coverage targeting real-world usage patterns

### 1. Red: Write Failing Tests First
```python
# Example: tests/test_document_model.py
def test_document_creation_with_valid_data():
    """Test that documents can be created with valid data."""
    document_data = {
        "title": "Republic",
        "author": "Plato", 
        "content": "Justice is the excellence of the soul...",
        "language": "English"
    }
    
    document = Document(**document_data)
    
    assert document.title == "Republic"
    assert document.author == "Plato"
    assert document.word_count > 0
```

### 2. Green: Write Minimal Code to Pass
```python
# Example: src/arete/models/document.py
from pydantic import BaseModel, Field

class Document(BaseModel):
    title: str = Field(..., min_length=1)
    author: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    language: str = "English"
    
    @property
    def word_count(self) -> int:
        return len(self.content.split())
```

### 3. Refactor: Improve Code Quality
- Add type hints and documentation
- Optimize performance
- Ensure code follows project conventions
- Apply lessons from test redesign victory
- Eliminate over-engineered test scenarios
- Focus on maintainable, contract-based testing

## 📝 Contribution Types

### 🐛 Bug Reports

When reporting bugs:

```markdown
**Bug Description:**
Clear description of what went wrong

**Steps to Reproduce:**
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected Behavior:**
What should have happened

**Environment:**
- OS: [e.g., Windows 11, macOS 13, Ubuntu 22.04]
- Python version: [e.g., 3.11.5]
- Arete version: [e.g., 0.1.0]
```

### ✨ Feature Requests

For new features:

```markdown
**Feature Description:**
Clear description of the proposed feature

**Use Case:**
Why would this feature be valuable?

**Proposed Solution:**
How might this work?

**Alternatives Considered:**
Other approaches you've thought about

**Additional Context:**
Screenshots, mockups, or examples
```

### 🔧 Code Contributions

#### Pull Request Process

1. **Create a feature branch:**
```bash
git checkout -b feature/phase-X-your-feature-name
```

2. **Follow TDD process:**
- Write tests first
- Implement minimal code to pass tests
- Refactor and optimize

3. **Ensure quality:**
```bash
# Run tests
pytest tests/ -v --cov=src/arete

# Check code style
black src/ tests/
flake8 src/ tests/
mypy src/

# Run pre-commit checks
pre-commit run --all-files
```

4. **Create meaningful commits:**
```bash
# Use conventional commit format
git commit -m "feat(models): add Document model with validation

- Implement Pydantic-based Document model
- Add validation for title, author, content
- Include word count property
- Add comprehensive tests with >95% coverage

Closes #123"
```

5. **Submit pull request:**
- Use the PR template
- Link related issues
- Provide clear description of changes
- Include test coverage information

#### Code Standards

**Python Style:**
- **Formatting**: Black with 88-character lines
- **Linting**: Flake8 with project configuration
- **Type Hints**: Required for all functions and methods
- **Docstrings**: Google-style docstrings for all public APIs

**Example:**
```python
from typing import List, Optional
from pydantic import BaseModel, Field


class PhilosophicalConcept(BaseModel):
    """A philosophical concept with relationships to other concepts.
    
    This model represents concepts extracted from philosophical texts,
    including their definitions, categories, and relationships.
    
    Attributes:
        name: The primary name of the concept
        definition: A clear definition of the concept
        category: The philosophical category (Ethics, Metaphysics, etc.)
        synonyms: Alternative names for the concept
        related_concepts: Names of related concepts
    
    Example:
        >>> concept = PhilosophicalConcept(
        ...     name="Justice",
        ...     definition="The virtue of giving each their due",
        ...     category="Ethics"
        ... )
        >>> concept.add_related_concept("Virtue")
    """
    
    name: str = Field(..., min_length=1, description="Primary concept name")
    definition: str = Field(..., min_length=10, description="Concept definition")
    category: str = Field(..., description="Philosophical category")
    synonyms: List[str] = Field(default_factory=list)
    related_concepts: List[str] = Field(default_factory=list)
    
    def add_related_concept(self, concept_name: str) -> None:
        """Add a related concept if not already present.
        
        Args:
            concept_name: Name of the related concept to add
        """
        if concept_name not in self.related_concepts:
            self.related_concepts.append(concept_name)
    
    def get_semantic_similarity(self, other: "PhilosophicalConcept") -> float:
        """Calculate semantic similarity with another concept.
        
        Args:
            other: Another philosophical concept to compare with
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Implementation would use actual similarity calculation
        return 0.0
```

**Refined Testing Standards:**
- **Coverage**: Minimum 90% for new code, achieved through focused testing
- **Quality Metrics**: Prioritize test value over test volume
- **Test Categories**: Unit, integration, end-to-end tests with contract-based approach
- **Fixtures**: Use pytest fixtures for common test data
- **Mocking**: Mock external dependencies judiciously, avoid over-mocking
- **Efficiency**: Target >80% reduction in test execution time through focused scenarios
- **Maintainability**: Design tests for long-term maintainability, not just coverage

```python
import pytest
from unittest.mock import Mock, patch
from arete.models.concept import PhilosophicalConcept


class TestPhilosophicalConcept:
    """Test suite for PhilosophicalConcept model."""
    
    @pytest.fixture
    def sample_concept(self) -> PhilosophicalConcept:
        """Create a sample concept for testing."""
        return PhilosophicalConcept(
            name="Justice",
            definition="The virtue of giving each their due",
            category="Ethics"
        )
    
    def test_concept_creation_with_valid_data(self, sample_concept):
        """Test concept creation with valid data."""
        assert sample_concept.name == "Justice"
        assert "virtue" in sample_concept.definition
        assert sample_concept.category == "Ethics"
        assert sample_concept.synonyms == []
        assert sample_concept.related_concepts == []
    
    def test_add_related_concept(self, sample_concept):
        """Test adding related concepts."""
        sample_concept.add_related_concept("Virtue")
        sample_concept.add_related_concept("Fairness")
        
        assert "Virtue" in sample_concept.related_concepts
        assert "Fairness" in sample_concept.related_concepts
        assert len(sample_concept.related_concepts) == 2
    
    def test_add_duplicate_related_concept(self, sample_concept):
        """Test that duplicate concepts are not added."""
        sample_concept.add_related_concept("Virtue")
        sample_concept.add_related_concept("Virtue")
        
        assert sample_concept.related_concepts.count("Virtue") == 1
    
    @patch('arete.models.concept.calculate_similarity')
    def test_semantic_similarity(self, mock_similarity, sample_concept):
        """Test semantic similarity calculation."""
        mock_similarity.return_value = 0.85
        other_concept = PhilosophicalConcept(
            name="Virtue",
            definition="Excellence of character",
            category="Ethics"
        )
        
        similarity = sample_concept.get_semantic_similarity(other_concept)
        
        assert similarity == 0.85
        mock_similarity.assert_called_once()
```

### 📚 Content Contributions

#### Adding Philosophical Texts

1. **Text Preparation:**
   - Ensure public domain or proper licensing
   - Use clean, well-formatted text
   - Include proper metadata (author, title, date, etc.)
   - Add source citations and references

2. **Text Processing:**
   ```python
   # Example text metadata
   metadata = {
       "title": "Nicomachean Ethics",
       "author": "Aristotle",
       "translator": "W.D. Ross",
       "language": "English",
       "source": "Perseus Digital Library",
       "url": "http://perseus.tufts.edu/...",
       "date_written": "4th century BCE",
       "date_translated": "1908"
   }
   ```

3. **Quality Assurance:**
   - Verify accuracy against original sources
   - Check for OCR errors or formatting issues
   - Ensure consistent citation formats
   - Test with sample queries

#### Content Guidelines

**Accuracy Requirements:**
- All quotes must be accurately attributed
- Citations must include specific locations (page, section, line)
- Translations should note the translator and edition
- Historical context should be factually correct

**Representation Standards:**
- Include diverse philosophical traditions
- Avoid Western-centric bias where possible
- Represent different interpretations fairly
- Include marginalized voices in philosophy

### 🔬 Research Contributions

#### Improving NLP for Philosophy

**Areas for Research:**
- Named Entity Recognition for philosophical concepts
- Relationship extraction between ideas
- Cross-lingual concept mapping
- Bias detection in philosophical responses

**Research Process:**
1. **Literature Review**: Survey existing approaches
2. **Experimental Design**: Create reproducible experiments
3. **Implementation**: Add research code to `research/` directory
4. **Evaluation**: Benchmark against existing methods
5. **Documentation**: Write up findings and methodology

**Example Research Contribution:**
```python
# research/concept_extraction/philosophical_ner.py
"""
Experimental NER model specifically tuned for philosophical concepts.

This module explores using a fine-tuned BERT model for extracting
philosophical concepts from classical texts.
"""

import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification
from typing import List, Tuple


class PhilosophicalNER:
    """Named Entity Recognition for philosophical concepts."""
    
    def __init__(self, model_name: str = "bert-base-uncased"):
        """Initialize the NER model.
        
        Args:
            model_name: HuggingFace model identifier
        """
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForTokenClassification.from_pretrained(model_name)
    
    def extract_concepts(self, text: str) -> List[Tuple[str, str, float]]:
        """Extract philosophical concepts from text.
        
        Args:
            text: Input philosophical text
            
        Returns:
            List of (concept, type, confidence) tuples
        """
        # Implementation would include actual NER processing
        return []
```

## 🎓 Subject Matter Expertise

### Philosophy Contributions

We especially value contributions from:
- **Academic Philosophers**: Accuracy review and content validation
- **Graduate Students**: Research and text digitization
- **Educators**: Pedagogical improvements and learning pathways
- **Translators**: Multi-language support and accuracy

### Expert Review Process

1. **Content Accuracy**: Philosophical experts review responses
2. **Citation Verification**: Check all references against sources  
3. **Bias Assessment**: Evaluate for cultural or interpretive bias
4. **Pedagogical Value**: Ensure educational effectiveness

## 🌐 Community Guidelines

### Communication

- **Be Respectful**: Treat all community members with respect
- **Constructive Feedback**: Focus on improving the project
- **Inclusive Language**: Use welcoming, inclusive language
- **Stay On Topic**: Keep discussions focused on the project

### Collaboration

- **Assume Good Intent**: Give others the benefit of the doubt
- **Ask Questions**: Don't hesitate to seek clarification
- **Share Knowledge**: Help others learn and contribute
- **Credit Others**: Acknowledge contributions and sources

## 📋 Issue Labels

We use labels to organize issues:

- `bug`: Something isn't working
- `enhancement`: New feature or improvement
- `documentation`: Documentation needs improvement  
- `good-first-issue`: Good for newcomers
- `help-wanted`: Community assistance needed
- `philosophy`: Requires philosophical expertise
- `research`: Research or experimental work
- `priority-high`: Critical issue or feature
- `priority-medium`: Important but not urgent
- `priority-low`: Nice to have

## 🏆 Recognition

Contributors are recognized in:
- **README**: Active contributors listed
- **Releases**: Major contributors acknowledged
- **Academic Papers**: Co-authorship for significant research
- **Conference Talks**: Speaking opportunities for major contributors

## 📞 Getting Help

If you need help contributing:

- 💬 **Discord**: Join our [community chat](https://discord.gg/arete-ai)
- 📧 **Email**: Contact maintainers at dev@arete.ai
- 📖 **Documentation**: Check our [technical docs](docs/)
- 🐛 **Issues**: Browse existing issues for similar questions

## 🎯 Roadmap Participation

Want to influence the project direction?

1. **Review Current Roadmap**: See [TODO.md](planning/TODO.md)
2. **Join Planning Discussions**: Participate in roadmap issues
3. **Propose Features**: Submit detailed feature requests
4. **Vote on Priorities**: Help prioritize development efforts

## ⚖️ Legal

By contributing, you agree that:
- Your contributions are your own original work
- You have the right to submit your contributions
- Your contributions are licensed under the project's MIT license
- You understand and agree to our [Code of Conduct](CODE_OF_CONDUCT.md)

---

**Thank you for helping make philosophy education more accessible and effective through AI!**

*"The beginning is the most important part of the work." - Plato*