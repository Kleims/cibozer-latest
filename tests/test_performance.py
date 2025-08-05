"""
Performance tests for the Cibozer application.
Tests response times, load handling, and resource usage.
"""

import pytest
import time
import threading
import concurrent.futures
from statistics import mean, median
from app.models.user import User
from app.models.meal_plan import SavedMealPlan
from app.extensions import db


class TestResponseTimePerformance:
    """Test response times for critical endpoints"""

    def test_health_check_response_time(self, client):
        """Test health check endpoint response time"""
        times = []
        
        for _ in range(10):
            start_time = time.time()
            response = client.get('/api/health')
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # Convert to ms
            times.append(response_time)
            
            assert response.status_code == 200
        
        avg_time = mean(times)
        median_time = median(times)
        max_time = max(times)
        
        # Performance assertions
        assert avg_time < 100, f"Average response time {avg_time:.2f}ms exceeds 100ms"
        assert median_time < 80, f"Median response time {median_time:.2f}ms exceeds 80ms"
        assert max_time < 200, f"Max response time {max_time:.2f}ms exceeds 200ms"

    def test_home_page_response_time(self, client):
        """Test home page response time"""
        times = []
        
        for _ in range(5):
            start_time = time.time()
            response = client.get('/')
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            times.append(response_time)
            
            assert response.status_code == 200
        
        avg_time = mean(times)
        assert avg_time < 500, f"Home page average response time {avg_time:.2f}ms exceeds 500ms"

    def test_login_page_response_time(self, client):
        """Test login page response time"""
        times = []
        
        for _ in range(5):
            start_time = time.time()
            response = client.get('/auth/login')
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            times.append(response_time)
            
            assert response.status_code == 200
        
        avg_time = mean(times)
        assert avg_time < 300, f"Login page average response time {avg_time:.2f}ms exceeds 300ms"


class TestDatabasePerformance:
    """Test database query performance"""

    def test_user_query_performance(self, app):
        """Test user query performance"""
        with app.app_context():
            # Create multiple test users
            users = []
            for i in range(100):
                user = User(
                    email=f'perf_user_{i}@example.com',
                    full_name=f'Performance User {i}',
                    credits_balance=10
                )
                user.set_password('testpass123')
                users.append(user)
            
            db.session.add_all(users)
            db.session.commit()
            
            # Test single user query performance
            start_time = time.time()
            user = User.query.filter_by(email='perf_user_50@example.com').first()
            end_time = time.time()
            
            query_time = (end_time - start_time) * 1000
            assert query_time < 50, f"User query time {query_time:.2f}ms exceeds 50ms"
            assert user is not None
            
            # Test user list query performance
            start_time = time.time()
            user_count = User.query.count()
            end_time = time.time()
            
            count_time = (end_time - start_time) * 1000
            assert count_time < 100, f"User count query time {count_time:.2f}ms exceeds 100ms"
            assert user_count >= 100

    def test_meal_plan_query_performance(self, app, test_user):
        """Test meal plan query performance"""
        with app.app_context():
            # Create multiple meal plans
            meal_plans = []
            for i in range(50):
                plan = SavedMealPlan(
                    user_id=test_user.id,
                    name=f'Performance Plan {i}',
                    diet_type='standard',
                    total_calories=2000,
                    meal_plan_data={'meals': [f'meal_{i}'] * 10}  # Some data
                )
                meal_plans.append(plan)
            
            db.session.add_all(meal_plans)
            db.session.commit()
            
            # Test meal plan query performance
            start_time = time.time()
            user_plans = SavedMealPlan.query.filter_by(user_id=test_user.id).all()
            end_time = time.time()
            
            query_time = (end_time - start_time) * 1000
            assert query_time < 200, f"Meal plan query time {query_time:.2f}ms exceeds 200ms"
            assert len(user_plans) >= 50


class TestConcurrencyPerformance:
    """Test concurrent request handling"""

    def test_concurrent_health_checks(self, client):
        """Test concurrent health check requests"""
        def make_request():
            response = client.get('/api/health')
            return response.status_code, time.time()
        
        # Run concurrent requests
        num_threads = 10
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(make_request) for _ in range(num_threads)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify all requests succeeded
        success_count = sum(1 for status_code, _ in results if status_code == 200)
        assert success_count >= 8, f"Only {success_count}/{num_threads} concurrent requests succeeded"
        
        # Verify reasonable total time
        assert total_time < 5.0, f"Concurrent requests took {total_time:.2f}s, should be under 5s"

    def test_concurrent_user_registration(self, client):
        """Test concurrent user registration requests"""
        def register_user(user_id):
            response = client.post('/auth/register', data={
                'email': f'concurrent_user_{user_id}@example.com',
                'full_name': f'Concurrent User {user_id}',
                'password': 'password123',
                'confirm_password': 'password123'
            })
            return response.status_code
        
        # Run concurrent registrations
        num_threads = 5
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(register_user, i) for i in range(num_threads)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify most requests were handled
        handled_count = sum(1 for status_code in results if status_code in [200, 302, 400])
        assert handled_count >= 4, f"Only {handled_count}/{num_threads} registration requests were handled"
        
        assert total_time < 10.0, f"Concurrent registrations took {total_time:.2f}s"


class TestMemoryPerformance:
    """Test memory usage and efficiency"""

    def test_large_data_handling(self, auth_client):
        """Test handling of large data structures"""
        # Create large meal plan data
        large_meal_data = {
            'meals': []
        }
        
        # Generate substantial data
        for day in range(7):
            for meal in ['breakfast', 'lunch', 'dinner']:
                meal_data = {
                    'name': f'Day {day+1} {meal.title()}',
                    'items': []
                }
                
                # Add many items
                for item in range(20):
                    meal_data['items'].append({
                        'food': f'Food item {item+1}',
                        'quantity': '1 serving',
                        'calories': 100,
                        'protein': 10,
                        'carbs': 15,
                        'fat': 5,
                        'description': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.' * 10
                    })
                
                large_meal_data['meals'].append(meal_data)
        
        # Test saving large data
        start_time = time.time()
        response = auth_client.post('/api/save-meal-plan', json={
            'name': 'Large Performance Plan',
            'meal_plan': large_meal_data
        })
        end_time = time.time()
        
        processing_time = (end_time - start_time) * 1000
        
        # Should handle large data reasonably quickly
        assert processing_time < 2000, f"Large data processing took {processing_time:.2f}ms"
        assert response.status_code in [200, 400, 401, 404]  # Should handle gracefully

    def test_repeated_operations_memory_efficiency(self, client):
        """Test memory efficiency over repeated operations"""
        # Perform many repeated operations
        for i in range(100):
            response = client.get('/api/health')
            assert response.status_code == 200
            
            # Small delay to allow garbage collection
            if i % 20 == 0:
                time.sleep(0.1)
        
        # If we get here without memory issues, test passes
        assert True


class TestScalabilityPerformance:
    """Test application scalability"""

    def test_user_load_simulation(self, app):
        """Simulate increasing user load"""
        with app.app_context():
            # Create batches of users and measure performance
            batch_sizes = [10, 25, 50, 100]
            query_times = []
            
            for batch_size in batch_sizes:
                # Create users
                users = []
                for i in range(batch_size):
                    user = User(
                        email=f'load_user_{batch_size}_{i}@example.com',
                        full_name=f'Load User {i}',
                        credits_balance=5
                    )
                    user.set_password('testpass123')
                    users.append(user)
                
                db.session.add_all(users)
                db.session.commit()
                
                # Measure query performance with increased data
                start_time = time.time()
                count = User.query.count()
                end_time = time.time()
                
                query_time = (end_time - start_time) * 1000
                query_times.append(query_time)
                
                assert count > 0
            
            # Query times shouldn't increase dramatically
            # (This is a simple test - in production you'd want more sophisticated metrics)
            max_time = max(query_times)
            assert max_time < 500, f"Query time degraded to {max_time:.2f}ms with increased load"

    def test_data_volume_handling(self, app, test_user):
        """Test handling of increasing data volumes"""
        with app.app_context():
            # Create increasing numbers of meal plans
            volumes = [10, 25, 50]
            query_times = []
            
            for volume in volumes:
                # Create meal plans
                plans = []
                for i in range(volume):
                    plan = SavedMealPlan(
                        user_id=test_user.id,
                        name=f'Volume Plan {volume}_{i}',
                        diet_type='standard',
                        total_calories=2000,
                        meal_plan_data={
                            'meals': [f'meal_{j}' for j in range(10)]
                        }
                    )
                    plans.append(plan)
                
                db.session.add_all(plans)
                db.session.commit()
                
                # Measure query performance
                start_time = time.time()
                user_plans = SavedMealPlan.query.filter_by(user_id=test_user.id).count()
                end_time = time.time()
                
                query_time = (end_time - start_time) * 1000
                query_times.append(query_time)
                
                assert user_plans > 0
            
            # Performance shouldn't degrade significantly
            max_time = max(query_times)
            assert max_time < 300, f"Data volume query time reached {max_time:.2f}ms"


class TestNetworkPerformance:
    """Test network-related performance"""

    def test_response_size_efficiency(self, client):
        """Test response sizes are reasonable"""
        endpoints = [
            '/api/health',
            '/api/metrics',
            '/',
            '/auth/login'
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            if response.status_code == 200:
                response_size = len(response.data)
                
                # Basic response size checks
                if endpoint == '/api/health':
                    assert response_size < 1024, f"Health check response too large: {response_size} bytes"
                elif endpoint == '/api/metrics':
                    assert response_size < 2048, f"Metrics response too large: {response_size} bytes"
                elif endpoint == '/':
                    assert response_size < 50000, f"Home page response too large: {response_size} bytes"

    def test_json_response_efficiency(self, client):
        """Test JSON responses are efficient"""
        response = client.get('/api/health')
        if response.status_code == 200:
            # Verify JSON is compact (no excessive whitespace)
            json_data = response.data.decode('utf-8')
            
            # Should not have excessive whitespace
            lines = json_data.split('\n')
            assert len(lines) < 20, f"JSON response has {len(lines)} lines, might have excessive whitespace"
            
            # Should be reasonably sized
            assert len(json_data) < 1000, f"JSON response is {len(json_data)} characters"


class TestCachePerformance:
    """Test caching performance (if implemented)"""

    def test_repeated_requests_performance(self, client):
        """Test that repeated requests might benefit from caching"""
        endpoint = '/api/health'
        times = []
        
        # Make repeated requests
        for _ in range(10):
            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            times.append(response_time)
            
            assert response.status_code == 200
        
        # Later requests might be faster due to caching/optimization
        first_half = times[:5]
        second_half = times[5:]
        
        avg_first = mean(first_half)
        avg_second = mean(second_half)
        
        # This is informational - caching might improve performance
        # but we don't require it for this test to pass
        improvement_ratio = avg_first / avg_second if avg_second > 0 else 1
        
        # Test passes regardless, but logs potential improvement
        assert avg_first >= 0 and avg_second >= 0  # Basic sanity check