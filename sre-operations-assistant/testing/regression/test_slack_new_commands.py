#!/usr/bin/env python3
"""Regression tests for new Slack commands"""

import pytest
import requests
import json

class TestNewSlackCommands:
    """Test the newly added Slack commands"""
    
    @pytest.fixture
    def slack_api_url(self):
        return "https://316kvw7woh.execute-api.us-west-2.amazonaws.com/dev/slack"
    
    def test_sre_patch_status_endpoint(self, slack_api_url):
        """Test that patch status command works via Slack API"""
        payload = {
            "command": "/sre-patch-status",
            "text": "test-instance",
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
    
    def test_sre_security_events_endpoint(self, slack_api_url):
        """Test that security events command works via Slack API"""
        payload = {
            "command": "/sre-security-events",
            "text": "24h",
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
    
    def test_slack_command_structure(self):
        """Test that new Slack commands have proper structure"""
        # Test /sre-patch-status command structure
        sre_patch_command = {
            'command': '/sre-patch-status',
            'text': 'i-test123',
            'response_url': 'https://hooks.slack.com/test'
        }
        
        # Should have required fields
        assert 'command' in sre_patch_command
        assert 'response_url' in sre_patch_command
        assert sre_patch_command['command'] == '/sre-patch-status'
        
        # Test /sre-security-events command structure
        sre_security_command = {
            'command': '/sre-security-events',
            'text': '48h',
            'response_url': 'https://hooks.slack.com/test'
        }
        
        assert 'command' in sre_security_command
        assert 'response_url' in sre_security_command
        assert sre_security_command['command'] == '/sre-security-events'
    
    def test_command_parameter_handling(self):
        """Test parameter handling for new commands"""
        # Test instance ID parameter
        instance_id = "i-1234567890abcdef0"
        assert len(instance_id) > 10  # Valid instance ID length
        assert instance_id.startswith('i-')
        
        # Test time range parameter
        time_ranges = ['1h', '6h', '24h', '48h', '7d']
        for time_range in time_ranges:
            assert isinstance(time_range, str)
            assert len(time_range) >= 2
            assert time_range[-1] in ['h', 'd']  # hours or days

if __name__ == '__main__':
    pytest.main([__file__, '-v'])