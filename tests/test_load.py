"""Load testing for Cibozer application using locust"""
from locust import HttpUser, task, between
import random
import json

class CibozerUser(HttpUser):
    """Simulated user behavior for load testing"""
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Setup: Login or register user"""
        # Register new user
        user_num = random.randint(10000, 99999)
        self.email = f"loadtest{user_num}@example.com"
        self.password = "LoadTest123!"
        
        response = self.client.post("/auth/register", data={
            "email": self.email,
            "password": self.password,
            "password_confirm": self.password,
            "full_name": f"Load Test User {user_num}"
        })
        
        if response.status_code != 200:
            # Try login if already exists
            self.client.post("/auth/login", data={
                "email": self.email,
                "password": self.password
            })
    
    @task(3)
    def generate_meal_plan(self):
        """Generate a meal plan - most common task"""
        meal_configs = [
            {"calories": 2000, "diet": "standard", "days": 1},
            {"calories": 1800, "diet": "keto", "days": 3},
            {"calories": 2200, "diet": "vegan", "days": 7},
            {"calories": 1500, "diet": "paleo", "days": 1},
        ]
        
        config = random.choice(meal_configs)
        
        with self.client.post("/api/generate",
                            json=config,
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 403:
                # Out of credits - expected for free users
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(2)
    def view_dashboard(self):
        """View user dashboard"""
        self.client.get("/dashboard")
    
    @task(1)
    def save_meal_plan(self):
        """Save a generated meal plan"""
        # First generate a plan
        response = self.client.post("/api/generate",
                                  json={
                                      "calories": 2000,
                                      "diet": "standard",
                                      "days": 1
                                  })
        
        if response.status_code == 200:
            meal_plan = response.json().get("meal_plan")
            
            # Save it
            self.client.post("/api/save-meal-plan",
                           json={
                               "name": f"Load Test Plan {random.randint(1, 100)}",
                               "meal_plan": meal_plan
                           })
    
    @task(1)
    def load_saved_plans(self):
        """Load user's saved meal plans"""
        self.client.get("/api/load-meal-plans")
    
    @task(1)
    def export_grocery_list(self):
        """Export grocery list from a plan"""
        # Generate simple plan for export
        response = self.client.post("/api/generate",
                                  json={
                                      "calories": 2000,
                                      "diet": "standard",
                                      "days": 1
                                  })
        
        if response.status_code == 200:
            meal_plan = response.json().get("meal_plan")
            
            self.client.post("/api/export-grocery-list",
                           json={"meal_plan": meal_plan})

class PremiumUser(CibozerUser):
    """Premium user with additional behaviors"""
    
    def on_start(self):
        """Login as premium user"""
        self.email = "premium_load@example.com"
        self.password = "PremiumTest123!"
        
        self.client.post("/auth/login", data={
            "email": self.email,
            "password": self.password
        })
    
    @task(1)
    def export_pdf(self):
        """Export meal plan as PDF - premium feature"""
        # Generate plan first
        response = self.client.post("/api/generate",
                                  json={
                                      "calories": 2000,
                                      "diet": "keto",
                                      "days": 7
                                  })
        
        if response.status_code == 200:
            meal_plan = response.json().get("meal_plan")
            
            self.client.post("/api/export-pdf",
                           json={
                               "title": "Premium Meal Plan",
                               "meal_plan": meal_plan
                           })

class APIUser(HttpUser):
    """API-only user for testing API endpoints"""
    wait_time = between(0.5, 2)
    
    def on_start(self):
        """Get API key or authenticate"""
        # For now, use session auth
        self.client.post("/auth/login", data={
            "email": "api_user@example.com",
            "password": "APITest123!"
        })
    
    @task(5)
    def health_check(self):
        """Check API health endpoint"""
        self.client.get("/api/health")
    
    @task(3)
    def get_metrics(self):
        """Get application metrics"""
        self.client.get("/api/metrics")
    
    @task(2)
    def user_status(self):
        """Check user status"""
        self.client.get("/api/user-status")

# Stress test scenario
class StressTestUser(HttpUser):
    """Aggressive user behavior for stress testing"""
    wait_time = between(0.1, 0.5)  # Very short wait times
    
    @task
    def rapid_requests(self):
        """Make rapid requests to stress the system"""
        endpoints = [
            "/api/health",
            "/api/metrics",
            "/dashboard",
            "/"
        ]
        
        endpoint = random.choice(endpoints)
        self.client.get(endpoint, name=endpoint)

# Mobile user simulation
class MobileUser(CibozerUser):
    """Mobile user with specific behaviors"""
    
    def on_start(self):
        """Set mobile headers"""
        super().on_start()
        self.client.headers.update({
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15"
        })
    
    @task(2)
    def check_offline_capability(self):
        """Check service worker and offline resources"""
        self.client.get("/static/sw.js")
        self.client.get("/static/manifest.json")

# Run with: locust -f tests/test_load.py --host=http://localhost:5000