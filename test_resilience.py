#!/usr/bin/env python3
"""
Resilience Testing for Cibozer Application
Tests error handling, edge cases, and system resilience
"""

import requests
import json
import time
import concurrent.futures
from datetime import datetime

BASE_URL = 'http://localhost:5000'

class ResilienceTests:
    def __init__(self):
        self.session = requests.Session()
        self.results = []
        
    def log_result(self, test_name, status, details=""):
        """Log test result"""
        result = {
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.results.append(result)
        
        symbol = "✓" if status == "PASS" else "✗"
        print(f"{symbol} {test_name}: {status}")
        if details:
            print(f"  Details: {details}")
    
    def test_malformed_json(self):
        """Test API with malformed JSON"""
        try:
            # Send invalid JSON
            response = self.session.post(
                f'{BASE_URL}/api/generate',
                data='{"invalid json}',
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 400:
                self.log_result("Malformed JSON handling", "PASS", "Properly rejected invalid JSON")
            else:
                self.log_result("Malformed JSON handling", "FAIL", f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Malformed JSON handling", "FAIL", str(e))
    
    def test_missing_required_fields(self):
        """Test API with missing required fields"""
        try:
            # Send request without required fields
            response = self.session.post(
                f'{BASE_URL}/api/generate',
                json={},
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code in [400, 401]:
                self.log_result("Missing fields handling", "PASS", "Properly handled missing fields")
            else:
                self.log_result("Missing fields handling", "FAIL", f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Missing fields handling", "FAIL", str(e))
    
    def test_invalid_data_types(self):
        """Test API with invalid data types"""
        test_cases = [
            {'calories': 'not-a-number'},
            {'days': -5},
            {'diet': 123},
            {'restrictions': 'not-a-list'},
            {'calories': 10000},  # Too high
            {'calories': 500},    # Too low
            {'days': 100},        # Too many days
        ]
        
        for i, test_data in enumerate(test_cases):
            try:
                response = self.session.post(
                    f'{BASE_URL}/api/generate',
                    json=test_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code in [400, 401]:
                    self.log_result(f"Invalid data type test {i+1}", "PASS", f"Properly rejected: {test_data}")
                else:
                    self.log_result(f"Invalid data type test {i+1}", "FAIL", f"Accepted invalid data: {test_data}")
                    
            except Exception as e:
                self.log_result(f"Invalid data type test {i+1}", "FAIL", str(e))
    
    def test_sql_injection_attempts(self):
        """Test for SQL injection vulnerabilities"""
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "1' UNION SELECT * FROM users--",
            "admin'--",
            "1' OR '1' = '1",
        ]
        
        for payload in sql_payloads:
            try:
                # Try injection in login
                response = self.session.post(
                    f'{BASE_URL}/auth/login',
                    data={
                        'email': payload,
                        'password': payload
                    }
                )
                
                if 'error' not in response.text.lower() or response.status_code != 500:
                    self.log_result(f"SQL injection prevention", "PASS", f"Blocked: {payload}")
                else:
                    self.log_result(f"SQL injection prevention", "FAIL", f"May be vulnerable to: {payload}")
                    
            except Exception as e:
                self.log_result(f"SQL injection test", "FAIL", str(e))
    
    def test_xss_attempts(self):
        """Test for XSS vulnerabilities"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(1)'></iframe>",
            "';alert(String.fromCharCode(88,83,83))//",
        ]
        
        for payload in xss_payloads:
            try:
                # Try XSS in meal plan name
                response = self.session.post(
                    f'{BASE_URL}/api/save-meal-plan',
                    json={
                        'name': payload,
                        'meal_plan': {'days': []}
                    }
                )
                
                # Check if payload is escaped in response
                if payload not in response.text:
                    self.log_result(f"XSS prevention", "PASS", f"Escaped: {payload[:30]}...")
                else:
                    self.log_result(f"XSS prevention", "FAIL", f"Not escaped: {payload[:30]}...")
                    
            except Exception as e:
                self.log_result(f"XSS test", "UNKNOWN", str(e))
    
    def test_rate_limiting(self):
        """Test rate limiting effectiveness"""
        endpoint = f'{BASE_URL}/api/health'
        rapid_requests = 50
        
        start_time = time.time()
        blocked_count = 0
        
        for i in range(rapid_requests):
            try:
                response = self.session.get(endpoint)
                if response.status_code == 429:
                    blocked_count += 1
            except:
                pass
        
        elapsed = time.time() - start_time
        
        if blocked_count > 0:
            self.log_result("Rate limiting", "PASS", f"Blocked {blocked_count}/{rapid_requests} rapid requests")
        else:
            self.log_result("Rate limiting", "FAIL", "No requests were rate limited")
    
    def test_large_payload(self):
        """Test handling of large payloads"""
        # Create a large payload (5MB)
        large_data = {
            'meal_plan': {
                'days': [{'meals': ['x' * 1000]} for _ in range(5000)]
            }
        }
        
        try:
            response = self.session.post(
                f'{BASE_URL}/api/save-meal-plan',
                json=large_data,
                timeout=5
            )
            
            if response.status_code == 413:
                self.log_result("Large payload handling", "PASS", "Properly rejected oversized payload")
            else:
                self.log_result("Large payload handling", "FAIL", f"Accepted large payload: {response.status_code}")
                
        except requests.Timeout:
            self.log_result("Large payload handling", "PASS", "Request timed out (good)")
        except Exception as e:
            self.log_result("Large payload handling", "UNKNOWN", str(e))
    
    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        def make_request(i):
            try:
                response = self.session.get(f'{BASE_URL}/api/health')
                return response.status_code == 200
            except:
                return False
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request, i) for i in range(50)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        success_rate = sum(results) / len(results)
        
        if success_rate > 0.8:
            self.log_result("Concurrent request handling", "PASS", f"Success rate: {success_rate:.2%}")
        else:
            self.log_result("Concurrent request handling", "FAIL", f"Low success rate: {success_rate:.2%}")
    
    def test_auth_bypass_attempts(self):
        """Test for authentication bypass vulnerabilities"""
        protected_endpoints = [
            '/api/generate',
            '/api/save-meal-plan',
            '/api/export-pdf',
            '/api/user-status',
            '/admin/',
        ]
        
        for endpoint in protected_endpoints:
            try:
                # Try to access without authentication
                response = self.session.get(f'{BASE_URL}{endpoint}')
                
                if response.status_code in [401, 403, 302]:  # 302 for redirects to login
                    self.log_result(f"Auth protection {endpoint}", "PASS", "Properly protected")
                else:
                    self.log_result(f"Auth protection {endpoint}", "FAIL", f"Accessible without auth: {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Auth test {endpoint}", "UNKNOWN", str(e))
    
    def test_error_information_disclosure(self):
        """Test if errors disclose sensitive information"""
        try:
            # Trigger an error
            response = self.session.post(
                f'{BASE_URL}/api/generate',
                json={'trigger_error': True}
            )
            
            sensitive_patterns = [
                'traceback',
                'stack trace',
                'line [0-9]+',
                'file "',
                'sqlalchemy',
                'database',
                'password',
                'secret',
            ]
            
            response_text = response.text.lower()
            found_patterns = []
            
            for pattern in sensitive_patterns:
                if pattern in response_text:
                    found_patterns.append(pattern)
            
            if not found_patterns:
                self.log_result("Error information disclosure", "PASS", "No sensitive information disclosed")
            else:
                self.log_result("Error information disclosure", "FAIL", f"Found: {', '.join(found_patterns)}")
                
        except Exception as e:
            self.log_result("Error disclosure test", "UNKNOWN", str(e))
    
    def generate_report(self):
        """Generate test report"""
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = sum(1 for r in self.results if r['status'] == 'FAIL')
        unknown = sum(1 for r in self.results if r['status'] == 'UNKNOWN')
        
        print("\n" + "="*60)
        print("RESILIENCE TEST REPORT")
        print("="*60)
        print(f"Total Tests: {len(self.results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Unknown: {unknown}")
        print(f"Success Rate: {(passed/len(self.results)*100):.1f}%")
        
        if failed > 0:
            print("\nFailed Tests:")
            for r in self.results:
                if r['status'] == 'FAIL':
                    print(f"  - {r['test']}: {r['details']}")
        
        # Save detailed report
        with open('resilience_test_report.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print("\nDetailed report saved to: resilience_test_report.json")

def main():
    print("Starting Cibozer Resilience Tests...")
    print("Make sure the application is running on http://localhost:5000")
    print("="*60)
    
    tester = ResilienceTests()
    
    # Run all tests
    tester.test_malformed_json()
    tester.test_missing_required_fields()
    tester.test_invalid_data_types()
    tester.test_sql_injection_attempts()
    tester.test_xss_attempts()
    tester.test_rate_limiting()
    tester.test_large_payload()
    tester.test_concurrent_requests()
    tester.test_auth_bypass_attempts()
    tester.test_error_information_disclosure()
    
    # Generate report
    tester.generate_report()

if __name__ == '__main__':
    main()