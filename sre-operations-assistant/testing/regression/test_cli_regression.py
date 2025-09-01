#!/usr/bin/env python3
"""Regression tests for CLI functionality"""

import subprocess
import json
import time
import pytest
from pathlib import Path

class TestCLIRegression:
    """Regression tests for CLI commands"""
    
    @pytest.fixture
    def cli_path(self):
        """Path to CLI script"""
        return Path(__file__).parent.parent.parent / "cli" / "sre_cli.py"
    
    def run_cli_command(self, cli_path, command, timeout=30):
        """Run CLI command and return result"""
        try:
            result = subprocess.run([
                'python3', str(cli_path), 'ask', command
            ], capture_output=True, text=True, timeout=timeout)
            return {
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': 'Command timed out'
            }
    
    def test_cli_help_command(self, cli_path):
        """Test CLI help command works"""
        result = subprocess.run([
            'python3', str(cli_path), '--help'
        ], capture_output=True, text=True, timeout=10)
        
        assert result.returncode == 0
        assert 'SRE Operations Assistant' in result.stdout
    
    def test_cli_status_command(self, cli_path):
        """Test CLI status command"""
        result = self.run_cli_command(cli_path, "show status")
        
        # Should not crash
        assert result['returncode'] in [0, 1]  # May fail due to AWS permissions, but shouldn't crash
        assert 'Error:' not in result['stderr'] or 'timeout' in result['stderr'].lower()
    
    def test_cli_metrics_all_instances(self, cli_path):
        """Test CLI metrics command for all instances"""
        result = self.run_cli_command(cli_path, "show metrics")
        
        # Should not crash and should handle the request
        assert result['returncode'] in [0, 1]
        # Should not show the old error message
        assert "requires a single instance" not in result['stdout']
    
    def test_cli_metrics_specific_instance(self, cli_path):
        """Test CLI metrics command for specific instance"""
        result = self.run_cli_command(cli_path, "show cpu centos-db")
        
        # Should not crash
        assert result['returncode'] in [0, 1]
        assert 'Error:' not in result['stderr'] or 'timeout' in result['stderr'].lower()
    
    def test_cli_vulnerability_scan(self, cli_path):
        """Test CLI vulnerability scan"""
        result = self.run_cli_command(cli_path, "scan all vulnerabilities")
        
        # Should not crash
        assert result['returncode'] in [0, 1]
        assert 'Error:' not in result['stderr'] or 'timeout' in result['stderr'].lower()
    
    def test_cli_list_instances(self, cli_path):
        """Test CLI list instances command"""
        result = self.run_cli_command(cli_path, "list instances")
        
        # Should not crash
        assert result['returncode'] in [0, 1]
        assert 'Error:' not in result['stderr'] or 'timeout' in result['stderr'].lower()
    
    def test_cli_config_command(self, cli_path):
        """Test CLI config command"""
        result = subprocess.run([
            'python3', str(cli_path), 'config'
        ], capture_output=True, text=True, timeout=10)
        
        # Should show current configuration
        assert result.returncode == 0
        assert 'Configuration' in result.stdout or 'mode' in result.stdout

if __name__ == '__main__':
    pytest.main([__file__, '-v'])