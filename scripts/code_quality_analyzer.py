#!/usr/bin/env python3
"""
Comprehensive Code Quality Analysis System
Advanced code quality assessment and improvement recommendations for Cibozer
"""

import os
import sys
import ast
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import argparse


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


@dataclass 
class CodeQualityMetrics:
    """Code quality metrics data"""
    lines_of_code: int
    cyclomatic_complexity: float
    maintainability_index: float
    code_coverage: float
    test_coverage: float
    technical_debt_hours: float
    duplication_percentage: float
    security_hotspots: int
    code_smells: int
    bugs: int
    vulnerabilities: int
    quality_gate_status: str


@dataclass
class CodeIssue:
    """Code quality issue"""
    file_path: str
    line_number: int
    issue_type: str
    severity: str
    message: str
    rule: str
    suggestion: str = ""


class CodeQualityAnalyzer:
    """Comprehensive code quality analysis system"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.reports_dir = self.root_dir / "quality_reports"
        self.ensure_directories()
        
        # Analysis results
        self.issues: List[CodeIssue] = []
        self.metrics = CodeQualityMetrics(
            lines_of_code=0,
            cyclomatic_complexity=0.0,
            maintainability_index=0.0,
            code_coverage=0.0,
            test_coverage=0.0,
            technical_debt_hours=0.0,
            duplication_percentage=0.0,
            security_hotspots=0,
            code_smells=0,
            bugs=0,
            vulnerabilities=0,
            quality_gate_status="UNKNOWN"
        )
    
    def ensure_directories(self):
        """Ensure required directories exist"""
        self.reports_dir.mkdir(exist_ok=True, parents=True)
    
    def analyze_python_code_structure(self) -> Dict[str, Any]:
        """Analyze Python code structure and complexity"""
        print(f"{Colors.BLUE}🐍 Analyzing Python code structure...{Colors.END}")
        
        analysis = {
            'files_analyzed': 0,
            'total_lines': 0,
            'functions': 0,
            'classes': 0,
            'complexity_by_file': {},
            'large_functions': [],
            'complex_functions': [],
            'missing_docstrings': [],
            'long_parameter_lists': [],
            'deep_nesting': []
        }
        
        python_files = list(self.root_dir.glob('**/*.py'))
        python_files = [f for f in python_files if not any(part.startswith('.') for part in f.parts)]
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    analysis['total_lines'] += len(lines)
                
                # Parse AST
                tree = ast.parse(content)
                file_analysis = self._analyze_ast(tree, py_file)
                
                analysis['files_analyzed'] += 1
                analysis['functions'] += file_analysis['functions']
                analysis['classes'] += file_analysis['classes']
                analysis['complexity_by_file'][str(py_file.relative_to(self.root_dir))] = file_analysis['complexity']
                
                # Collect issues
                analysis['large_functions'].extend(file_analysis['large_functions'])
                analysis['complex_functions'].extend(file_analysis['complex_functions'])
                analysis['missing_docstrings'].extend(file_analysis['missing_docstrings'])
                analysis['long_parameter_lists'].extend(file_analysis['long_parameter_lists'])
                analysis['deep_nesting'].extend(file_analysis['deep_nesting'])
                
            except Exception as e:
                print(f"   ⚠️  Error analyzing {py_file}: {e}")
        
        # Calculate metrics
        self.metrics.lines_of_code = analysis['total_lines']
        if analysis['functions'] > 0:
            avg_complexity = sum(analysis['complexity_by_file'].values()) / len(analysis['complexity_by_file'])
            self.metrics.cyclomatic_complexity = avg_complexity
        
        print(f"   ✅ Analyzed {analysis['files_analyzed']} Python files")
        print(f"   📊 Total lines: {analysis['total_lines']:,}")
        print(f"   🔧 Functions: {analysis['functions']}")
        print(f"   🏗️  Classes: {analysis['classes']}")
        print(f"   🔄 Average complexity: {self.metrics.cyclomatic_complexity:.2f}")
        
        return analysis
    
    def _analyze_ast(self, tree: ast.AST, file_path: Path) -> Dict[str, Any]:
        """Analyze AST for code metrics"""
        analysis = {
            'functions': 0,
            'classes': 0,
            'complexity': 0,
            'large_functions': [],
            'complex_functions': [],
            'missing_docstrings': [],
            'long_parameter_lists': [],
            'deep_nesting': []
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                analysis['functions'] += 1
                func_analysis = self._analyze_function(node, file_path)
                analysis['complexity'] += func_analysis['complexity']
                
                # Check for issues
                if func_analysis['lines'] > 50:
                    analysis['large_functions'].append({
                        'file': str(file_path.relative_to(self.root_dir)),
                        'function': node.name,
                        'line': node.lineno,
                        'lines': func_analysis['lines']
                    })
                
                if func_analysis['complexity'] > 10:
                    analysis['complex_functions'].append({
                        'file': str(file_path.relative_to(self.root_dir)),
                        'function': node.name,
                        'line': node.lineno,
                        'complexity': func_analysis['complexity']
                    })
                
                if not ast.get_docstring(node):
                    analysis['missing_docstrings'].append({
                        'file': str(file_path.relative_to(self.root_dir)),
                        'function': node.name,
                        'line': node.lineno,
                        'type': 'function'
                    })
                
                if len(node.args.args) > 5:
                    analysis['long_parameter_lists'].append({
                        'file': str(file_path.relative_to(self.root_dir)),
                        'function': node.name,
                        'line': node.lineno,
                        'parameters': len(node.args.args)
                    })
                
                # Check nesting depth
                max_depth = self._calculate_max_nesting_depth(node)
                if max_depth > 4:
                    analysis['deep_nesting'].append({
                        'file': str(file_path.relative_to(self.root_dir)),
                        'function': node.name,
                        'line': node.lineno,
                        'depth': max_depth
                    })
            
            elif isinstance(node, ast.ClassDef):
                analysis['classes'] += 1
                
                if not ast.get_docstring(node):
                    analysis['missing_docstrings'].append({
                        'file': str(file_path.relative_to(self.root_dir)),
                        'class': node.name,
                        'line': node.lineno,
                        'type': 'class'
                    })
        
        return analysis
    
    def _analyze_function(self, func_node: ast.FunctionDef, file_path: Path) -> Dict[str, Any]:
        """Analyze individual function"""
        # Calculate lines of code
        if hasattr(func_node, 'end_lineno'):
            lines = func_node.end_lineno - func_node.lineno + 1
        else:
            lines = 1  # Fallback
        
        # Calculate cyclomatic complexity
        complexity = self._calculate_cyclomatic_complexity(func_node)
        
        return {
            'lines': lines,
            'complexity': complexity
        }
    
    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.With, ast.AsyncWith):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _calculate_max_nesting_depth(self, node: ast.AST) -> int:
        """Calculate maximum nesting depth in a function"""
        
        def get_depth(node, current_depth=0):
            max_depth = current_depth
            
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, 
                                    ast.With, ast.AsyncWith, ast.Try)):
                    child_depth = get_depth(child, current_depth + 1)
                    max_depth = max(max_depth, child_depth)
                else:
                    child_depth = get_depth(child, current_depth)
                    max_depth = max(max_depth, child_depth)
            
            return max_depth
        
        return get_depth(node)
    
    def run_static_analysis_tools(self) -> Dict[str, Any]:
        """Run static analysis tools"""
        print(f"{Colors.BLUE}🔍 Running static analysis tools...{Colors.END}")
        
        analysis_results = {
            'flake8': self._run_flake8(),
            'pylint': self._run_pylint(),
            'mypy': self._run_mypy(),
            'bandit': self._run_bandit(),
            'safety': self._run_safety()
        }
        
        # Aggregate results
        total_issues = sum(len(results.get('issues', [])) for results in analysis_results.values())
        print(f"   📊 Total issues found: {total_issues}")
        
        return analysis_results
    
    def _run_flake8(self) -> Dict[str, Any]:
        """Run Flake8 linting"""
        print(f"   🎯 Running Flake8...")
        
        try:
            result = subprocess.run([
                'flake8', '.', 
                '--max-line-length=120',
                '--extend-ignore=E203,W503',
                '--exclude=.git,__pycache__,venv,env,.venv,.env',
                '--format=json'
            ], capture_output=True, text=True, cwd=self.root_dir)
            
            if result.stdout:
                # Parse flake8 output (not actually JSON by default)
                issues = []
                for line in result.stdout.strip().split('\n'):
                    if ':' in line:
                        parts = line.split(':', 3)
                        if len(parts) >= 4:
                            file_path, line_no, col, message = parts
                            issues.append(CodeIssue(
                                file_path=file_path,
                                line_number=int(line_no),
                                issue_type='style',
                                severity='minor',
                                message=message.strip(),
                                rule='flake8'
                            ))
                
                print(f"     ✅ Flake8: {len(issues)} issues found")
                return {'status': 'completed', 'issues': issues}
            else:
                print(f"     ✅ Flake8: No issues found")
                return {'status': 'completed', 'issues': []}
                
        except FileNotFoundError:
            print(f"     ⚠️  Flake8 not installed")
            return {'status': 'skipped', 'reason': 'flake8 not found'}
        except Exception as e:
            print(f"     ❌ Flake8 failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def _run_pylint(self) -> Dict[str, Any]:
        """Run Pylint analysis"""
        print(f"   🔍 Running Pylint...")
        
        try:
            result = subprocess.run([
                'pylint', 'app/', 
                '--output-format=json',
                '--disable=C0103,R0903,W0613'  # Disable some common false positives
            ], capture_output=True, text=True, cwd=self.root_dir)
            
            if result.stdout:
                try:
                    pylint_output = json.loads(result.stdout)
                    issues = []
                    
                    for item in pylint_output:
                        severity_map = {
                            'error': 'major',
                            'warning': 'minor',
                            'info': 'info',
                            'convention': 'info',
                            'refactor': 'minor'
                        }
                        
                        issues.append(CodeIssue(
                            file_path=item['path'],
                            line_number=item['line'],
                            issue_type=item['type'],
                            severity=severity_map.get(item['type'], 'minor'),
                            message=item['message'],
                            rule=item['message-id']
                        ))
                    
                    print(f"     ✅ Pylint: {len(issues)} issues found")
                    return {'status': 'completed', 'issues': issues}
                    
                except json.JSONDecodeError:
                    print(f"     ⚠️  Pylint output parsing failed")
                    return {'status': 'failed', 'error': 'JSON parsing failed'}
            else:
                print(f"     ✅ Pylint: No issues found")
                return {'status': 'completed', 'issues': []}
                
        except FileNotFoundError:
            print(f"     ⚠️  Pylint not installed")
            return {'status': 'skipped', 'reason': 'pylint not found'}
        except Exception as e:
            print(f"     ❌ Pylint failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def _run_mypy(self) -> Dict[str, Any]:
        """Run MyPy type checking"""
        print(f"   🔍 Running MyPy...")
        
        try:
            result = subprocess.run([
                'mypy', 'app/', 
                '--ignore-missing-imports',
                '--json-report', str(self.reports_dir / 'mypy-report')
            ], capture_output=True, text=True, cwd=self.root_dir)
            
            issues = []
            
            # Parse MyPy output
            for line in result.stdout.strip().split('\n'):
                if ':' in line and 'error:' in line:
                    parts = line.split(':', 2)
                    if len(parts) >= 3:
                        file_line, error_type, message = parts
                        file_path, line_no = file_line.rsplit(':', 1)
                        
                        issues.append(CodeIssue(
                            file_path=file_path,
                            line_number=int(line_no) if line_no.isdigit() else 0,
                            issue_type='type',
                            severity='minor',
                            message=message.strip(),
                            rule='mypy'
                        ))
            
            print(f"     ✅ MyPy: {len(issues)} issues found")
            return {'status': 'completed', 'issues': issues}
                
        except FileNotFoundError:
            print(f"     ⚠️  MyPy not installed")
            return {'status': 'skipped', 'reason': 'mypy not found'}
        except Exception as e:
            print(f"     ❌ MyPy failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def _run_bandit(self) -> Dict[str, Any]:
        """Run Bandit security analysis"""
        print(f"   🔒 Running Bandit security analysis...")
        
        try:
            result = subprocess.run([
                'bandit', '-r', '.', 
                '-f', 'json',
                '-x', '.git,__pycache__,venv,env,.venv,.env'
            ], capture_output=True, text=True, cwd=self.root_dir)
            
            if result.stdout:
                try:
                    bandit_output = json.loads(result.stdout)
                    issues = []
                    
                    for item in bandit_output.get('results', []):
                        severity_map = {
                            'LOW': 'info',
                            'MEDIUM': 'minor',
                            'HIGH': 'major'
                        }
                        
                        issues.append(CodeIssue(
                            file_path=item['filename'],
                            line_number=item['line_number'],
                            issue_type='security',
                            severity=severity_map.get(item['issue_severity'], 'minor'),
                            message=item['issue_text'],
                            rule=item['test_id']
                        ))
                    
                    # Update security metrics
                    self.metrics.security_hotspots = len([i for i in issues if i.severity == 'major'])
                    self.metrics.vulnerabilities = len([i for i in issues if i.issue_type == 'security'])
                    
                    print(f"     ✅ Bandit: {len(issues)} security issues found")
                    return {'status': 'completed', 'issues': issues}
                    
                except json.JSONDecodeError:
                    print(f"     ⚠️  Bandit output parsing failed")
                    return {'status': 'failed', 'error': 'JSON parsing failed'}
            else:
                print(f"     ✅ Bandit: No security issues found")
                return {'status': 'completed', 'issues': []}
                
        except FileNotFoundError:
            print(f"     ⚠️  Bandit not installed")
            return {'status': 'skipped', 'reason': 'bandit not found'}
        except Exception as e:
            print(f"     ❌ Bandit failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def _run_safety(self) -> Dict[str, Any]:
        """Run Safety dependency vulnerability check"""
        print(f"   🛡️  Running Safety dependency check...")
        
        try:
            result = subprocess.run([
                'safety', 'check', '--json'
            ], capture_output=True, text=True, cwd=self.root_dir)
            
            if result.stdout:
                try:
                    safety_output = json.loads(result.stdout)
                    issues = []
                    
                    for item in safety_output:
                        issues.append(CodeIssue(
                            file_path='requirements.txt',
                            line_number=0,
                            issue_type='dependency_vulnerability',
                            severity='major',
                            message=f"Vulnerable dependency: {item['package']} {item['installed_version']}",
                            rule='safety',
                            suggestion=f"Update to version {item['vulnerable_versions']}"
                        ))
                    
                    print(f"     ✅ Safety: {len(issues)} vulnerable dependencies found")
                    return {'status': 'completed', 'issues': issues}
                    
                except json.JSONDecodeError:
                    print(f"     ⚠️  Safety output parsing failed")
                    return {'status': 'failed', 'error': 'JSON parsing failed'}
            else:
                print(f"     ✅ Safety: No vulnerable dependencies found")
                return {'status': 'completed', 'issues': []}
                
        except FileNotFoundError:
            print(f"     ⚠️  Safety not installed")
            return {'status': 'skipped', 'reason': 'safety not found'}
        except Exception as e:
            print(f"     ❌ Safety failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def analyze_test_coverage(self) -> Dict[str, Any]:
        """Analyze test coverage"""
        print(f"{Colors.BLUE}🧪 Analyzing test coverage...{Colors.END}")
        
        try:
            # Run coverage
            subprocess.run(['coverage', 'run', '-m', 'pytest'], 
                         capture_output=True, cwd=self.root_dir)
            
            # Get coverage report
            result = subprocess.run(['coverage', 'json'], 
                                  capture_output=True, text=True, cwd=self.root_dir)
            
            if result.returncode == 0:
                coverage_file = self.root_dir / 'coverage.json'
                if coverage_file.exists():
                    with open(coverage_file, 'r') as f:
                        coverage_data = json.load(f)
                    
                    total_coverage = coverage_data['totals']['percent_covered']
                    self.metrics.test_coverage = total_coverage
                    
                    print(f"   ✅ Test coverage: {total_coverage:.1f}%")
                    
                    return {
                        'total_coverage': total_coverage,
                        'files': coverage_data['files'],
                        'totals': coverage_data['totals']
                    }
            
            print(f"   ⚠️  Coverage analysis failed")
            return {'status': 'failed'}
            
        except FileNotFoundError:
            print(f"   ⚠️  Coverage tool not installed")
            return {'status': 'skipped', 'reason': 'coverage not found'}
        except Exception as e:
            print(f"   ❌ Coverage analysis failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def detect_code_duplication(self) -> Dict[str, Any]:
        """Detect code duplication"""
        print(f"{Colors.BLUE}👥 Detecting code duplication...{Colors.END}")
        
        # Simple duplication detection based on similar lines
        duplicates = []
        file_contents = {}
        
        python_files = list(self.root_dir.glob('**/*.py'))
        python_files = [f for f in python_files if not any(part.startswith('.') for part in f.parts)]
        
        # Read all files
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = [line.strip() for line in f.readlines() if line.strip()]
                    file_contents[py_file] = lines
            except Exception:
                continue
        
        # Simple duplicate detection
        min_lines = 5  # Minimum lines to consider as duplication
        
        for file1, lines1 in file_contents.items():
            for file2, lines2 in file_contents.items():
                if file1 >= file2:  # Avoid checking same pair twice
                    continue
                
                # Find common sequences
                common_sequences = self._find_common_sequences(lines1, lines2, min_lines)
                
                for seq in common_sequences:
                    duplicates.append({
                        'file1': str(file1.relative_to(self.root_dir)),
                        'file2': str(file2.relative_to(self.root_dir)),
                        'lines': seq['length'],
                        'similarity': seq['similarity']
                    })
        
        # Calculate duplication percentage (simplified)
        total_lines = sum(len(lines) for lines in file_contents.values())
        duplicate_lines = sum(dup['lines'] for dup in duplicates)
        duplication_percentage = (duplicate_lines / total_lines * 100) if total_lines > 0 else 0
        
        self.metrics.duplication_percentage = duplication_percentage
        
        print(f"   ✅ Code duplication: {duplication_percentage:.1f}%")
        print(f"   📊 Duplicate blocks found: {len(duplicates)}")
        
        return {
            'duplication_percentage': duplication_percentage,
            'duplicate_blocks': duplicates,
            'total_lines': total_lines,
            'duplicate_lines': duplicate_lines
        }
    
    def _find_common_sequences(self, lines1: List[str], lines2: List[str], 
                              min_length: int) -> List[Dict[str, Any]]:
        """Find common sequences between two files"""
        sequences = []
        
        for i in range(len(lines1) - min_length + 1):
            for j in range(len(lines2) - min_length + 1):
                length = 0
                while (i + length < len(lines1) and 
                       j + length < len(lines2) and 
                       lines1[i + length] == lines2[j + length]):
                    length += 1
                
                if length >= min_length:
                    sequences.append({
                        'start1': i,
                        'start2': j,
                        'length': length,
                        'similarity': 1.0  # Exact match
                    })
        
        return sequences
    
    def calculate_technical_debt(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate technical debt estimation"""
        print(f"{Colors.BLUE}💳 Calculating technical debt...{Colors.END}")
        
        # Technical debt calculation based on various factors
        debt_factors = {
            'code_smells': 0,
            'complex_functions': 0,
            'large_functions': 0,
            'missing_tests': 0,
            'security_issues': 0,
            'duplicated_code': 0
        }
        
        # Count code smells from static analysis
        for tool_results in analysis_results.get('static_analysis', {}).values():
            if isinstance(tool_results, dict) and 'issues' in tool_results:
                debt_factors['code_smells'] += len(tool_results['issues'])
        
        # Add complexity issues
        structure_analysis = analysis_results.get('structure', {})
        debt_factors['complex_functions'] = len(structure_analysis.get('complex_functions', []))
        debt_factors['large_functions'] = len(structure_analysis.get('large_functions', []))
        
        # Add security issues
        debt_factors['security_issues'] = self.metrics.security_hotspots
        
        # Add duplication
        debt_factors['duplicated_code'] = int(self.metrics.duplication_percentage)
        
        # Calculate debt hours (rough estimation)
        debt_hours = (
            debt_factors['code_smells'] * 0.5 +
            debt_factors['complex_functions'] * 2.0 +
            debt_factors['large_functions'] * 1.0 +
            debt_factors['security_issues'] * 4.0 +
            debt_factors['duplicated_code'] * 0.1
        )
        
        self.metrics.technical_debt_hours = debt_hours
        self.metrics.code_smells = debt_factors['code_smells']
        
        print(f"   ✅ Technical debt: {debt_hours:.1f} hours")
        print(f"   📊 Code smells: {debt_factors['code_smells']}")
        
        return {
            'total_debt_hours': debt_hours,
            'debt_factors': debt_factors,
            'debt_breakdown': {
                'code_smells': debt_factors['code_smells'] * 0.5,
                'complexity': debt_factors['complex_functions'] * 2.0,
                'size': debt_factors['large_functions'] * 1.0,
                'security': debt_factors['security_issues'] * 4.0,
                'duplication': debt_factors['duplicated_code'] * 0.1
            }
        }
    
    def calculate_maintainability_index(self, analysis_results: Dict[str, Any]) -> float:
        """Calculate maintainability index"""
        # Simplified maintainability index calculation
        # Real calculation would use Halstead metrics and other factors
        
        base_score = 100
        
        # Deduct points for complexity
        complexity_penalty = min(self.metrics.cyclomatic_complexity * 2, 20)
        
        # Deduct points for low test coverage
        coverage_penalty = max(0, (80 - self.metrics.test_coverage) * 0.3)
        
        # Deduct points for code smells
        smells_penalty = min(self.metrics.code_smells * 0.1, 15)
        
        # Deduct points for duplication
        duplication_penalty = self.metrics.duplication_percentage * 0.5
        
        maintainability = base_score - complexity_penalty - coverage_penalty - smells_penalty - duplication_penalty
        maintainability = max(0, maintainability)  # Ensure non-negative
        
        self.metrics.maintainability_index = maintainability
        
        return maintainability
    
    def generate_quality_report(self, analysis_results: Dict[str, Any]) -> str:
        """Generate comprehensive quality report"""
        timestamp = datetime.now().isoformat()
        report_file = self.reports_dir / f"code_quality_report_{timestamp.replace(':', '-')}.json"
        
        # Determine quality gate status
        quality_gate_status = self._determine_quality_gate_status()
        self.metrics.quality_gate_status = quality_gate_status
        
        report = {
            'timestamp': timestamp,
            'metrics': asdict(self.metrics),
            'analysis_results': analysis_results,
            'quality_gate_status': quality_gate_status,
            'recommendations': self._generate_recommendations(analysis_results),
            'summary': {
                'total_issues': len(self.issues),
                'critical_issues': len([i for i in self.issues if i.severity == 'major']),
                'files_analyzed': analysis_results.get('structure', {}).get('files_analyzed', 0),
                'maintainability_rating': self._get_maintainability_rating(self.metrics.maintainability_index)
            }
        }
        
        # Save report
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"{Colors.GREEN}✅ Quality report generated: {report_file}{Colors.END}")
        
        return str(report_file)
    
    def _determine_quality_gate_status(self) -> str:
        """Determine overall quality gate status"""
        if (self.metrics.test_coverage >= 80 and 
            self.metrics.maintainability_index >= 70 and 
            self.metrics.security_hotspots == 0 and
            self.metrics.duplication_percentage < 5):
            return "PASSED"
        elif (self.metrics.test_coverage >= 60 and 
              self.metrics.maintainability_index >= 50 and 
              self.metrics.security_hotspots <= 2):
            return "WARNING"
        else:
            return "FAILED"
    
    def _get_maintainability_rating(self, index: float) -> str:
        """Get maintainability rating from index"""
        if index >= 85:
            return "A"
        elif index >= 70:
            return "B"
        elif index >= 50:
            return "C"
        elif index >= 25:
            return "D"
        else:
            return "F"
    
    def _generate_recommendations(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        # Coverage recommendations
        if self.metrics.test_coverage < 80:
            recommendations.append(f"Increase test coverage from {self.metrics.test_coverage:.1f}% to at least 80%")
        
        # Complexity recommendations
        if self.metrics.cyclomatic_complexity > 5:
            recommendations.append("Reduce cyclomatic complexity by refactoring complex functions")
        
        # Security recommendations
        if self.metrics.security_hotspots > 0:
            recommendations.append(f"Address {self.metrics.security_hotspots} security hotspots")
        
        # Duplication recommendations
        if self.metrics.duplication_percentage > 5:
            recommendations.append(f"Reduce code duplication from {self.metrics.duplication_percentage:.1f}%")
        
        # Technical debt recommendations
        if self.metrics.technical_debt_hours > 40:
            recommendations.append(f"Address technical debt (estimated {self.metrics.technical_debt_hours:.1f} hours)")
        
        # Structure recommendations
        structure = analysis_results.get('structure', {})
        if structure.get('large_functions'):
            recommendations.append(f"Refactor {len(structure['large_functions'])} large functions")
        
        if structure.get('missing_docstrings'):
            recommendations.append(f"Add docstrings to {len(structure['missing_docstrings'])} functions/classes")
        
        return recommendations
    
    def run_comprehensive_analysis(self) -> str:
        """Run complete code quality analysis"""
        print(f"{Colors.BOLD}🔍 Starting Comprehensive Code Quality Analysis{Colors.END}")
        print("=" * 80)
        
        analysis_results = {}
        
        try:
            # 1. Code structure analysis
            print(f"\n{Colors.BOLD}📊 Code Structure Analysis{Colors.END}")
            analysis_results['structure'] = self.analyze_python_code_structure()
            
            # 2. Static analysis
            print(f"\n{Colors.BOLD}🔍 Static Analysis{Colors.END}")
            analysis_results['static_analysis'] = self.run_static_analysis_tools()
            
            # 3. Test coverage
            print(f"\n{Colors.BOLD}🧪 Test Coverage Analysis{Colors.END}")
            analysis_results['coverage'] = self.analyze_test_coverage()
            
            # 4. Code duplication
            print(f"\n{Colors.BOLD}👥 Code Duplication Analysis{Colors.END}")
            analysis_results['duplication'] = self.detect_code_duplication()
            
            # 5. Technical debt calculation
            print(f"\n{Colors.BOLD}💳 Technical Debt Calculation{Colors.END}")
            analysis_results['technical_debt'] = self.calculate_technical_debt(analysis_results)
            
            # 6. Calculate maintainability index
            maintainability = self.calculate_maintainability_index(analysis_results)
            
            # 7. Generate comprehensive report
            print(f"\n{Colors.BOLD}📄 Generating Quality Report{Colors.END}")
            report_file = self.generate_quality_report(analysis_results)
            
            # Print summary
            self._print_analysis_summary()
            
            return report_file
            
        except Exception as e:
            print(f"{Colors.RED}❌ Analysis failed: {e}{Colors.END}")
            raise
    
    def _print_analysis_summary(self):
        """Print analysis summary"""
        print(f"\n{Colors.BOLD}📊 Code Quality Summary{Colors.END}")
        print("=" * 50)
        print(f"📈 Maintainability Index: {self.metrics.maintainability_index:.1f} ({self._get_maintainability_rating(self.metrics.maintainability_index)})")
        print(f"🧪 Test Coverage: {self.metrics.test_coverage:.1f}%")
        print(f"🔄 Cyclomatic Complexity: {self.metrics.cyclomatic_complexity:.2f}")
        print(f"👥 Code Duplication: {self.metrics.duplication_percentage:.1f}%")
        print(f"💳 Technical Debt: {self.metrics.technical_debt_hours:.1f} hours")
        print(f"🔒 Security Hotspots: {self.metrics.security_hotspots}")
        print(f"🎯 Quality Gate: {self.metrics.quality_gate_status}")
        
        if self.metrics.quality_gate_status == "PASSED":
            print(f"\n{Colors.GREEN}🎉 Quality gate PASSED! Code meets quality standards.{Colors.END}")
        elif self.metrics.quality_gate_status == "WARNING":
            print(f"\n{Colors.YELLOW}⚠️  Quality gate WARNING. Consider improvements.{Colors.END}")
        else:
            print(f"\n{Colors.RED}❌ Quality gate FAILED. Code quality improvements required.{Colors.END}")


def main():
    """CLI interface for code quality analysis"""
    parser = argparse.ArgumentParser(description='Cibozer Code Quality Analysis')
    parser.add_argument('command', choices=[
        'analyze', 'structure', 'lint', 'coverage', 'duplication', 'debt'
    ], default='analyze', nargs='?')
    parser.add_argument('--output', help='Output file for reports')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    analyzer = CodeQualityAnalyzer()
    
    try:
        if args.command == 'analyze':
            report_file = analyzer.run_comprehensive_analysis()
            print(f"\n📄 Full report: {report_file}")
        
        elif args.command == 'structure':
            results = analyzer.analyze_python_code_structure()
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(results, f, indent=2)
        
        elif args.command == 'lint':
            results = analyzer.run_static_analysis_tools()
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(results, f, indent=2)
        
        elif args.command == 'coverage':
            results = analyzer.analyze_test_coverage()
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(results, f, indent=2)
        
        elif args.command == 'duplication':
            results = analyzer.detect_code_duplication()
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(results, f, indent=2)
        
        elif args.command == 'debt':
            # Need to run analysis first to calculate debt
            structure = analyzer.analyze_python_code_structure()
            static_analysis = analyzer.run_static_analysis_tools()
            analysis_results = {'structure': structure, 'static_analysis': static_analysis}
            results = analyzer.calculate_technical_debt(analysis_results)
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(results, f, indent=2)
    
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Analysis cancelled{Colors.END}")
        return 1
    except Exception as e:
        print(f"{Colors.RED}❌ Error: {e}{Colors.END}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())