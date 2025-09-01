#!/usr/bin/env python3
"""Regression tests for Slack bot functionality"""

import pytest
import requests
import json
import time

class TestSlackBotRegression:
    """Regression tests for Slack bot endpoints"""
    
    @pytest.fixture
    def mcp_server_url(self):
        """MCP server URL for testing"""
        return "https://sre-ops.threemoonsnetwork.net"
    
    def test_vulnerability_scan_endpoint(self, mcp_server_url):
        """Test vulnerability scan endpoint (used by Slack bot)"""
        payload = {
            "method": "get_inspector_findings",
            "params": {"instance_id": "test-instance", "severity": "all"}
        }
        
        response = requests.post(
            f"{mcp_server_url}/mcp",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'total_count' in data
        assert 'summary' in data
        # Should not have old error messages
        assert 'requires a single instance' not in str(data)
    
    def test_patch_compliance_endpoint(self, mcp_server_url):
        """Test patch compliance endpoint (used by Slack bot)"""
        payload = {
            "method": "check_patch_compliance",
            "params": {"instance_ids": []}
        }
        
        response = requests.post(
            f"{mcp_server_url}/mcp",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should return valid response structure
        assert isinstance(data, dict)
    
    def test_metrics_endpoint_single_instance(self, mcp_server_url):
        """Test metrics endpoint for single instance (Slack bot usage)"""
        payload = {
            "method": "get_ec2_cloudwatch_metrics",
            "params": {
                "instance_id": "test-instance",
                "metric_names": ["CPUUtilization"],
                "time_range": "1h"
            }
        }
        
        response = requests.post(
            f"{mcp_server_url}/mcp",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should handle the request without crashing
        assert isinstance(data, dict)
    
    def test_metrics_endpoint_all_instances(self, mcp_server_url):
        """Test metrics endpoint for all instances"""
        payload = {
            "method": "get_ec2_cloudwatch_metrics",
            "params": {
                "metric_names": ["CPUUtilization"],
                "time_range": "1h"
            }
        }
        
        response = requests.post(
            f"{mcp_server_url}/mcp",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should handle request for all instances
        assert isinstance(data, dict)
    
    def test_health_endpoint_stability(self, mcp_server_url):
        """Test health endpoint remains stable"""
        response = requests.get(f"{mcp_server_url}/health", timeout=10)
        
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
    
    def test_invalid_method_handling(self, mcp_server_url):
        """Test server handles invalid methods gracefully"""
        payload = {
            "method": "invalid_method_xyz",
            "params": {}
        }
        
        response = requests.post(
            f"{mcp_server_url}/mcp",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        
        # Should handle gracefully, not crash
        assert response.status_code in [200, 400, 404, 500]
    
    def test_malformed_request_handling(self, mcp_server_url):
        """Test server handles malformed requests"""
        response = requests.post(
            f"{mcp_server_url}/mcp",
            data="invalid json",
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        # Should handle gracefully
        assert response.status_code in [400, 422, 500]

class TestSlackBotStability:
    """Test Slack bot stability under various conditions"""
    
    @pytest.fixture
    def mcp_server_url(self):
        return "https://sre-ops.threemoonsnetwork.net"
    
    def test_concurrent_slack_requests(self, mcp_server_url):
        """Test handling of concurrent Slack bot requests"""
        import concurrent.futures
        
        def make_vuln_request():
            payload = {
                "method": "get_inspector_findings",
                "params": {"severity": "all"}
            }
            response = requests.post(
                f"{mcp_server_url}/mcp",
                json=payload,
                timeout=30
            )
            return response.status_code
        
        # Simulate 3 concurrent Slack commands
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_vuln_request) for _ in range(3)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All should succeed
        assert all(status == 200 for status in results)
    
    def test_large_response_handling(self, mcp_server_url):
        """Test handling of potentially large responses"""
        payload = {
            "method": "generate_vulnerability_report",
            "params": {
                "instance_ids": [],
                "format": "summary"
            }
        }
        
        response = requests.post(
            f"{mcp_server_url}/mcp",
            json=payload,
            timeout=60  # Longer timeout for potentially large response
        )
        
        assert response.status_code == 200
        # Should not timeout or crash
        data = response.json()
        assert isinstance(data, dict)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])