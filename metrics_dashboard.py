#!/usr/bin/env python3
"""
Cibozer Metrics Dashboard
Real-time tracking of launch metrics and KPIs
Usage: python metrics_dashboard.py [--live] [--export]
"""

import os
import json
import datetime
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse
from dataclasses import dataclass
from collections import defaultdict

# Try imports for visualization (optional)
try:
    import matplotlib.pyplot as plt
    import pandas as pd
    HAS_VISUALIZATION = True
except ImportError:
    HAS_VISUALIZATION = False

# Configuration
PROJECT_ROOT = Path(__file__).parent
METRICS_DB = PROJECT_ROOT / "metrics.db"
METRICS_FILE = PROJECT_ROOT / "launch_metrics.json"

@dataclass
class MetricSnapshot:
    """Single metric measurement"""
    name: str
    value: float
    timestamp: datetime.datetime
    category: str
    status: str  # "healthy", "warning", "critical"

class MetricsDashboard:
    """Main metrics tracking and reporting system"""
    
    # Metric definitions with thresholds
    METRIC_DEFINITIONS = {
        "technical": {
            "test_coverage": {
                "unit": "%",
                "target": 80,
                "warning": 60,
                "critical": 40,
                "direction": "higher_better"
            },
            "page_load_time": {
                "unit": "seconds",
                "target": 2.0,
                "warning": 3.0,
                "critical": 5.0,
                "direction": "lower_better"
            },
            "error_rate": {
                "unit": "%",
                "target": 0.1,
                "warning": 1.0,
                "critical": 5.0,
                "direction": "lower_better"
            },
            "uptime": {
                "unit": "%",
                "target": 99.9,
                "warning": 99.0,
                "critical": 95.0,
                "direction": "higher_better"
            },
            "security_score": {
                "unit": "score",
                "target": 90,
                "warning": 70,
                "critical": 50,
                "direction": "higher_better"
            }
        },
        "user": {
            "total_users": {
                "unit": "users",
                "target": 1000,
                "warning": 500,
                "critical": 100,
                "direction": "higher_better"
            },
            "day_1_retention": {
                "unit": "%",
                "target": 40,
                "warning": 30,
                "critical": 20,
                "direction": "higher_better"
            },
            "day_7_retention": {
                "unit": "%",
                "target": 25,
                "warning": 20,
                "critical": 15,
                "direction": "higher_better"
            },
            "day_30_retention": {
                "unit": "%",
                "target": 30,
                "warning": 20,
                "critical": 10,
                "direction": "higher_better"
            },
            "conversion_rate": {
                "unit": "%",
                "target": 5,
                "warning": 3,
                "critical": 1,
                "direction": "higher_better"
            },
            "churn_rate": {
                "unit": "%",
                "target": 10,
                "warning": 15,
                "critical": 20,
                "direction": "lower_better"
            },
            "nps_score": {
                "unit": "score",
                "target": 50,
                "warning": 30,
                "critical": 0,
                "direction": "higher_better"
            }
        },
        "business": {
            "mrr": {
                "unit": "$",
                "target": 500,
                "warning": 250,
                "critical": 100,
                "direction": "higher_better"
            },
            "cac": {
                "unit": "$",
                "target": 30,
                "warning": 40,
                "critical": 50,
                "direction": "lower_better"
            },
            "ltv": {
                "unit": "$",
                "target": 120,
                "warning": 100,
                "critical": 90,
                "direction": "higher_better"
            },
            "ltv_cac_ratio": {
                "unit": "ratio",
                "target": 4,
                "warning": 3,
                "critical": 2,
                "direction": "higher_better"
            },
            "paying_users": {
                "unit": "users",
                "target": 50,
                "warning": 25,
                "critical": 10,
                "direction": "higher_better"
            }
        },
        "engagement": {
            "daily_active_users": {
                "unit": "users",
                "target": 300,
                "warning": 150,
                "critical": 50,
                "direction": "higher_better"
            },
            "avg_session_duration": {
                "unit": "minutes",
                "target": 5,
                "warning": 3,
                "critical": 1,
                "direction": "higher_better"
            },
            "meals_generated_daily": {
                "unit": "meals",
                "target": 500,
                "warning": 250,
                "critical": 100,
                "direction": "higher_better"
            },
            "videos_generated_daily": {
                "unit": "videos",
                "target": 50,
                "warning": 25,
                "critical": 10,
                "direction": "higher_better"
            }
        }
    }
    
    def __init__(self):
        self.setup_database()
        self.current_metrics = self.load_current_metrics()
    
    def setup_database(self):
        """Initialize metrics database"""
        conn = sqlite3.connect(METRICS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                value REAL NOT NULL,
                category TEXT NOT NULL,
                status TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                description TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def load_current_metrics(self) -> Dict:
        """Load current metrics from file"""
        if METRICS_FILE.exists():
            with open(METRICS_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    def save_current_metrics(self):
        """Save current metrics to file"""
        with open(METRICS_FILE, 'w') as f:
            json.dump(self.current_metrics, f, indent=2)
    
    def evaluate_metric_status(self, value: float, definition: Dict) -> str:
        """Evaluate if metric is healthy, warning, or critical"""
        if value is None:
            return "unknown"
        
        target = definition["target"]
        warning = definition["warning"]
        critical = definition["critical"]
        direction = definition["direction"]
        
        if direction == "higher_better":
            if value >= target:
                return "healthy"
            elif value >= warning:
                return "warning"
            elif value >= critical:
                return "critical"
            else:
                return "critical"
        else:  # lower_better
            if value <= target:
                return "healthy"
            elif value <= warning:
                return "warning"
            elif value <= critical:
                return "critical"
            else:
                return "critical"
    
    def record_metric(self, category: str, name: str, value: float):
        """Record a metric value"""
        # Update current metrics
        if category not in self.current_metrics:
            self.current_metrics[category] = {}
        self.current_metrics[category][name] = value
        self.save_current_metrics()
        
        # Get definition
        if category in self.METRIC_DEFINITIONS and name in self.METRIC_DEFINITIONS[category]:
            definition = self.METRIC_DEFINITIONS[category][name]
            status = self.evaluate_metric_status(value, definition)
        else:
            status = "unknown"
        
        # Store in database
        conn = sqlite3.connect(METRICS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO metrics (name, value, category, status)
            VALUES (?, ?, ?, ?)
        ''', (name, value, category, status))
        
        conn.commit()
        conn.close()
    
    def record_event(self, event_type: str, description: str):
        """Record a significant event"""
        conn = sqlite3.connect(METRICS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO events (event_type, description)
            VALUES (?, ?)
        ''', (event_type, description))
        
        conn.commit()
        conn.close()
    
    def get_metric_history(self, name: str, days: int = 7) -> List[MetricSnapshot]:
        """Get historical data for a metric"""
        conn = sqlite3.connect(METRICS_DB)
        cursor = conn.cursor()
        
        since = datetime.datetime.now() - datetime.timedelta(days=days)
        
        cursor.execute('''
            SELECT name, value, category, status, timestamp
            FROM metrics
            WHERE name = ? AND timestamp >= ?
            ORDER BY timestamp
        ''', (name, since))
        
        results = []
        for row in cursor.fetchall():
            results.append(MetricSnapshot(
                name=row[0],
                value=row[1],
                category=row[2],
                status=row[3],
                timestamp=datetime.datetime.fromisoformat(row[4])
            ))
        
        conn.close()
        return results
    
    def collect_system_metrics(self):
        """Collect metrics from the running system"""
        # Test coverage
        try:
            import subprocess
            result = subprocess.run(
                "pytest --cov=. --cov-report=term 2>/dev/null | grep TOTAL | awk '{print $4}' | sed 's/%//'",
                shell=True,
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                coverage = float(result.stdout.strip())
                self.record_metric("technical", "test_coverage", coverage)
        except:
            pass
        
        # Simulated metrics for demo (replace with real collection)
        import random
        
        # Simulate some metrics
        if "user" not in self.current_metrics or "total_users" not in self.current_metrics["user"]:
            self.record_metric("user", "total_users", 0)
        else:
            # Simulate user growth
            current_users = self.current_metrics["user"]["total_users"]
            new_users = max(0, current_users + random.randint(-5, 20))
            self.record_metric("user", "total_users", new_users)
        
        # More simulated metrics would go here...
    
    def generate_report(self) -> str:
        """Generate a text report of current metrics"""
        report = []
        report.append("="*60)
        report.append("CIBOZER METRICS DASHBOARD")
        report.append(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("="*60)
        report.append("")
        
        # Overall health score
        total_metrics = 0
        healthy_metrics = 0
        warning_metrics = 0
        critical_metrics = 0
        
        # Process each category
        for category, metrics in self.METRIC_DEFINITIONS.items():
            report.append(f"\n{category.upper()} METRICS")
            report.append("-"*40)
            
            for metric_name, definition in metrics.items():
                # Get current value
                current_value = None
                if category in self.current_metrics and metric_name in self.current_metrics[category]:
                    current_value = self.current_metrics[category][metric_name]
                
                # Evaluate status
                if current_value is not None:
                    status = self.evaluate_metric_status(current_value, definition)
                    total_metrics += 1
                    
                    if status == "healthy":
                        healthy_metrics += 1
                        status_icon = "[OK]"
                    elif status == "warning":
                        warning_metrics += 1
                        status_icon = "[!]"
                    elif status == "critical":
                        critical_metrics += 1
                        status_icon = "[X]"
                    else:
                        status_icon = "[?]"
                    
                    value_str = f"{current_value:.1f}{definition['unit']}"
                else:
                    status_icon = "[?]"
                    value_str = "N/A"
                
                # Format metric line
                target = definition['target']
                target_str = f"{target:.1f}{definition['unit']}"
                
                report.append(
                    f"{status_icon} {metric_name.replace('_', ' ').title()}: "
                    f"{value_str} (Target: {target_str})"
                )
        
        # Summary
        report.append("\n" + "="*60)
        report.append("SUMMARY")
        report.append("="*60)
        
        if total_metrics > 0:
            health_percentage = (healthy_metrics / total_metrics) * 100
            report.append(f"Overall Health: {health_percentage:.1f}%")
            report.append(f"Healthy Metrics: {healthy_metrics}/{total_metrics}")
            report.append(f"Warning Metrics: {warning_metrics}")
            report.append(f"Critical Metrics: {critical_metrics}")
        else:
            report.append("No metrics collected yet")
        
        # Key insights
        report.append("\nKEY INSIGHTS:")
        
        # Check for critical issues
        if critical_metrics > 0:
            report.append("[!] CRITICAL: Address critical metrics immediately!")
        
        # Check user retention
        if "user" in self.current_metrics:
            user_metrics = self.current_metrics["user"]
            if "day_30_retention" in user_metrics and user_metrics["day_30_retention"]:
                if user_metrics["day_30_retention"] < 10:
                    report.append("[!] User retention is below industry average")
                elif user_metrics["day_30_retention"] > 30:
                    report.append("[OK] Excellent user retention!")
        
        # Check business metrics
        if "business" in self.current_metrics:
            biz_metrics = self.current_metrics["business"]
            if "ltv_cac_ratio" in biz_metrics and biz_metrics["ltv_cac_ratio"]:
                if biz_metrics["ltv_cac_ratio"] < 3:
                    report.append("[!] LTV:CAC ratio needs improvement")
                elif biz_metrics["ltv_cac_ratio"] > 4:
                    report.append("[OK] Strong unit economics!")
        
        report.append("\n" + "="*60)
        
        return "\n".join(report)
    
    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in various formats"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "json":
            filename = f"metrics_export_{timestamp}.json"
            data = {
                "timestamp": datetime.datetime.now().isoformat(),
                "current_metrics": self.current_metrics,
                "metric_definitions": self.METRIC_DEFINITIONS
            }
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            return filename
        
        elif format == "csv" and HAS_VISUALIZATION:
            filename = f"metrics_export_{timestamp}.csv"
            
            # Flatten metrics for CSV
            rows = []
            for category, metrics in self.current_metrics.items():
                for name, value in metrics.items():
                    rows.append({
                        "category": category,
                        "metric": name,
                        "value": value,
                        "timestamp": datetime.datetime.now().isoformat()
                    })
            
            df = pd.DataFrame(rows)
            df.to_csv(filename, index=False)
            return filename
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def visualize_metrics(self):
        """Create visualization dashboard (requires matplotlib)"""
        if not HAS_VISUALIZATION:
            print("Visualization requires matplotlib and pandas. Install with: pip install matplotlib pandas")
            return
        
        # This would create charts and graphs
        # Implementation depends on specific visualization needs
        pass


def simulate_metrics():
    """Simulate some metrics for testing"""
    dashboard = MetricsDashboard()
    
    # Technical metrics
    dashboard.record_metric("technical", "test_coverage", 32)
    dashboard.record_metric("technical", "page_load_time", 2.5)
    dashboard.record_metric("technical", "error_rate", 0.5)
    dashboard.record_metric("technical", "uptime", 99.5)
    
    # User metrics
    dashboard.record_metric("user", "total_users", 150)
    dashboard.record_metric("user", "day_1_retention", 35)
    dashboard.record_metric("user", "conversion_rate", 3.5)
    
    # Business metrics
    dashboard.record_metric("business", "mrr", 150)
    dashboard.record_metric("business", "cac", 35)
    dashboard.record_metric("business", "ltv", 105)
    dashboard.record_metric("business", "ltv_cac_ratio", 3.0)
    
    # Events
    dashboard.record_event("launch", "Started beta testing")
    dashboard.record_event("milestone", "Reached 100 users")


def main():
    parser = argparse.ArgumentParser(description='Cibozer Metrics Dashboard')
    parser.add_argument('--live', action='store_true', help='Live monitoring mode')
    parser.add_argument('--export', choices=['json', 'csv'], help='Export metrics')
    parser.add_argument('--simulate', action='store_true', help='Simulate metrics for testing')
    parser.add_argument('--collect', action='store_true', help='Collect system metrics')
    
    args = parser.parse_args()
    
    dashboard = MetricsDashboard()
    
    if args.simulate:
        simulate_metrics()
        print("Simulated metrics added")
    
    if args.collect:
        dashboard.collect_system_metrics()
        print("System metrics collected")
    
    if args.export:
        filename = dashboard.export_metrics(args.export)
        print(f"Metrics exported to: {filename}")
        return
    
    if args.live:
        # Live monitoring mode
        import time
        print("Starting live monitoring mode (Ctrl+C to exit)")
        
        while True:
            try:
                # Clear screen (cross-platform)
                os.system('cls' if os.name == 'nt' else 'clear')
                
                # Collect and display
                dashboard.collect_system_metrics()
                print(dashboard.generate_report())
                
                # Wait before refresh
                time.sleep(30)  # Refresh every 30 seconds
                
            except KeyboardInterrupt:
                print("\nExiting live mode")
                break
    else:
        # Single report
        print(dashboard.generate_report())


if __name__ == "__main__":
    main()