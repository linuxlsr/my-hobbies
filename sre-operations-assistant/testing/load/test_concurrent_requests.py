#!/usr/bin/env python3
"""Load testing for SRE Operations Assistant"""

from locust import HttpUser, task, between
import json
import random

class SREOperationsUser(HttpUser):
    """Simulate user interactions with SRE Operations Assistant"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    host = "https://sre-ops.threemoonsnetwork.net"
    
    def on_start(self):
        """Setup for each user"""
        self.instance_ids = [
            "i-test001", "i-test002", "i-test003", 
            "i-test004", "i-test005"
        ]
        self.severities = ["all", "critical", "high", "medium"]
    
    @task(3)
    def vulnerability_scan(self):
        """Test vulnerability scanning endpoint"""
        payload = {
            "method": "get_inspector_findings",
            "params": {
                "instance_id": random.choice(self.instance_ids),
                "severity": random.choice(self.severities)
            }
        }
        
        with self.client.post(
            "/mcp",
            json=payload,
            headers={'Content-Type': 'application/json'},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'total_count' in data:
                        response.success()
                    else:
                        response.failure("Missing total_count in response")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(2)
    def patch_compliance_check(self):
        """Test patch compliance checking"""
        payload = {
            "method": "check_patch_compliance",
            "params": {
                "instance_ids": random.sample(self.instance_ids, 2)
            }
        }
        
        with self.client.post(
            "/mcp",
            json=payload,
            headers={'Content-Type': 'application/json'},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(2)
    def cloudwatch_metrics(self):
        """Test CloudWatch metrics collection"""
        payload = {
            "method": "get_ec2_cloudwatch_metrics",
            "params": {
                "instance_id": random.choice(self.instance_ids),
                "metric_names": ["CPUUtilization", "NetworkIn", "NetworkOut"],
                "time_range": random.choice(["1h", "6h", "24h"])
            }
        }
        
        with self.client.post(
            "/mcp",
            json=payload,
            headers={'Content-Type': 'application/json'},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(1)
    def security_events_monitoring(self):
        """Test security events monitoring"""
        payload = {
            "method": "monitor_security_events",
            "params": {
                "instance_ids": random.sample(self.instance_ids, 3),
                "time_range": "24h"
            }
        }
        
        with self.client.post(
            "/mcp",
            json=payload,
            headers={'Content-Type': 'application/json'},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(1)
    def health_check(self):
        """Test health check endpoint"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'status' in data:
                        response.success()
                    else:
                        response.failure("Missing status in health check")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON in health check")
            else:
                response.failure(f"Health check failed: HTTP {response.status_code}")

class SlackBotUser(HttpUser):
    """Simulate Slack bot interactions"""
    
    wait_time = between(2, 5)  # Slack commands are less frequent
    host = "https://sre-ops.threemoonsnetwork.net"
    
    @task
    def simulate_slack_vulnerability_check(self):
        """Simulate Slack vulnerability check command"""
        payload = {
            "method": "get_inspector_findings",
            "params": {
                "instance_id": f"centos-db-{random.randint(1, 10)}",
                "severity": "all"
            }
        }
        
        with self.client.post(
            "/mcp",
            json=payload,
            headers={'Content-Type': 'application/json'},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                # Simulate processing time for Slack response
                import time
                time.sleep(0.5)
                response.success()
            else:
                response.failure(f"Slack simulation failed: HTTP {response.status_code}")

if __name__ == "__main__":
    # Run load test from command line
    import os
    os.system("locust -f test_concurrent_requests.py --host=https://sre-ops.threemoonsnetwork.net")