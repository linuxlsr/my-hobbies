#!/usr/bin/env python3
"""Unit tests for MCP functions"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from mcp_server import AWSInspector, AWSCloudWatch

class TestAWSInspector:
    """Test AWS Inspector integration"""
    
    @patch('boto3.client')
    def test_get_findings_success(self, mock_boto3):
        """Test successful vulnerability findings retrieval"""
        # Mock Inspector client
        mock_client = Mock()
        mock_boto3.return_value = mock_client
        
        # Mock response
        mock_client.list_findings.return_value = {
            'findings': [
                {'severity': 'CRITICAL', 'title': 'Test Critical Vuln'},
                {'severity': 'HIGH', 'title': 'Test High Vuln'},
                {'severity': 'MEDIUM', 'title': 'Test Medium Vuln'}
            ],
            'nextToken': None
        }
        
        inspector = AWSInspector()
        result = inspector.get_findings(['i-test123'], 'all')
        
        assert result['total_count'] == 3
        assert result['critical_count'] == 1
        assert result['high_count'] == 1
        assert result['medium_count'] == 1
        assert 'Found 3 vulnerabilities' in result['summary']
    
    @patch('boto3.client')
    def test_get_findings_pagination(self, mock_boto3):
        """Test pagination handling"""
        mock_client = Mock()
        mock_boto3.return_value = mock_client
        
        # Mock paginated responses
        mock_client.list_findings.side_effect = [
            {
                'findings': [{'severity': 'CRITICAL', 'title': 'Vuln 1'}],
                'nextToken': 'token123'
            },
            {
                'findings': [{'severity': 'HIGH', 'title': 'Vuln 2'}],
                'nextToken': None
            }
        ]
        
        inspector = AWSInspector()
        result = inspector.get_findings(['i-test123'], 'all')
        
        assert result['total_count'] == 2
        assert mock_client.list_findings.call_count == 2
    
    @patch('boto3.client')
    def test_get_findings_error_handling(self, mock_boto3):
        """Test error handling"""
        mock_client = Mock()
        mock_boto3.return_value = mock_client
        mock_client.list_findings.side_effect = Exception("API Error")
        
        inspector = AWSInspector()
        result = inspector.get_findings(['i-test123'], 'all')
        
        assert result['total_count'] == 0
        assert 'error' in result
        assert 'API Error' in result['error']

class TestAWSCloudWatch:
    """Test AWS CloudWatch integration"""
    
    @patch('boto3.client')
    def test_get_metrics_success(self, mock_boto3):
        """Test successful metrics retrieval"""
        mock_client = Mock()
        mock_boto3.return_value = mock_client
        
        # Mock CloudWatch response
        mock_client.get_metric_statistics.return_value = {
            'Datapoints': [
                {'Timestamp': '2025-01-01T00:00:00Z', 'Average': 50.0, 'Maximum': 75.0},
                {'Timestamp': '2025-01-01T00:05:00Z', 'Average': 60.0, 'Maximum': 80.0}
            ]
        }
        
        cloudwatch = AWSCloudWatch()
        result = cloudwatch.get_metrics('i-test123', ['CPUUtilization'], '1h')
        
        assert 'CPUUtilization' in result['metrics_data']
        assert len(result['metrics_data']['CPUUtilization']['datapoints']) == 2
        assert result['metrics_data']['CPUUtilization']['average'] == 55.0
    
    @patch('boto3.client')
    def test_get_metrics_no_data(self, mock_boto3):
        """Test handling of no metric data"""
        mock_client = Mock()
        mock_boto3.return_value = mock_client
        mock_client.get_metric_statistics.return_value = {'Datapoints': []}
        
        cloudwatch = AWSCloudWatch()
        result = cloudwatch.get_metrics('i-test123', ['CPUUtilization'], '1h')
        
        assert result['metrics_data']['CPUUtilization']['datapoints'] == []
        assert result['metrics_data']['CPUUtilization']['average'] == 0

class TestMCPServerEndpoints:
    """Test MCP server endpoint functions"""
    
    @pytest.mark.asyncio
    async def test_get_inspector_findings(self):
        """Test get_inspector_findings function"""
        with patch('src.mcp_server.AWSInspector') as mock_inspector_class:
            mock_inspector = Mock()
            mock_inspector_class.return_value = mock_inspector
            mock_inspector.get_findings.return_value = {
                'total_count': 5,
                'critical_count': 1,
                'summary': 'Test summary'
            }
            
            # Import after patching
            from mcp_server import get_inspector_findings
            
            result = get_inspector_findings('i-test123', 'all')
            
            assert result['total_count'] == 5
            assert result['critical_count'] == 1
            mock_inspector.get_findings.assert_called_once_with(['i-test123'], 'all')
    
    @pytest.mark.asyncio
    async def test_analyze_ec2_vulnerabilities(self):
        """Test analyze_ec2_vulnerabilities function"""
        with patch('src.mcp_server.AWSInspector') as mock_inspector_class:
            mock_inspector = Mock()
            mock_inspector_class.return_value = mock_inspector
            mock_inspector.get_findings.return_value = {
                'findings': [{'severity': 'CRITICAL', 'title': 'Test'}],
                'critical_count': 1,
                'total_count': 1
            }
            
            from mcp_server import analyze_ec2_vulnerabilities
            
            result = await analyze_ec2_vulnerabilities('i-test123')
            
            assert result['critical_count'] == 1
            assert result['total_count'] == 1

if __name__ == '__main__':
    pytest.main([__file__, '-v'])