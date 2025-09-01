#!/usr/bin/env python3
"""Simple test runner for SRE Operations Assistant"""

import sys
import os
import unittest
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_basic_imports():
    """Test basic Python imports"""
    try:
        import boto3
        import json
        import asyncio
        print("✅ Basic imports successful")
        return True
    except ImportError as e:
        print(f"❌ Basic import error: {e}")
        return False

def test_cli_exists():
    """Test that CLI exists"""
    try:
        cli_path = os.path.join(os.path.dirname(__file__), '..', 'cli', 'sre_cli.py')
        if os.path.exists(cli_path):
            print("✅ CLI exists")
            return True
        else:
            print("❌ CLI not found")
            return False
    except Exception as e:
        print(f"❌ CLI check error: {e}")
        return False

def test_infrastructure_exists():
    """Test that infrastructure files exist"""
    try:
        infra_path = os.path.join(os.path.dirname(__file__), '..', 'infrastructure')
        if os.path.exists(infra_path) and os.path.exists(os.path.join(infra_path, 'main.tf')):
            print("✅ Infrastructure files exist")
            return True
        else:
            print("❌ Infrastructure files not found")
            return False
    except Exception as e:
        print(f"❌ Infrastructure check error: {e}")
        return False

def test_bots_exist():
    """Test that bot files exist"""
    try:
        bots_path = os.path.join(os.path.dirname(__file__), '..', 'bots')
        slack_bot = os.path.join(bots_path, 'slack_lambda.py')
        teams_bot = os.path.join(bots_path, 'teams_lambda.py')
        
        if os.path.exists(slack_bot) and os.path.exists(teams_bot):
            print("✅ Bot files exist")
            return True
        else:
            print("❌ Bot files not found")
            return False
    except Exception as e:
        print(f"❌ Bot check error: {e}")
        return False

def main():
    """Run all tests"""
    print("SRE Operations Assistant - Test Runner")
    print("=" * 50)
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("CLI Exists", test_cli_exists),
        ("Infrastructure Exists", test_infrastructure_exists),
        ("Bots Exist", test_bots_exist)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        print("-" * 30)
        
        if test_func():
            passed += 1
        else:
            print(f"Test {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())