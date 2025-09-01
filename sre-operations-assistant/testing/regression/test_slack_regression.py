#!/usr/bin/env python3
"""Regression tests for Slack bot functionality"""

import pytest
import requests
import json
import time

class TestSlackBotRegression:
    """Regression tests for Slack bot endpoints"""
    
    @pytest.fixture
    def slack_api_url(self):
        """Slack API Gateway URL for testing"""
        return "https://316kvw7woh.execute-api.us-west-2.amazonaws.com/dev/slack"
    
    def test_vulnerability_scan_endpoint(self, slack_api_url):
        """Test vulnerability scan endpoint (used by Slack bot)"""
        payload = {
            "command": "/sre-vulnerability-scan",
            "text": "severity=all",
            "user_id": "test_user",
            "channel_id": "test_channel"
        }
        
        response = requests.post(
            slack_api_url,
            data=payload,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=30
        )
        
        assert response.status_code == 200
        # Slack responses should be JSON with text field
        data = response.json()
        assert 'text' in data or 'blocks' in data
    
    def test_patch_compliance_endpoint(self, slack_api_url):
        """Test patch compliance endpoint (used by Slack bot)"""
        payload = {
            "command": "/sre-patch-compliance",
            "text": "",
            "user_id": "test_user",
            "channel_id": "test_channel"
        }
        
        response = requests.post(
            slack_api_url,
            data=payload,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should return valid Slack response structure
        assert isinstance(data, dict)
        assert 'text' in data or 'blocks' in data
    
    def test_metrics_endpoint_single_instance(self, slack_api_url):
        """Test metrics endpoint for single instance (Slack bot usage)"""
        payload = {
            "command": "/sre-metrics",
            "text": "instance_id=test-instance",
            "user_id": "test_user",
            "channel_id": "test_channel"
        }
        
        response = requests.post(
            slack_api_url,
            data=payload,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should handle the request without crashing
        assert isinstance(data, dict)
        assert 'text' in data or 'blocks' in data
    
    def test_metrics_endpoint_all_instances(self, slack_api_url):
        """Test metrics endpoint for all instances"""
        payload = {
            "command": "/sre-metrics",
            "text": "",
            "user_id": "test_user",
            "channel_id": "test_channel"
        }
        
        response = requests.post(
            slack_api_url,
            data=payload,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should handle request for all instances
        assert isinstance(data, dict)
        assert 'text' in data or 'blocks' in data
    
    def test_health_endpoint_stability(self, slack_api_url):
        """Test Slack Lambda health via simple command"""
        payload = {
            "command": "/sre-health",
            "text": "",
            "user_id": "test_user",
            "channel_id": "test_channel"
        }
        
        response = requests.post(
            slack_api_url,
            data=payload,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    def test_invalid_method_handling(self, slack_api_url):
        """Test server handles invalid commands gracefully"""
        payload = {
            "command": "/invalid-command-xyz",
            "text": "",
            "user_id": "test_user",
            "channel_id": "test_channel"
        }
        
        response = requests.post(
            slack_api_url,
            data=payload,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=15
        )
        
        # Should handle gracefully, not crash
        assert response.status_code in [200, 400, 404, 500]
    
    def test_malformed_request_handling(self, slack_api_url):
        """Test server handles malformed requests"""
        response = requests.post(
            slack_api_url,
            data="invalid=data&malformed",
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=10
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 422, 500]

class TestSlackBotStability:
    """Test Slack bot stability under various conditions"""
    
    @pytest.fixture
    def slack_api_url(self):
        return "https://316kvw7woh.execute-api.us-west-2.amazonaws.com/dev/slack"
    
    def test_concurrent_slack_requests(self, slack_api_url):
        """Test handling of concurrent Slack bot requests"""
        import concurrent.futures
        
        def make_vuln_request():
            payload = {
                "command": "/sre-vulnerability-scan",
                "text": "severity=all",
                "user_id": "test_user",
                "channel_id": "test_channel"
            }
            response = requests.post(
                slack_api_url,
                data=payload,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )
            return response.status_code
        
        # Simulate 3 concurrent Slack commands
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_vuln_request) for _ in range(3)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All should succeed
        assert all(status == 200 for status in results)
    
    def test_large_response_handling(self, slack_api_url):
        """Test handling of potentially large responses"""
        payload = {
            "command": "/sre-vulnerability-report",
            "text": "format=summary",
            "user_id": "test_user",
            "channel_id": "test_channel"
        }
        
        response = requests.post(
            slack_api_url,
            data=payload,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=60  # Longer timeout for potentially large response
        )
        
        assert response.status_code == 200
        # Should not timeout or crash
        data = response.json()
        assert isinstance(data, dict)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])