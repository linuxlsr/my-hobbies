#!/usr/bin/env python3
"""Debug what methods are available on ECS server"""

import requests

def debug_ecs_methods():
    """Test what methods work on ECS vs local"""
    
    endpoints = {
        "Local": "http://localhost:8000",
        "ECS": "http://sre-ops-assistant-alb-942046254.us-west-2.elb.amazonaws.com"
    }
    
    # Test methods - old vs new
    test_methods = [
        # Old methods that should work
        ("get_inspector_findings", {"instance_id": "i-02cda701eb446f378", "severity": "all"}),
        ("analyze_optimal_patch_window", {"instance_id": "i-02cda701eb446f378", "days_ahead": 7}),
        ("check_patch_compliance", {"instance_ids": ["i-02cda701eb446f378"]}),
        
        # New methods that might not be deployed
        ("get_ec2_cloudwatch_metrics", {"instance_id": "i-02cda701eb446f378", "metric_names": ["CPUUtilization"], "time_range": "24h"}),
        ("analyze_cloudtrail_events", {"instance_id": "i-02cda701eb446f378", "event_types": [], "time_range": "24h"}),
    ]
    
    for endpoint_name, endpoint_url in endpoints.items():
        print(f"\n🔍 Testing {endpoint_name}: {endpoint_url}")
        print("-" * 50)
        
        # Test health first
        try:
            health = requests.get(f"{endpoint_url}/health", timeout=5)
            if health.status_code == 200:
                print("✅ Health check passed")
            else:
                print(f"❌ Health check failed: {health.status_code}")
                continue
        except Exception as e:
            print(f"❌ Cannot connect: {e}")
            continue
        
        # Test each method
        for method_name, params in test_methods:
            try:
                response = requests.post(f"{endpoint_url}/mcp", json={
                    "method": method_name,
                    "params": params
                }, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    if "error" in data:
                        print(f"⚠️  {method_name}: Function error")
                    else:
                        print(f"✅ {method_name}: Working")
                elif response.status_code == 400:
                    print(f"❌ {method_name}: Method not found (400)")
                else:
                    print(f"❌ {method_name}: HTTP {response.status_code}")
            except Exception as e:
                print(f"❌ {method_name}: {str(e)}")

if __name__ == "__main__":
    debug_ecs_methods()