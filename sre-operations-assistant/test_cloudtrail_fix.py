#!/usr/bin/env python3
"""Test CloudTrail fix locally"""

import requests
import sys

def test_cloudtrail_fix():
    """Test the CloudTrail parameter fix"""
    
    # Test against local server
    endpoint = "http://localhost:8000"
    test_instance = "i-02cda701eb446f378"
    
    print("🧪 Testing CloudTrail fix locally...")
    
    try:
        # Test health first
        health_response = requests.get(f"{endpoint}/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ Local server not running")
            return False
        
        print("✅ Local server healthy")
        
        # Test CloudTrail function
        response = requests.post(f"{endpoint}/mcp", json={
            "method": "analyze_cloudtrail_events",
            "params": {
                "instance_id": test_instance,
                "event_types": [],
                "time_range": "24h"
            }
        }, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if "error" in data:
                print(f"❌ Function error: {data['error']}")
                return False
            else:
                print("✅ CloudTrail function working")
                events = len(data.get('events', []))
                suspicious = len(data.get('suspicious_activity', []))
                print(f"   Events: {events}, Suspicious: {suspicious}")
                return True
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

if __name__ == "__main__":
    if test_cloudtrail_fix():
        print("\n🎉 CloudTrail fix verified locally!")
        print("Now deploy to ECS with: bash quick_deploy.sh")
    else:
        print("\n❌ Fix needs more work")
        sys.exit(1)