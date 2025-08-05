"""Performance monitoring and optimization routes."""
from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required
from datetime import datetime, timezone
import psutil
import time

from app.utils.decorators import admin_required
from app.utils.caching import get_cache_stats
from app.utils.database_performance import get_database_stats

performance_bp = Blueprint('performance', __name__)


@performance_bp.route('/api/performance/metrics', methods=['POST'])
def collect_performance_metrics():
    """Collect client-side performance metrics."""
    try:
        metrics = request.get_json()
        
        if not metrics:
            return jsonify({'error': 'No metrics provided'}), 400
        
        # Store metrics (in production, send to monitoring service)
        current_app.logger.info(f"Performance metrics: {metrics}")
        
        # You could store these in a time-series database like InfluxDB
        # or send to a service like DataDog, New Relic, etc.
        
        return jsonify({'success': True, 'message': 'Metrics recorded'})
        
    except Exception as e:
        current_app.logger.error(f"Performance metrics collection failed: {e}")
        return jsonify({'error': 'Failed to collect metrics'}), 500


@performance_bp.route('/api/performance/server-metrics')
@login_required
@admin_required
def get_server_metrics():
    """Get server-side performance metrics."""
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Network I/O
        network = psutil.net_io_counters()
        
        # Process-specific metrics
        process = psutil.Process()
        process_memory = process.memory_info()
        
        # Database metrics
        db_stats = get_database_stats()
        
        # Cache metrics
        cache_stats = get_cache_stats()
        
        metrics = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'system': {
                'cpu_percent': cpu_percent,
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                }
            },
            'process': {
                'memory_rss': process_memory.rss,
                'memory_vms': process_memory.vms,
                'cpu_percent': process.cpu_percent(),
                'num_threads': process.num_threads(),
                'create_time': process.create_time()
            },
            'database': db_stats,
            'cache': cache_stats
        }
        
        return jsonify(metrics)
        
    except Exception as e:
        current_app.logger.error(f"Server metrics collection failed: {e}")
        return jsonify({'error': 'Failed to collect server metrics'}), 500


@performance_bp.route('/api/performance/lighthouse')
@login_required
@admin_required  
def run_lighthouse_audit():
    """Run Lighthouse performance audit."""
    try:
        import subprocess
        import json
        import tempfile
        
        # This requires lighthouse CLI to be installed
        # npm install -g lighthouse
        
        base_url = request.args.get('url', 'http://localhost:5000')
        
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as f:
            output_file = f.name
        
        try:
            # Run Lighthouse
            cmd = [
                'lighthouse',
                base_url,
                '--output=json',
                f'--output-path={output_file}',
                '--chrome-flags="--headless --no-sandbox"',
                '--quiet'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                with open(output_file, 'r') as f:
                    lighthouse_data = json.load(f)
                
                # Extract key metrics
                metrics = {
                    'performance_score': lighthouse_data['categories']['performance']['score'] * 100,
                    'accessibility_score': lighthouse_data['categories']['accessibility']['score'] * 100,
                    'best_practices_score': lighthouse_data['categories']['best-practices']['score'] * 100,
                    'seo_score': lighthouse_data['categories']['seo']['score'] * 100,
                    'metrics': {
                        'first_contentful_paint': lighthouse_data['audits']['first-contentful-paint']['numericValue'],
                        'largest_contentful_paint': lighthouse_data['audits']['largest-contentful-paint']['numericValue'],
                        'cumulative_layout_shift': lighthouse_data['audits']['cumulative-layout-shift']['numericValue'],
                        'total_blocking_time': lighthouse_data['audits']['total-blocking-time']['numericValue']
                    },
                    'opportunities': [
                        {
                            'title': audit['title'],
                            'description': audit['description'],
                            'score': audit.get('score', 0),
                            'savings': audit.get('details', {}).get('overallSavingsMs', 0)
                        }
                        for audit_id, audit in lighthouse_data['audits'].items()
                        if audit.get('scoreDisplayMode') == 'numeric' and audit.get('score', 1) < 0.9
                    ]
                }
                
                return jsonify({
                    'success': True,
                    'lighthouse_data': metrics,
                    'report_url': f'/api/performance/lighthouse-report?file={output_file}'
                })
            else:
                return jsonify({
                    'error': 'Lighthouse audit failed',
                    'details': result.stderr
                }), 500
                
        except subprocess.TimeoutExpired:
            return jsonify({'error': 'Lighthouse audit timed out'}), 500
        except FileNotFoundError:
            return jsonify({
                'error': 'Lighthouse CLI not found. Install with: npm install -g lighthouse'
            }), 500
        
    except Exception as e:
        current_app.logger.error(f"Lighthouse audit failed: {e}")
        return jsonify({'error': 'Failed to run Lighthouse audit'}), 500


@performance_bp.route('/api/performance/optimize')
@login_required
@admin_required
def run_performance_optimization():
    """Run automatic performance optimizations."""
    try:
        from scripts.performance_optimizer import PerformanceOptimizer
        
        optimizer = PerformanceOptimizer()
        
        # Run specific optimizations based on query parameters
        optimizations = request.args.getlist('optimize')
        
        if not optimizations:
            # Run all optimizations
            report = optimizer.run_all_optimizations()
        else:
            report = {'optimizations': {}, 'total_savings': 0}
            
            # Run specific optimizations
            for opt in optimizations:
                if opt == 'images' and hasattr(optimizer, 'optimize_images'):
                    savings = optimizer.optimize_images()
                    report['optimizations']['images'] = {'total_savings': savings}
                    report['total_savings'] += savings
                    
                elif opt == 'css' and hasattr(optimizer, 'optimize_css_critical_path'):
                    optimizer.optimize_css_critical_path()
                    report['optimizations']['css'] = {'status': 'completed'}
                    
                elif opt == 'js' and hasattr(optimizer, 'optimize_javascript_performance'):
                    savings = optimizer.optimize_javascript_performance()
                    report['optimizations']['javascript'] = {'total_savings': savings}
                    report['total_savings'] += savings
                    
                elif opt == 'compression' and hasattr(optimizer, 'enable_compression'):
                    savings = optimizer.enable_compression()
                    report['optimizations']['compression'] = {'total_savings': savings}
                    report['total_savings'] += savings
        
        return jsonify({
            'success': True,
            'optimization_report': report,
            'message': f'Optimizations complete. Total savings: {report["total_savings"]:,} bytes'
        })
        
    except Exception as e:
        current_app.logger.error(f"Performance optimization failed: {e}")
        return jsonify({'error': 'Performance optimization failed'}), 500


@performance_bp.route('/api/performance/build')
@login_required
@admin_required
def trigger_production_build():
    """Trigger production build process."""
    try:
        import subprocess
        import sys
        
        # Run production build
        result = subprocess.run(
            [sys.executable, 'build_production.py'],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes
        )
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': 'Production build completed successfully',
                'output': result.stdout
            })
        else:
            return jsonify({
                'error': 'Production build failed',
                'details': result.stderr
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Build process timed out'}), 500
    except Exception as e:
        current_app.logger.error(f"Production build failed: {e}")
        return jsonify({'error': 'Failed to trigger production build'}), 500


@performance_bp.route('/api/performance/cache/warm', methods=['POST'])
@login_required
@admin_required
def warm_cache():
    """Warm application cache."""
    try:
        from app.utils.caching import warm_cache
        
        warm_cache()
        
        return jsonify({
            'success': True,
            'message': 'Cache warming completed'
        })
        
    except Exception as e:
        current_app.logger.error(f"Cache warming failed: {e}")
        return jsonify({'error': 'Cache warming failed'}), 500


@performance_bp.route('/api/performance/cache/clear', methods=['POST'])
@login_required
@admin_required
def clear_cache():
    """Clear application cache."""
    try:
        from app.extensions import cache
        
        cache.clear()
        
        return jsonify({
            'success': True,
            'message': 'Cache cleared successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f"Cache clearing failed: {e}")
        return jsonify({'error': 'Cache clearing failed'}), 500


@performance_bp.route('/api/performance/bundle-analysis')
@login_required
@admin_required
def analyze_bundle():
    """Analyze JavaScript and CSS bundle sizes."""
    try:
        import os
        from pathlib import Path
        
        analysis = {
            'javascript': {},
            'css': {},
            'total_size': 0,
            'recommendations': []
        }
        
        # Analyze JavaScript files
        js_dir = Path('static/js')
        if js_dir.exists():
            total_js_size = 0
            for js_file in js_dir.rglob('*.js'):
                if 'node_modules' in str(js_file) or 'dist' in str(js_file):
                    continue
                    
                size = js_file.stat().st_size
                total_js_size += size
                analysis['javascript'][str(js_file)] = {
                    'size': size,
                    'size_kb': round(size / 1024, 2)
                }
            
            analysis['javascript']['total_size'] = total_js_size
            analysis['total_size'] += total_js_size
            
            # Check for minified versions
            for js_file in analysis['javascript']:
                if not js_file.endswith('total_size'):
                    minified_path = Path(js_file.replace('.js', '.min.js'))
                    if not minified_path.exists():
                        analysis['recommendations'].append(f"Create minified version of {js_file}")
        
        # Analyze CSS files
        css_dir = Path('static/css')
        if css_dir.exists():
            total_css_size = 0
            for css_file in css_dir.rglob('*.css'):
                if 'node_modules' in str(css_file) or 'dist' in str(css_file):
                    continue
                    
                size = css_file.stat().st_size
                total_css_size += size
                analysis['css'][str(css_file)] = {
                    'size': size,
                    'size_kb': round(size / 1024, 2)
                }
            
            analysis['css']['total_size'] = total_css_size
            analysis['total_size'] += total_css_size
        
        # Generate recommendations
        if analysis['total_size'] > 500 * 1024:  # 500KB
            analysis['recommendations'].append("Total bundle size is large (>500KB). Consider code splitting.")
        
        if analysis['javascript'].get('total_size', 0) > 300 * 1024:  # 300KB
            analysis['recommendations'].append("JavaScript bundle is large (>300KB). Consider lazy loading.")
        
        return jsonify({
            'success': True,
            'bundle_analysis': analysis
        })
        
    except Exception as e:
        current_app.logger.error(f"Bundle analysis failed: {e}")
        return jsonify({'error': 'Bundle analysis failed'}), 500