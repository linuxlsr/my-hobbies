#!/usr/bin/env python3
"""Unit tests for automated patching functions"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

class TestAutomatedPatching:
    """Test automated patching functions"""
    
    @pytest.mark.asyncio
    async def test_execute_automated_patching_success(self):
        """Test successful automated patching execution"""
        # Mock the MCP server functions
        with patch('mcp_server.ssm') as mock_ssm, \
             patch('mcp_server._capture_system_state') as mock_capture, \
             patch('mcp_server._generate_rollback_commands') as mock_rollback_cmds:
            
            # Setup mocks
            mock_ssm.execute_patch_now.return_value = {"status": "success", "command_id": "cmd-123"}
            mock_capture.return_value = {"packages": {"captured": True}}
            mock_rollback_cmds.return_value = ["sudo systemctl stop app"]
            
            # Import after mocking
            from mcp_server import execute_automated_patching
            
            # Test execution
            result = await execute_automated_patching(
                instance_ids=["i-123", "i-456"],
                patch_level="high",
                rollback_enabled=True
            )
            
            # Verify results
            assert result["patch_status"]["total_instances"] == 2
            assert result["patch_status"]["success_rate"] == 100.0
            assert result["rollback_enabled"] is True
            assert len(result["rollback_plan"]) == 2
            assert result["patch_level"] == "high"
    
    @pytest.mark.asyncio
    async def test_execute_automated_patching_without_rollback(self):
        """Test automated patching without rollback"""
        with patch('mcp_server.ssm') as mock_ssm:
            mock_ssm.execute_patch_now.return_value = {"status": "success"}
            
            from mcp_server import execute_automated_patching
            
            result = await execute_automated_patching(
                instance_ids=["i-123"],
                patch_level="critical",
                rollback_enabled=False
            )
            
            assert result["rollback_enabled"] is False
            assert result["rollback_plan"] == []
            assert result["patch_level"] == "critical"
    
    @pytest.mark.asyncio
    async def test_rollback_changes_success(self):
        """Test successful rollback operation"""
        with patch('mcp_server._verify_system_health') as mock_verify:
            mock_verify.return_value = {
                "system_responsive": True,
                "health_score": 95
            }
            
            from mcp_server import rollback_changes
            
            result = await rollback_changes("i-123", "rollback-123")
            
            assert result["rollback_status"] == "success"
            assert result["instance_id"] == "i-123"
            assert result["rollback_id"] == "rollback-123"
            assert len(result["rollback_steps"]) == 4
            assert all(step["status"] == "completed" for step in result["rollback_steps"])
            assert result["restored_state"]["services_restored"] is True
    
    @pytest.mark.asyncio
    async def test_rollback_changes_failure(self):
        """Test rollback operation with failure"""
        with patch('mcp_server._verify_system_health') as mock_verify, \
             patch('asyncio.sleep', side_effect=Exception("Step failed")):
            
            mock_verify.return_value = {"system_responsive": False}
            
            from mcp_server import rollback_changes
            
            result = await rollback_changes("i-123", "rollback-123")
            
            assert result["rollback_status"] == "failed"
            assert any(step["status"] == "failed" for step in result["rollback_steps"])
    
    @pytest.mark.asyncio
    async def test_create_approval_workflow_auto_approve(self):
        """Test approval workflow with auto-approval"""
        from mcp_server import create_approval_workflow
        
        remediation_plan = {
            "instance_ids": ["i-123", "i-456"],
            "total_vulnerabilities": 3
        }
        
        result = await create_approval_workflow(remediation_plan, "medium")
        
        assert result["approval_status"] == "auto_approved"
        assert result["auto_approved"] is True
        assert result["ready_for_execution"] is True
        assert "workflow_id" in result
        assert result["criticality"] == "medium"
        assert "approval_url" in result
    
    @pytest.mark.asyncio
    async def test_create_approval_workflow_manual_approval(self):
        """Test approval workflow requiring manual approval"""
        from mcp_server import create_approval_workflow
        
        remediation_plan = {
            "instance_ids": ["i-123"],
            "total_vulnerabilities": 15  # Above auto-approve threshold
        }
        
        result = await create_approval_workflow(remediation_plan, "high")
        
        assert result["approval_status"] == "pending_approval"
        assert result["auto_approved"] is False
        assert result["ready_for_execution"] is False
        assert result["approvers_required"] == 1
        assert "approval_deadline" in result
    
    @pytest.mark.asyncio
    async def test_create_approval_workflow_critical(self):
        """Test approval workflow for critical vulnerabilities"""
        from mcp_server import create_approval_workflow
        
        remediation_plan = {
            "instance_ids": ["i-123"],
            "total_vulnerabilities": 1
        }
        
        result = await create_approval_workflow(remediation_plan, "critical")
        
        # Critical always requires manual approval
        assert result["approval_status"] == "pending_approval"
        assert result["auto_approved"] is False
        assert result["approvers_required"] == 1
    
    @pytest.mark.asyncio
    async def test_capture_system_state(self):
        """Test system state capture"""
        from mcp_server import _capture_system_state
        
        result = await _capture_system_state("i-123")
        
        assert result["packages"]["captured"] is True
        assert result["services"]["captured"] is True
        assert result["configuration"]["captured"] is True
        assert "captured_at" in result
    
    @pytest.mark.asyncio
    async def test_generate_rollback_commands(self):
        """Test rollback command generation"""
        from mcp_server import _generate_rollback_commands
        
        commands = await _generate_rollback_commands("i-123")
        
        assert isinstance(commands, list)
        assert len(commands) > 0
        assert any("systemctl" in cmd for cmd in commands)
        assert any("rollback" in cmd for cmd in commands)
    
    @pytest.mark.asyncio
    async def test_verify_system_health(self):
        """Test system health verification"""
        from mcp_server import _verify_system_health
        
        result = await _verify_system_health("i-123")
        
        assert result["system_responsive"] is True
        assert result["services_running"] is True
        assert result["health_score"] == 95
        assert "verified_at" in result
    
    @pytest.mark.asyncio
    async def test_execute_automated_patching_error_handling(self):
        """Test error handling in automated patching"""
        with patch('mcp_server.ssm') as mock_ssm:
            mock_ssm.execute_patch_now.side_effect = Exception("Patching failed")
            
            from mcp_server import execute_automated_patching
            
            result = await execute_automated_patching(["i-123"])
            
            assert "error" in result
            assert result["patch_status"]["error"] == "Patching failed"
    
    @pytest.mark.asyncio
    async def test_create_approval_workflow_error_handling(self):
        """Test error handling in approval workflow creation"""
        from mcp_server import create_approval_workflow
        
        # Test with invalid remediation plan
        result = await create_approval_workflow(None, "high")
        
        assert result["approval_status"] == "error"
        assert "error" in result
        assert result["workflow_id"] is None

if __name__ == '__main__':
    pytest.main([__file__, '-v'])