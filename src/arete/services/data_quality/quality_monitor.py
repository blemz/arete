"""
Quality Monitoring System for Arete Graph-RAG System.

Provides continuous monitoring capabilities for RAG system quality including:
- Scheduled quality evaluations
- Automated alerting on quality degradation
- Quality trend tracking and analysis
- Performance monitoring integration
- Real-time quality dashboard data
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass
import statistics
from enum import Enum

from arete.services.data_quality.ragas_quality_service import (
    RAGASQualityService,
    EvaluationResult,
    QualityThresholds
)
from arete.config import Settings, get_settings

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class MonitoringStatus(str, Enum):
    """Monitoring system status."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class QualityAlert:
    """Quality alert data structure."""
    alert_id: str
    severity: AlertSeverity
    metric_name: str
    current_value: float
    threshold_value: float
    message: str
    timestamp: datetime
    query_samples: List[str] = None


@dataclass
class MonitoringStats:
    """Monitoring system statistics."""
    total_evaluations: int
    monitoring_uptime_hours: float
    average_quality_score: float
    quality_trend_slope: float
    alerts_triggered: int
    last_evaluation_time: Optional[datetime]


class QualityMonitor:
    """Continuous quality monitoring system for RAG pipeline."""
    
    def __init__(
        self,
        quality_service: RAGASQualityService,
        config: Dict[str, Any],
        settings: Optional[Settings] = None
    ):
        """Initialize quality monitor."""
        self.quality_service = quality_service
        self.config = config
        self.settings = settings or get_settings()
        self.logger = logging.getLogger(__name__)
        
        # Monitoring state
        self.status = MonitoringStatus.STOPPED
        self.start_time: Optional[datetime] = None
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Quality tracking
        self.evaluation_history: List[EvaluationResult] = []
        self.recent_alerts: List[QualityAlert] = []
        
        # Configuration
        self.evaluation_interval_hours = config.get('evaluation_interval_hours', 24)
        self.sample_size = config.get('sample_size', 10)
        self.alert_thresholds = config.get('alert_thresholds', {})
        self.max_history_size = config.get('max_history_size', 1000)
        
        # Alert callbacks
        self.alert_callbacks: List[Callable[[QualityAlert], None]] = []
        
        # Sample query generators
        self.query_generators: List[Callable[[], Dict[str, Any]]] = []
        
    def add_alert_callback(self, callback: Callable[[QualityAlert], None]) -> None:
        """Add callback for quality alerts."""
        self.alert_callbacks.append(callback)
        self.logger.info("Added quality alert callback")
    
    def add_query_generator(self, generator: Callable[[], Dict[str, Any]]) -> None:
        """Add sample query generator for monitoring."""
        self.query_generators.append(generator)
        self.logger.info("Added sample query generator")
    
    async def start_monitoring(self) -> None:
        """Start continuous quality monitoring."""
        if self.status == MonitoringStatus.RUNNING:
            self.logger.warning("Quality monitoring already running")
            return
            
        self.logger.info("Starting quality monitoring system")
        self.status = MonitoringStatus.STARTING
        self.start_time = datetime.now(timezone.utc)
        
        try:
            # Start monitoring task
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            self.status = MonitoringStatus.RUNNING
            self.logger.info("Quality monitoring system started successfully")
            
        except Exception as e:
            self.status = MonitoringStatus.ERROR
            self.logger.error(f"Failed to start quality monitoring: {str(e)}")
            raise
    
    async def stop_monitoring(self) -> None:
        """Stop continuous quality monitoring."""
        if self.status != MonitoringStatus.RUNNING:
            self.logger.warning("Quality monitoring not running")
            return
            
        self.logger.info("Stopping quality monitoring system")
        self.status = MonitoringStatus.STOPPING
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            
        self.status = MonitoringStatus.STOPPED
        self.logger.info("Quality monitoring system stopped")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.status == MonitoringStatus.RUNNING:
            try:
                # Run quality evaluation
                await self._run_evaluation_cycle()
                
                # Wait for next evaluation
                sleep_seconds = self.evaluation_interval_hours * 3600
                await asyncio.sleep(sleep_seconds)
                
            except asyncio.CancelledError:
                self.logger.info("Quality monitoring loop cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error in quality monitoring loop: {str(e)}")
                # Continue monitoring but wait a bit before retrying
                await asyncio.sleep(300)  # 5 minutes
    
    async def _run_evaluation_cycle(self) -> None:
        """Run a single evaluation cycle."""
        self.logger.info("Starting quality evaluation cycle")
        
        try:
            # Generate sample queries
            sample_queries = await self._generate_sample_queries()
            
            if not sample_queries:
                self.logger.warning("No sample queries generated for evaluation")
                return
            
            # Run evaluations
            evaluation_results = []
            for query_data in sample_queries:
                try:
                    result = await self.quality_service.evaluate_single_query(
                        question=query_data["question"],
                        contexts=query_data["contexts"],
                        answer=query_data["answer"],
                        ground_truth=query_data.get("ground_truth")
                    )
                    evaluation_results.append(result)
                    
                except Exception as e:
                    self.logger.error(f"Failed to evaluate query: {str(e)}")
                    continue
            
            # Store results
            self.evaluation_history.extend(evaluation_results)
            
            # Trim history if needed
            if len(self.evaluation_history) > self.max_history_size:
                self.evaluation_history = self.evaluation_history[-self.max_history_size:]
            
            # Check for quality alerts
            await self._check_quality_alerts(evaluation_results)
            
            self.logger.info(f"Completed evaluation cycle with {len(evaluation_results)} results")
            
        except Exception as e:
            self.logger.error(f"Error in evaluation cycle: {str(e)}")
            raise
    
    async def _generate_sample_queries(self) -> List[Dict[str, Any]]:
        """Generate sample queries for evaluation."""
        sample_queries = []
        
        if not self.query_generators:
            # Use default philosophical sample queries
            sample_queries = self._get_default_sample_queries()
        else:
            # Use registered generators
            for generator in self.query_generators:
                try:
                    queries = generator()
                    if isinstance(queries, list):
                        sample_queries.extend(queries)
                    else:
                        sample_queries.append(queries)
                except Exception as e:
                    self.logger.error(f"Error in query generator: {str(e)}")
        
        # Limit to configured sample size
        if len(sample_queries) > self.sample_size:
            sample_queries = sample_queries[:self.sample_size]
        
        return sample_queries
    
    def _get_default_sample_queries(self) -> List[Dict[str, Any]]:
        """Get default philosophical sample queries for monitoring."""
        return [
            {
                "question": "What is virtue according to Aristotle?",
                "contexts": [
                    "Aristotle defines virtue as a disposition to choose the mean between extremes.",
                    "In the Nicomachean Ethics, virtue is described as excellence of character."
                ],
                "answer": "According to Aristotle, virtue is a habitual disposition to choose the mean between extremes of excess and deficiency.",
                "ground_truth": "Virtue is the mean between extremes according to Aristotle."
            },
            {
                "question": "What is justice according to Plato?",
                "contexts": [
                    "In the Republic, Plato defines justice as each part doing its own work.",
                    "Justice in the soul mirrors justice in the state for Plato."
                ],
                "answer": "Plato defines justice as a state where each part performs its proper function without interfering with others.",
                "ground_truth": "Justice is each part doing its own work according to Plato."
            },
            {
                "question": "What is the Good according to Augustine?",
                "contexts": [
                    "Augustine sees the Good as God, the source of all being and truth.",
                    "In Augustine's view, the Good is what all things desire and seek."
                ],
                "answer": "For Augustine, the Good is God himself, the ultimate source of all being, truth, and goodness.",
                "ground_truth": "The Good is God according to Augustine."
            }
        ]
    
    async def _check_quality_alerts(self, results: List[EvaluationResult]) -> None:
        """Check for quality alerts based on evaluation results."""
        if not results:
            return
        
        # Calculate current metrics
        current_metrics = {
            'faithfulness': statistics.mean([r.faithfulness_score for r in results]),
            'answer_relevancy': statistics.mean([r.answer_relevancy_score for r in results]),
            'context_precision': statistics.mean([r.context_precision_score for r in results]),
            'context_recall': statistics.mean([r.context_recall_score for r in results]),
            'overall_quality': statistics.mean([r.overall_quality_score for r in results])
        }
        
        # Check against thresholds
        thresholds = self.quality_service.get_quality_thresholds()
        
        alert_checks = [
            ('faithfulness', current_metrics['faithfulness'], thresholds.faithfulness_min, AlertSeverity.CRITICAL),
            ('answer_relevancy', current_metrics['answer_relevancy'], thresholds.answer_relevancy_min, AlertSeverity.WARNING),
            ('context_precision', current_metrics['context_precision'], thresholds.context_precision_min, AlertSeverity.WARNING),
            ('context_recall', current_metrics['context_recall'], thresholds.context_recall_min, AlertSeverity.WARNING),
            ('overall_quality', current_metrics['overall_quality'], thresholds.overall_quality_min, AlertSeverity.CRITICAL)
        ]
        
        # Check for threshold violations
        for metric_name, current_value, threshold, severity in alert_checks:
            if current_value < threshold:
                alert = QualityAlert(
                    alert_id=f"quality_{metric_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    severity=severity,
                    metric_name=metric_name,
                    current_value=current_value,
                    threshold_value=threshold,
                    message=f"{metric_name} quality below threshold: {current_value:.3f} < {threshold:.3f}",
                    timestamp=datetime.now(timezone.utc),
                    query_samples=[r.question for r in results[:3]]  # Include sample queries
                )
                
                await self._trigger_alert(alert)
        
        # Check for quality drops (compared to recent history)
        if len(self.evaluation_history) > 20:  # Need sufficient history
            await self._check_quality_drops(current_metrics)
    
    async def _check_quality_drops(self, current_metrics: Dict[str, float]) -> None:
        """Check for significant quality drops compared to historical performance."""
        # Get recent historical average (last 20 evaluations before current)
        recent_history = self.evaluation_history[:-len(current_metrics)][-20:]
        
        if len(recent_history) < 10:  # Need sufficient history
            return
        
        historical_metrics = {
            'faithfulness': statistics.mean([r.faithfulness_score for r in recent_history]),
            'answer_relevancy': statistics.mean([r.answer_relevancy_score for r in recent_history]),
            'overall_quality': statistics.mean([r.overall_quality_score for r in recent_history])
        }
        
        # Check for significant drops
        drop_thresholds = self.alert_thresholds
        
        for metric_name in ['faithfulness', 'answer_relevancy', 'overall_quality']:
            drop_threshold = drop_thresholds.get(f'{metric_name}_drop', 0.1)
            
            historical_value = historical_metrics[metric_name]
            current_value = current_metrics[metric_name]
            drop = historical_value - current_value
            
            if drop > drop_threshold:
                alert = QualityAlert(
                    alert_id=f"drop_{metric_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    severity=AlertSeverity.WARNING,
                    metric_name=f"{metric_name}_drop",
                    current_value=current_value,
                    threshold_value=historical_value - drop_threshold,
                    message=f"Significant {metric_name} quality drop detected: {drop:.3f} decrease from recent average",
                    timestamp=datetime.now(timezone.utc)
                )
                
                await self._trigger_alert(alert)
    
    async def _trigger_alert(self, alert: QualityAlert) -> None:
        """Trigger a quality alert."""
        self.recent_alerts.append(alert)
        
        # Trim recent alerts list
        if len(self.recent_alerts) > 100:
            self.recent_alerts = self.recent_alerts[-100:]
        
        self.logger.warning(f"Quality alert triggered: {alert.message}")
        
        # Call alert callbacks
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                self.logger.error(f"Error in alert callback: {str(e)}")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status and statistics."""
        stats = self.get_monitoring_stats()
        
        return {
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime_hours": stats.monitoring_uptime_hours,
            "statistics": {
                "total_evaluations": stats.total_evaluations,
                "average_quality_score": stats.average_quality_score,
                "quality_trend_slope": stats.quality_trend_slope,
                "alerts_triggered": stats.alerts_triggered,
                "last_evaluation_time": stats.last_evaluation_time.isoformat() if stats.last_evaluation_time else None
            },
            "recent_alerts": [
                {
                    "severity": alert.severity.value,
                    "metric_name": alert.metric_name,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat()
                }
                for alert in self.recent_alerts[-5:]  # Last 5 alerts
            ]
        }
    
    def get_monitoring_stats(self) -> MonitoringStats:
        """Get monitoring system statistics."""
        # Calculate uptime
        uptime_hours = 0.0
        if self.start_time:
            uptime_delta = datetime.now(timezone.utc) - self.start_time
            uptime_hours = uptime_delta.total_seconds() / 3600
        
        # Calculate quality statistics
        total_evaluations = len(self.evaluation_history)
        average_quality_score = 0.0
        quality_trend_slope = 0.0
        last_evaluation_time = None
        
        if self.evaluation_history:
            average_quality_score = statistics.mean([
                r.overall_quality_score for r in self.evaluation_history
            ])
            
            # Calculate trend slope (simple linear regression)
            if len(self.evaluation_history) >= 2:
                scores = [r.overall_quality_score for r in self.evaluation_history]
                quality_trend_slope = self._calculate_trend_slope(scores)
            
            last_evaluation_time = max([r.evaluation_timestamp for r in self.evaluation_history])
        
        return MonitoringStats(
            total_evaluations=total_evaluations,
            monitoring_uptime_hours=uptime_hours,
            average_quality_score=average_quality_score,
            quality_trend_slope=quality_trend_slope,
            alerts_triggered=len(self.recent_alerts),
            last_evaluation_time=last_evaluation_time
        )
    
    def _calculate_trend_slope(self, scores: List[float]) -> float:
        """Calculate trend slope using simple linear regression."""
        n = len(scores)
        if n < 2:
            return 0.0
        
        x = list(range(n))
        y = scores
        
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
            
        return numerator / denominator
    
    def get_quality_history(self, hours: int = 24) -> List[EvaluationResult]:
        """Get quality evaluation history for specified time period."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        return [
            result for result in self.evaluation_history 
            if result.evaluation_timestamp >= cutoff_time
        ]
    
    def get_recent_alerts(self, hours: int = 24) -> List[QualityAlert]:
        """Get recent alerts for specified time period."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        return [
            alert for alert in self.recent_alerts 
            if alert.timestamp >= cutoff_time
        ]
    
    async def run_manual_evaluation(self, sample_size: Optional[int] = None) -> List[EvaluationResult]:
        """Run manual quality evaluation."""
        self.logger.info("Running manual quality evaluation")
        
        # Use provided sample size or default
        original_sample_size = self.sample_size
        if sample_size:
            self.sample_size = sample_size
        
        try:
            # Generate and evaluate queries
            sample_queries = await self._generate_sample_queries()
            evaluation_results = []
            
            for query_data in sample_queries:
                result = await self.quality_service.evaluate_single_query(
                    question=query_data["question"],
                    contexts=query_data["contexts"],
                    answer=query_data["answer"],
                    ground_truth=query_data.get("ground_truth")
                )
                evaluation_results.append(result)
            
            # Store results in history
            self.evaluation_history.extend(evaluation_results)
            
            self.logger.info(f"Manual evaluation completed with {len(evaluation_results)} results")
            return evaluation_results
            
        finally:
            # Restore original sample size
            self.sample_size = original_sample_size