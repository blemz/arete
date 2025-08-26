"""
Comprehensive tests for prompt versioning and rollback system.

Tests cover version creation, storage, retrieval, rollback capabilities,
and integration with the existing prompt template system.
"""

import pytest
from unittest.mock import Mock, patch
from typing import List, Dict, Any
from datetime import datetime, timedelta
import json
import tempfile
import os

from arete.services.prompt_versioning import (
    PromptVersioningService,
    PromptVersion,
    VersionMetadata,
    RollbackResult,
    VersionComparison,
    VersioningConfig
)
from arete.services.prompt_template import (
    PromptType,
    PhilosophicalContext,
    Citation
)


class TestPromptVersion:
    """Test PromptVersion data class."""
    
    def test_version_creation(self):
        """Test basic prompt version creation."""
        version = PromptVersion(
            version_id="v1.0.0",
            template_name="PhilosophicalTutoringTemplate",
            provider="anthropic",
            prompt_type=PromptType.TUTORING,
            system_prompt="You are a philosophy tutor...",
            template_config={"student_level": "undergraduate"},
            metadata=VersionMetadata(
                created_by="developer",
                description="Initial tutoring template",
                tags=["stable", "undergraduate"]
            )
        )
        
        assert version.version_id == "v1.0.0"
        assert version.template_name == "PhilosophicalTutoringTemplate"
        assert version.provider == "anthropic"
        assert version.prompt_type == PromptType.TUTORING
        assert version.metadata.created_by == "developer"
        assert "stable" in version.metadata.tags
    
    def test_version_serialization(self):
        """Test version serialization to/from dict."""
        version = PromptVersion(
            version_id="v2.1.0",
            template_name="ExplanationTemplate", 
            provider="ollama",
            prompt_type=PromptType.EXPLANATION,
            system_prompt="Explain philosophical concepts clearly...",
            template_config={"context": "ancient"},
            metadata=VersionMetadata(
                created_by="expert",
                description="Enhanced explanation template"
            )
        )
        
        # Serialize to dict
        version_dict = version.to_dict()
        assert version_dict["version_id"] == "v2.1.0"
        assert version_dict["provider"] == "ollama"
        
        # Deserialize from dict
        restored_version = PromptVersion.from_dict(version_dict)
        assert restored_version.version_id == version.version_id
        assert restored_version.provider == version.provider
        assert restored_version.system_prompt == version.system_prompt


class TestVersionMetadata:
    """Test VersionMetadata data class."""
    
    def test_metadata_creation(self):
        """Test metadata creation with defaults."""
        metadata = VersionMetadata(
            created_by="ai_engineer",
            description="Performance optimized prompts"
        )
        
        assert metadata.created_by == "ai_engineer"
        assert metadata.description == "Performance optimized prompts"
        assert isinstance(metadata.created_at, datetime)
        assert metadata.tags == []
        assert metadata.performance_metrics == {}
    
    def test_metadata_with_performance(self):
        """Test metadata with performance metrics."""
        metrics = {
            "accuracy": 0.92,
            "response_time": 1.2,
            "citation_quality": 0.88
        }
        
        metadata = VersionMetadata(
            created_by="optimizer",
            description="High-performance version",
            tags=["optimized", "tested"],
            performance_metrics=metrics
        )
        
        assert metadata.performance_metrics["accuracy"] == 0.92
        assert "optimized" in metadata.tags


class TestPromptVersioningService:
    """Test PromptVersioningService functionality."""
    
    @pytest.fixture
    def temp_storage_dir(self):
        """Create temporary directory for version storage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def versioning_config(self, temp_storage_dir):
        """Create versioning configuration."""
        return VersioningConfig(
            storage_path=temp_storage_dir,
            max_versions_per_template=10,
            auto_backup=True,
            compression_enabled=False  # Disable for easier testing
        )
    
    @pytest.fixture
    def versioning_service(self, versioning_config):
        """Create versioning service instance."""
        return PromptVersioningService(config=versioning_config)
    
    def test_service_initialization(self, versioning_service, versioning_config):
        """Test service initialization."""
        assert versioning_service.config == versioning_config
        assert versioning_service.versions == {}
        assert os.path.exists(versioning_config.storage_path)
    
    def test_create_version(self, versioning_service):
        """Test creating a new prompt version."""
        version = PromptVersion(
            version_id="v1.0.0",
            template_name="TestTemplate",
            provider="anthropic",
            prompt_type=PromptType.TUTORING,
            system_prompt="Test system prompt",
            template_config={"level": "beginner"},
            metadata=VersionMetadata(
                created_by="tester",
                description="Test version"
            )
        )
        
        result = versioning_service.create_version(version)
        
        assert result is True
        assert "TestTemplate" in versioning_service.versions
        assert len(versioning_service.versions["TestTemplate"]) == 1
        assert versioning_service.versions["TestTemplate"][0].version_id == "v1.0.0"
    
    def test_create_multiple_versions(self, versioning_service):
        """Test creating multiple versions of the same template."""
        template_name = "MultiVersionTemplate"
        
        # Create first version
        v1 = PromptVersion(
            version_id="v1.0.0",
            template_name=template_name,
            provider="anthropic",
            prompt_type=PromptType.TUTORING,
            system_prompt="Version 1 prompt",
            template_config={},
            metadata=VersionMetadata(created_by="dev1", description="Initial")
        )
        
        # Create second version
        v2 = PromptVersion(
            version_id="v1.1.0",
            template_name=template_name,
            provider="anthropic",
            prompt_type=PromptType.TUTORING,
            system_prompt="Version 2 prompt - improved",
            template_config={},
            metadata=VersionMetadata(created_by="dev2", description="Enhanced")
        )
        
        versioning_service.create_version(v1)
        versioning_service.create_version(v2)
        
        assert len(versioning_service.versions[template_name]) == 2
        version_ids = [v.version_id for v in versioning_service.versions[template_name]]
        assert "v1.0.0" in version_ids
        assert "v1.1.0" in version_ids
    
    def test_get_version(self, versioning_service):
        """Test retrieving a specific version."""
        version = PromptVersion(
            version_id="v2.0.0",
            template_name="RetrievalTest",
            provider="ollama",
            prompt_type=PromptType.EXPLANATION,
            system_prompt="Retrieval test prompt",
            template_config={"style": "detailed"},
            metadata=VersionMetadata(created_by="retriever", description="For testing retrieval")
        )
        
        versioning_service.create_version(version)
        
        # Test successful retrieval
        retrieved = versioning_service.get_version("RetrievalTest", "v2.0.0")
        assert retrieved is not None
        assert retrieved.version_id == "v2.0.0"
        assert retrieved.system_prompt == "Retrieval test prompt"
        
        # Test non-existent version
        not_found = versioning_service.get_version("RetrievalTest", "v999.0.0")
        assert not_found is None
        
        # Test non-existent template
        no_template = versioning_service.get_version("NonExistentTemplate", "v1.0.0")
        assert no_template is None
    
    def test_get_latest_version(self, versioning_service):
        """Test retrieving the latest version of a template."""
        template_name = "LatestTest"
        
        # Create versions in non-chronological order
        versions = [
            PromptVersion("v1.0.0", template_name, "anthropic", PromptType.TUTORING,
                         "Old prompt", {}, VersionMetadata("dev", "Old")),
            PromptVersion("v2.1.0", template_name, "anthropic", PromptType.TUTORING,
                         "Latest prompt", {}, VersionMetadata("dev", "Latest")),
            PromptVersion("v1.5.0", template_name, "anthropic", PromptType.TUTORING,
                         "Middle prompt", {}, VersionMetadata("dev", "Middle"))
        ]
        
        for version in versions:
            versioning_service.create_version(version)
        
        latest = versioning_service.get_latest_version(template_name)
        assert latest is not None
        assert latest.version_id == "v2.1.0"  # Should be semantically latest
        assert latest.system_prompt == "Latest prompt"
    
    def test_list_versions(self, versioning_service):
        """Test listing all versions of a template."""
        template_name = "ListTest"
        
        # Create several versions
        for i in range(3):
            version = PromptVersion(
                version_id=f"v1.{i}.0",
                template_name=template_name,
                provider="anthropic",
                prompt_type=PromptType.TUTORING,
                system_prompt=f"Prompt version {i}",
                template_config={},
                metadata=VersionMetadata(created_by=f"dev{i}", description=f"Version {i}")
            )
            versioning_service.create_version(version)
        
        versions = versioning_service.list_versions(template_name)
        assert len(versions) == 3
        
        # Should be sorted by semantic version (latest first)
        version_ids = [v.version_id for v in versions]
        assert version_ids == ["v1.2.0", "v1.1.0", "v1.0.0"]
    
    def test_rollback_to_version(self, versioning_service):
        """Test rolling back to a previous version."""
        template_name = "RollbackTest"
        
        # Create original version
        original = PromptVersion(
            version_id="v1.0.0",
            template_name=template_name,
            provider="anthropic",
            prompt_type=PromptType.TUTORING,
            system_prompt="Original stable prompt",
            template_config={"quality": "stable"},
            metadata=VersionMetadata(created_by="dev1", description="Stable version")
        )
        
        # Create problematic version
        problematic = PromptVersion(
            version_id="v1.1.0",
            template_name=template_name,
            provider="anthropic",
            prompt_type=PromptType.TUTORING,
            system_prompt="Problematic prompt with issues",
            template_config={"quality": "unstable"},
            metadata=VersionMetadata(created_by="dev2", description="Broken version")
        )
        
        versioning_service.create_version(original)
        versioning_service.create_version(problematic)
        
        # Rollback to original
        rollback_result = versioning_service.rollback_to_version(template_name, "v1.0.0")
        
        assert rollback_result.success is True
        assert rollback_result.previous_version == "v1.1.0"
        assert rollback_result.target_version == "v1.0.0"
        assert rollback_result.rollback_version_id.startswith("v1.0.0-rollback-")
        
        # Verify new rollback version was created
        rollback_version = versioning_service.get_version(template_name, rollback_result.rollback_version_id)
        assert rollback_version is not None
        assert rollback_version.system_prompt == "Original stable prompt"
        assert rollback_version.metadata.description.startswith("Rollback from v1.1.0 to v1.0.0")
    
    def test_rollback_nonexistent_version(self, versioning_service):
        """Test rollback to non-existent version fails gracefully."""
        rollback_result = versioning_service.rollback_to_version("NonExistent", "v1.0.0")
        
        assert rollback_result.success is False
        assert "not found" in rollback_result.error_message.lower()
    
    def test_compare_versions(self, versioning_service):
        """Test comparing two versions."""
        template_name = "CompareTest"
        
        # Create two versions
        v1 = PromptVersion(
            version_id="v1.0.0",
            template_name=template_name,
            provider="anthropic",
            prompt_type=PromptType.TUTORING,
            system_prompt="Short prompt",
            template_config={"length": "short"},
            metadata=VersionMetadata(
                created_by="dev1",
                description="Initial version",
                performance_metrics={"accuracy": 0.80, "speed": 1.5}
            )
        )
        
        v2 = PromptVersion(
            version_id="v2.0.0",
            template_name=template_name,
            provider="anthropic",
            prompt_type=PromptType.TUTORING,
            system_prompt="Much longer and more detailed prompt with better instructions",
            template_config={"length": "detailed"},
            metadata=VersionMetadata(
                created_by="dev2", 
                description="Enhanced version",
                performance_metrics={"accuracy": 0.92, "speed": 2.1}
            )
        )
        
        versioning_service.create_version(v1)
        versioning_service.create_version(v2)
        
        comparison = versioning_service.compare_versions(template_name, "v1.0.0", "v2.0.0")
        
        assert comparison is not None
        assert comparison.template_name == template_name
        assert comparison.version1_id == "v1.0.0"
        assert comparison.version2_id == "v2.0.0"
        
        # Check differences
        assert "system_prompt" in comparison.differences
        assert "template_config" in comparison.differences
        
        # Check performance comparison
        assert comparison.performance_comparison["accuracy"]["v1.0.0"] == 0.80
        assert comparison.performance_comparison["accuracy"]["v2.0.0"] == 0.92
        assert comparison.performance_comparison["speed"]["v1.0.0"] == 1.5
        assert comparison.performance_comparison["speed"]["v2.0.0"] == 2.1
    
    def test_version_persistence(self, versioning_service):
        """Test that versions are persisted to storage."""
        version = PromptVersion(
            version_id="v1.0.0",
            template_name="PersistenceTest",
            provider="anthropic",
            prompt_type=PromptType.TUTORING,
            system_prompt="Test persistence",
            template_config={},
            metadata=VersionMetadata(created_by="tester", description="Persistence test")
        )
        
        versioning_service.create_version(version)
        versioning_service.save_to_storage()
        
        # Create new service instance to test loading
        new_service = PromptVersioningService(config=versioning_service.config)
        new_service.load_from_storage()
        
        loaded_version = new_service.get_version("PersistenceTest", "v1.0.0")
        assert loaded_version is not None
        assert loaded_version.system_prompt == "Test persistence"
    
    def test_max_versions_limit(self, versioning_service):
        """Test that max versions per template is enforced."""
        # Set low limit for testing
        versioning_service.config.max_versions_per_template = 3
        template_name = "LimitTest"
        
        # Create more versions than the limit
        for i in range(5):
            version = PromptVersion(
                version_id=f"v1.{i}.0",
                template_name=template_name,
                provider="anthropic",
                prompt_type=PromptType.TUTORING,
                system_prompt=f"Version {i}",
                template_config={},
                metadata=VersionMetadata(created_by="tester", description=f"Version {i}")
            )
            versioning_service.create_version(version)
        
        # Should only keep the most recent 3 versions
        versions = versioning_service.list_versions(template_name)
        assert len(versions) == 3
        
        # Should keep the latest versions (v1.4.0, v1.3.0, v1.2.0)
        version_ids = [v.version_id for v in versions]
        assert "v1.4.0" in version_ids
        assert "v1.3.0" in version_ids
        assert "v1.2.0" in version_ids
        assert "v1.1.0" not in version_ids
        assert "v1.0.0" not in version_ids
    
    def test_delete_version(self, versioning_service):
        """Test deleting a specific version."""
        version = PromptVersion(
            version_id="v1.0.0",
            template_name="DeleteTest",
            provider="anthropic",
            prompt_type=PromptType.TUTORING,
            system_prompt="To be deleted",
            template_config={},
            metadata=VersionMetadata(created_by="tester", description="Delete test")
        )
        
        versioning_service.create_version(version)
        assert versioning_service.get_version("DeleteTest", "v1.0.0") is not None
        
        # Delete the version
        success = versioning_service.delete_version("DeleteTest", "v1.0.0")
        assert success is True
        
        # Verify it's gone
        assert versioning_service.get_version("DeleteTest", "v1.0.0") is None


class TestVersionComparison:
    """Test VersionComparison functionality."""
    
    def test_comparison_creation(self):
        """Test version comparison creation."""
        comparison = VersionComparison(
            template_name="TestTemplate",
            version1_id="v1.0.0",
            version2_id="v2.0.0",
            differences={"system_prompt": {"added": 50, "removed": 10}},
            performance_comparison={"accuracy": {"v1.0.0": 0.80, "v2.0.0": 0.92}},
            recommendation="v2.0.0 shows significant improvement"
        )
        
        assert comparison.template_name == "TestTemplate"
        assert comparison.version1_id == "v1.0.0"
        assert comparison.version2_id == "v2.0.0"
        assert comparison.recommendation == "v2.0.0 shows significant improvement"


class TestRollbackResult:
    """Test RollbackResult functionality."""
    
    def test_successful_rollback(self):
        """Test successful rollback result."""
        result = RollbackResult(
            success=True,
            previous_version="v2.0.0",
            target_version="v1.0.0",
            rollback_version_id="v1.0.0-rollback-20250826-123456"
        )
        
        assert result.success is True
        assert result.previous_version == "v2.0.0"
        assert result.target_version == "v1.0.0"
        assert result.error_message is None
        assert "rollback" in result.rollback_version_id
    
    def test_failed_rollback(self):
        """Test failed rollback result."""
        result = RollbackResult(
            success=False,
            error_message="Target version v1.0.0 not found"
        )
        
        assert result.success is False
        assert result.error_message == "Target version v1.0.0 not found"
        assert result.previous_version is None
        assert result.target_version is None