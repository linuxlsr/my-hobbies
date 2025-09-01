#!/usr/bin/env python3
"""Basic framework tests to validate testing setup"""

import pytest
import json
import sys
import os

def test_python_version():
    """Test Python version compatibility"""
    assert sys.version_info >= (3, 8), "Python 3.8+ required"

def test_imports():
    """Test that required modules can be imported"""
    import boto3
    import pytest
    import json
    assert True

def test_mock_data_loading():
    """Test loading mock response data"""
    fixtures_path = os.path.join(os.path.dirname(__file__), '../fixtures/mock_responses.json')
    
    with open(fixtures_path, 'r') as f:
        mock_data = json.load(f)
    
    assert 'inspector_findings' in mock_data
    assert 'cloudwatch_metrics' in mock_data
    assert 'success_response' in mock_data['inspector_findings']

def test_basic_assertions():
    """Test basic assertion functionality"""
    assert 1 + 1 == 2
    assert "test" in "testing"
    assert len([1, 2, 3]) == 3

def test_mock_aws_response():
    """Test mock AWS response structure"""
    mock_response = {
        'findings': [
            {'severity': 'CRITICAL', 'title': 'Test vulnerability'}
        ],
        'total_count': 1,
        'critical_count': 1,
        'summary': 'Test summary'
    }
    
    assert mock_response['total_count'] == 1
    assert mock_response['critical_count'] == 1
    assert len(mock_response['findings']) == 1

class TestFrameworkSetup:
    """Test framework setup and configuration"""
    
    def test_fixture_availability(self):
        """Test that fixture files are available"""
        fixtures_dir = os.path.join(os.path.dirname(__file__), '../fixtures')
        assert os.path.exists(fixtures_dir)
        
        mock_file = os.path.join(fixtures_dir, 'mock_responses.json')
        assert os.path.exists(mock_file)
    
    def test_directory_structure(self):
        """Test testing directory structure"""
        testing_dir = os.path.join(os.path.dirname(__file__), '..')
        
        expected_dirs = ['unit', 'integration', 'load', 'fixtures']
        for dir_name in expected_dirs:
            dir_path = os.path.join(testing_dir, dir_name)
            assert os.path.exists(dir_path), f"Directory {dir_name} should exist"
    
    def test_requirements_file(self):
        """Test that requirements file exists and is readable"""
        req_file = os.path.join(os.path.dirname(__file__), '../requirements.txt')
        assert os.path.exists(req_file)
        
        with open(req_file, 'r') as f:
            content = f.read()
            assert 'pytest' in content
            assert 'boto3' in content

if __name__ == '__main__':
    pytest.main([__file__, '-v'])