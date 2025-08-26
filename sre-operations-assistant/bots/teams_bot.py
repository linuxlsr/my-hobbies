"""Microsoft Teams Bot Integration for SRE Operations"""

import pymsteams
import os
from typing import Dict, Any


class SRETeamsBot:
    """Teams bot for SRE operations and alerts"""
    
    def __init__(self):
        self.webhook_url = os.environ.get("TEAMS_WEBHOOK_URL")
    
    def send_vulnerability_report(self, vulnerability_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send vulnerability report to Teams"""
        try:
            card = pymsteams.connectorcard(self.webhook_url)
            card.title("🔍 Vulnerability Assessment Report")
            card.color("0076D7")
            
            # Add summary section
            summary_section = pymsteams.cardsection()
            summary_section.activityTitle("Summary")
            summary_section.addFact("Total Instances", str(vulnerability_data.get('total_instances', 0)))
            summary_section.addFact("Critical Vulnerabilities", str(vulnerability_data.get('critical_count', 0)))
            summary_section.addFact("High Vulnerabilities", str(vulnerability_data.get('high_count', 0)))
            card.addSection(summary_section)
            
            # Add action buttons
            card.addLinkButton("View Full Report", "https://console.aws.amazon.com/inspector/")
            card.addLinkButton("Schedule Patches", "#")
            
            card.send()
            return {"status": "success"}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def send_patch_approval_request(self, patch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send patch approval request to Teams"""
        try:
            card = pymsteams.connectorcard(self.webhook_url)
            card.title("📋 Patch Approval Required")
            card.color("FF6D00")
            
            # Add patch details
            patch_section = pymsteams.cardsection()
            patch_section.activityTitle("Patch Details")
            patch_section.addFact("Instance ID", patch_data.get('instance_id', 'Unknown'))
            patch_section.addFact("Criticality", patch_data.get('criticality', 'High'))
            patch_section.addFact("Estimated Downtime", patch_data.get('downtime', '15 minutes'))
            patch_section.addFact("Optimal Window", patch_data.get('window', 'Tonight 2-4 AM'))
            card.addSection(patch_section)
            
            # Add approval actions
            card.addLinkButton("Approve Patch", f"#approve_{patch_data.get('patch_id')}")
            card.addLinkButton("Reschedule", f"#reschedule_{patch_data.get('patch_id')}")
            
            card.send()
            return {"status": "success"}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def send_critical_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send critical security alert to Teams"""
        try:
            card = pymsteams.connectorcard(self.webhook_url)
            card.title("🚨 CRITICAL SECURITY ALERT")
            card.color("D13438")
            
            # Add alert details
            alert_section = pymsteams.cardsection()
            alert_section.activityTitle("Alert Details")
            alert_section.addFact("Instance ID", alert_data.get('instance_id', 'Unknown'))
            alert_section.addFact("Vulnerability", alert_data.get('vulnerability', 'Unknown'))
            alert_section.addFact("CVSS Score", str(alert_data.get('cvss_score', 'N/A')))
            alert_section.addFact("Detected", alert_data.get('detected_time', 'Just now'))
            card.addSection(alert_section)
            
            # Add immediate actions
            card.addLinkButton("Emergency Patch", f"#emergency_{alert_data.get('alert_id')}")
            card.addLinkButton("Isolate Instance", f"#isolate_{alert_data.get('instance_id')}")
            
            card.send()
            return {"status": "success"}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}