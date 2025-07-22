#!/usr/bin/env python3
"""
Accurate Health Calculation for Iteration 37
Focuses on realistic metrics and handles issues gracefully
"""

import os
import json
import time
from datetime import datetime

def calculate_health_scores():
    """Calculate accurate health scores for iteration 37"""
    
    print("=== ACCURATE HEALTH CALCULATION - ITERATION 37 ===")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # === TEST HEALTH ===
    print("TEST HEALTH ANALYSIS")
    
    # Based on actual test runs:
    # test_app_config.py: 11/11 passed (100%)
    # test_models.py: 10/10 passed (100%)  
    # test_payments.py: 3/8 passed, 4 errors, 1 failed (37.5%)
    # test_auth.py: 12/28 passed, 16 failed (42.9%)
    
    backend_tests_run = 57  # Total tests attempted across key modules
    backend_tests_passed = 36  # Actual passes from working modules
    backend_pass_rate = (backend_tests_passed / backend_tests_run) * 100
    
    # No frontend tests currently working
    frontend_tests_run = 0
    frontend_tests_passed = 0
    frontend_pass_rate = 0 if frontend_tests_run == 0 else (frontend_tests_passed / frontend_tests_run) * 100
    
    # Test Health = (Backend_Pass_Rate × 0.6) + (Frontend_Pass_Rate × 0.4)
    test_health = (backend_pass_rate * 0.6) + (frontend_pass_rate * 0.4)
    
    print(f"  Backend Tests:              {backend_tests_passed}/{backend_tests_run} ({backend_pass_rate:.1f}%)")
    print(f"  Frontend Tests:             {frontend_tests_passed}/{frontend_tests_run} ({frontend_pass_rate:.1f}%)")
    print(f"  Test Health Score:          {test_health:.1f}%")
    print()
    
    # === COVERAGE ANALYSIS ===
    print("COVERAGE ANALYSIS")
    
    # Based on actual coverage report for working tests only
    total_statements = 7727
    missed_statements = 7341
    covered_statements = total_statements - missed_statements
    actual_coverage = (covered_statements / total_statements) * 100
    
    # Weighted coverage (same as actual since no frontend)
    weighted_coverage = actual_coverage
    
    print(f"  Total Statements:           {total_statements}")
    print(f"  Covered Statements:         {covered_statements}")
    print(f"  Actual Coverage:            {actual_coverage:.1f}%")
    print(f"  Weighted Coverage:          {weighted_coverage:.1f}%")
    print()
    
    # === SECURITY HEALTH ===
    print("SECURITY ANALYSIS")
    
    # Based on actual pip-audit results:
    # 5 known vulnerabilities in 4 packages
    # requests: 1 vulnerability (medium)
    # setuptools: 1 vulnerability (high - RCE potential)  
    # torch: 1 vulnerability (medium - DoS)
    # tornado: 2 vulnerabilities (medium - DoS)
    
    critical_vulnerabilities = 0  # None marked as critical
    high_vulnerabilities = 1      # setuptools RCE
    medium_vulnerabilities = 4    # requests, torch, tornado(2)
    
    # Security Health = 100 - (Critical × 20) - (High × 10) - (Medium × 2)
    security_health = 100 - (critical_vulnerabilities * 20) - (high_vulnerabilities * 10) - (medium_vulnerabilities * 2)
    security_health = max(0, security_health)  # Floor at 0
    
    print(f"  Critical Vulnerabilities:   {critical_vulnerabilities}")
    print(f"  High Vulnerabilities:       {high_vulnerabilities}")
    print(f"  Medium Vulnerabilities:     {medium_vulnerabilities}")
    print(f"  Security Health Score:      {security_health:.1f}%")
    print()
    
    # === PERFORMANCE HEALTH ===
    print("PERFORMANCE ANALYSIS")
    
    # Load baseline from file
    baseline_time = 0.032509  # From performance_baseline.json
    
    # Current performance from app import test
    current_time = 3.445  # Measured app import time
    
    # Performance Health = 100 × (Baseline_Time / Current_Time)
    performance_health = min(100, 100 * (baseline_time / current_time))
    
    print(f"  Baseline Time:              {baseline_time:.3f}s")
    print(f"  Current Time:               {current_time:.3f}s")
    print(f"  Performance Health Score:   {performance_health:.1f}%")
    print()
    
    # === TECHNICAL DEBT ===
    print("TECHNICAL DEBT ANALYSIS")
    
    # Based on actual TODO/FIXME grep
    total_todos = 32  # From grep results across all files
    code_todos = 2    # Only in .py files (health_calculation_iteration36.py, setup_notifications.py)
    
    # Estimate tech debt score (higher TODO count = higher debt)
    tech_debt = min(100, (total_todos / 50) * 100)  # Scale: 50 TODOs = 100% debt
    
    print(f"  Total TODOs/FIXMEs:         {total_todos}")
    print(f"  Code TODOs:                 {code_todos}")
    print(f"  Tech Debt Score:            {tech_debt:.1f}%")
    print()
    
    # === OVERALL HEALTH ===
    print("OVERALL HEALTH CALCULATION")
    
    # Overall Health = (Test × 0.5) + (Security × 0.3) + (Performance × 0.2)
    overall_health = (test_health * 0.5) + (security_health * 0.3) + (performance_health * 0.2)
    
    print(f"  Test Health (50%):          {test_health:.1f}% -> {test_health * 0.5:.1f}")
    print(f"  Security Health (30%):      {security_health:.1f}% -> {security_health * 0.3:.1f}")
    print(f"  Performance Health (20%):   {performance_health:.1f}% -> {performance_health * 0.2:.1f}")
    print(f"  OVERALL HEALTH SCORE:       {overall_health:.1f}%")
    print()
    
    # === MODE DETERMINATION ===
    print("ITERATION MODE ANALYSIS")
    
    # Based on APEX_CONFIG.md rules for iteration 37:
    iteration = 37
    
    mode_reasons = []
    
    if critical_vulnerabilities > 0:
        recommended_mode = "SECURITY"
        mode_reasons.append(f"Critical vulnerabilities detected: {critical_vulnerabilities}")
    elif overall_health < 40 or len([t for t in ['auth', 'payments'] if 'failed' in str(t)]) > 3:
        recommended_mode = "EMERGENCY"
        mode_reasons.append(f"Health below 40% ({overall_health:.1f}%) or critical failures")
    elif iteration % 30 == 0:
        recommended_mode = "SECURITY"
        mode_reasons.append(f"Iteration {iteration} is divisible by 30")
    elif iteration % 20 == 0:
        recommended_mode = "DOCUMENTATION"
        mode_reasons.append(f"Iteration {iteration} is divisible by 20")
    elif iteration % 15 == 0 and performance_health < 70:
        recommended_mode = "PERFORMANCE"
        mode_reasons.append(f"Iteration {iteration} divisible by 15 and performance degraded ({performance_health:.1f}%)")
    elif iteration % 10 == 0:
        recommended_mode = "ARCHITECTURE"
        mode_reasons.append(f"Iteration {iteration} is divisible by 10")
    elif overall_health < 70:
        recommended_mode = "RECOVERY"
        mode_reasons.append(f"Health below 70% ({overall_health:.1f}%)")
    elif tech_debt > 80:
        recommended_mode = "DEBT_PAYMENT"
        mode_reasons.append(f"Tech debt above 80% ({tech_debt:.1f}%)")
    elif overall_health > 85 and iteration % 5 == 0:
        recommended_mode = "FEATURE"
        mode_reasons.append(f"Health above 85% and iteration divisible by 5")
    else:
        recommended_mode = "STANDARD"
        mode_reasons.append("Default mode - no special triggers")
    
    print(f"  Current Iteration:          {iteration}")
    print(f"  Recommended Mode:           {recommended_mode}")
    print(f"  Reasoning:                  {'; '.join(mode_reasons)}")
    print()
    
    # === SUMMARY ===
    print("EXECUTIVE SUMMARY")
    print(f"  Overall Health:             {overall_health:.1f}% ({'CRITICAL' if overall_health < 40 else 'POOR' if overall_health < 60 else 'FAIR' if overall_health < 80 else 'GOOD'})")
    print(f"  Key Issues:")
    print(f"    - Test failures in auth/payments modules ({100-backend_pass_rate:.1f}% failure rate)")
    print(f"    - Very low code coverage ({actual_coverage:.1f}%)")
    print(f"    - {high_vulnerabilities} high + {medium_vulnerabilities} medium security vulnerabilities")
    print(f"    - Significant performance degradation (106x slower than baseline)")
    print(f"  Recommended Action:         {recommended_mode} mode")
    print()
    
    # === METRICS EXPORT ===
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "iteration": iteration,
        "overall_health": round(overall_health, 1),
        "test_health": round(test_health, 1),
        "security_health": round(security_health, 1), 
        "performance_health": round(performance_health, 1),
        "coverage": round(actual_coverage, 1),
        "weighted_coverage": round(weighted_coverage, 1),
        "backend_tests_passed": backend_tests_passed,
        "backend_tests_total": backend_tests_run,
        "frontend_tests_passed": frontend_tests_passed,
        "frontend_tests_total": frontend_tests_run,
        "critical_vulnerabilities": critical_vulnerabilities,
        "high_vulnerabilities": high_vulnerabilities,
        "medium_vulnerabilities": medium_vulnerabilities,
        "total_todos": total_todos,
        "tech_debt": round(tech_debt, 1),
        "baseline_time": baseline_time,
        "current_time": current_time,
        "recommended_mode": recommended_mode,
        "mode_reasons": mode_reasons
    }
    
    # Save metrics
    with open("health_metrics_iteration37.json", "w") as f:
        json.dump(metrics, f, indent=2)
    
    print("Metrics saved to health_metrics_iteration37.json")
    
    return metrics

if __name__ == "__main__":
    calculate_health_scores()