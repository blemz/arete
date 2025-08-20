"""
Expert Validation Service for Arete Graph-RAG system.

Provides workflow for domain expert review and validation of extracted knowledge triples.
Supports confidence scoring, expert annotations, and quality assurance for philosophical
knowledge graph construction.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ValidationStatus(str, Enum):
    """Status options for validation items."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
    EXPERT_REVIEW = "expert_review"


class ValidationPriority(str, Enum):
    """Priority levels for validation items."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ExpertAnnotation(BaseModel):
    """Expert annotation for a validation item."""
    
    expert_id: str = Field(..., description="ID of the reviewing expert")
    expert_name: str = Field(..., description="Name of the reviewing expert")
    status: ValidationStatus = Field(..., description="Validation status assigned")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Expert confidence score")
    comments: Optional[str] = Field(None, description="Expert comments and feedback")
    suggested_changes: Optional[Dict[str, Any]] = Field(None, description="Suggested changes to the item")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When annotation was created")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ValidationItem(BaseModel):
    """Item requiring expert validation."""
    
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for validation item")
    item_type: str = Field(..., description="Type of item (entity, relationship, triple)")
    item_data: Dict[str, Any] = Field(..., description="The actual data to be validated")
    extraction_confidence: float = Field(..., ge=0.0, le=1.0, description="Original extraction confidence")
    priority: ValidationPriority = Field(default=ValidationPriority.MEDIUM, description="Validation priority")
    status: ValidationStatus = Field(default=ValidationStatus.PENDING, description="Current validation status")
    source_document_id: Optional[UUID] = Field(None, description="Source document ID")
    context: Optional[str] = Field(None, description="Textual context for the item")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    # Expert validation
    annotations: List[ExpertAnnotation] = Field(default_factory=list, description="Expert annotations")
    final_status: Optional[ValidationStatus] = Field(None, description="Final validation status")
    consensus_score: Optional[float] = Field(None, description="Expert consensus score")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def add_annotation(self, annotation: ExpertAnnotation) -> None:
        """Add an expert annotation."""
        self.annotations.append(annotation)
        self.updated_at = datetime.utcnow()
        
        # Update status if this is the first annotation or if it changes status
        if not self.final_status or annotation.status != self.status:
            self.status = annotation.status
    
    def calculate_consensus(self) -> float:
        """Calculate consensus score based on expert annotations."""
        if not self.annotations:
            return 0.0
        
        # Simple consensus: percentage of approving experts
        approved_count = sum(1 for ann in self.annotations if ann.status == ValidationStatus.APPROVED)
        return approved_count / len(self.annotations)
    
    def get_latest_annotation(self) -> Optional[ExpertAnnotation]:
        """Get the most recent expert annotation."""
        if not self.annotations:
            return None
        return max(self.annotations, key=lambda ann: ann.timestamp)


class ExpertValidationService:
    """
    Service for managing expert validation workflow.
    
    Handles submission of items for validation, tracking of expert reviews,
    consensus building, and final approval workflow for knowledge graph elements.
    """
    
    def __init__(self):
        """Initialize ExpertValidationService."""
        self._validation_queue: Dict[UUID, ValidationItem] = {}
        self._expert_assignments: Dict[str, List[UUID]] = {}
        
        # Validation thresholds and rules
        self.min_consensus_threshold = 0.7  # 70% agreement for approval
        self.min_expert_reviews = 2  # Minimum number of expert reviews
        self.auto_approve_threshold = 0.95  # High confidence items for auto-approval
        self.requires_expert_threshold = 0.5  # Low confidence items require expert review
    
    def submit_for_validation(
        self,
        item_type: str,
        item_data: Dict[str, Any],
        extraction_confidence: float,
        source_document_id: Optional[UUID] = None,
        context: Optional[str] = None,
        priority: ValidationPriority = ValidationPriority.MEDIUM
    ) -> ValidationItem:
        """
        Submit an item for expert validation.
        
        Args:
            item_type: Type of item (entity, relationship, triple)
            item_data: The actual data to be validated
            extraction_confidence: Original extraction confidence score
            source_document_id: Optional source document ID
            context: Optional textual context
            priority: Validation priority level
            
        Returns:
            ValidationItem created for tracking
        """
        # Determine initial status and priority based on confidence
        initial_status = self._determine_initial_status(extraction_confidence)
        if extraction_confidence < self.requires_expert_threshold:
            priority = ValidationPriority.HIGH
        
        validation_item = ValidationItem(
            item_type=item_type,
            item_data=item_data,
            extraction_confidence=extraction_confidence,
            priority=priority,
            status=initial_status,
            source_document_id=source_document_id,
            context=context
        )
        
        self._validation_queue[validation_item.id] = validation_item
        
        logger.info(f"Submitted {item_type} for validation: {validation_item.id} "
                   f"(confidence: {extraction_confidence:.2f}, priority: {priority})")
        
        return validation_item
    
    def _determine_initial_status(self, confidence: float) -> ValidationStatus:
        """Determine initial validation status based on confidence."""
        if confidence >= self.auto_approve_threshold:
            return ValidationStatus.APPROVED
        elif confidence < self.requires_expert_threshold:
            return ValidationStatus.EXPERT_REVIEW
        else:
            return ValidationStatus.PENDING
    
    def submit_expert_annotation(
        self,
        validation_id: UUID,
        expert_id: str,
        expert_name: str,
        status: ValidationStatus,
        confidence_score: Optional[float] = None,
        comments: Optional[str] = None,
        suggested_changes: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Submit expert annotation for a validation item.
        
        Args:
            validation_id: ID of the validation item
            expert_id: ID of the reviewing expert
            expert_name: Name of the reviewing expert
            status: Validation status assigned by expert
            confidence_score: Optional expert confidence score
            comments: Optional expert comments
            suggested_changes: Optional suggested changes
            
        Returns:
            True if annotation was added successfully
        """
        if validation_id not in self._validation_queue:
            logger.error(f"Validation item not found: {validation_id}")
            return False
        
        validation_item = self._validation_queue[validation_id]
        
        annotation = ExpertAnnotation(
            expert_id=expert_id,
            expert_name=expert_name,
            status=status,
            confidence_score=confidence_score,
            comments=comments,
            suggested_changes=suggested_changes
        )
        
        validation_item.add_annotation(annotation)
        
        # Check if we have enough reviews to make a final decision
        self._evaluate_consensus(validation_item)
        
        logger.info(f"Expert annotation added by {expert_name} for item {validation_id}: {status}")
        
        return True
    
    def _evaluate_consensus(self, validation_item: ValidationItem) -> None:
        """Evaluate expert consensus and update final status if appropriate."""
        if len(validation_item.annotations) < self.min_expert_reviews:
            return  # Need more reviews
        
        consensus_score = validation_item.calculate_consensus()
        validation_item.consensus_score = consensus_score
        
        # Determine final status based on consensus
        if consensus_score >= self.min_consensus_threshold:
            validation_item.final_status = ValidationStatus.APPROVED
            logger.info(f"Item {validation_item.id} approved with consensus {consensus_score:.2f}")
        else:
            # Check if majority rejects
            rejected_count = sum(1 for ann in validation_item.annotations 
                               if ann.status == ValidationStatus.REJECTED)
            if rejected_count / len(validation_item.annotations) >= 0.5:
                validation_item.final_status = ValidationStatus.REJECTED
                logger.info(f"Item {validation_item.id} rejected with consensus {consensus_score:.2f}")
            else:
                validation_item.final_status = ValidationStatus.NEEDS_REVISION
                logger.info(f"Item {validation_item.id} needs revision with consensus {consensus_score:.2f}")
    
    def get_validation_item(self, validation_id: UUID) -> Optional[ValidationItem]:
        """Get validation item by ID."""
        return self._validation_queue.get(validation_id)
    
    def get_pending_validations(
        self,
        expert_id: Optional[str] = None,
        priority: Optional[ValidationPriority] = None,
        item_type: Optional[str] = None
    ) -> List[ValidationItem]:
        """
        Get pending validation items.
        
        Args:
            expert_id: Optional filter by assigned expert
            priority: Optional filter by priority
            item_type: Optional filter by item type
            
        Returns:
            List of pending validation items
        """
        items = []
        
        for validation_item in self._validation_queue.values():
            # Filter by status
            if validation_item.status not in [ValidationStatus.PENDING, ValidationStatus.EXPERT_REVIEW]:
                continue
            
            # Filter by expert assignment
            if expert_id and expert_id in self._expert_assignments:
                if validation_item.id not in self._expert_assignments[expert_id]:
                    continue
            
            # Filter by priority
            if priority and validation_item.priority != priority:
                continue
            
            # Filter by item type
            if item_type and validation_item.item_type != item_type:
                continue
            
            items.append(validation_item)
        
        # Sort by priority and creation time
        priority_order = {
            ValidationPriority.CRITICAL: 0,
            ValidationPriority.HIGH: 1,
            ValidationPriority.MEDIUM: 2,
            ValidationPriority.LOW: 3
        }
        
        items.sort(key=lambda x: (priority_order[x.priority], x.created_at))
        
        return items
    
    def assign_expert(self, expert_id: str, validation_ids: List[UUID]) -> bool:
        """
        Assign validation items to an expert.
        
        Args:
            expert_id: ID of the expert
            validation_ids: List of validation item IDs to assign
            
        Returns:
            True if assignment was successful
        """
        # Verify all validation items exist
        for validation_id in validation_ids:
            if validation_id not in self._validation_queue:
                logger.error(f"Cannot assign non-existent validation item: {validation_id}")
                return False
        
        # Create or update expert assignments
        if expert_id not in self._expert_assignments:
            self._expert_assignments[expert_id] = []
        
        self._expert_assignments[expert_id].extend(validation_ids)
        
        logger.info(f"Assigned {len(validation_ids)} validation items to expert {expert_id}")
        
        return True
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """
        Get validation statistics and metrics.
        
        Returns:
            Dictionary with validation statistics
        """
        total_items = len(self._validation_queue)
        
        if total_items == 0:
            return {
                "total_items": 0,
                "status_distribution": {},
                "priority_distribution": {},
                "type_distribution": {},
                "average_consensus_score": 0.0,
                "expert_activity": {}
            }
        
        # Status distribution
        status_dist = {}
        for item in self._validation_queue.values():
            status = item.final_status or item.status
            status_dist[status.value] = status_dist.get(status.value, 0) + 1
        
        # Priority distribution
        priority_dist = {}
        for item in self._validation_queue.values():
            priority_dist[item.priority.value] = priority_dist.get(item.priority.value, 0) + 1
        
        # Type distribution
        type_dist = {}
        for item in self._validation_queue.values():
            type_dist[item.item_type] = type_dist.get(item.item_type, 0) + 1
        
        # Average consensus score
        consensus_scores = [item.consensus_score for item in self._validation_queue.values() 
                           if item.consensus_score is not None]
        avg_consensus = sum(consensus_scores) / len(consensus_scores) if consensus_scores else 0.0
        
        # Expert activity
        expert_activity = {}
        for item in self._validation_queue.values():
            for annotation in item.annotations:
                expert_id = annotation.expert_id
                if expert_id not in expert_activity:
                    expert_activity[expert_id] = {"reviews": 0, "approvals": 0}
                expert_activity[expert_id]["reviews"] += 1
                if annotation.status == ValidationStatus.APPROVED:
                    expert_activity[expert_id]["approvals"] += 1
        
        return {
            "total_items": total_items,
            "status_distribution": status_dist,
            "priority_distribution": priority_dist,
            "type_distribution": type_dist,
            "average_consensus_score": avg_consensus,
            "expert_activity": expert_activity,
            "pending_count": sum(1 for item in self._validation_queue.values() 
                               if item.status in [ValidationStatus.PENDING, ValidationStatus.EXPERT_REVIEW])
        }
    
    def get_approved_items(self) -> List[ValidationItem]:
        """Get all approved validation items."""
        return [
            item for item in self._validation_queue.values()
            if item.final_status == ValidationStatus.APPROVED or 
               (item.status == ValidationStatus.APPROVED and item.final_status is None)
        ]
    
    def export_validation_data(self) -> Dict[str, Any]:
        """
        Export validation data for analysis or backup.
        
        Returns:
            Dictionary with all validation data
        """
        return {
            "validation_items": [item.dict() for item in self._validation_queue.values()],
            "expert_assignments": self._expert_assignments,
            "statistics": self.get_validation_statistics(),
            "export_timestamp": datetime.utcnow().isoformat(),
            "thresholds": {
                "min_consensus_threshold": self.min_consensus_threshold,
                "min_expert_reviews": self.min_expert_reviews,
                "auto_approve_threshold": self.auto_approve_threshold,
                "requires_expert_threshold": self.requires_expert_threshold
            }
        }