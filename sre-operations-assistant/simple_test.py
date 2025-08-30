#!/usr/bin/env python3
import requests

# Test old method (should work)
print("Testing old method on ECS...")
response = requests.post("http://sre-ops-assistant-alb-942046254.us-west-2.elb.amazonaws.com/mcp", json={
    "method": "get_inspector_findings",
    "params": {"instance_id": "i-02cda701eb446f378", "severity": "all"}
}, timeout=30)
print(f"get_inspector_findings: {response.status_code}")

# Test new method (might not work)
print("Testing new method on ECS...")
response = requests.post("http://sre-ops-assistant-alb-942046254.us-west-2.elb.amazonaws.com/mcp", json={
    "method": "get_ec2_cloudwatch_metrics", 
    "params": {"instance_id": "i-02cda701eb446f378", "metric_names": ["CPUUtilization"], "time_range": "24h"}
}, timeout=30)
print(f"get_ec2_cloudwatch_metrics: {response.status_code}")
if response.status_code != 200:
    print(f"Response: {response.text}")