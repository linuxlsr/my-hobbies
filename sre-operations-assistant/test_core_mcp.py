#!/usr/bin/env python3
"""Test script for core MCP functions via CLI"""

import subprocess
import sys
import os

def run_cli_command(command):
    """Run CLI command and return result"""
    try:
        result = subprocess.run(
            ["python", "cli/sre_cli.py"] + command.split(),
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def test_core_functions():
    """Test all core MCP functions"""
    print("🧪 Testing Core MCP Functions")
    print("=" * 50)
    
    # Test instance ID - replace with actual instance
    test_instance = "i-1234567890abcdef0"
    
    tests = [
        {
            "name": "CloudWatch Metrics",
            "command": f"cloudwatch-metrics -i {test_instance} -m CPUUtilization,NetworkIn -t 24h"
        },
        {
            "name": "CloudTrail Events", 
            "command": f"cloudtrail-events -i {test_instance} -t 24h"
        },
        {
            "name": "Security Events",
            "command": f"security-events -i {test_instance} -t 24h"
        },
        {
            "name": "Configuration Changes",
            "command": f"config-changes -i {test_instance} -t 24h"
        },
        {
            "name": "Vulnerability Scan",
            "command": f"vulnerabilities -i {test_instance} -s all"
        }
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print(f"\n🔍 Testing: {test['name']}")
        print("-" * 30)
        
        returncode, stdout, stderr = run_cli_command(test['command'])
        
        if returncode == 0:
            print(f"✅ {test['name']} - PASSED")
            if stdout:
                # Show first few lines of output
                lines = stdout.strip().split('\n')[:3]
                for line in lines:
                    print(f"   {line}")
            passed += 1
        else:
            print(f"❌ {test['name']} - FAILED")
            if stderr:
                print(f"   Error: {stderr.strip()}")
            if stdout:
                print(f"   Output: {stdout.strip()}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All core MCP functions working!")
    else:
        print("⚠️  Some functions need attention")

def test_interactive_mode():
    """Test interactive mode with sample commands"""
    print("\n🎮 Testing Interactive Mode")
    print("=" * 30)
    
    sample_commands = [
        "scan all instances",
        f"analyze vulnerabilities for i-1234567890abcdef0",
        f"get cloudwatch metrics for i-1234567890abcdef0",
        "help"
    ]
    
    print("Sample commands to test in interactive mode:")
    for cmd in sample_commands:
        print(f"  • {cmd}")
    
    print("\nTo test interactive mode manually:")
    print("python cli/sre_cli.py interactive")

if __name__ == "__main__":
    print("SRE Operations Assistant - Core Function Tests")
    print("=" * 60)
    
    # Change to project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    test_core_functions()
    test_interactive_mode()
    
    print("\n" + "=" * 60)
    print("Testing complete!")