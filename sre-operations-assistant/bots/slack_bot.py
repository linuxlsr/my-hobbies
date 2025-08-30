"""Slack Bot Integration for SRE Operations"""

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import boto3
import json
from typing import Dict, Any


class SRESlackBot:
    """Slack bot for SRE operations and alerts"""
    
    def __init__(self):
        # Get token from Secrets Manager
        secrets_client = boto3.client('secretsmanager')
        try:
            response = secrets_client.get_secret_value(SecretId='sre-ops-assistant/sre-slack-token')
            token = response['SecretString']
        except Exception:
            token = None
        
        self.client = WebClient(token=token) if token else None
    
    def handle_vulnerability_check(self, channel: str, instance_id: str = None) -> Dict[str, Any]:
        """Handle /sre-vuln-check command"""
        try:
            import requests
            
            # Get MCP server endpoint from environment or use ALB
            import os
            mcp_url = os.environ.get('MCP_SERVER_URL', 'http://sre-ops-assistant-alb-942046254.us-west-2.elb.amazonaws.com')
            
            # Call MCP server
            response = requests.post(f"{mcp_url}/mcp", json={
                "method": "get_inspector_findings",
                "params": {"instance_id": instance_id, "severity": "all"}
            }, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                summary = data.get('summary', 'No data')
                critical = data.get('critical_count', 0)
                high = data.get('high_count', 0)
                total = data.get('total_count', 0)
                
                slack_response = {
                    "text": f"🔍 Vulnerability Check Results",
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Instance:* {instance_id or 'All instances'}\n*Summary:* {summary}\n*Critical:* {critical} | *High:* {high} | *Total:* {total}"
                            }
                        }
                    ]
                }
            else:
                slack_response = {
                    "text": f"❌ Error checking vulnerabilities: {response.status_code}"
                }
            
            if self.client:
                self.client.chat_postMessage(channel=channel, **slack_response)
            return {"status": "success"}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def handle_patch_status(self, channel: str, instance_id: str = None) -> Dict[str, Any]:
        """Handle /sre-patch-status command"""
        try:
            import requests
            import os
            
            mcp_url = os.environ.get('MCP_SERVER_URL', 'http://sre-ops-assistant-alb-942046254.us-west-2.elb.amazonaws.com')
            
            # Call MCP server for patch status
            response = requests.post(f"{mcp_url}/mcp", json={
                "method": "check_patch_compliance",
                "params": {"instance_ids": [instance_id] if instance_id else []}
            }, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    if instance_id:
                        compliance_data = data.get('compliance_data', {})
                        instance_data = compliance_data.get(instance_id, {})
                        compliance_status = instance_data.get('compliance_status', 'unknown')
                        missing_count = instance_data.get('missing_count', 0)
                        installed_count = instance_data.get('installed_count', 0)
                        
                        slack_response = {
                            "text": "📋 Patch Status Report",
                            "blocks": [
                                {
                                    "type": "section",
                                    "text": {
                                        "type": "mrkdwn",
                                        "text": f"*Instance:* {instance_id}\n*Compliance:* {compliance_status}\n*Missing:* {missing_count} | *Installed:* {installed_count}"
                                    }
                                }
                            ]
                        }
                    else:
                        summary = data.get('summary', {})
                        slack_response = {
                            "text": "📋 Patch Status Summary",
                            "blocks": [
                                {
                                    "type": "section",
                                    "text": {
                                        "type": "mrkdwn",
                                        "text": f"*Total Instances:* {summary.get('total_instances', 0)}\n*Compliant:* {summary.get('compliant_count', 0)} | *Non-compliant:* {summary.get('non_compliant_count', 0)}"
                                    }
                                }
                            ]
                        }
                else:
                    slack_response = {
                        "text": f"❌ Patch status check failed: {data.get('error', 'Unknown error')}"
                    }
            else:
                slack_response = {
                    "text": f"❌ Error checking patch status: {response.status_code}"
                }
            
            if self.client:
                self.client.chat_postMessage(channel=channel, **slack_response)
            return {"status": "success"}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def handle_patch_now(self, channel: str, instance_id: str) -> Dict[str, Any]:
        """Handle /sre-patch-now command"""
        try:
            import requests
            import os
            
            if not instance_id:
                slack_response = {
                    "text": "❌ Instance ID required for patching. Usage: /sre-patch-now i-1234567890abcdef0"
                }
                if self.client:
                    self.client.chat_postMessage(channel=channel, **slack_response)
                return {"status": "error", "error": "Instance ID required"}
            
            mcp_url = os.environ.get('MCP_SERVER_URL', 'http://sre-ops-assistant-alb-942046254.us-west-2.elb.amazonaws.com')
            
            # Call MCP server for patch execution
            response = requests.post(f"{mcp_url}/mcp", json={
                "method": "execute_patch_now",
                "params": {"instance_ids": [instance_id], "patch_level": "non_critical"}
            }, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    slack_response = {
                        "text": "🔧 Patch Execution Started",
                        "blocks": [
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": f"*Instance:* {instance_id}\n*Command ID:* {data.get('command_id')}\n*Status:* {data.get('message')}"
                                }
                            }
                        ]
                    }
                else:
                    slack_response = {
                        "text": f"❌ Patch execution failed: {data.get('error', 'Unknown error')}"
                    }
            else:
                slack_response = {
                    "text": f"❌ Error executing patch: {response.status_code}"
                }
            
            if self.client:
                self.client.chat_postMessage(channel=channel, **slack_response)
            return {"status": "success"}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def send_critical_alert(self, channel: str, vulnerability: Dict[str, Any]) -> Dict[str, Any]:
        """Send critical vulnerability alert"""
        try:
            response = {
                "text": "🚨 CRITICAL VULNERABILITY DETECTED",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "🚨 Critical Vulnerability Alert"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Instance:* {vulnerability.get('instance_id', 'Unknown')}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Severity:* {vulnerability.get('severity', 'Critical')}"
                            }
                        ]
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Schedule Patch"
                                },
                                "style": "primary",
                                "action_id": "schedule_patch"
                            },
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "View Details"
                                },
                                "action_id": "view_details"
                            }
                        ]
                    }
                ]
            }
            
            self.client.chat_postMessage(channel=channel, **response)
            return {"status": "success"}
            
        except SlackApiError as e:
            return {"status": "error", "error": str(e)}