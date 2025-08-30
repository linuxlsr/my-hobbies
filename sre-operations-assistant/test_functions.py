#!/usr/bin/env python3
"""Quick test of core MCP functions"""

import requests
import sys

def test_functions():
    # Try to connect to MCP server
    endpoints = [
        "http://localhost:8000",
        "http://127.0.0.1:8000"
        # Add your ALB URL here when testing ECS
    ]
    
    mcp_url = None
    for url in endpoints:
        try:
            response = requests.get(f"{url}/health", timeout=3)
            if response.status_code == 200:
                mcp_url = url
                print(f"✅ Connected to MCP server: {url}")
                break
        except:
            continue
    
    if not mcp_url:
        print("❌ MCP server not accessible")
        print("Make sure the server is running or update endpoints in this script")
        return
    
    # Test instance - replace with actual instance ID
    test_instance = "i-1234567890abcdef0"
    
    # Test core functions
    functions = [
        ("get_ec2_cloudwatch_metrics", {
            "instance_id": test_instance,
            "metric_names": ["CPUUtilization"],
            "time_range": "24h"
        }),
        ("analyze_cloudtrail_events", {
            "instance_id": test_instance,
            "event_types": [],
            "time_range": "24h"
        }),
        ("monitor_security_events", {
            "instance_ids": [test_instance],
            "time_range": "24h"
        }),
        ("analyze_configuration_changes", {
            "instance_ids": [test_instance],
            "time_range": "24h"
        }),
        ("get_inspector_findings", {
            "instance_id": test_instance,
            "severity": "all"
        })
    ]
    
    print("\n🧪 Testing Core MCP Functions:")
    print("=" * 40)
    
    for method, params in functions:
        try:
            response = requests.post(f"{mcp_url}/mcp", json={
                "method": method,
                "params": params
            }, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    print(f"⚠️  {method}: {data['error']}")
                else:
                    print(f"✅ {method}: Working")
            else:
                print(f"❌ {method}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {method}: {str(e)}")
    
    print("\n✨ Core function testing complete!")

if __name__ == "__main__":
    test_functions()