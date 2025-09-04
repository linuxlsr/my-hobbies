#!/usr/bin/env python3
"""Comprehensive test runner for PowerballAI"""

import unittest
import sys
import subprocess
import time
import requests
from pathlib import Path

def check_web_server():
    """Check if web server is running"""
    try:
        response = requests.get("http://localhost:5000/api/status", timeout=5)
        return response.status_code == 200
    except:
        return False

def start_web_server():
    """Start web server for testing"""
    print("🚀 Starting web server for testing...")
    web_app = Path(__file__).parent.parent / 'web' / 'app.py'
    
    process = subprocess.Popen([
        sys.executable, str(web_app)
    ], cwd=web_app.parent.parent)
    
    # Wait for server to start
    for i in range(30):
        if check_web_server():
            print("✅ Web server started successfully")
            return process
        time.sleep(2)
    
    process.terminate()
    raise Exception("Failed to start web server")

def run_test_suite(test_module, description):
    """Run a specific test suite"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print('='*60)
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(test_module)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful(), len(result.failures), len(result.errors)

def main():
    """Main test runner"""
    print("🎱 PowerballAI Comprehensive Test Suite")
    print("="*60)
    
    # Change to project directory
    project_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(project_dir))
    
    # Import test modules
    try:
        from tests import test_cli, test_web, test_external
    except ImportError as e:
        print(f"❌ Failed to import test modules: {e}")
        return 1
    
    results = []
    web_server_process = None
    
    try:
        # 1. Run CLI tests
        success, failures, errors = run_test_suite(test_cli, "CLI Interface Tests")
        results.append(("CLI Tests", success, failures, errors))
        
        # 2. Start web server and run web tests
        if not check_web_server():
            try:
                web_server_process = start_web_server()
            except Exception as e:
                print(f"❌ Could not start web server: {e}")
                print("⚠️  Skipping web interface tests")
                results.append(("Web Tests", False, 0, 1))
        
        if check_web_server():
            success, failures, errors = run_test_suite(test_web, "Web Interface Tests")
            results.append(("Web Tests", success, failures, errors))
        
        # 3. Run external tests (optional)
        print(f"\n{'='*60}")
        print("🌐 External Deployment Tests")
        print('='*60)
        print("Testing external deployment at https://your-domain.com")
        
        try:
            # Quick check if external site is available
            response = requests.get("https://your-domain.com", timeout=10)
            if response.status_code == 200:
                success, failures, errors = run_test_suite(test_external, "External Deployment Tests")
                results.append(("External Tests", success, failures, errors))
            else:
                print("⚠️  External site not available, skipping external tests")
                results.append(("External Tests", None, 0, 0))
        except Exception as e:
            print(f"⚠️  External site not available: {e}")
            results.append(("External Tests", None, 0, 0))
        
    finally:
        # Clean up web server
        if web_server_process:
            print("\n🛑 Stopping web server...")
            web_server_process.terminate()
            web_server_process.wait()
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 TEST RESULTS SUMMARY")
    print('='*60)
    
    total_success = 0
    total_tests = 0
    
    for test_name, success, failures, errors in results:
        if success is None:
            status = "⚠️  SKIPPED"
        elif success:
            status = "✅ PASSED"
            total_success += 1
        else:
            status = f"❌ FAILED ({failures} failures, {errors} errors)"
        
        print(f"{test_name:20} {status}")
        if success is not None:
            total_tests += 1
    
    print(f"\n📈 Overall: {total_success}/{total_tests} test suites passed")
    
    if total_success == total_tests and total_tests > 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed!")
        return 1

if __name__ == '__main__':
    sys.exit(main())