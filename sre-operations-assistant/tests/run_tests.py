#!/usr/bin/env python3
"""Simple test runner for SRE Operations Assistant"""

import sys
import os
import unittest
from unittest.mock import Mock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from aws_services import AWSInspector, AWSCloudWatch, AWSCloudTrail
    print("✅ Successfully imported AWS services")
except ImportError as e:
    print(f"❌ Failed to import AWS services: {e}")
    sys.exit(1)

def test_imports():
    """Test that all modules can be imported"""
    try:
        from vulnerability_analyzer import VulnerabilityAnalyzer
        from patch_scheduler import PatchScheduler
        from systems_manager import AWSSystemsManager
        print("✅ All core modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_aws_services():
    """Test AWS service initialization"""
    try:
        inspector = AWSInspector()
        cloudwatch = AWSCloudWatch()
        cloudtrail = AWSCloudTrail()
        print("✅ AWS services initialized successfully")
        return True
    except Exception as e:
        print(f"❌ AWS service initialization error: {e}")
        return False

def test_mcp_functions():
    """Test MCP function definitions"""
    try:
        import mcp_server
        
        # Check if core functions exist
        functions_to_check = [
            'get_inspector_findings',
            'get_ec2_cloudwatch_metrics', 
            'analyze_cloudtrail_events',
            'monitor_security_events',
            'analyze_configuration_changes'
        ]
        
        for func_name in functions_to_check:
            if hasattr(mcp_server, func_name):
                print(f"✅ Function {func_name} exists")
            else:
                print(f"❌ Function {func_name} missing")
                return False
        
        print("✅ All MCP functions defined")
        return True
    except Exception as e:
        print(f"❌ MCP function check error: {e}")
        return False

def main():
    """Run all tests"""
    print("SRE Operations Assistant - Test Runner")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("AWS Services", test_aws_services), 
        ("MCP Functions", test_mcp_functions)
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