"""
Tests for Expert Validation Service.
"""

import uuid
import pytest
from datetime import datetime
from unittest.mock import Mock

from arete.services.expert_validation_service import (
    ExpertValidationService, ValidationItem, ExpertAnnotation,
    ValidationStatus, ValidationPriority
)


class TestExpertAnnotation:
    """Test ExpertAnnotation model."""
    
    def test_annotation_creation(self):
        """Test creating an expert annotation."""
        annotation = ExpertAnnotation(
            expert_id="expert1",
            expert_name="Dr. Smith",
            status=ValidationStatus.APPROVED,
            confidence_score=0.9,
            comments="This relationship is well-supported."
        )
        
        assert annotation.expert_id == "expert1"
        assert annotation.expert_name == "Dr. Smith"
        assert annotation.status == ValidationStatus.APPROVED
        assert annotation.confidence_score == 0.9
        assert annotation.comments == "This relationship is well-supported."
        assert isinstance(annotation.timestamp, datetime)


class TestValidationItem:
    """Test ValidationItem model."""
    
    def test_validation_item_creation(self):
        """Test creating a validation item."""
        item_data = {
            "subject": "Socrates",
            "relation": "TEACHES",
            "object": "Plato"
        }
        
        item = ValidationItem(
            item_type="relationship",
            item_data=item_data,
            extraction_confidence=0.8,
            priority=ValidationPriority.HIGH
        )
        
        assert item.item_type == "relationship"
        assert item.item_data == item_data
        assert item.extraction_confidence == 0.8
        assert item.priority == ValidationPriority.HIGH
        assert item.status == ValidationStatus.PENDING
        assert len(item.annotations) == 0
    
    def test_add_annotation(self):
        """Test adding an annotation to a validation item."""
        item = ValidationItem(
            item_type="entity",
            item_data={"name": "Socrates"},
            extraction_confidence=0.7
        )
        
        annotation = ExpertAnnotation(
            expert_id="expert1",
            expert_name="Dr. Smith",
            status=ValidationStatus.APPROVED
        )
        
        item.add_annotation(annotation)
        
        assert len(item.annotations) == 1
        assert item.annotations[0] == annotation
        assert item.status == ValidationStatus.APPROVED
        assert item.updated_at is not None
    
    def test_calculate_consensus(self):
        """Test consensus calculation."""
        item = ValidationItem(
            item_type="relationship",
            item_data={"subject": "A", "relation": "R", "object": "B"},
            extraction_confidence=0.6
        )
        
        # No annotations - should return 0.0
        assert item.calculate_consensus() == 0.0
        
        # Add some annotations
        item.add_annotation(ExpertAnnotation(
            expert_id="expert1", expert_name="Expert 1", status=ValidationStatus.APPROVED
        ))
        item.add_annotation(ExpertAnnotation(
            expert_id="expert2", expert_name="Expert 2", status=ValidationStatus.APPROVED
        ))
        item.add_annotation(ExpertAnnotation(
            expert_id="expert3", expert_name="Expert 3", status=ValidationStatus.REJECTED
        ))
        
        # 2 out of 3 approved = 0.67
        consensus = item.calculate_consensus()
        assert abs(consensus - 0.6667) < 0.001
    
    def test_get_latest_annotation(self):
        """Test getting the latest annotation."""
        item = ValidationItem(
            item_type="entity",
            item_data={"name": "Plato"},
            extraction_confidence=0.8
        )
        
        # No annotations
        assert item.get_latest_annotation() is None
        
        # Add annotations
        ann1 = ExpertAnnotation(expert_id="expert1", expert_name="Expert 1", status=ValidationStatus.PENDING)
        ann2 = ExpertAnnotation(expert_id="expert2", expert_name="Expert 2", status=ValidationStatus.APPROVED)
        
        item.add_annotation(ann1)
        item.add_annotation(ann2)
        
        latest = item.get_latest_annotation()
        assert latest == ann2  # Should be the most recent


class TestExpertValidationService:
    """Test ExpertValidationService functionality."""
    
    @pytest.fixture
    def validation_service(self):
        """Create a validation service for testing."""
        return ExpertValidationService()
    
    def test_submit_for_validation_basic(self, validation_service):
        """Test basic validation submission."""
        item_data = {"subject": "Socrates", "relation": "TEACHES", "object": "Plato"}
        
        validation_item = validation_service.submit_for_validation(
            item_type="relationship",
            item_data=item_data,
            extraction_confidence=0.7
        )
        
        assert validation_item.item_type == "relationship"
        assert validation_item.item_data == item_data
        assert validation_item.extraction_confidence == 0.7
        assert validation_item.status == ValidationStatus.PENDING
    
    def test_auto_approval_high_confidence(self, validation_service):
        """Test automatic approval for high confidence items."""
        validation_item = validation_service.submit_for_validation(
            item_type="entity",
            item_data={"name": "Socrates"},
            extraction_confidence=0.96  # Above auto-approve threshold
        )
        
        assert validation_item.status == ValidationStatus.APPROVED
    
    def test_expert_review_low_confidence(self, validation_service):
        """Test expert review requirement for low confidence items."""
        validation_item = validation_service.submit_for_validation(
            item_type="entity",
            item_data={"name": "UnknownPhilosopher"},
            extraction_confidence=0.3  # Below expert review threshold
        )
        
        assert validation_item.status == ValidationStatus.EXPERT_REVIEW
        assert validation_item.priority == ValidationPriority.HIGH
    
    def test_submit_expert_annotation(self, validation_service):
        """Test submitting expert annotations."""
        # Submit item for validation
        validation_item = validation_service.submit_for_validation(
            item_type="relationship",
            item_data={"subject": "A", "relation": "R", "object": "B"},
            extraction_confidence=0.6
        )
        
        # Submit expert annotation
        success = validation_service.submit_expert_annotation(
            validation_id=validation_item.id,
            expert_id="expert1",
            expert_name="Dr. Smith",
            status=ValidationStatus.APPROVED,
            confidence_score=0.9,
            comments="Well-supported relationship"
        )
        
        assert success is True
        
        # Check that annotation was added
        retrieved_item = validation_service.get_validation_item(validation_item.id)
        assert len(retrieved_item.annotations) == 1
        assert retrieved_item.annotations[0].expert_id == "expert1"
        assert retrieved_item.annotations[0].status == ValidationStatus.APPROVED
    
    def test_consensus_evaluation(self, validation_service):
        """Test consensus evaluation with multiple experts."""
        # Submit item for validation
        validation_item = validation_service.submit_for_validation(
            item_type="relationship",
            item_data={"subject": "A", "relation": "R", "object": "B"},
            extraction_confidence=0.6
        )
        
        # Add multiple expert annotations
        validation_service.submit_expert_annotation(
            validation_item.id, "expert1", "Expert 1", ValidationStatus.APPROVED
        )
        validation_service.submit_expert_annotation(
            validation_item.id, "expert2", "Expert 2", ValidationStatus.APPROVED
        )
        
        # Check consensus after minimum reviews
        retrieved_item = validation_service.get_validation_item(validation_item.id)
        assert retrieved_item.final_status == ValidationStatus.APPROVED
        assert retrieved_item.consensus_score == 1.0
    
    def test_rejection_consensus(self, validation_service):
        """Test rejection when majority rejects."""
        validation_item = validation_service.submit_for_validation(
            item_type="entity",
            item_data={"name": "FakePhilosopher"},
            extraction_confidence=0.6
        )
        
        # Add rejecting annotations
        validation_service.submit_expert_annotation(
            validation_item.id, "expert1", "Expert 1", ValidationStatus.REJECTED
        )
        validation_service.submit_expert_annotation(
            validation_item.id, "expert2", "Expert 2", ValidationStatus.REJECTED
        )
        
        retrieved_item = validation_service.get_validation_item(validation_item.id)
        assert retrieved_item.final_status == ValidationStatus.REJECTED
    
    def test_get_pending_validations(self, validation_service):
        """Test getting pending validation items."""
        # Submit multiple items
        item1 = validation_service.submit_for_validation(
            "entity", {"name": "Socrates"}, 0.6, priority=ValidationPriority.HIGH
        )
        item2 = validation_service.submit_for_validation(
            "relationship", {"subject": "A", "relation": "R", "object": "B"}, 0.7
        )
        item3 = validation_service.submit_for_validation(
            "entity", {"name": "Plato"}, 0.98  # Should be auto-approved
        )
        
        # Get pending items
        pending = validation_service.get_pending_validations()
        
        # Should return pending items, ordered by priority
        assert len(pending) == 2  # item3 is auto-approved
        assert pending[0].id == item1.id  # HIGH priority first
        assert pending[1].id == item2.id
    
    def test_get_pending_validations_with_filters(self, validation_service):
        """Test getting pending validations with filters."""
        item1 = validation_service.submit_for_validation(
            "entity", {"name": "Socrates"}, 0.6, priority=ValidationPriority.HIGH
        )
        item2 = validation_service.submit_for_validation(
            "relationship", {"subject": "A", "relation": "R", "object": "B"}, 0.7
        )
        
        # Filter by priority
        high_priority = validation_service.get_pending_validations(priority=ValidationPriority.HIGH)
        assert len(high_priority) == 1
        assert high_priority[0].id == item1.id
        
        # Filter by item type
        entities = validation_service.get_pending_validations(item_type="entity")
        assert len(entities) == 1
        assert entities[0].id == item1.id
    
    def test_assign_expert(self, validation_service):
        """Test expert assignment."""
        item1 = validation_service.submit_for_validation(
            "entity", {"name": "Socrates"}, 0.6
        )
        item2 = validation_service.submit_for_validation(
            "entity", {"name": "Plato"}, 0.6
        )
        
        # Assign items to expert
        success = validation_service.assign_expert("expert1", [item1.id, item2.id])
        assert success is True
        
        # Check assignment
        assert "expert1" in validation_service._expert_assignments
        assert item1.id in validation_service._expert_assignments["expert1"]
        assert item2.id in validation_service._expert_assignments["expert1"]
    
    def test_get_validation_statistics(self, validation_service):
        """Test validation statistics."""
        # Submit various items
        validation_service.submit_for_validation("entity", {"name": "Socrates"}, 0.6)
        validation_service.submit_for_validation("relationship", {"subject": "A", "relation": "R", "object": "B"}, 0.7)
        validation_service.submit_for_validation("entity", {"name": "Plato"}, 0.98)  # Auto-approved
        
        stats = validation_service.get_validation_statistics()
        
        assert stats["total_items"] == 3
        assert "status_distribution" in stats
        assert "priority_distribution" in stats
        assert "type_distribution" in stats
        assert stats["type_distribution"]["entity"] == 2
        assert stats["type_distribution"]["relationship"] == 1
    
    def test_get_approved_items(self, validation_service):
        """Test getting approved items."""
        item1 = validation_service.submit_for_validation("entity", {"name": "Socrates"}, 0.6)
        item2 = validation_service.submit_for_validation("entity", {"name": "Plato"}, 0.98)  # Auto-approved
        
        # Manually approve item1
        validation_service.submit_expert_annotation(
            item1.id, "expert1", "Expert 1", ValidationStatus.APPROVED
        )
        validation_service.submit_expert_annotation(
            item1.id, "expert2", "Expert 2", ValidationStatus.APPROVED
        )
        
        approved = validation_service.get_approved_items()
        assert len(approved) == 2
        approved_ids = {item.id for item in approved}
        assert item1.id in approved_ids
        assert item2.id in approved_ids
    
    def test_export_validation_data(self, validation_service):
        """Test exporting validation data."""
        validation_service.submit_for_validation("entity", {"name": "Socrates"}, 0.6)
        
        export_data = validation_service.export_validation_data()
        
        assert "validation_items" in export_data
        assert "expert_assignments" in export_data
        assert "statistics" in export_data
        assert "export_timestamp" in export_data
        assert "thresholds" in export_data
        
        assert len(export_data["validation_items"]) == 1
        assert export_data["thresholds"]["min_consensus_threshold"] == 0.7