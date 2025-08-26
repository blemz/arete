"""
Prompt versioning and rollback system for philosophical tutoring.

This module provides comprehensive version management for prompt templates,
including creation, storage, retrieval, rollback capabilities, and comparison
functionality for maintaining and evolving prompt quality over time.
"""

import logging
import json
import os
import gzip
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from enum import Enum

from arete.services.prompt_template import PromptType, PhilosophicalContext

# Setup logger
logger = logging.getLogger(__name__)


@dataclass
class VersionMetadata:
    """Metadata for a prompt version."""
    created_by: str
    description: str
    created_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    parent_version: Optional[str] = None
    is_rollback: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VersionMetadata':
        """Create from dictionary."""
        data = data.copy()
        if 'created_at' in data:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


@dataclass
class PromptVersion:
    """A versioned prompt template."""
    version_id: str
    template_name: str
    provider: str
    prompt_type: PromptType
    system_prompt: str
    template_config: Dict[str, Any]
    metadata: VersionMetadata
    user_prompt_template: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['prompt_type'] = self.prompt_type.value
        data['metadata'] = self.metadata.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptVersion':
        """Create from dictionary."""
        data = data.copy()
        data['prompt_type'] = PromptType(data['prompt_type'])
        data['metadata'] = VersionMetadata.from_dict(data['metadata'])
        return cls(**data)
    
    def get_semantic_version(self) -> Tuple[int, int, int]:
        """Parse semantic version for comparison."""
        try:
            # Handle rollback versions
            if '-rollback-' in self.version_id:
                base_version = self.version_id.split('-rollback-')[0]
            else:
                base_version = self.version_id
            
            # Remove 'v' prefix if present
            if base_version.startswith('v'):
                base_version = base_version[1:]
            
            # Simple semantic version parsing (major.minor.patch)
            match = re.match(r'^(\d+)\.(\d+)\.(\d+)', base_version)
            if match:
                return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
            else:
                # Try simpler patterns
                parts = base_version.split('.')
                if len(parts) >= 3:
                    return (int(parts[0]), int(parts[1]), int(parts[2]))
                elif len(parts) == 2:
                    return (int(parts[0]), int(parts[1]), 0)
                elif len(parts) == 1:
                    return (int(parts[0]), 0, 0)
                    
        except Exception:
            # Fallback for non-semantic versions
            logger.warning(f"Could not parse semantic version from {self.version_id}")
            return (0, 0, 0)


@dataclass
class RollbackResult:
    """Result of a rollback operation."""
    success: bool
    previous_version: Optional[str] = None
    target_version: Optional[str] = None
    rollback_version_id: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class VersionComparison:
    """Comparison between two prompt versions."""
    template_name: str
    version1_id: str
    version2_id: str
    differences: Dict[str, Any]
    performance_comparison: Dict[str, Dict[str, float]]
    recommendation: str
    comparison_timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class VersioningConfig:
    """Configuration for the versioning system."""
    storage_path: str
    max_versions_per_template: int = 50
    auto_backup: bool = True
    compression_enabled: bool = True
    retention_days: int = 365
    backup_interval_hours: int = 24


class PromptVersioningService:
    """
    Service for managing prompt template versions.
    
    Provides comprehensive version control including creation, storage,
    retrieval, rollback, and comparison capabilities for prompt templates.
    """
    
    def __init__(self, config: VersioningConfig):
        """
        Initialize the versioning service.
        
        Args:
            config: Versioning configuration
        """
        self.config = config
        self.versions: Dict[str, List[PromptVersion]] = {}
        self.storage_path = Path(config.storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Load existing versions
        self.load_from_storage()
        
        logger.info(f"PromptVersioningService initialized with storage at {self.storage_path}")
    
    def create_version(self, version: PromptVersion) -> bool:
        """
        Create a new prompt version.
        
        Args:
            version: The prompt version to create
            
        Returns:
            True if successful, False otherwise
        """
        try:
            template_name = version.template_name
            
            # Initialize template list if needed
            if template_name not in self.versions:
                self.versions[template_name] = []
            
            # Check for duplicate version ID
            existing_ids = [v.version_id for v in self.versions[template_name]]
            if version.version_id in existing_ids:
                logger.warning(f"Version {version.version_id} already exists for {template_name}")
                return False
            
            # Add new version
            self.versions[template_name].append(version)
            
            # Sort versions by semantic version (latest first)
            self._sort_versions(template_name)
            
            # Enforce max versions limit
            self._enforce_version_limit(template_name)
            
            # Auto-save if enabled
            if self.config.auto_backup:
                self.save_to_storage()
            
            logger.info(f"Created version {version.version_id} for {template_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create version {version.version_id}: {e}")
            return False
    
    def get_version(self, template_name: str, version_id: str) -> Optional[PromptVersion]:
        """
        Retrieve a specific version.
        
        Args:
            template_name: Name of the template
            version_id: Version identifier
            
        Returns:
            The prompt version if found, None otherwise
        """
        if template_name not in self.versions:
            return None
        
        for version in self.versions[template_name]:
            if version.version_id == version_id:
                return version
        
        return None
    
    def get_latest_version(self, template_name: str) -> Optional[PromptVersion]:
        """
        Get the latest version of a template.
        
        Args:
            template_name: Name of the template
            
        Returns:
            The latest version if found, None otherwise
        """
        if template_name not in self.versions or not self.versions[template_name]:
            return None
        
        # Versions are already sorted by semantic version (latest first)
        return self.versions[template_name][0]
    
    def list_versions(self, template_name: str) -> List[PromptVersion]:
        """
        List all versions of a template.
        
        Args:
            template_name: Name of the template
            
        Returns:
            List of versions sorted by semantic version (latest first)
        """
        if template_name not in self.versions:
            return []
        
        return self.versions[template_name].copy()
    
    def rollback_to_version(self, template_name: str, target_version_id: str) -> RollbackResult:
        """
        Rollback to a previous version by creating a new rollback version.
        
        Args:
            template_name: Name of the template
            target_version_id: Version to rollback to
            
        Returns:
            Result of the rollback operation
        """
        try:
            # Find target version
            target_version = self.get_version(template_name, target_version_id)
            if not target_version:
                return RollbackResult(
                    success=False,
                    error_message=f"Target version {target_version_id} not found for template {template_name}"
                )
            
            # Get current latest version
            current_version = self.get_latest_version(template_name)
            if not current_version:
                return RollbackResult(
                    success=False,
                    error_message=f"No current version found for template {template_name}"
                )
            
            # Create rollback version ID
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            rollback_version_id = f"{target_version_id}-rollback-{timestamp}"
            
            # Create rollback version (copy of target with new metadata)
            rollback_metadata = VersionMetadata(
                created_by="system",
                description=f"Rollback from {current_version.version_id} to {target_version_id}",
                tags=["rollback", "system-generated"],
                parent_version=current_version.version_id,
                is_rollback=True
            )
            
            rollback_version = PromptVersion(
                version_id=rollback_version_id,
                template_name=target_version.template_name,
                provider=target_version.provider,
                prompt_type=target_version.prompt_type,
                system_prompt=target_version.system_prompt,
                template_config=target_version.template_config.copy(),
                metadata=rollback_metadata,
                user_prompt_template=target_version.user_prompt_template
            )
            
            # Create the rollback version
            if self.create_version(rollback_version):
                logger.info(f"Rollback successful: {current_version.version_id} -> {target_version_id}")
                return RollbackResult(
                    success=True,
                    previous_version=current_version.version_id,
                    target_version=target_version_id,
                    rollback_version_id=rollback_version_id
                )
            else:
                return RollbackResult(
                    success=False,
                    error_message="Failed to create rollback version"
                )
                
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return RollbackResult(
                success=False,
                error_message=str(e)
            )
    
    def compare_versions(self, template_name: str, version1_id: str, version2_id: str) -> Optional[VersionComparison]:
        """
        Compare two versions of a template.
        
        Args:
            template_name: Name of the template
            version1_id: First version to compare
            version2_id: Second version to compare
            
        Returns:
            Comparison result if both versions found, None otherwise
        """
        version1 = self.get_version(template_name, version1_id)
        version2 = self.get_version(template_name, version2_id)
        
        if not version1 or not version2:
            return None
        
        # Compare system prompts
        differences = {}
        
        # System prompt comparison
        if version1.system_prompt != version2.system_prompt:
            len1, len2 = len(version1.system_prompt), len(version2.system_prompt)
            differences["system_prompt"] = {
                "changed": True,
                "length_change": len2 - len1,
                "v1_length": len1,
                "v2_length": len2
            }
        
        # Template config comparison
        if version1.template_config != version2.template_config:
            differences["template_config"] = {
                "changed": True,
                "v1_config": version1.template_config,
                "v2_config": version2.template_config
            }
        
        # Provider comparison
        if version1.provider != version2.provider:
            differences["provider"] = {
                "changed": True,
                "v1_provider": version1.provider,
                "v2_provider": version2.provider
            }
        
        # Performance metrics comparison
        performance_comparison = {}
        metrics1 = version1.metadata.performance_metrics
        metrics2 = version2.metadata.performance_metrics
        
        all_metrics = set(metrics1.keys()) | set(metrics2.keys())
        for metric in all_metrics:
            performance_comparison[metric] = {
                version1_id: metrics1.get(metric, 0.0),
                version2_id: metrics2.get(metric, 0.0)
            }
        
        # Generate recommendation
        recommendation = self._generate_comparison_recommendation(version1, version2, differences, performance_comparison)
        
        return VersionComparison(
            template_name=template_name,
            version1_id=version1_id,
            version2_id=version2_id,
            differences=differences,
            performance_comparison=performance_comparison,
            recommendation=recommendation
        )
    
    def delete_version(self, template_name: str, version_id: str) -> bool:
        """
        Delete a specific version.
        
        Args:
            template_name: Name of the template
            version_id: Version to delete
            
        Returns:
            True if successful, False otherwise
        """
        if template_name not in self.versions:
            return False
        
        original_count = len(self.versions[template_name])
        self.versions[template_name] = [
            v for v in self.versions[template_name] 
            if v.version_id != version_id
        ]
        
        success = len(self.versions[template_name]) < original_count
        
        if success:
            logger.info(f"Deleted version {version_id} from {template_name}")
            if self.config.auto_backup:
                self.save_to_storage()
        
        return success
    
    def save_to_storage(self) -> bool:
        """
        Save all versions to persistent storage.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            storage_file = self.storage_path / "prompt_versions.json"
            backup_file = self.storage_path / f"prompt_versions_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Prepare data for serialization
            data = {
                "metadata": {
                    "saved_at": datetime.now().isoformat(),
                    "version_count": sum(len(versions) for versions in self.versions.values()),
                    "template_count": len(self.versions)
                },
                "versions": {}
            }
            
            for template_name, versions in self.versions.items():
                data["versions"][template_name] = [version.to_dict() for version in versions]
            
            # Save main file
            with open(storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Create backup if enabled
            if self.config.auto_backup:
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                # Compress backup if enabled
                if self.config.compression_enabled:
                    with open(backup_file, 'rb') as f_in:
                        with gzip.open(f"{backup_file}.gz", 'wb') as f_out:
                            f_out.writelines(f_in)
                    os.remove(backup_file)
            
            logger.info(f"Saved {data['metadata']['version_count']} versions to storage")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save versions to storage: {e}")
            return False
    
    def load_from_storage(self) -> bool:
        """
        Load versions from persistent storage.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            storage_file = self.storage_path / "prompt_versions.json"
            
            if not storage_file.exists():
                logger.info("No existing version storage found, starting fresh")
                return True
            
            with open(storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load versions
            self.versions = {}
            for template_name, version_dicts in data.get("versions", {}).items():
                self.versions[template_name] = [
                    PromptVersion.from_dict(version_dict) 
                    for version_dict in version_dicts
                ]
                # Ensure proper sorting
                self._sort_versions(template_name)
            
            version_count = sum(len(versions) for versions in self.versions.values())
            logger.info(f"Loaded {version_count} versions from storage")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load versions from storage: {e}")
            return False
    
    def cleanup_old_versions(self, days_to_keep: int = None) -> int:
        """
        Clean up old versions based on retention policy.
        
        Args:
            days_to_keep: Days to retain (uses config default if None)
            
        Returns:
            Number of versions cleaned up
        """
        days_to_keep = days_to_keep or self.config.retention_days
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        cleaned_count = 0
        
        for template_name in list(self.versions.keys()):
            versions_to_keep = []
            for version in self.versions[template_name]:
                # Always keep the latest version and rollback versions
                if (version == self.versions[template_name][0] or 
                    version.metadata.is_rollback or
                    version.metadata.created_at > cutoff_date):
                    versions_to_keep.append(version)
                else:
                    cleaned_count += 1
                    logger.info(f"Cleaning up old version {version.version_id} from {template_name}")
            
            self.versions[template_name] = versions_to_keep
        
        if cleaned_count > 0 and self.config.auto_backup:
            self.save_to_storage()
        
        logger.info(f"Cleaned up {cleaned_count} old versions")
        return cleaned_count
    
    def get_version_history(self, template_name: str, limit: int = 10) -> List[PromptVersion]:
        """
        Get version history for a template.
        
        Args:
            template_name: Name of the template
            limit: Maximum number of versions to return
            
        Returns:
            List of versions in chronological order (newest first)
        """
        versions = self.list_versions(template_name)
        return versions[:limit]
    
    def _sort_versions(self, template_name: str) -> None:
        """Sort versions by semantic version (latest first)."""
        if template_name in self.versions:
            self.versions[template_name].sort(
                key=lambda v: v.get_semantic_version(),
                reverse=True
            )
    
    def _enforce_version_limit(self, template_name: str) -> None:
        """Enforce maximum versions per template limit."""
        if (template_name in self.versions and 
            len(self.versions[template_name]) > self.config.max_versions_per_template):
            
            # Keep the most recent versions
            excess_count = len(self.versions[template_name]) - self.config.max_versions_per_template
            removed_versions = self.versions[template_name][-excess_count:]
            self.versions[template_name] = self.versions[template_name][:-excess_count]
            
            logger.info(f"Removed {excess_count} excess versions from {template_name}")
    
    def _generate_comparison_recommendation(
        self, 
        version1: PromptVersion, 
        version2: PromptVersion,
        differences: Dict[str, Any],
        performance_comparison: Dict[str, Dict[str, float]]
    ) -> str:
        """Generate recommendation based on version comparison."""
        recommendations = []
        
        # Performance-based recommendations
        for metric, values in performance_comparison.items():
            v1_score = values.get(version1.version_id, 0.0)
            v2_score = values.get(version2.version_id, 0.0)
            
            if v2_score > v1_score * 1.1:  # 10% improvement threshold
                recommendations.append(f"{version2.version_id} shows {metric} improvement ({v2_score:.2f} vs {v1_score:.2f})")
            elif v1_score > v2_score * 1.1:
                recommendations.append(f"{version1.version_id} shows better {metric} ({v1_score:.2f} vs {v2_score:.2f})")
        
        # Structural recommendations
        if "system_prompt" in differences:
            length_change = differences["system_prompt"]["length_change"]
            if length_change > 50:
                recommendations.append(f"{version2.version_id} has significantly expanded prompt (+{length_change} chars)")
            elif length_change < -50:
                recommendations.append(f"{version2.version_id} has more concise prompt ({length_change} chars)")
        
        # Default recommendation
        if not recommendations:
            recommendations.append("Both versions have similar characteristics")
        
        return "; ".join(recommendations)


# Convenience functions
def create_versioning_service(storage_path: str, **config_kwargs) -> PromptVersioningService:
    """
    Create a versioning service with default configuration.
    
    Args:
        storage_path: Path to store versions
        **config_kwargs: Additional configuration options
        
    Returns:
        Configured versioning service
    """
    config = VersioningConfig(storage_path=storage_path, **config_kwargs)
    return PromptVersioningService(config)


def create_prompt_version(
    version_id: str,
    template_name: str,
    provider: str,
    prompt_type: PromptType,
    system_prompt: str,
    created_by: str,
    description: str,
    template_config: Dict[str, Any] = None,
    performance_metrics: Dict[str, float] = None,
    tags: List[str] = None
) -> PromptVersion:
    """
    Convenience function to create a prompt version.
    
    Args:
        version_id: Version identifier
        template_name: Name of the template
        provider: LLM provider name
        prompt_type: Type of prompt
        system_prompt: The system prompt content
        created_by: Creator identifier
        description: Version description
        template_config: Template configuration
        performance_metrics: Performance metrics
        tags: Version tags
        
    Returns:
        Configured prompt version
    """
    metadata = VersionMetadata(
        created_by=created_by,
        description=description,
        tags=tags or [],
        performance_metrics=performance_metrics or {}
    )
    
    return PromptVersion(
        version_id=version_id,
        template_name=template_name,
        provider=provider,
        prompt_type=prompt_type,
        system_prompt=system_prompt,
        template_config=template_config or {},
        metadata=metadata
    )