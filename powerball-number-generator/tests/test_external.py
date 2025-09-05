#!/usr/bin/env python3
"""External deployment tests for PowerballAI"""

import requests
import time
import json
import os
import subprocess
import sys
from pathlib import Path

def get_terraform_output():
    """Get deployment URL from Terraform outputs"""
    terraform_dir = Path(__file__).parent.parent / "terraform"
    
    try:
        # Try to get terraform output
        result = subprocess.run(
            ["terraform", "output", "-json"],
            cwd=terraform_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            outputs = json.loads(result.stdout)
            if "application_url" in outputs:
                return outputs["application_url"]["value"]
    except Exception as e:
        print(f"Could not get Terraform output: {e}")
    
    # Check for terraform.tfvars for actual values
    try:
        tfvars_file = terraform_dir / "terraform.tfvars"
        if tfvars_file.exists():
            domain = "example.com"
            subdomain = "app"
            
            with open(tfvars_file, 'r') as f:
                content = f.read()
                for line in content.split('\n'):
                    if line.strip().startswith('domain_name'):
                        domain = line.split('=')[1].strip().strip('"')
                    elif line.strip().startswith('subdomain'):
                        subdomain = line.split('=')[1].strip().strip('"')
            
            return f"https://{subdomain}.{domain}"
    except Exception as e:
        print(f"Could not read terraform.tfvars: {e}")
    
    # Fallback: read variables.tf defaults
    try:
        vars_file = terraform_dir / "variables.tf"
        if vars_file.exists():
            with open(vars_file, 'r') as f:
                content = f.read()
                domain = "example.com"
                subdomain = "app"
                
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'variable "domain_name"' in line:
                        for j in range(i, min(i+10, len(lines))):
                            if 'default' in lines[j] and '=' in lines[j]:
                                domain = lines[j].split('"')[1]
                                break
                    elif 'variable "subdomain"' in line:
                        for j in range(i, min(i+10, len(lines))):
                            if 'default' in lines[j] and '=' in lines[j]:
                                subdomain = lines[j].split('"')[1]
                                break
                
                return f"https://{subdomain}.{domain}"
    except Exception as e:
        print(f"Could not read Terraform variables: {e}")
    
    return f"https://{os.environ.get('POWERBALL_SITE_NAME', 'app.example.com')}"

# Get production site URL from Terraform
SITE_URL = get_terraform_output()
print(f"Testing deployment at: {SITE_URL}")

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

def check_deployment_exists():
    """Check if deployment actually exists"""
    terraform_dir = Path(__file__).parent.parent / "terraform"
    
    # Check for terraform state file
    tfstate_file = terraform_dir / "terraform.tfstate"
    if not tfstate_file.exists() or tfstate_file.stat().st_size == 0:
        print(f"⚠️ No Terraform state found at {tfstate_file} - skipping external tests")
        return False
    
    # Check for actual terraform.tfvars (not example)
    tfvars_file = terraform_dir / "terraform.tfvars"
    if not tfvars_file.exists():
        print(f"⚠️ No terraform.tfvars found - skipping external tests")
        return False
    
    if "example.com" in SITE_URL or "your-domain.com" in SITE_URL:
        print(f"⚠️ Using default/placeholder URL: {SITE_URL}")
        print("No actual deployment detected - skipping external tests")
        return False
    
    print(f"✅ External deployment detected at: {SITE_URL}")
    return True

def run_external_tests():
    """Run all external tests"""
    print(f"=== External Deployment Tests for {SITE_URL} ===\n")
    
    if not check_deployment_exists():
        return True  # Skip tests but don't fail
    
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

# Unit test compatibility
import unittest

class TestExternalDeployment(unittest.TestCase):
    """External deployment test cases"""
    
    def setUp(self):
        self.site_url = SITE_URL
        self.deployment_exists = check_deployment_exists()
    
    def test_deployment_accessibility(self):
        """Test if deployment is accessible"""
        if not self.deployment_exists:
            self.skipTest("No actual deployment detected")
        
        response = requests.get(self.site_url, timeout=10)
        self.assertEqual(response.status_code, 200)
    
    def test_health_endpoint(self):
        """Test health endpoint"""
        if not self.deployment_exists:
            self.skipTest("No actual deployment detected")
        
        response = requests.get(f"{self.site_url}/health", timeout=10)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'ok')
    
    def test_api_status(self):
        """Test API status endpoint"""
        if not self.deployment_exists:
            self.skipTest("No actual deployment detected")
        
        response = requests.get(f"{self.site_url}/api/status", timeout=15)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('status', data)
    
    def test_prediction_api(self):
        """Test prediction API"""
        if not self.deployment_exists:
            self.skipTest("No actual deployment detected")
        
        payload = {"tickets": 1, "strategy": "balanced"}
        response = requests.post(
            f"{self.site_url}/api/predict", 
            json=payload, 
            timeout=20,
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('predictions', data)
    
    def test_ssl_certificate(self):
        """Test SSL certificate validity"""
        if not self.deployment_exists:
            self.skipTest("No actual deployment detected")
        
        # This will raise SSLError if certificate is invalid
        response = requests.get(self.site_url, timeout=10)
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--unittest":
        unittest.main(argv=[''])
    else:
        success = run_external_tests()
        exit(0 if success else 1)