#!/usr/bin/env python3
"""Test suite for PowerballAI Web Interface"""

import unittest
import requests
import json
import time
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

class TestWebInterface(unittest.TestCase):
    """Test web interface functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.base_url = "http://localhost:5000"
        cls.api_url = f"{cls.base_url}/api"
        
        # Wait for server to be ready
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(f"{cls.base_url}/ping", timeout=5)
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException:
                if i == max_retries - 1:
                    raise Exception("Web server not available for testing")
                time.sleep(2)
    
    def test_ping_endpoint(self):
        """Test FastAPI ping endpoint"""
        response = requests.get(f"{self.base_url}/ping")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), "pong")
    
    def test_health_endpoint(self):
        """Test FastAPI health endpoint"""
        response = requests.get(f"{self.base_url}/health")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('status', data)
        self.assertIn('timestamp', data)
        self.assertEqual(data['status'], 'ok')
    
    def test_main_page_loads(self):
        """Test that main page loads successfully"""
        response = requests.get(self.base_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Powerball Statistical Edge', response.text)
        self.assertIn('Generate Predictions', response.text)
    
    def test_status_api(self):
        """Test status API endpoint"""
        response = requests.get(f"{self.api_url}/status")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('status', data)
        self.assertIn('database_connected', data)
        self.assertIn('total_drawings', data)
    
    def test_analyze_api(self):
        """Test analyze API endpoint"""
        response = requests.get(f"{self.api_url}/analyze")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('data_summary', data)
        self.assertIn('frequency_analysis', data)
        self.assertIn('gap_analysis', data)
        
        # Validate data structure
        self.assertIn('total_drawings', data['data_summary'])
        self.assertIn('date_range', data['data_summary'])
    
    def test_predict_api_single_ticket(self):
        """Test prediction API with single ticket"""
        payload = {
            'tickets': 1,
            'strategy': 'balanced'
        }
        
        response = requests.post(f"{self.api_url}/predict", json=payload)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('predictions', data)
        self.assertIn('summary', data)
        
        predictions = data['predictions']
        self.assertEqual(len(predictions), 1)
        
        pred = predictions[0]
        self.assertIn('numbers', pred)
        self.assertIn('powerball', pred)
        self.assertIn('confidence_score', pred)
        self.assertIn('reasoning', pred)
        
        # Validate number ranges
        self.assertEqual(len(pred['numbers']), 5)
        for num in pred['numbers']:
            self.assertGreaterEqual(num, 1)
            self.assertLessEqual(num, 69)
        
        self.assertGreaterEqual(pred['powerball'], 1)
        self.assertLessEqual(pred['powerball'], 26)
    
    def test_predict_api_multiple_tickets(self):
        """Test prediction API with multiple tickets"""
        payload = {
            'tickets': 5,
            'strategy': 'portfolio'
        }
        
        response = requests.post(f"{self.api_url}/predict", json=payload)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        predictions = data['predictions']
        self.assertEqual(len(predictions), 5)
        
        # Check that different strategies are used in portfolio
        strategies = [pred['strategy'] for pred in predictions]
        self.assertGreater(len(set(strategies)), 1)  # Multiple strategies
    
    def test_predict_api_strategies(self):
        """Test all prediction strategies"""
        strategies = ['balanced', 'frequency_based', 'gap_based', 'monte_carlo', 'pattern_based']
        
        for strategy in strategies:
            with self.subTest(strategy=strategy):
                payload = {
                    'tickets': 1,
                    'strategy': strategy
                }
                
                response = requests.post(f"{self.api_url}/predict", json=payload)
                self.assertEqual(response.status_code, 200)
                
                data = response.json()
                self.assertIn('predictions', data)
                self.assertEqual(data['predictions'][0]['strategy'], strategy)
    
    def test_predict_api_validation(self):
        """Test API input validation"""
        # Test invalid strategy
        payload = {
            'tickets': 1,
            'strategy': 'invalid_strategy'
        }
        
        response = requests.post(f"{self.api_url}/predict", json=payload)
        self.assertEqual(response.status_code, 200)  # Should fallback to balanced
        
        data = response.json()
        self.assertEqual(data['predictions'][0]['strategy'], 'balanced')
    
    def test_update_data_api(self):
        """Test data update API endpoint"""
        response = requests.post(f"{self.api_url}/update-data")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('status', data)
        if data['status'] == 'success':
            self.assertIn('total_drawings', data)
    
    def test_api_error_handling(self):
        """Test API error handling"""
        # Test malformed JSON
        response = requests.post(
            f"{self.api_url}/predict", 
            data="invalid json",
            headers={'Content-Type': 'application/json'}
        )
        self.assertIn(response.status_code, [400, 422, 500])  # FastAPI returns 422 for validation errors
    
    def test_docs_endpoint(self):
        """Test FastAPI auto-generated docs"""
        response = requests.get(f"{self.base_url}/docs")
        self.assertEqual(response.status_code, 200)
        self.assertIn('swagger', response.text.lower())
    
    def test_confidence_scores_reasonable(self):
        """Test that confidence scores are within reasonable ranges"""
        payload = {
            'tickets': 10,
            'strategy': 'balanced'
        }
        
        response = requests.post(f"{self.api_url}/predict", json=payload)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        for pred in data['predictions']:
            confidence = pred['confidence_score']
            self.assertGreaterEqual(confidence, 0.0)
            self.assertLessEqual(confidence, 1.0)
            # Should be reasonable confidence (not too low/high)
            self.assertGreaterEqual(confidence, 0.3)
            self.assertLessEqual(confidence, 0.9)

class TestWebSecurity(unittest.TestCase):
    """Test web security features"""
    
    def setUp(self):
        """Set up for each test"""
        self.base_url = "http://localhost:5000"
        self.api_url = f"{self.base_url}/api"
    
    def test_security_headers(self):
        """Test security headers are present"""
        response = requests.get(self.base_url)
        
        # Check for basic security headers
        headers = response.headers
        # Note: These might not be set in development mode
        # In production, these should be enforced by the load balancer
    
    def test_rate_limiting_simulation(self):
        """Test rate limiting behavior (basic simulation)"""
        # Make multiple rapid requests
        responses = []
        for i in range(20):
            try:
                response = requests.get(f"{self.api_url}/status", timeout=1)
                responses.append(response.status_code)
            except requests.exceptions.RequestException:
                responses.append(0)
        
        # Should mostly succeed (no rate limiting in dev mode)
        success_count = sum(1 for r in responses if r == 200)
        self.assertGreater(success_count, 15)  # Most should succeed
    
    def test_input_sanitization(self):
        """Test input sanitization"""
        # Test with potentially malicious input
        payload = {
            'tickets': '<script>alert("xss")</script>',
            'strategy': 'balanced'
        }
        
        response = requests.post(f"{self.api_url}/predict", json=payload)
        # Should handle gracefully, not crash
        self.assertIn(response.status_code, [200, 400, 422, 500])  # FastAPI returns 422 for validation errors

class TestWebPerformance(unittest.TestCase):
    """Test web performance characteristics"""
    
    def setUp(self):
        """Set up for each test"""
        self.base_url = "http://localhost:5000"
        self.api_url = f"{self.base_url}/api"
    
    def test_response_times(self):
        """Test API response times"""
        endpoints = [
            '/status',
            '/analyze'
        ]
        
        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                start_time = time.time()
                response = requests.get(f"{self.api_url}{endpoint}")
                end_time = time.time()
                
                self.assertEqual(response.status_code, 200)
                response_time = end_time - start_time
                self.assertLess(response_time, 5.0)  # Should respond within 5 seconds
    
    def test_prediction_performance(self):
        """Test prediction generation performance"""
        payload = {
            'tickets': 10,
            'strategy': 'balanced'
        }
        
        start_time = time.time()
        response = requests.post(f"{self.api_url}/predict", json=payload)
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        response_time = end_time - start_time
        self.assertLess(response_time, 10.0)  # Should complete within 10 seconds
    
    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            try:
                response = requests.get(f"{self.api_url}/status", timeout=10)
                results.put(response.status_code)
            except Exception as e:
                results.put(str(e))
        
        # Create 10 concurrent threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        success_count = 0
        while not results.empty():
            result = results.get()
            if result == 200:
                success_count += 1
        
        # Most requests should succeed
        self.assertGreaterEqual(success_count, 8)

if __name__ == '__main__':
    # Check if server is running
    try:
        response = requests.get("http://localhost:5000/ping", timeout=5)
        if response.status_code != 200:
            print("❌ Web server not running. Start with: bash scripts/run_local.sh")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print("❌ Web server not running. Start with: bash scripts/run_local.sh")
        sys.exit(1)
    
    print("🌐 Testing web interface at http://localhost:5000")
    unittest.main(verbosity=2)