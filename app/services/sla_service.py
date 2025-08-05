"""
SLA (Service Level Agreement) Monitoring Service for Cibozer
Tracks and monitors service level objectives and agreements
"""

import time
import threading
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import json


class SLAStatus(Enum):
    """SLA status enumeration"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical" 
    BREACHED = "breached"


class MetricType(Enum):
    """SLA metric types"""
    AVAILABILITY = "availability"
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    CUSTOM = "custom"


@dataclass
class SLATarget:
    """Defines an SLA target/objective"""
    name: str
    description: str
    metric_type: MetricType
    target_value: float
    comparison: str  # ">=", "<=", "==", ">", "<"
    time_window_minutes: int
    alert_threshold: float  # Percentage threshold for alerts (0-100)
    critical_threshold: float  # Percentage threshold for critical alerts (0-100)
    tags: Dict[str, str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}


@dataclass 
class SLAMeasurement:
    """A single SLA measurement"""
    timestamp: float
    target_name: str
    value: float
    status: SLAStatus
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SLAReport:
    """SLA compliance report"""
    target_name: str
    time_period: str
    total_measurements: int
    compliant_measurements: int
    compliance_percentage: float
    status: SLAStatus
    average_value: float
    min_value: float
    max_value: float
    breaches: List[Dict[str, Any]]
    uptime_percentage: Optional[float] = None
    downtime_minutes: Optional[float] = None


class SLAService:
    """Main SLA monitoring service"""
    
    def __init__(self):
        self.targets = {}  # target_name -> SLATarget
        self.measurements = defaultdict(lambda: deque(maxlen=10000))  # target_name -> deque of measurements
        self.breaches = defaultdict(lambda: deque(maxlen=1000))  # target_name -> deque of breaches
        self.alerts = deque(maxlen=5000)  # Recent SLA alerts
        self.compliance_cache = {}  # Cached compliance calculations
        self._lock = threading.RLock()
        
        # Pre-defined SLA targets for common web application metrics
        self.setup_default_targets()
    
    def setup_default_targets(self):
        """Setup default SLA targets for web applications"""
        default_targets = [
            SLATarget(
                name="system_availability",
                description="System uptime and availability",
                metric_type=MetricType.AVAILABILITY,
                target_value=99.9,  # 99.9% uptime
                comparison=">=",
                time_window_minutes=60,
                alert_threshold=99.5,
                critical_threshold=99.0,
                tags={"category": "availability", "priority": "critical"}
            ),
            SLATarget(
                name="api_response_time",
                description="API endpoint response time",
                metric_type=MetricType.RESPONSE_TIME,
                target_value=500.0,  # 500ms or less
                comparison="<=",
                time_window_minutes=15,
                alert_threshold=750.0,
                critical_threshold=1000.0,
                tags={"category": "performance", "priority": "high"}
            ),
            SLATarget(
                name="error_rate",
                description="Application error rate",
                metric_type=MetricType.ERROR_RATE,
                target_value=1.0,  # 1% or less errors
                comparison="<=",
                time_window_minutes=30,
                alert_threshold=2.0,
                critical_threshold=5.0,
                tags={"category": "reliability", "priority": "high"}
            ),
            SLATarget(
                name="meal_generation_success",
                description="Meal plan generation success rate",
                metric_type=MetricType.CUSTOM,
                target_value=95.0,  # 95% success rate
                comparison=">=",
                time_window_minutes=60,
                alert_threshold=90.0,
                critical_threshold=85.0,
                tags={"category": "business", "priority": "critical", "feature": "meal_generation"}
            ),
            SLATarget(
                name="user_registration_time",
                description="User registration process completion time",
                metric_type=MetricType.RESPONSE_TIME,
                target_value=3000.0,  # 3 seconds or less
                comparison="<=",
                time_window_minutes=30,
                alert_threshold=5000.0,
                critical_threshold=10000.0,
                tags={"category": "user_experience", "priority": "medium"}
            ),
            SLATarget(
                name="payment_processing_success",
                description="Payment processing success rate",
                metric_type=MetricType.CUSTOM,
                target_value=99.5,  # 99.5% success rate
                comparison=">=",
                time_window_minutes=60,
                alert_threshold=98.0,
                critical_threshold=95.0,
                tags={"category": "business", "priority": "critical", "feature": "payments"}
            )
        ]
        
        for target in default_targets:
            self.add_target(target)
    
    def add_target(self, target: SLATarget):
        """Add a new SLA target"""
        with self._lock:
            self.targets[target.name] = target
    
    def remove_target(self, target_name: str):
        """Remove an SLA target"""
        with self._lock:
            if target_name in self.targets:
                del self.targets[target_name]
                if target_name in self.measurements:
                    del self.measurements[target_name]
                if target_name in self.breaches:
                    del self.breaches[target_name]
    
    def record_measurement(self, target_name: str, value: float, 
                          metadata: Dict[str, Any] = None) -> bool:
        """Record a measurement for an SLA target"""
        if target_name not in self.targets:
            return False
        
        target = self.targets[target_name]
        timestamp = time.time()
        
        # Determine status based on target
        status = self._evaluate_measurement(target, value)
        
        measurement = SLAMeasurement(
            timestamp=timestamp,
            target_name=target_name,
            value=value,
            status=status,
            metadata=metadata or {}
        )
        
        with self._lock:
            self.measurements[target_name].append(measurement)
            
            # Check for breach
            if status in [SLAStatus.CRITICAL, SLAStatus.BREACHED]:
                self._record_breach(target, measurement)
            
            # Clear compliance cache for this target
            self._clear_compliance_cache(target_name)
        
        return True
    
    def _evaluate_measurement(self, target: SLATarget, value: float) -> SLAStatus:
        """Evaluate a measurement against SLA target"""
        comparison = target.comparison
        target_value = target.target_value
        alert_threshold = target.alert_threshold
        critical_threshold = target.critical_threshold
        
        # Determine if measurement meets target
        meets_target = False
        if comparison == ">=":
            meets_target = value >= target_value
            in_warning = value < alert_threshold
            in_critical = value < critical_threshold
        elif comparison == "<=":
            meets_target = value <= target_value
            in_warning = value > alert_threshold
            in_critical = value > critical_threshold
        elif comparison == "==":
            meets_target = abs(value - target_value) < 0.01
            in_warning = abs(value - target_value) > (alert_threshold * 0.01)
            in_critical = abs(value - target_value) > (critical_threshold * 0.01)
        elif comparison == ">":
            meets_target = value > target_value
            in_warning = value <= alert_threshold
            in_critical = value <= critical_threshold
        elif comparison == "<":
            meets_target = value < target_value
            in_warning = value >= alert_threshold
            in_critical = value >= critical_threshold
        
        if not meets_target:
            if in_critical:
                return SLAStatus.CRITICAL
            elif in_warning:
                return SLAStatus.WARNING
            else:
                return SLAStatus.BREACHED
        
        return SLAStatus.HEALTHY
    
    def _record_breach(self, target: SLATarget, measurement: SLAMeasurement):
        """Record an SLA breach"""
        breach = {
            'timestamp': measurement.timestamp,
            'target_name': target.name,
            'value': measurement.value,
            'target_value': target.target_value,
            'status': measurement.status.value,
            'description': target.description,
            'metadata': measurement.metadata
        }
        
        self.breaches[target.name].append(breach)
        
        # Create alert
        self._create_alert(target, measurement, breach)
    
    def _create_alert(self, target: SLATarget, measurement: SLAMeasurement, breach: Dict[str, Any]):
        """Create an SLA alert"""
        alert = {
            'timestamp': measurement.timestamp,
            'alert_id': f"sla_{target.name}_{int(measurement.timestamp)}",
            'type': 'sla_breach',
            'severity': measurement.status.value,
            'target_name': target.name,
            'description': f"SLA breach: {target.description}",
            'value': measurement.value,
            'target_value': target.target_value,
            'comparison': target.comparison,
            'breach_percentage': self._calculate_breach_percentage(target, measurement.value),
            'tags': target.tags,
            'metadata': measurement.metadata
        }
        
        self.alerts.append(alert)
    
    def _calculate_breach_percentage(self, target: SLATarget, value: float) -> float:
        """Calculate how much a value breaches the target (as percentage)"""
        if target.comparison in [">=", ">"]:
            if target.target_value == 0:
                return 0
            return max(0, (target.target_value - value) / target.target_value * 100)
        elif target.comparison in ["<=", "<"]:
            if target.target_value == 0:
                return 0 if value == 0 else 100
            return max(0, (value - target.target_value) / target.target_value * 100)
        else:  # ==
            if target.target_value == 0:
                return 0 if value == 0 else 100
            return abs(value - target.target_value) / target.target_value * 100
    
    def get_compliance_report(self, target_name: str, hours: int = 24) -> Optional[SLAReport]:
        """Get compliance report for a target"""
        if target_name not in self.targets:
            return None
        
        cache_key = f"{target_name}_{hours}"
        if cache_key in self.compliance_cache:
            cached_report, cached_time = self.compliance_cache[cache_key]
            # Use cache if less than 5 minutes old
            if time.time() - cached_time < 300:
                return cached_report
        
        target = self.targets[target_name]
        since_timestamp = time.time() - (hours * 3600)
        
        # Get measurements within time window
        measurements = [
            m for m in self.measurements[target_name]
            if m.timestamp >= since_timestamp
        ]
        
        if not measurements:
            return None
        
        # Calculate compliance
        compliant_measurements = [
            m for m in measurements 
            if m.status == SLAStatus.HEALTHY
        ]
        
        compliance_percentage = (len(compliant_measurements) / len(measurements)) * 100
        
        # Calculate statistics
        values = [m.value for m in measurements]
        average_value = sum(values) / len(values)
        min_value = min(values)
        max_value = max(values)
        
        # Get breaches in time window
        breach_list = [
            b for b in self.breaches[target_name]
            if b['timestamp'] >= since_timestamp
        ]
        
        # Determine overall status
        if compliance_percentage >= target.target_value:
            status = SLAStatus.HEALTHY
        elif compliance_percentage >= target.alert_threshold:
            status = SLAStatus.WARNING
        elif compliance_percentage >= target.critical_threshold:
            status = SLAStatus.CRITICAL
        else:
            status = SLAStatus.BREACHED
        
        # Calculate uptime if availability metric
        uptime_percentage = None
        downtime_minutes = None
        if target.metric_type == MetricType.AVAILABILITY:
            uptime_percentage = compliance_percentage
            downtime_minutes = (100 - compliance_percentage) / 100 * (hours * 60)
        
        report = SLAReport(
            target_name=target_name,
            time_period=f"{hours} hours",
            total_measurements=len(measurements),
            compliant_measurements=len(compliant_measurements),
            compliance_percentage=compliance_percentage,
            status=status,
            average_value=average_value,
            min_value=min_value,
            max_value=max_value,
            breaches=breach_list,
            uptime_percentage=uptime_percentage,
            downtime_minutes=downtime_minutes
        )
        
        # Cache the report
        self.compliance_cache[cache_key] = (report, time.time())
        
        return report
    
    def get_all_compliance_reports(self, hours: int = 24) -> Dict[str, SLAReport]:
        """Get compliance reports for all targets"""
        reports = {}
        for target_name in self.targets:
            report = self.get_compliance_report(target_name, hours)
            if report:
                reports[target_name] = report
        return reports
    
    def get_sla_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive SLA dashboard data"""
        reports = self.get_all_compliance_reports(24)
        
        # Overall SLA health
        all_healthy = all(r.status == SLAStatus.HEALTHY for r in reports.values())
        has_critical = any(r.status == SLAStatus.CRITICAL for r in reports.values())
        has_breached = any(r.status == SLAStatus.BREACHED for r in reports.values())
        
        if has_breached:
            overall_status = SLAStatus.BREACHED
        elif has_critical:
            overall_status = SLAStatus.CRITICAL
        elif not all_healthy:
            overall_status = SLAStatus.WARNING
        else:
            overall_status = SLAStatus.HEALTHY
        
        # Calculate overall compliance
        if reports:
            overall_compliance = sum(r.compliance_percentage for r in reports.values()) / len(reports)
        else:
            overall_compliance = 100.0
        
        # Get recent alerts
        recent_alerts = list(self.alerts)[-50:]  # Last 50 alerts
        
        # Category breakdown
        categories = defaultdict(lambda: {'targets': 0, 'compliant': 0, 'total_compliance': 0})
        for target_name, report in reports.items():
            target = self.targets[target_name]
            category = target.tags.get('category', 'other')
            categories[category]['targets'] += 1
            categories[category]['total_compliance'] += report.compliance_percentage
            if report.status == SLAStatus.HEALTHY:
                categories[category]['compliant'] += 1
        
        # Calculate average compliance per category
        for category_data in categories.values():
            if category_data['targets'] > 0:
                category_data['avg_compliance'] = category_data['total_compliance'] / category_data['targets']
                category_data['compliance_rate'] = (category_data['compliant'] / category_data['targets']) * 100
        
        return {
            'overall_status': overall_status.value,
            'overall_compliance': overall_compliance,
            'total_targets': len(self.targets),
            'healthy_targets': len([r for r in reports.values() if r.status == SLAStatus.HEALTHY]),
            'warning_targets': len([r for r in reports.values() if r.status == SLAStatus.WARNING]),
            'critical_targets': len([r for r in reports.values() if r.status == SLAStatus.CRITICAL]),
            'breached_targets': len([r for r in reports.values() if r.status == SLAStatus.BREACHED]),
            'reports': {name: asdict(report) for name, report in reports.items()},
            'recent_alerts': recent_alerts,
            'categories': dict(categories),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _clear_compliance_cache(self, target_name: str = None):
        """Clear compliance cache"""
        if target_name:
            # Clear cache for specific target
            keys_to_remove = [k for k in self.compliance_cache.keys() if k.startswith(f"{target_name}_")]
            for key in keys_to_remove:
                del self.compliance_cache[key]
        else:
            # Clear all cache
            self.compliance_cache.clear()
    
    def cleanup_old_data(self, days: int = 7):
        """Clean up old measurements and breaches"""
        cutoff_time = time.time() - (days * 24 * 3600)
        
        with self._lock:
            # Clean measurements
            for target_name in self.measurements:
                measurements = self.measurements[target_name]
                # Keep only recent measurements
                while measurements and measurements[0].timestamp < cutoff_time:
                    measurements.popleft()
            
            # Clean breaches
            for target_name in self.breaches:
                breaches = self.breaches[target_name]
                # Keep only recent breaches
                while breaches and breaches[0]['timestamp'] < cutoff_time:
                    breaches.popleft()
            
            # Clean alerts
            while self.alerts and self.alerts[0]['timestamp'] < cutoff_time:
                self.alerts.popleft()
            
            # Clear cache
            self._clear_compliance_cache()
    
    def export_sla_data(self, target_name: str = None, hours: int = 24) -> Dict[str, Any]:
        """Export SLA data for analysis"""
        if target_name:
            targets_to_export = [target_name] if target_name in self.targets else []
        else:
            targets_to_export = list(self.targets.keys())
        
        export_data = {
            'export_timestamp': datetime.utcnow().isoformat(),
            'time_period_hours': hours,
            'targets': {},
            'measurements': {},
            'breaches': {},
            'compliance_reports': {}
        }
        
        since_timestamp = time.time() - (hours * 3600)
        
        for target_name in targets_to_export:
            target = self.targets[target_name]
            export_data['targets'][target_name] = asdict(target)
            
            # Get measurements
            measurements = [
                asdict(m) for m in self.measurements[target_name]
                if m.timestamp >= since_timestamp
            ]
            export_data['measurements'][target_name] = measurements
            
            # Get breaches
            breaches = [
                b for b in self.breaches[target_name]
                if b['timestamp'] >= since_timestamp
            ]
            export_data['breaches'][target_name] = breaches
            
            # Get compliance report
            report = self.get_compliance_report(target_name, hours)
            if report:
                export_data['compliance_reports'][target_name] = asdict(report)
        
        return export_data


# Global SLA service instance
_sla_service = None
_sla_lock = threading.Lock()


def get_sla_service() -> SLAService:
    """Get the global SLA service instance"""
    global _sla_service
    if _sla_service is None:
        with _sla_lock:
            if _sla_service is None:
                _sla_service = SLAService()
    return _sla_service


# Convenience functions for common SLA measurements
def record_availability(available: bool, metadata: Dict[str, Any] = None):
    """Record system availability measurement"""
    sla_service = get_sla_service()
    value = 100.0 if available else 0.0
    sla_service.record_measurement('system_availability', value, metadata)


def record_response_time(endpoint: str, duration_ms: float, metadata: Dict[str, Any] = None):
    """Record API response time measurement"""
    sla_service = get_sla_service()
    combined_metadata = {'endpoint': endpoint}
    if metadata:
        combined_metadata.update(metadata)
    sla_service.record_measurement('api_response_time', duration_ms, combined_metadata)


def record_error_rate(total_requests: int, errors: int, metadata: Dict[str, Any] = None):
    """Record error rate measurement"""
    if total_requests > 0:
        error_rate = (errors / total_requests) * 100
        sla_service = get_sla_service()
        combined_metadata = {'total_requests': total_requests, 'errors': errors}
        if metadata:
            combined_metadata.update(metadata)
        sla_service.record_measurement('error_rate', error_rate, combined_metadata)


def record_meal_generation_success(successful: bool, metadata: Dict[str, Any] = None):
    """Record meal generation success"""
    sla_service = get_sla_service()
    value = 100.0 if successful else 0.0
    sla_service.record_measurement('meal_generation_success', value, metadata)


def record_payment_success(successful: bool, metadata: Dict[str, Any] = None):
    """Record payment processing success"""
    sla_service = get_sla_service()
    value = 100.0 if successful else 0.0
    sla_service.record_measurement('payment_processing_success', value, metadata)