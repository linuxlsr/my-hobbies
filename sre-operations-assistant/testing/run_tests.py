#!/usr/bin/env python3
"""Test runner for SRE Operations Assistant testing framework"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_unit_tests():
    """Run unit tests"""
    print("🧪 Running unit tests...")
    result = subprocess.run([
        sys.executable, '-m', 'pytest', 
        'testing/unit/', 
        '-v', '--tb=short'
    ], cwd=Path(__file__).parent.parent)
    return result.returncode == 0

def run_integration_tests():
    """Run integration tests"""
    print("🔗 Running integration tests...")
    result = subprocess.run([
        sys.executable, '-m', 'pytest',
        'testing/integration/',
        '-v', '--tb=short'
    ], cwd=Path(__file__).parent.parent)
    return result.returncode == 0

def run_load_tests():
    """Run load tests"""
    print("⚡ Running load tests...")
    print("Starting Locust load test (run for 60 seconds)...")
    
    # Run locust in headless mode for automated testing
    result = subprocess.run([
        'locust', 
        '-f', 'testing/load/test_concurrent_requests.py',
        '--host=https://sre-ops.threemoonsnetwork.net',
        '--users=10',
        '--spawn-rate=2', 
        '--run-time=60s',
        '--headless',
        '--html=testing/load_test_report.html'
    ], cwd=Path(__file__).parent.parent)
    
    return result.returncode == 0

def run_regression_tests():
    """Run regression tests"""
    print("🔄 Running regression tests...")
    result = subprocess.run([
        sys.executable, '-m', 'pytest',
        'testing/regression/',
        '-v', '--tb=short'
    ], cwd=Path(__file__).parent.parent)
    return result.returncode == 0

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'pytest', 'moto', 'boto3', 'requests'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Install with: pip install -r testing/requirements.txt")
        return False
    
    return True

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description='SRE Operations Assistant Test Runner')
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--load', action='store_true', help='Run load tests only')
    parser.add_argument('--regression', action='store_true', help='Run regression tests only')
    parser.add_argument('--all', action='store_true', help='Run all tests (default)')
    
    args = parser.parse_args()
    
    # Default to running all tests if no specific test type is specified
    if not any([args.unit, args.integration, args.load, args.regression]):
        args.all = True
    
    print("🚀 SRE Operations Assistant Test Suite")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    results = []
    
    if args.unit or args.all:
        results.append(("Unit Tests", run_unit_tests()))
    
    if args.integration or args.all:
        results.append(("Integration Tests", run_integration_tests()))
    
    if args.load or args.all:
        results.append(("Load Tests", run_load_tests()))
    
    if args.regression or args.all:
        results.append(("Regression Tests", run_regression_tests()))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    all_passed = True
    for test_type, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_type}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n💥 Some tests failed!")
        return 1

if __name__ == '__main__':
    sys.exit(main())