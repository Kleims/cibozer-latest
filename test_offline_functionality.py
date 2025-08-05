#!/usr/bin/env python3
"""
Test Offline Functionality for Cibozer
Tests service worker, caching, and offline capabilities
"""

import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException


class OfflineFunctionalityTester:
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        self.results = {
            'service_worker': {'status': 'PENDING', 'details': []},
            'caching': {'status': 'PENDING', 'details': []},
            'offline_pages': {'status': 'PENDING', 'details': []},
            'offline_api': {'status': 'PENDING', 'details': []},
            'pwa_features': {'status': 'PENDING', 'details': []},
            'performance': {'status': 'PENDING', 'details': []}
        }
        
        # Setup Chrome with network conditions
        self.chrome_options = Options()
        self.chrome_options.add_argument('--disable-web-security')
        self.chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        self.chrome_options.add_argument('--user-data-dir=/tmp/chrome-test')
        
        # Don't run headless initially to see what's happening
        # self.chrome_options.add_argument('--headless')
        
        self.driver = None
    
    def setup_driver(self):
        """Initialize Chrome driver with offline capabilities"""
        try:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.driver.set_window_size(1200, 800)
            return True
        except WebDriverException as e:
            print(f"Failed to initialize Chrome driver: {e}")
            return False
    
    def test_service_worker_registration(self):
        """Test if service worker registers successfully"""
        print("🔧 Testing Service Worker Registration...")
        
        try:
            self.driver.get(self.base_url)
            
            # Wait for page load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check if service worker is registered
            sw_registered = self.driver.execute_script("""
                return new Promise(resolve => {
                    if ('serviceWorker' in navigator) {
                        navigator.serviceWorker.ready.then(registration => {
                            resolve({
                                registered: true,
                                scope: registration.scope,
                                state: registration.active ? registration.active.state : 'no active worker'
                            });
                        }).catch(error => {
                            resolve({registered: false, error: error.message});
                        });
                    } else {
                        resolve({registered: false, error: 'Service Worker not supported'});
                    }
                });
            """)
            
            if sw_registered['registered']:
                self.results['service_worker']['status'] = 'PASS'
                self.results['service_worker']['details'].append(
                    f"✅ Service Worker registered with scope: {sw_registered['scope']}"
                )
                self.results['service_worker']['details'].append(
                    f"✅ Worker state: {sw_registered['state']}"
                )
            else:
                self.results['service_worker']['status'] = 'FAIL'
                self.results['service_worker']['details'].append(
                    f"❌ Service Worker registration failed: {sw_registered.get('error', 'Unknown error')}"
                )
            
        except Exception as e:
            self.results['service_worker']['status'] = 'FAIL'
            self.results['service_worker']['details'].append(f"❌ Exception: {str(e)}")
    
    def test_caching_behavior(self):
        """Test if static assets are being cached"""
        print("💾 Testing Caching Behavior...")
        
        try:
            # Load page first time
            self.driver.get(self.base_url)
            time.sleep(3)  # Allow caching
            
            # Check cache storage
            cache_info = self.driver.execute_script("""
                return new Promise(async resolve => {
                    if ('caches' in window) {
                        try {
                            const cacheNames = await caches.keys();
                            const cacheContents = {};
                            
                            for (const name of cacheNames) {
                                const cache = await caches.open(name);
                                const requests = await cache.keys();
                                cacheContents[name] = requests.map(req => req.url);
                            }
                            
                            resolve({
                                supported: true,
                                caches: cacheNames,
                                contents: cacheContents,
                                totalCaches: cacheNames.length
                            });
                        } catch (error) {
                            resolve({supported: true, error: error.message});
                        }
                    } else {
                        resolve({supported: false});
                    }
                });
            """)
            
            if cache_info['supported']:
                if cache_info.get('totalCaches', 0) > 0:
                    self.results['caching']['status'] = 'PASS'
                    self.results['caching']['details'].append(
                        f"✅ Found {cache_info['totalCaches']} cache(s): {cache_info['caches']}"
                    )
                    
                    for cache_name, urls in cache_info.get('contents', {}).items():
                        self.results['caching']['details'].append(
                            f"✅ Cache '{cache_name}' contains {len(urls)} items"
                        )
                else:
                    self.results['caching']['status'] = 'FAIL'
                    self.results['caching']['details'].append("❌ No caches found")
            else:
                self.results['caching']['status'] = 'FAIL'
                self.results['caching']['details'].append("❌ Cache API not supported")
            
        except Exception as e:
            self.results['caching']['status'] = 'FAIL'
            self.results['caching']['details'].append(f"❌ Exception: {str(e)}")
    
    def test_offline_page_access(self):
        """Test offline page functionality"""
        print("📱 Testing Offline Page Access...")
        
        try:
            # First load the offline page while online
            self.driver.get(f"{self.base_url}/offline")
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
            
            title = self.driver.find_element(By.TAG_NAME, "h1").text
            
            if "offline" in title.lower():
                self.results['offline_pages']['status'] = 'PASS'
                self.results['offline_pages']['details'].append(
                    f"✅ Offline page accessible with title: '{title}'"
                )
                
                # Check for offline features
                features = self.driver.find_elements(By.CLASS_NAME, "feature-item")
                self.results['offline_pages']['details'].append(
                    f"✅ Found {len(features)} offline features listed"
                )
                
                # Check connection status indicator
                status_indicator = self.driver.find_elements(By.ID, "statusIndicator")
                if status_indicator:
                    self.results['offline_pages']['details'].append(
                        "✅ Connection status indicator present"
                    )
            else:
                self.results['offline_pages']['status'] = 'FAIL'
                self.results['offline_pages']['details'].append(
                    f"❌ Unexpected page title: '{title}'"
                )
            
        except Exception as e:
            self.results['offline_pages']['status'] = 'FAIL'
            self.results['offline_pages']['details'].append(f"❌ Exception: {str(e)}")
    
    def test_offline_api_responses(self):
        """Test API responses when offline"""
        print("🌐 Testing Offline API Responses...")
        
        try:
            # First, load page and let service worker cache
            self.driver.get(self.base_url)
            time.sleep(3)
            
            # Simulate offline mode
            self.driver.execute_cdp_cmd('Network.enable', {})
            self.driver.execute_cdp_cmd('Network.emulateNetworkConditions', {
                'offline': True,
                'latency': 0,
                'downloadThroughput': 0,
                'uploadThroughput': 0
            })
            
            # Try to make API request while offline
            api_response = self.driver.execute_script("""
                return fetch('/api/health')
                    .then(response => response.json())
                    .then(data => ({success: true, data: data}))
                    .catch(error => ({success: false, error: error.message}));
            """)
            
            # Restore network
            self.driver.execute_cdp_cmd('Network.emulateNetworkConditions', {
                'offline': False,
                'latency': 0,
                'downloadThroughput': -1,
                'uploadThroughput': -1
            })
            
            if api_response['success']:
                data = api_response['data']
                if data.get('offline') or data.get('_offline'):
                    self.results['offline_api']['status'] = 'PASS'
                    self.results['offline_api']['details'].append(
                        "✅ API returned offline response when network unavailable"
                    )
                else:
                    self.results['offline_api']['status'] = 'PARTIAL'
                    self.results['offline_api']['details'].append(
                        "⚠️ API responded but didn't indicate offline status"
                    )
            else:
                # This might be expected if no cached response exists
                self.results['offline_api']['status'] = 'PARTIAL'
                self.results['offline_api']['details'].append(
                    f"⚠️ API request failed offline (might be expected): {api_response['error']}"
                )
            
        except Exception as e:
            self.results['offline_api']['status'] = 'FAIL'
            self.results['offline_api']['details'].append(f"❌ Exception: {str(e)}")
    
    def test_pwa_features(self):
        """Test Progressive Web App features"""
        print("📱 Testing PWA Features...")
        
        try:
            self.driver.get(self.base_url)
            
            # Check for manifest
            manifest_link = self.driver.find_elements(By.CSS_SELECTOR, 'link[rel="manifest"]')
            
            if manifest_link:
                self.results['pwa_features']['details'].append("✅ Web app manifest found")
                
                # Try to get manifest content
                manifest_href = manifest_link[0].get_attribute('href')
                try:
                    response = requests.get(manifest_href)
                    if response.status_code == 200:
                        manifest_data = response.json()
                        self.results['pwa_features']['details'].append(
                            f"✅ Manifest loaded: {manifest_data.get('name', 'Unknown app')}"
                        )
                    else:
                        self.results['pwa_features']['details'].append(
                            f"⚠️ Manifest link found but returns {response.status_code}"
                        )
                except:
                    self.results['pwa_features']['details'].append(
                        "⚠️ Manifest link found but content not accessible"
                    )
            else:
                self.results['pwa_features']['details'].append("❌ No web app manifest found")
            
            # Check for theme color
            theme_color = self.driver.find_elements(By.CSS_SELECTOR, 'meta[name="theme-color"]')
            if theme_color:
                color = theme_color[0].get_attribute('content')
                self.results['pwa_features']['details'].append(f"✅ Theme color set: {color}")
            
            # Check for viewport meta tag
            viewport = self.driver.find_elements(By.CSS_SELECTOR, 'meta[name="viewport"]')
            if viewport:
                self.results['pwa_features']['details'].append("✅ Viewport meta tag present")
            
            # Check if app is installable
            is_installable = self.driver.execute_script("""
                return new Promise(resolve => {
                    let installPrompt = null;
                    
                    window.addEventListener('beforeinstallprompt', (e) => {
                        installPrompt = e;
                        resolve(true);
                    });
                    
                    // Give it a moment to fire
                    setTimeout(() => {
                        resolve(installPrompt !== null);
                    }, 2000);
                });
            """)
            
            if is_installable:
                self.results['pwa_features']['details'].append("✅ App is installable")
            
            # Determine overall PWA status
            pwa_features_count = len([d for d in self.results['pwa_features']['details'] if d.startswith('✅')])
            if pwa_features_count >= 2:
                self.results['pwa_features']['status'] = 'PASS'
            elif pwa_features_count >= 1:
                self.results['pwa_features']['status'] = 'PARTIAL'
            else:
                self.results['pwa_features']['status'] = 'FAIL'
            
        except Exception as e:
            self.results['pwa_features']['status'] = 'FAIL'
            self.results['pwa_features']['details'].append(f"❌ Exception: {str(e)}")
    
    def test_performance_metrics(self):
        """Test performance and loading metrics"""
        print("⚡ Testing Performance Metrics...")
        
        try:
            # Load page and measure performance
            start_time = time.time()
            self.driver.get(self.base_url)
            
            # Wait for page to be fully loaded
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            load_time = time.time() - start_time
            
            # Get performance metrics from browser
            perf_metrics = self.driver.execute_script("""
                const perfData = performance.getEntriesByType('navigation')[0];
                return {
                    domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
                    loadComplete: perfData.loadEventEnd - perfData.loadEventStart,
                    firstPaint: performance.getEntriesByType('paint').find(p => p.name === 'first-paint')?.startTime || 0,
                    firstContentfulPaint: performance.getEntriesByType('paint').find(p => p.name === 'first-contentful-paint')?.startTime || 0
                };
            """)
            
            self.results['performance']['details'].append(
                f"✅ Page load time: {load_time:.2f}s"
            )
            
            if perf_metrics['domContentLoaded']:
                self.results['performance']['details'].append(
                    f"✅ DOM Content Loaded: {perf_metrics['domContentLoaded']:.2f}ms"
                )
            
            if perf_metrics['firstContentfulPaint']:
                fcp = perf_metrics['firstContentfulPaint']
                status = "✅" if fcp < 2000 else "⚠️" if fcp < 4000 else "❌"
                self.results['performance']['details'].append(
                    f"{status} First Contentful Paint: {fcp:.2f}ms"
                )
            
            # Check if performance is acceptable
            if load_time < 3 and perf_metrics.get('firstContentfulPaint', 0) < 2000:
                self.results['performance']['status'] = 'PASS'
            elif load_time < 5:
                self.results['performance']['status'] = 'PARTIAL'
            else:
                self.results['performance']['status'] = 'FAIL'
            
        except Exception as e:
            self.results['performance']['status'] = 'FAIL'
            self.results['performance']['details'].append(f"❌ Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all offline functionality tests"""
        print("🚀 Starting Offline Functionality Tests for Cibozer\n")
        
        if not self.setup_driver():
            print("❌ Failed to setup test driver")
            return False
        
        try:
            # Run all tests
            self.test_service_worker_registration()
            self.test_caching_behavior()
            self.test_offline_page_access()
            self.test_offline_api_responses()
            self.test_pwa_features()
            self.test_performance_metrics()
            
            return True
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def print_results(self):
        """Print formatted test results"""
        print("\n" + "="*60)
        print("📊 OFFLINE FUNCTIONALITY TEST RESULTS")
        print("="*60)
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results.values() if r['status'] == 'PASS'])
        partial_tests = len([r for r in self.results.values() if r['status'] == 'PARTIAL'])
        failed_tests = len([r for r in self.results.values() if r['status'] == 'FAIL'])
        
        print(f"\n📈 SUMMARY: {passed_tests}/{total_tests} PASSED, {partial_tests} PARTIAL, {failed_tests} FAILED\n")
        
        for test_name, result in self.results.items():
            status_emoji = {
                'PASS': '✅',
                'PARTIAL': '⚠️',
                'FAIL': '❌',
                'PENDING': '⏳'
            }
            
            print(f"{status_emoji[result['status']]} {test_name.upper()}: {result['status']}")
            for detail in result['details']:
                print(f"   {detail}")
            print()
        
        # Overall assessment
        if passed_tests == total_tests:
            print("🎉 EXCELLENT: All offline functionality tests passed!")
        elif passed_tests + partial_tests >= total_tests * 0.8:
            print("👍 GOOD: Most offline functionality is working well")
        elif passed_tests + partial_tests >= total_tests * 0.5:
            print("⚠️ NEEDS IMPROVEMENT: Some offline functionality issues found")
        else:
            print("❌ CRITICAL: Major offline functionality problems detected")
    
    def save_results(self, filename='offline_test_results.json'):
        """Save test results to JSON file"""
        with open(filename, 'w') as f:
            json.dump({
                'timestamp': time.time(),
                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'results': self.results
            }, f, indent=2)
        print(f"📄 Results saved to {filename}")


def main():
    """Run offline functionality tests"""
    tester = OfflineFunctionalityTester()
    
    if tester.run_all_tests():
        tester.print_results()
        tester.save_results()
    else:
        print("❌ Test setup failed")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())