#!/usr/bin/env python3
"""External deployment tests for PowerballAI"""

import requests
import time
import json
import os

# Production site URL
SITE_URL = f"https://{os.environ.get('POWERBALL_SITE_NAME', 'your-domain.com')}"

def test_site_accessibility():
    """Test if the site is accessible"""
    print("Testing site accessibility...")
    try:
        response = requests.get(SITE_URL, timeout=10)
        print(f"Status Code: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✅ Site is accessible")
        return True
    except Exception as e:
        print(f"❌ Site accessibility failed: {e}")
        return False

def test_health_endpoint():
    """Test health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{SITE_URL}/health", timeout=10)
        print(f"Health Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get('status') == 'ok'
        print("✅ Health endpoint working")
        return True
    except Exception as e:
        print(f"❌ Health endpoint failed: {e}")
        return False

def test_status_api():
    """Test status API endpoint"""
    print("Testing status API...")
    try:
        response = requests.get(f"{SITE_URL}/api/status", timeout=15)
        print(f"API Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        print(f"API Response: {data}")
        print("✅ Status API working")
        return True
    except Exception as e:
        print(f"❌ Status API failed: {e}")
        return False

def test_prediction_api():
    """Test prediction API"""
    print("Testing prediction API...")
    try:
        payload = {"tickets": 1, "strategy": "balanced"}
        response = requests.post(
            f"{SITE_URL}/api/predict", 
            json=payload, 
            timeout=20,
            headers={'Content-Type': 'application/json'}
        )
        print(f"Prediction Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert 'predictions' in data
        print("✅ Prediction API working")
        return True
    except Exception as e:
        print(f"❌ Prediction API failed: {e}")
        return False

def test_ssl_certificate():
    """Test SSL certificate"""
    print("Testing SSL certificate...")
    try:
        response = requests.get(SITE_URL, timeout=10)
        print("✅ SSL certificate valid")
        return True
    except requests.exceptions.SSLError as e:
        print(f"❌ SSL certificate failed: {e}")
        return False

def run_external_tests():
    """Run all external tests"""
    print(f"=== External Deployment Tests for {SITE_URL} ===\n")
    
    tests = [
        test_site_accessibility,
        test_health_endpoint,
        test_status_api,
        test_prediction_api,
        test_ssl_certificate
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
        print()
    
    print(f"=== External Test Results ===")
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 All external tests passed!")
        return True
    else:
        print("⚠️ Some external tests failed")
        return False

if __name__ == "__main__":
    success = run_external_tests()
    exit(0 if success else 1)