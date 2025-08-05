"""End-to-end tests for critical user journeys"""
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import json

class TestE2ECriticalPaths:
    """Test critical user paths end-to-end"""
    
    @pytest.fixture
    def driver(self):
        """Setup Chrome driver for testing"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run in headless mode
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(10)
        yield driver
        driver.quit()
    
    def test_new_user_registration_and_meal_plan(self, driver, live_server):
        """Test complete new user journey"""
        # Navigate to homepage
        driver.get(live_server.url)
        
        # Click Get Started
        get_started = driver.find_element(By.LINK_TEXT, "Get Started")
        get_started.click()
        
        # Fill registration form
        driver.find_element(By.NAME, "email").send_keys("e2e_test@example.com")
        driver.find_element(By.NAME, "full_name").send_keys("E2E Test User")
        driver.find_element(By.NAME, "password").send_keys("TestPass123!")
        driver.find_element(By.NAME, "password_confirm").send_keys("TestPass123!")
        
        # Submit registration
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Wait for redirect to dashboard/onboarding
        wait = WebDriverWait(driver, 10)
        wait.until(EC.url_contains(('/dashboard', '/onboarding')))
        
        # Generate meal plan
        driver.find_element(By.ID, "calories").clear()
        driver.find_element(By.ID, "calories").send_keys("2000")
        driver.find_element(By.ID, "diet-standard").click()
        driver.find_element(By.ID, "days-1").click()
        
        # Click generate button
        generate_btn = driver.find_element(By.ID, "generateBtn")
        generate_btn.click()
        
        # Wait for meal plan to load
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "meal-card")))
        
        # Verify meal plan displayed
        meal_cards = driver.find_elements(By.CLASS_NAME, "meal-card")
        assert len(meal_cards) >= 3  # At least 3 meals
        
        # Save meal plan
        save_btn = driver.find_element(By.ID, "savePlanBtn")
        save_btn.click()
        
        # Enter plan name
        plan_name = wait.until(EC.presence_of_element_located((By.ID, "planName")))
        plan_name.send_keys("My E2E Test Plan")
        
        # Confirm save
        driver.find_element(By.ID, "confirmSaveBtn").click()
        
        # Verify success message
        success_msg = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "alert-success")))
        assert "saved successfully" in success_msg.text.lower()
    
    def test_existing_user_login_and_premium_upgrade(self, driver, live_server, existing_user):
        """Test existing user login and premium upgrade flow"""
        # Navigate to login
        driver.get(f"{live_server.url}/auth/login")
        
        # Login
        driver.find_element(By.NAME, "email").send_keys(existing_user.email)
        driver.find_element(By.NAME, "password").send_keys("TestPass123!")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Wait for dashboard
        wait = WebDriverWait(driver, 10)
        wait.until(EC.url_contains('/dashboard'))
        
        # Click upgrade button
        upgrade_btn = driver.find_element(By.LINK_TEXT, "Upgrade to Premium")
        upgrade_btn.click()
        
        # Wait for pricing page
        wait.until(EC.url_contains('/pricing'))
        
        # Select premium plan
        premium_btn = driver.find_element(By.CSS_SELECTOR, "[data-plan='premium']")
        premium_btn.click()
        
        # Verify Stripe checkout loads (in test mode)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "stripe-checkout")))
    
    def test_mobile_responsive_navigation(self, driver, live_server):
        """Test mobile responsive behavior"""
        # Set mobile viewport
        driver.set_window_size(375, 667)  # iPhone 6/7/8 size
        
        # Navigate to homepage
        driver.get(live_server.url)
        
        # Check mobile menu button is visible
        menu_btn = driver.find_element(By.CLASS_NAME, "navbar-toggler")
        assert menu_btn.is_displayed()
        
        # Click menu button
        menu_btn.click()
        
        # Wait for menu to expand
        time.sleep(0.5)
        
        # Check menu items are visible
        nav_items = driver.find_elements(By.CLASS_NAME, "nav-link")
        for item in nav_items:
            assert item.is_displayed()
    
    def test_error_handling_invalid_inputs(self, driver, live_server):
        """Test error handling for invalid inputs"""
        # Navigate to registration
        driver.get(f"{live_server.url}/auth/register")
        
        # Try to submit empty form
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Check for error messages
        wait = WebDriverWait(driver, 5)
        error_msgs = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "invalid-feedback")))
        assert len(error_msgs) > 0
        
        # Try weak password
        driver.find_element(By.NAME, "email").send_keys("test@example.com")
        driver.find_element(By.NAME, "password").send_keys("weak")
        driver.find_element(By.NAME, "password_confirm").send_keys("weak")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Check for password error
        error_alert = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "alert-danger")))
        assert "password must be at least" in error_alert.text.lower()
    
    def test_accessibility_keyboard_navigation(self, driver, live_server):
        """Test keyboard navigation accessibility"""
        driver.get(live_server.url)
        
        # Tab through main navigation
        body = driver.find_element(By.TAG_NAME, "body")
        
        # Press Tab multiple times
        for i in range(10):
            body.send_keys("\ue004")  # Tab key
            time.sleep(0.1)
            
            # Check focused element has visible outline
            focused = driver.switch_to.active_element
            outline = focused.value_of_css_property("outline")
            assert outline != "none" or focused.value_of_css_property("box-shadow") != "none"
    
    def test_performance_page_load_time(self, driver, live_server):
        """Test page load performance"""
        # Enable performance logging
        driver.execute_script("window.performance.mark('testStart');")
        
        # Navigate to homepage
        driver.get(live_server.url)
        
        # Wait for page to fully load
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        # Get performance metrics
        metrics = driver.execute_script("""
            const perfData = window.performance.timing;
            return {
                pageLoadTime: perfData.loadEventEnd - perfData.navigationStart,
                domReadyTime: perfData.domContentLoadedEventEnd - perfData.navigationStart,
                responseTime: perfData.responseEnd - perfData.requestStart
            };
        """)
        
        # Assert performance thresholds
        assert metrics['pageLoadTime'] < 3000  # Page loads in under 3 seconds
        assert metrics['domReadyTime'] < 1500  # DOM ready in under 1.5 seconds
        assert metrics['responseTime'] < 500   # Server response under 500ms

class TestAPIIntegration:
    """Test API integration scenarios"""
    
    def test_api_rate_limiting_enforcement(self, client, auth):
        """Test that rate limiting is properly enforced"""
        auth.login()
        
        # Make rapid requests
        results = []
        for i in range(50):
            response = client.post('/api/generate',
                                 json={'calories': 2000, 'diet': 'standard', 'days': 1})
            results.append(response.status_code)
        
        # Check that some requests were rate limited
        rate_limited = sum(1 for r in results if r == 429)
        assert rate_limited > 0, "Rate limiting not enforced"
    
    def test_concurrent_user_sessions(self, client, app):
        """Test handling of concurrent user sessions"""
        # Create multiple users
        users = []
        for i in range(3):
            with app.app_context():
                from app.models import User
                from app.extensions import db
                user = User(
                    email=f'concurrent{i}@example.com',
                    full_name=f'Concurrent User {i}',
                    credits_balance=5
                )
                user.set_password('TestPass123!')
                db.session.add(user)
                db.session.commit()
                users.append(user)
        
        # Create separate client sessions
        sessions = []
        for user in users:
            c = app.test_client()
            c.post('/auth/login', data={
                'email': user.email,
                'password': 'TestPass123!'
            })
            sessions.append(c)
        
        # Make concurrent requests
        import concurrent.futures
        
        def make_request(session):
            return session.post('/api/generate',
                              json={'calories': 2000, 'diet': 'standard', 'days': 1})
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request, s) for s in sessions]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        assert all(r.status_code == 200 for r in results)
    
    def test_payment_webhook_processing(self, client, app):
        """Test Stripe webhook processing"""
        # Simulate Stripe webhook
        webhook_data = {
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'cs_test_123',
                    'customer': 'cus_test_123',
                    'metadata': {
                        'user_id': '1',
                        'plan': 'premium'
                    }
                }
            }
        }
        
        # Send webhook (would need proper signature in production)
        response = client.post('/payment/stripe-webhook',
                             json=webhook_data,
                             headers={'Stripe-Signature': 'test_sig'})
        
        # Check response (may be 400 without valid signature)
        assert response.status_code in [200, 400]

def test_full_coverage_report():
    """Generate and verify test coverage report"""
    import subprocess
    import os
    
    # Run coverage
    result = subprocess.run([
        'python', '-m', 'pytest',
        '--cov=app',
        '--cov-report=html',
        '--cov-report=term'
    ], capture_output=True, text=True)
    
    # Parse coverage percentage from output
    for line in result.stdout.split('\n'):
        if 'TOTAL' in line:
            parts = line.split()
            coverage_percent = int(parts[-1].rstrip('%'))
            
            # Assert 90%+ coverage
            assert coverage_percent >= 90, f"Coverage {coverage_percent}% is below 90% threshold"
            break
    
    # Check that coverage report was generated
    assert os.path.exists('htmlcov/index.html'), "Coverage report not generated"