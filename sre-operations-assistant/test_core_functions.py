#!/usr/bin/env python3
"""Test script for core MCP functions"""

import asyncio
import requests
import json

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_INSTANCE_ID = "i-1234567890abcdef0"  # Replace with actual instance ID

async def test_core_mcp_functions():
    """Test all core MCP functions"""
    
    test_cases = [
        {
            "name": "get_ec2_cloudwatch_metrics",
            "method": "get_ec2_cloudwatch_metrics",
            "params": {
                "instance_id": TEST_INSTANCE_ID,
                "metric_names": ["CPUUtilization", "NetworkIn"],
                "time_range": "24h"
            }
        },
        {
            "name": "analyze_cloudtrail_events", 
            "method": "analyze_cloudtrail_events",
            "params": {
                "instance_id": TEST_INSTANCE_ID,
                "event_types": ["RunInstances", "StopInstances"],
                "time_range": "24h"
            }
        },
        {
            "name": "monitor_security_events",
            "method": "monitor_security_events", 
            "params": {
                "instance_ids": [TEST_INSTANCE_ID],
                "event_types": ["login", "privilege_escalation"],
                "time_range": "24h"
            }
        },
        {
            "name": "analyze_configuration_changes",
            "method": "analyze_configuration_changes",
            "params": {
                "instance_ids": [TEST_INSTANCE_ID],
                "time_range": "24h"
            }
        }
    ]
    
    print("Testing Core MCP Functions")
    print("=" * 50)
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        print("-" * 30)
        
        try:
            response = requests.post(
                f"{BASE_URL}/mcp",
                json={
                    "method": test_case["method"],
                    "params": test_case["params"]
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ SUCCESS: {test_case['name']}")
                
                # Print key metrics from response
                if "error" in result:
                    print(f"   Error: {result['error']}")
                elif test_case["method"] == "get_ec2_cloudwatch_metrics":
                    metrics_count = len(result.get("metrics", {}))
                    anomalies_count = len(result.get("anomalies", []))
                    print(f"   Metrics collected: {metrics_count}")
                    print(f"   Anomalies detected: {anomalies_count}")
                elif test_case["method"] == "analyze_cloudtrail_events":
                    events_count = len(result.get("events", []))
                    security_events = len(result.get("security_events", []))
                    suspicious = len(result.get("suspicious_activity", []))
                    print(f"   Total events: {events_count}")
                    print(f"   Security events: {security_events}")
                    print(f"   Suspicious activity: {suspicious}")
                elif test_case["method"] == "monitor_security_events":
                    alerts_count = len(result.get("alerts", []))
                    instances_count = result.get("total_instances", 0)
                    print(f"   Instances monitored: {instances_count}")
                    print(f"   Security alerts: {alerts_count}")
                elif test_case["method"] == "analyze_configuration_changes":
                    changes_count = result.get("total_changes", 0)
                    compliance = result.get("compliance_status", "unknown")
                    print(f"   Configuration changes: {changes_count}")
                    print(f"   Compliance status: {compliance}")
                    
            else:
                print(f"❌ FAILED: {test_case['name']} - HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ CONNECTION ERROR: {test_case['name']}")
            print(f"   Error: {str(e)}")
        except Exception as e:
            print(f"❌ UNEXPECTED ERROR: {test_case['name']}")
            print(f"   Error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("Core MCP Functions Test Complete")

def test_health_endpoint():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint working")
            return True
        else:
            print(f"❌ Health endpoint failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {str(e)}")
        return False

if __name__ == "__main__":
    print("SRE Operations Assistant - Core Functions Test")
    print("=" * 60)
    
    # Test health first
    if test_health_endpoint():
        # Run core function tests
        asyncio.run(test_core_mcp_functions())
    else:
        print("Server not responding. Please start the MCP server first:")
        print("cd src && python mcp_server.py")