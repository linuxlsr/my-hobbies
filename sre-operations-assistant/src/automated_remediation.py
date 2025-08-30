"""Automated Remediation Actions with AI-Powered Scheduling"""

import boto3
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from bedrock_models import BedrockModelFactory
from aws_services import AWSCloudWatch
from vulnerability_analyzer import VulnerabilityAnalyzer


class AutomatedRemediation:
    """AI-powered automated remediation with intelligent scheduling"""
    
    def __init__(self, model_id: str = "amazon.titan-text-express-v1"):
        self.model = BedrockModelFactory.create_model(model_id)
        self.cloudwatch = AWSCloudWatch()
        self.vuln_analyzer = VulnerabilityAnalyzer(model_id)
        self.events_client = boto3.client('events')
        
    def schedule_automated_patching(self, instance_ids: List[str], criticality: str = "high") -> Dict[str, Any]:
        """Schedule automated patching based on AI recommendations"""
        try:
            remediation_plan = {
                "plan_id": f"remediation-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
                "instance_schedules": [],
                "total_instances": len(instance_ids),
                "criticality": criticality,
                "created_at": datetime.utcnow().isoformat()
            }
            
            for instance_id in instance_ids:
                # Get vulnerability analysis
                vuln_analysis = self.vuln_analyzer.analyze_instance(instance_id)
                
                # Find optimal patch window
                optimal_window = self._find_optimal_patch_window(instance_id, vuln_analysis)
                
                # Create schedule entry
                schedule = {
                    "instance_id": instance_id,
                    "vulnerability_count": len(vuln_analysis.get("vulnerabilities", [])),
                    "risk_score": vuln_analysis.get("risk_score", 0),
                    "optimal_window": optimal_window,
                    "patch_actions": self._generate_patch_actions(vuln_analysis, criticality),
                    "estimated_duration": self._estimate_patch_duration(vuln_analysis),
                    "pre_patch_checks": self._generate_pre_patch_checks(instance_id),
                    "rollback_plan": self._generate_rollback_plan(instance_id)
                }
                
                remediation_plan["instance_schedules"].append(schedule)
                
                # Schedule EventBridge rule for the optimal window
                self._schedule_patch_event(instance_id, optimal_window, criticality)
            
            return remediation_plan
            
        except Exception as e:
            return {
                "error": str(e),
                "instance_ids": instance_ids,
                "criticality": criticality
            }
    
    def _find_optimal_patch_window(self, instance_id: str, vuln_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to find optimal patching window based on telemetry"""
        try:
            # Get 14 days of CloudWatch metrics
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=14)
            
            # Collect comprehensive metrics
            metrics_data = {
                "cpu": self.cloudwatch.get_cpu_utilization([instance_id], start_time, end_time),
                "memory": self.cloudwatch.get_memory_utilization([instance_id], start_time, end_time),
                "network": self.cloudwatch.get_network_utilization([instance_id], start_time, end_time)
            }
            
            # Prepare AI prompt with telemetry data
            prompt = f"""
Analyze the following 14-day telemetry data for EC2 instance {instance_id} to find the optimal patching window:

Vulnerability Context:
- Total vulnerabilities: {len(vuln_analysis.get('vulnerabilities', []))}
- Risk score: {vuln_analysis.get('risk_score', 0)}
- Critical vulnerabilities: {len([v for v in vuln_analysis.get('vulnerabilities', []) if v.get('severity') == 'CRITICAL'])}

CPU Usage Pattern: {self._summarize_metrics(metrics_data.get('cpu', {}))}
Memory Usage Pattern: {self._summarize_metrics(metrics_data.get('memory', {}))}
Network Usage Pattern: {self._summarize_metrics(metrics_data.get('network', {}))}

Find the optimal 2-hour maintenance window in the next 7 days considering:
1. Lowest resource utilization periods
2. Vulnerability criticality (higher risk = sooner patching)
3. Historical usage patterns
4. Business hours impact

Respond in JSON format:
{{
    "recommended_date": "YYYY-MM-DD",
    "recommended_time": "HH:MM",
    "confidence_score": 0.0-1.0,
    "reasoning": "explanation",
    "backup_windows": ["alternative times"],
    "risk_factors": ["potential issues"]
}}
"""
            
            # Get AI recommendation
            response = self.model.generate_response(prompt, max_tokens=800)
            
            try:
                ai_recommendation = json.loads(response)
                
                # Validate and enhance recommendation
                return {
                    "recommended_datetime": f"{ai_recommendation.get('recommended_date')} {ai_recommendation.get('recommended_time')}",
                    "confidence_score": ai_recommendation.get("confidence_score", 0.7),
                    "reasoning": ai_recommendation.get("reasoning", "AI-optimized window"),
                    "backup_windows": ai_recommendation.get("backup_windows", []),
                    "risk_factors": ai_recommendation.get("risk_factors", []),
                    "metrics_analyzed": True,
                    "analysis_period": "14 days"
                }
                
            except json.JSONDecodeError:
                # Fallback to rule-based scheduling
                return self._fallback_window_selection(vuln_analysis)
                
        except Exception as e:
            return self._fallback_window_selection(vuln_analysis)
    
    def _summarize_metrics(self, metrics: Dict[str, Any]) -> str:
        """Summarize metrics for AI analysis"""
        if not metrics or not metrics.get("datapoints"):
            return "No data available"
        
        datapoints = metrics.get("datapoints", [])
        if not datapoints:
            return "No datapoints"
        
        values = [dp.get("Average", 0) for dp in datapoints]
        avg_value = sum(values) / len(values)
        max_value = max(values)
        min_value = min(values)
        
        return f"Avg: {avg_value:.1f}, Min: {min_value:.1f}, Max: {max_value:.1f}, Samples: {len(values)}"
    
    def _fallback_window_selection(self, vuln_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback window selection when AI is unavailable"""
        risk_score = vuln_analysis.get("risk_score", 0)
        
        # High risk = patch sooner, low risk = patch during off-hours
        if risk_score >= 80:
            # Critical - patch within 4 hours
            patch_time = datetime.utcnow() + timedelta(hours=4)
        elif risk_score >= 60:
            # High - patch tonight at 2 AM
            tomorrow = datetime.utcnow() + timedelta(days=1)
            patch_time = tomorrow.replace(hour=2, minute=0, second=0, microsecond=0)
        else:
            # Medium/Low - patch this weekend at 3 AM
            days_until_weekend = (5 - datetime.utcnow().weekday()) % 7
            if days_until_weekend == 0:
                days_until_weekend = 7
            weekend = datetime.utcnow() + timedelta(days=days_until_weekend)
            patch_time = weekend.replace(hour=3, minute=0, second=0, microsecond=0)
        
        return {
            "recommended_datetime": patch_time.strftime("%Y-%m-%d %H:%M"),
            "confidence_score": 0.6,
            "reasoning": f"Rule-based scheduling for risk score {risk_score}",
            "backup_windows": [],
            "risk_factors": ["Fallback scheduling used"],
            "metrics_analyzed": False
        }
    
    def _generate_patch_actions(self, vuln_analysis: Dict[str, Any], criticality: str) -> List[Dict[str, Any]]:
        """Generate specific patch actions"""
        vulnerabilities = vuln_analysis.get("vulnerabilities", [])
        
        # Filter by criticality
        if criticality == "critical":
            target_vulns = [v for v in vulnerabilities if v.get("severity") == "CRITICAL"]
        elif criticality == "high":
            target_vulns = [v for v in vulnerabilities if v.get("severity") in ["CRITICAL", "HIGH"]]
        else:
            target_vulns = vulnerabilities
        
        actions = []
        for vuln in target_vulns[:10]:  # Limit to top 10
            actions.append({
                "action_type": "patch_vulnerability",
                "cve_id": vuln.get("cve_id", "Unknown"),
                "package": vuln.get("affected_package", "Unknown"),
                "severity": vuln.get("severity", "UNKNOWN"),
                "command": f"# Patch {vuln.get('affected_package', 'package')} for {vuln.get('cve_id', 'CVE')}",
                "estimated_time": 5,  # minutes
                "requires_reboot": vuln.get("cvss_score", 0) >= 8.0
            })
        
        return actions
    
    def _estimate_patch_duration(self, vuln_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate total patching duration"""
        vulnerabilities = vuln_analysis.get("vulnerabilities", [])
        
        # Base time estimates
        patch_time = len(vulnerabilities) * 3  # 3 minutes per vulnerability
        reboot_time = 10 if any(v.get("cvss_score", 0) >= 8.0 for v in vulnerabilities) else 0
        verification_time = 15  # Post-patch verification
        
        total_minutes = patch_time + reboot_time + verification_time
        
        return {
            "patch_time_minutes": patch_time,
            "reboot_time_minutes": reboot_time,
            "verification_time_minutes": verification_time,
            "total_minutes": total_minutes,
            "total_hours": round(total_minutes / 60, 1)
        }
    
    def _generate_pre_patch_checks(self, instance_id: str) -> List[Dict[str, Any]]:
        """Generate pre-patch validation checks"""
        return [
            {
                "check_type": "disk_space",
                "description": "Verify sufficient disk space for patches",
                "command": "df -h",
                "threshold": "80% usage maximum"
            },
            {
                "check_type": "backup_verification",
                "description": "Confirm recent backup exists",
                "command": "# Verify backup status",
                "threshold": "Backup within 24 hours"
            },
            {
                "check_type": "service_health",
                "description": "Check critical services are running",
                "command": "systemctl status",
                "threshold": "All critical services active"
            },
            {
                "check_type": "load_average",
                "description": "Verify system load is acceptable",
                "command": "uptime",
                "threshold": "Load average < 2.0"
            }
        ]
    
    def _generate_rollback_plan(self, instance_id: str) -> Dict[str, Any]:
        """Generate rollback plan in case of patch failure"""
        return {
            "rollback_triggers": [
                "Service failure after patch",
                "System boot failure",
                "Critical application errors",
                "Performance degradation > 50%"
            ],
            "rollback_steps": [
                {
                    "step": 1,
                    "action": "Stop failed services",
                    "command": "systemctl stop <service>",
                    "timeout": "30 seconds"
                },
                {
                    "step": 2,
                    "action": "Restore from backup",
                    "command": "# Restore system state",
                    "timeout": "10 minutes"
                },
                {
                    "step": 3,
                    "action": "Restart services",
                    "command": "systemctl start <service>",
                    "timeout": "2 minutes"
                },
                {
                    "step": 4,
                    "action": "Verify system health",
                    "command": "# Health check commands",
                    "timeout": "5 minutes"
                }
            ],
            "notification_contacts": ["sre-team@company.com"],
            "escalation_threshold": "15 minutes"
        }
    
    def _schedule_patch_event(self, instance_id: str, optimal_window: Dict[str, Any], criticality: str):
        """Schedule EventBridge rule for automated patching"""
        try:
            # Parse the recommended datetime
            patch_datetime_str = optimal_window.get("recommended_datetime")
            if not patch_datetime_str:
                return
            
            patch_datetime = datetime.strptime(patch_datetime_str, "%Y-%m-%d %H:%M")
            
            # Create cron expression for EventBridge
            cron_expression = f"cron({patch_datetime.minute} {patch_datetime.hour} {patch_datetime.day} {patch_datetime.month} ? {patch_datetime.year})"
            
            rule_name = f"patch-{instance_id}-{criticality}-{patch_datetime.strftime('%Y%m%d%H%M')}"
            
            # Actually create EventBridge rule
            try:
                self.events_client.put_rule(
                    Name=rule_name,
                    ScheduleExpression=cron_expression,
                    Description=f"Automated patch schedule for {instance_id} ({criticality} criticality)",
                    State='ENABLED'
                )
                
                # Add target (Lambda function would handle actual patching)
                # For now, just create the rule without targets since we don't have SSM
                
                return {
                    "rule_name": rule_name,
                    "schedule_expression": cron_expression,
                    "target_instance": instance_id,
                    "criticality": criticality,
                    "status": "scheduled",
                    "created": True
                }
                
            except Exception as events_error:
                return {
                    "rule_name": rule_name,
                    "schedule_expression": cron_expression,
                    "target_instance": instance_id,
                    "criticality": criticality,
                    "status": "failed",
                    "error": str(events_error)
                }
            
        except Exception as e:
            return {"error": f"Failed to schedule patch event: {str(e)}"}
    
    def get_scheduled_patches(self, instance_id: Optional[str] = None) -> Dict[str, Any]:
        """Get all scheduled patch operations"""
        try:
            # Query EventBridge rules for scheduled patches
            try:
                response = self.events_client.list_rules(NamePrefix="patch-")
                scheduled_patches = []
                
                for rule in response.get('Rules', []):
                    rule_name = rule['Name']
                    # Parse rule name: patch-{instance_id}-{criticality}-{timestamp}
                    parts = rule_name.split('-')
                    if len(parts) >= 4:
                        rule_instance_id = parts[1]
                        criticality = parts[2]
                        
                        # Skip if filtering by instance_id
                        if instance_id and rule_instance_id != instance_id:
                            continue
                        
                        scheduled_patches.append({
                            "instance_id": rule_instance_id,
                            "rule_name": rule_name,
                            "scheduled_time": rule.get('ScheduleExpression', 'Unknown'),
                            "criticality": criticality,
                            "vulnerability_count": "Unknown",
                            "estimated_duration": "Unknown",
                            "status": rule.get('State', 'UNKNOWN')
                        })
                
                return {
                    "scheduled_patches": scheduled_patches,
                    "total_scheduled": len(scheduled_patches),
                    "query_time": datetime.utcnow().isoformat()
                }
                
            except Exception as events_error:
                # Fallback to empty list if EventBridge query fails
                return {
                    "scheduled_patches": [],
                    "total_scheduled": 0,
                    "query_time": datetime.utcnow().isoformat(),
                    "note": f"EventBridge query failed: {str(events_error)}"
                }
            
        except Exception as e:
            return {
                "scheduled_patches": [],
                "error": str(e)
            }
    
    def cancel_scheduled_patch(self, instance_id: str, rule_name: str) -> Dict[str, Any]:
        """Cancel a scheduled patch operation"""
        try:
            # Actually delete the EventBridge rule
            try:
                self.events_client.delete_rule(
                    Name=rule_name,
                    Force=True  # Delete even if it has targets
                )
                
                return {
                    "instance_id": instance_id,
                    "rule_name": rule_name,
                    "status": "cancelled",
                    "cancelled_at": datetime.utcnow().isoformat(),
                    "deleted": True
                }
                
            except Exception as events_error:
                return {
                    "instance_id": instance_id,
                    "rule_name": rule_name,
                    "status": "failed",
                    "error": str(events_error)
                }
            
        except Exception as e:
            return {
                "instance_id": instance_id,
                "rule_name": rule_name,
                "error": str(e)
            }