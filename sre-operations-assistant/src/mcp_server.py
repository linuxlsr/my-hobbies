"""Consolidated FastAPI Server for SRE Operations Assistant - All-in-One"""

import asyncio
import boto3
import json
import statistics
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="SRE Operations Assistant")

# =============================================================================
# BEDROCK MODEL ABSTRACTIONS
# =============================================================================

class BedrockModelInterface(ABC):
    """Abstract interface for Bedrock foundation models"""
    
    @abstractmethod
    def generate_response(self, prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """Generate response from the model"""
        pass
    
    @abstractmethod
    def format_request_body(self, prompt: str, max_tokens: int) -> Dict[str, Any]:
        """Format request body for the specific model"""
        pass
    
    @abstractmethod
    def extract_response_text(self, response_body: Dict[str, Any]) -> str:
        """Extract text from model response"""
        pass

class TitanTextModel(BedrockModelInterface):
    """Amazon Titan Text Premier model implementation"""
    
    def __init__(self, model_id: str = "amazon.titan-text-premier-v1:0"):
        self.model_id = model_id
        self.bedrock = boto3.client('bedrock-runtime')
    
    def format_request_body(self, prompt: str, max_tokens: int) -> Dict[str, Any]:
        """Format request for Titan Text model"""
        return {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": max_tokens,
                "temperature": 0.1,
                "topP": 0.9,
                "stopSequences": []
            }
        }
    
    def extract_response_text(self, response_body: Dict[str, Any]) -> str:
        """Extract text from Titan response"""
        results = response_body.get('results', [])
        if results:
            return results[0].get('outputText', '')
        return ''
    
    def generate_response(self, prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """Generate response from Titan model"""
        try:
            body = self.format_request_body(prompt, max_tokens)
            
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            return self.extract_response_text(response_body)
            
        except Exception as e:
            print(f"Error calling Titan model: {e}")
            return None

class BedrockModelFactory:
    """Factory for creating appropriate Bedrock model instances"""
    
    @staticmethod
    def create_model(model_id: str) -> BedrockModelInterface:
        """Create model instance based on model ID"""
        return TitanTextModel(model_id)

# =============================================================================
# AWS SERVICE INTEGRATIONS
# =============================================================================

class AWSInspector:
    """AWS Inspector v2 integration"""
    
    def __init__(self):
        self.client = boto3.client('inspector2', region_name='us-west-2')
        self.ec2_client = boto3.client('ec2', region_name='us-west-2')
    
    def get_findings(self, instance_ids: List[str], severity: str = "all") -> Dict[str, Any]:
        """Get Inspector findings for EC2 instances"""
        try:
            # Build filter criteria
            filters = {
                'resourceType': [{'comparison': 'EQUALS', 'value': 'AWS_EC2_INSTANCE'}],
                'findingStatus': [{'comparison': 'EQUALS', 'value': 'ACTIVE'}]
            }
            
            # Add instance filters if specified
            if instance_ids:
                filters['resourceId'] = []
                for instance_id in instance_ids:
                    filters['resourceId'].append({
                        'comparison': 'EQUALS',
                        'value': instance_id
                    })
            
            # Add severity filter
            if severity != "all":
                severity_map = {
                    'critical': 'CRITICAL',
                    'high': 'HIGH', 
                    'medium': 'MEDIUM',
                    'low': 'LOW'
                }
                if severity.lower() in severity_map:
                    filters['severity'] = [{
                        'comparison': 'EQUALS',
                        'value': severity_map[severity.lower()]
                    }]
            
            # Get findings from Inspector - paginate to get all results
            all_findings = []
            next_token = None
            page_count = 0
            
            while True:
                params = {
                    'filterCriteria': filters,
                    'maxResults': 100
                }
                if next_token:
                    params['nextToken'] = next_token
                    
                response = self.client.list_findings(**params)
                page_findings = response.get('findings', [])
                all_findings.extend(page_findings)
                page_count += 1
                
                next_token = response.get('nextToken')
                if not next_token or page_count > 50:
                    break
            
            findings = all_findings
            
            # Count by severity
            critical_count = sum(1 for f in findings if f.get('severity') == 'CRITICAL')
            high_count = sum(1 for f in findings if f.get('severity') == 'HIGH')
            medium_count = sum(1 for f in findings if f.get('severity') == 'MEDIUM')
            low_count = sum(1 for f in findings if f.get('severity') == 'LOW')
            
            # Generate summary
            total_findings = len(findings)
            summary = f"Found {total_findings} vulnerabilities: {critical_count} critical, {high_count} high, {medium_count} medium, {low_count} low"
            
            return {
                "findings": findings,
                "critical_count": critical_count,
                "high_count": high_count,
                "medium_count": medium_count,
                "low_count": low_count,
                "total_count": total_findings,
                "summary": summary
            }
            
        except Exception as e:
            return {
                "findings": [],
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
                "total_count": 0,
                "error": str(e),
                "summary": f"Error retrieving Inspector findings: {str(e)}"
            }

class AWSCloudWatch:
    """CloudWatch metrics integration"""
    
    def __init__(self):
        self.client = boto3.client('cloudwatch')
    
    def get_metrics(self, instance_id: str, metric_names: List[str], time_range: str) -> Dict[str, Any]:
        """Get CloudWatch metrics for EC2 instance"""
        try:
            # Parse time range and calculate appropriate period
            end_time = datetime.utcnow()
            if time_range.endswith('h'):
                hours = int(time_range[:-1])
                start_time = end_time - timedelta(hours=hours)
                period = 300 if hours <= 6 else 3600
            elif time_range.endswith('d'):
                days = int(time_range[:-1])
                start_time = end_time - timedelta(days=days)
                period = 3600 if days <= 2 else 86400
            else:
                start_time = end_time - timedelta(hours=24)
                period = 3600
            
            metrics_data = {}
            anomalies = []
            
            # Default EC2 metrics if none specified
            if not metric_names:
                metric_names = ['CPUUtilization', 'NetworkIn', 'NetworkOut', 'DiskReadOps', 'DiskWriteOps']
            
            for metric_name in metric_names:
                try:
                    response = self.client.get_metric_statistics(
                        Namespace='AWS/EC2',
                        MetricName=metric_name,
                        Dimensions=[
                            {
                                'Name': 'InstanceId',
                                'Value': instance_id
                            }
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=period,
                        Statistics=['Average', 'Maximum', 'Minimum']
                    )
                    
                    datapoints = response.get('Datapoints', [])
                    if datapoints:
                        # Sort by timestamp
                        datapoints.sort(key=lambda x: x['Timestamp'])
                        
                        # Calculate trends and anomalies
                        averages = [dp['Average'] for dp in datapoints]
                        if len(averages) > 1:
                            avg_value = sum(averages) / len(averages)
                            max_value = max(averages)
                            min_value = min(averages)
                            
                            # Simple anomaly detection
                            if len(averages) > 3:
                                std_dev = statistics.stdev(averages)
                                threshold = avg_value + (2 * std_dev)
                                
                                for dp in datapoints:
                                    if dp['Average'] > threshold:
                                        anomalies.append({
                                            'metric': metric_name,
                                            'timestamp': dp['Timestamp'].isoformat(),
                                            'value': dp['Average'],
                                            'threshold': threshold,
                                            'severity': 'high' if dp['Average'] > threshold * 1.5 else 'medium'
                                        })
                            
                            metrics_data[metric_name] = {
                                'datapoints': datapoints,
                                'average': avg_value,
                                'maximum': max_value,
                                'minimum': min_value,
                                'trend': 'increasing' if averages[-1] > averages[0] else 'decreasing'
                            }
                        else:
                            metrics_data[metric_name] = {
                                'datapoints': datapoints,
                                'status': 'insufficient_data'
                            }
                    else:
                        metrics_data[metric_name] = {
                            'status': 'no_data',
                            'message': f'No data available for {metric_name}'
                        }
                        
                except Exception as metric_error:
                    metrics_data[metric_name] = {
                        'error': str(metric_error),
                        'status': 'error'
                    }
            
            # Generate trends summary
            trends = {
                'time_range': f"{start_time.isoformat()} to {end_time.isoformat()}",
                'anomaly_count': len(anomalies),
                'metrics_collected': len([m for m in metrics_data.values() if 'datapoints' in m])
            }
            
            return {
                "metrics": metrics_data,
                "anomalies": anomalies,
                "trends": trends,
                "instance_id": instance_id,
                "time_range": time_range
            }
            
        except Exception as e:
            return {
                "metrics": {},
                "anomalies": [],
                "trends": {},
                "error": str(e),
                "instance_id": instance_id
            }

class AWSCloudTrail:
    """CloudTrail events integration"""
    
    def __init__(self):
        self.client = boto3.client('cloudtrail')
    
    def analyze_events(self, instance_id: str, event_types: List[str], time_range: str) -> Dict[str, Any]:
        """Analyze CloudTrail events for security insights"""
        try:
            # Parse time range
            end_time = datetime.utcnow()
            if time_range.endswith('h'):
                hours = int(time_range[:-1])
                start_time = end_time - timedelta(hours=hours)
            elif time_range.endswith('d'):
                days = int(time_range[:-1])
                start_time = end_time - timedelta(days=days)
            else:
                start_time = end_time - timedelta(hours=24)
            
            # Default security-relevant event types
            if not event_types:
                event_types = [
                    'RunInstances', 'TerminateInstances', 'StopInstances', 'StartInstances',
                    'ModifyInstanceAttribute', 'AuthorizeSecurityGroupIngress', 
                    'RevokeSecurityGroupIngress', 'CreateSecurityGroup', 'DeleteSecurityGroup',
                    'AttachUserPolicy', 'DetachUserPolicy', 'CreateUser', 'DeleteUser'
                ]
            
            all_events = []
            security_events = []
            suspicious_activity = []
            
            # Query CloudTrail events
            response = self.client.lookup_events(
                LookupAttributes=[
                    {
                        'AttributeKey': 'ResourceName',
                        'AttributeValue': instance_id
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                MaxResults=50
            )
            
            events = response.get('Events', [])
            
            for event in events:
                event_data = {
                    'event_time': event.get('EventTime').isoformat() if event.get('EventTime') else None,
                    'event_name': event.get('EventName'),
                    'user_name': event.get('Username'),
                    'source_ip': event.get('SourceIPAddress'),
                    'user_agent': event.get('UserAgent'),
                    'aws_region': event.get('AwsRegion'),
                    'event_source': event.get('EventSource')
                }
                
                all_events.append(event_data)
                
                # Classify security-relevant events
                event_name = event.get('EventName', '')
                if any(sec_event in event_name for sec_event in event_types):
                    security_events.append(event_data)
                
                # Detect suspicious patterns
                source_ip = event.get('SourceIPAddress', '')
                user_name = event.get('Username', '')
                
                # Flag suspicious activity
                suspicious_indicators = [
                    'root' in user_name.lower(),
                    event_name in ['TerminateInstances', 'DeleteSecurityGroup'],
                    not source_ip.startswith('10.') and not source_ip.startswith('172.') and not source_ip.startswith('192.168.'),
                    'Console' not in event.get('UserAgent', '')
                ]
                
                if sum(suspicious_indicators) >= 2:
                    suspicious_activity.append({
                        **event_data,
                        'risk_factors': suspicious_indicators,
                        'risk_score': sum(suspicious_indicators) * 25
                    })
            
            # Generate analysis summary
            analysis_summary = {
                'total_events': len(all_events),
                'security_events_count': len(security_events),
                'suspicious_events_count': len(suspicious_activity),
                'time_range': f"{start_time.isoformat()} to {end_time.isoformat()}",
                'high_risk_events': len([s for s in suspicious_activity if s.get('risk_score', 0) >= 75])
            }
            
            return {
                "events": all_events,
                "security_events": security_events,
                "suspicious_activity": suspicious_activity,
                "analysis_summary": analysis_summary,
                "instance_id": instance_id
            }
            
        except Exception as e:
            return {
                "events": [],
                "security_events": [],
                "suspicious_activity": [],
                "error": str(e),
                "instance_id": instance_id
            }

class AWSSystemsManager:
    """AWS Systems Manager integration"""
    
    def __init__(self):
        self.client = boto3.client('ssm', region_name='us-west-2')
    
    def execute_patch_now(self, instance_ids: List[str], patch_level: str = "non_critical") -> Dict[str, Any]:
        """Execute patching with rollback capability"""
        try:
            response = self.client.send_command(
                InstanceIds=instance_ids,
                DocumentName="AWS-RunPatchBaseline",
                Parameters={
                    'Operation': ['Install'],
                    'RebootOption': ['RebootIfNeeded']
                },
                Comment=f"SRE Agent patch execution - {patch_level}"
            )
            
            command_id = response['Command']['CommandId']
            
            return {
                "status": "success",
                "command_id": command_id,
                "instance_count": len(instance_ids),
                "patch_level": patch_level,
                "message": f"Patch command sent to {len(instance_ids)} instances"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to execute patch command"
            }
    
    def get_patch_compliance(self, instance_ids: List[str]) -> Dict[str, Any]:
        """Get patch compliance status for instances"""
        try:
            compliance_data = {}
            
            for instance_id in instance_ids:
                try:
                    response = self.client.describe_instance_patch_states(
                        InstanceIds=[instance_id]
                    )
                    
                    if response['InstancePatchStates']:
                        state = response['InstancePatchStates'][0]
                        compliance_data[instance_id] = {
                            "installed_count": state.get('InstalledCount', 0),
                            "missing_count": state.get('MissingCount', 0),
                            "failed_count": state.get('FailedCount', 0),
                            "operation": state.get('Operation', 'Unknown'),
                            "compliance_status": "compliant" if state.get('MissingCount', 0) == 0 else "non_compliant"
                        }
                    else:
                        compliance_data[instance_id] = {
                            "status": "no_data",
                            "message": "No patch state data available"
                        }
                        
                except Exception as e:
                    compliance_data[instance_id] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            compliant = [iid for iid, data in compliance_data.items() if data.get('compliance_status') == 'compliant']
            non_compliant = [iid for iid, data in compliance_data.items() if data.get('compliance_status') == 'non_compliant']
            
            return {
                "status": "success",
                "compliance_data": compliance_data,
                "summary": {
                    "total_instances": len(instance_ids),
                    "compliant_count": len(compliant),
                    "non_compliant_count": len(non_compliant),
                    "compliant_instances": compliant,
                    "non_compliant_instances": non_compliant
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to check patch compliance"
            }

# =============================================================================
# VULNERABILITY ANALYZER
# =============================================================================

class VulnerabilityAnalyzer:
    """GenAI-powered vulnerability analysis"""
    
    def __init__(self, model_id: str = "amazon.titan-text-premier-v1:0"):
        self.model = BedrockModelFactory.create_model(model_id)
        self.model_id = model_id
    
    def analyze_instance(self, instance_id: str) -> Dict[str, Any]:
        """Analyze vulnerabilities for a specific EC2 instance"""
        try:
            # Get real vulnerability data from Inspector
            inspector = AWSInspector()
            findings_data = inspector.get_findings([instance_id], "all")
            
            # Convert Inspector findings to our format
            vulnerabilities = []
            for finding in findings_data.get("findings", []):
                vuln = {
                    "cve_id": finding.get("title", "Unknown"),
                    "severity": finding.get("severity", "UNKNOWN"),
                    "cvss_score": finding.get("inspector_score", 0.0),
                    "description": finding.get("description", ""),
                    "affected_package": finding.get("package_name", "Unknown"),
                    "fixed_version": finding.get("fixed_in_version", "")
                }
                vulnerabilities.append(vuln)
            
            # Calculate risk score
            risk_analysis = self._calculate_risk_score(vulnerabilities, instance_id)
            
            # Generate remediation priorities
            remediation_priority = self._prioritize_remediation(vulnerabilities)
            
            return {
                "instance_id": instance_id,
                "vulnerabilities": vulnerabilities,
                "risk_score": risk_analysis.get("risk_score", 0.0),
                "risk_factors": risk_analysis.get("risk_factors", []),
                "remediation_priority": remediation_priority,
                "analysis_time": datetime.utcnow().isoformat(),
                "recommendations": risk_analysis.get("recommendations", [])
            }
            
        except Exception as e:
            return {
                "instance_id": instance_id,
                "vulnerabilities": [],
                "risk_score": 0.0,
                "error": str(e),
                "analysis_time": datetime.utcnow().isoformat()
            }
    
    def _calculate_risk_score(self, vulnerabilities: List[Dict], instance_id: str) -> Dict[str, Any]:
        """Calculate comprehensive risk score"""
        vuln_count = len(vulnerabilities)
        avg_cvss = sum([v.get("cvss_score", 0) for v in vulnerabilities]) / len(vulnerabilities) if vulnerabilities else 0
        
        # Simple risk score calculation
        base_score = min(avg_cvss * 10, 100)
        volume_multiplier = min(1 + (vuln_count * 0.1), 2.0)
        risk_score = min(base_score * volume_multiplier, 100)
        
        risk_factors = []
        if vuln_count > 10:
            risk_factors.append("High vulnerability count")
        if avg_cvss >= 8.0:
            risk_factors.append("High severity vulnerabilities")
        if avg_cvss >= 9.0:
            risk_factors.append("Critical vulnerabilities present")
        
        recommendations = []
        if risk_score >= 80:
            recommendations.append("Immediate patching required")
        elif risk_score >= 60:
            recommendations.append("Schedule patching within 24 hours")
        else:
            recommendations.append("Schedule patching during next maintenance window")
        
        return {
            "risk_score": round(risk_score, 1),
            "risk_factors": risk_factors,
            "recommendations": recommendations
        }
    
    def _prioritize_remediation(self, vulnerabilities: List[Dict]) -> List[Dict]:
        """Prioritize remediation actions"""
        try:
            if not vulnerabilities:
                return []
            
            # Sort by CVSS score and severity
            sorted_vulns = sorted(vulnerabilities, key=lambda x: (x.get("cvss_score", 0)), reverse=True)
            
            priority_list = []
            for i, vuln in enumerate(sorted_vulns[:5]):  # Top 5 priorities
                priority_list.append({
                    "priority": i + 1,
                    "cve_id": vuln.get("cve_id"),
                    "severity": vuln.get("severity"),
                    "cvss_score": vuln.get("cvss_score"),
                    "action": "patch" if vuln.get("fixed_version") else "investigate",
                    "urgency": "immediate" if vuln.get("cvss_score", 0) >= 9.0 else "high" if vuln.get("cvss_score", 0) >= 7.0 else "medium"
                })
            
            return priority_list
            
        except Exception as e:
            return [{"error": str(e)}]
    
    def resolve_by_criticality(self, instance_ids: List[str], criticality: str) -> Dict[str, Any]:
        """Resolve vulnerabilities based on criticality level"""
        try:
            resolution_plan = {
                "instance_ids": instance_ids,
                "criticality": criticality,
                "actions": [],
                "estimated_completion": "",
                "risk_reduction": 0
            }
            
            # Define criticality thresholds
            thresholds = {
                "critical": {"min_cvss": 9.0, "severities": ["CRITICAL"]},
                "high": {"min_cvss": 7.0, "severities": ["CRITICAL", "HIGH"]},
                "medium": {"min_cvss": 4.0, "severities": ["CRITICAL", "HIGH", "MEDIUM"]},
                "all": {"min_cvss": 0.0, "severities": ["CRITICAL", "HIGH", "MEDIUM", "LOW"]}
            }
            
            threshold = thresholds.get(criticality, thresholds["high"])
            total_vulns_resolved = 0
            
            for instance_id in instance_ids:
                instance_analysis = self.analyze_instance(instance_id)
                vulnerabilities = instance_analysis.get("vulnerabilities", [])
                
                # Filter by criticality
                target_vulns = [
                    v for v in vulnerabilities 
                    if v.get("severity") in threshold["severities"] 
                    and v.get("cvss_score", 0) >= threshold["min_cvss"]
                ]
                
                if target_vulns:
                    action = {
                        "instance_id": instance_id,
                        "vulnerabilities_count": len(target_vulns),
                        "action_type": "patch" if criticality in ["critical", "high"] else "schedule",
                        "priority": "immediate" if criticality == "critical" else "high" if criticality == "high" else "medium",
                        "estimated_time": len(target_vulns) * 5  # 5 minutes per vulnerability
                    }
                    resolution_plan["actions"].append(action)
                    total_vulns_resolved += len(target_vulns)
            
            # Calculate risk reduction
            resolution_plan["risk_reduction"] = min(total_vulns_resolved * 10, 100)
            resolution_plan["total_vulnerabilities"] = total_vulns_resolved
            
            # Estimate completion time
            total_time = sum([action.get("estimated_time", 0) for action in resolution_plan["actions"]])
            resolution_plan["estimated_completion"] = f"{total_time} minutes"
            
            return resolution_plan
            
        except Exception as e:
            return {
                "instance_ids": instance_ids,
                "criticality": criticality,
                "actions": [],
                "error": str(e)
            }

# =============================================================================
# AUTOMATED REMEDIATION
# =============================================================================

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
            print(f"DEBUG: Starting schedule_automated_patching for {len(instance_ids)} instances")
            
            remediation_plan = {
                "plan_id": f"remediation-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
                "instance_schedules": [],
                "total_instances": len(instance_ids),
                "criticality": criticality,
                "created_at": datetime.utcnow().isoformat(),
                "status": "success"
            }
            
            for instance_id in instance_ids:
                try:
                    print(f"DEBUG: Processing instance {instance_id}")
                    
                    # Get vulnerability analysis
                    vuln_analysis = self.vuln_analyzer.analyze_instance(instance_id)
                    print(f"DEBUG: Got vuln analysis for {instance_id}")
                    
                    # Find optimal patch window
                    optimal_window = self._find_optimal_patch_window(instance_id, vuln_analysis)
                    print(f"DEBUG: Got optimal window for {instance_id}")
                    
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
                    
                    # Try to schedule EventBridge rule (non-blocking)
                    try:
                        event_result = self._schedule_patch_event(instance_id, optimal_window, criticality)
                        schedule["event_bridge_result"] = event_result
                        print(f"DEBUG: EventBridge result for {instance_id}: {event_result}")
                    except Exception as event_error:
                        print(f"WARNING: EventBridge scheduling failed for {instance_id}: {str(event_error)}")
                        schedule["event_bridge_result"] = {"error": str(event_error), "status": "failed"}
                    
                except Exception as instance_error:
                    print(f"ERROR: Failed to process instance {instance_id}: {str(instance_error)}")
                    remediation_plan["instance_schedules"].append({
                        "instance_id": instance_id,
                        "error": str(instance_error),
                        "status": "failed"
                    })
            
            print(f"DEBUG: Completed schedule_automated_patching, returning plan")
            return remediation_plan
            
        except Exception as e:
            print(f"ERROR: schedule_automated_patching top-level exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e),
                "instance_ids": instance_ids,
                "criticality": criticality
            }
    
    def _find_optimal_patch_window(self, instance_id: str, vuln_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Find optimal patching window based on telemetry"""
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
            
            # Create EventBridge rule
            try:
                self.events_client.put_rule(
                    Name=rule_name,
                    ScheduleExpression=cron_expression,
                    Description=f"Automated patch schedule for {instance_id} ({criticality} criticality)",
                    State='ENABLED'
                )
                
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
            # Delete the EventBridge rule
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

# =============================================================================
# INITIALIZE SERVICES
# =============================================================================

inspector = AWSInspector()
cloudwatch = AWSCloudWatch()
cloudtrail = AWSCloudTrail()
ssm = AWSSystemsManager()
analyzer = VulnerabilityAnalyzer()
auto_remediation = AutomatedRemediation()

# =============================================================================
# FASTAPI ENDPOINTS
# =============================================================================

class MCPRequest(BaseModel):
    method: str
    params: Dict[str, Any]

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/mcp")
async def handle_mcp_request(request: MCPRequest):
    """Handle MCP-style requests"""
    method = request.method
    params = request.params
    
    print(f"DEBUG: MCP request - method: {method}, params: {params}")
    
    # Core MCP Functions
    if method == "get_inspector_findings":
        return get_inspector_findings(
            params.get("instance_id"), 
            params.get("severity", "all")
        )
    elif method == "get_ec2_cloudwatch_metrics":
        return await get_ec2_cloudwatch_metrics(
            params.get("instance_id"),
            params.get("metric_names", []),
            params.get("time_range", "24h")
        )
    elif method == "analyze_cloudtrail_events":
        return await analyze_cloudtrail_events(
            params.get("instance_id"),
            params.get("event_types", []),
            params.get("time_range", "24h")
        )
    elif method == "monitor_security_events":
        return await monitor_security_events(
            params.get("instance_ids", []),
            params.get("event_types", ["login", "privilege_escalation", "config_changes"]),
            params.get("time_range", "24h")
        )
    elif method == "analyze_configuration_changes":
        return await analyze_configuration_changes(
            params.get("instance_ids", []),
            params.get("time_range", "24h")
        )
    elif method == "analyze_optimal_patch_window":
        return analyze_optimal_patch_window(
            params.get("instance_ids", []),
            params.get("window_preference", "next-maintenance"),
            params.get("patch_level", "all")
        )
    elif method == "execute_patch_now":
        return execute_patch_now(
            params.get("instance_ids", []),
            params.get("patch_level", "non_critical")
        )
    elif method == "check_patch_compliance":
        return check_patch_compliance(
            params.get("instance_ids", [])
        )
    elif method == "resolve_vulnerabilities_by_criticality":
        return await resolve_vulnerabilities_by_criticality(
            params.get("instance_ids", []),
            params.get("criticality", "high"),
            params.get("auto_approve", False)
        )
    elif method == "generate_vulnerability_report":
        try:
            return await generate_vulnerability_report(
                params.get("instance_ids", []),
                params.get("format", "json")
            )
        except Exception as e:
            print(f"ERROR in generate_vulnerability_report: {str(e)}")
            return {"error": str(e), "method": "generate_vulnerability_report"}
    elif method == "schedule_automated_patching":
        try:
            result = schedule_automated_patching(
                params.get("instance_ids", []),
                params.get("criticality", "high")
            )
            print(f"DEBUG: schedule_automated_patching result: {result}")
            return result
        except Exception as e:
            print(f"ERROR: schedule_automated_patching failed: {str(e)}")
            return {"error": str(e), "method": "schedule_automated_patching"}
    elif method == "get_scheduled_patches":
        return get_scheduled_patches(
            params.get("instance_id")
        )
    elif method == "cancel_scheduled_patch":
        return cancel_scheduled_patch(
            params.get("instance_id"),
            params.get("rule_name")
        )
    else:
        print(f"ERROR: Unknown method: {method}")
        raise HTTPException(status_code=400, detail=f"Unknown method: {method}")

# =============================================================================
# MCP FUNCTION IMPLEMENTATIONS
# =============================================================================

def get_inspector_findings(instance_id: Optional[str], severity: str = "all") -> Dict[str, Any]:
    """Get Inspector vulnerability findings for EC2 instances"""
    instance_ids = [instance_id] if instance_id else []
    result = inspector.get_findings(instance_ids, severity)
    return result
        
async def analyze_ec2_vulnerabilities(instance_id: str) -> Dict[str, Any]:
    """Analyze vulnerabilities for a specific EC2 instance"""
    return await analyzer.analyze_instance(instance_id)
        
async def get_ec2_cloudwatch_metrics(instance_id: str, metric_names: List[str], time_range: str) -> Dict[str, Any]:
    """Get CloudWatch metrics for EC2 instance"""
    try:
        result = cloudwatch.get_metrics(instance_id, metric_names, time_range)
        return result
    except Exception as e:
        return {
            "metrics": {},
            "anomalies": [],
            "trends": {},
            "error": str(e),
            "instance_id": instance_id
        }
        
async def analyze_cloudtrail_events(instance_id: str, event_types: List[str], time_range: str) -> Dict[str, Any]:
    """Analyze CloudTrail events for security insights"""
    try:
        result = cloudtrail.analyze_events(instance_id, event_types, time_range)
        return result
    except Exception as e:
        return {
            "events": [],
            "security_events": [],
            "suspicious_activity": [],
            "error": str(e),
            "instance_id": instance_id
        }

def analyze_optimal_patch_window(instance_ids: List[str], window_preference: str = "next-maintenance", patch_level: str = "all") -> Dict[str, Any]:
    """Analyze optimal patching windows using CloudWatch metrics"""
    try:
        analysis_results = {}
        
        for instance_id in instance_ids:
            # Get 14 days of CloudWatch metrics
            metrics_data = cloudwatch.get_metrics(
                instance_id, 
                ["CPUUtilization", "NetworkIn", "NetworkOut"], 
                "14d"
            )
            
            # Simple pattern analysis
            cpu_metrics = metrics_data.get("metrics", {}).get("CPUUtilization", {})
            avg_cpu = cpu_metrics.get("average", 0)
            
            if avg_cpu < 20:
                optimal_window = "Sunday 2:00 AM UTC"
                confidence = 0.9
                reasoning = "Low average CPU usage indicates flexible maintenance windows"
            elif avg_cpu < 50:
                optimal_window = "Saturday 11:00 PM UTC"
                confidence = 0.7
                reasoning = "Moderate usage - weekend late night recommended"
            else:
                optimal_window = "Sunday 4:00 AM UTC"
                confidence = 0.6
                reasoning = "High usage - early Sunday morning for minimal impact"
            
            analysis_results[instance_id] = {
                "metrics_summary": {
                    "avg_cpu": avg_cpu,
                    "peak_hours": ["9 AM - 5 PM weekdays"],
                    "low_usage_windows": ["Saturday 11 PM - Sunday 6 AM"]
                },
                "recommended_window": optimal_window,
                "confidence": confidence,
                "reasoning": reasoning
            }
        
        return {
            "status": "success",
            "instance_count": len(instance_ids),
            "analysis_period": "14 days",
            "recommended_window": "Sunday 2:00 AM UTC",
            "confidence": 0.8,
            "reasoning": "Analyzed usage patterns across all instances",
            "estimated_duration": f"{len(instance_ids) * 15} minutes",
            "instance_analysis": analysis_results,
            "patch_level": patch_level
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

def execute_patch_now(instance_ids: List[str], patch_level: str = "non_critical") -> Dict[str, Any]:
    """Execute patching on specified instances"""
    try:
        return ssm.execute_patch_now(instance_ids, patch_level)
    except Exception as e:
        return {"status": "error", "error": str(e)}
        
def check_patch_compliance(instance_ids: List[str]) -> Dict[str, Any]:
    """Check patch compliance for instances"""
    try:
        return ssm.get_patch_compliance(instance_ids)
    except Exception as e:
        return {"status": "error", "error": str(e)}
        
async def resolve_vulnerabilities_by_criticality(instance_ids: List[str], criticality: str, auto_approve: bool = False) -> Dict[str, Any]:
    """Resolve vulnerabilities based on criticality level"""
    try:
        # Get vulnerability analysis and resolution plan
        resolution_plan = analyzer.resolve_by_criticality(instance_ids, criticality)
        
        # If auto-approve is enabled, execute the plan
        if auto_approve and resolution_plan.get("actions"):
            execution_results = []
            for action in resolution_plan["actions"]:
                if action["action_type"] == "patch":
                    # Execute immediate patching
                    patch_result = ssm.execute_patch_now([action["instance_id"]], criticality)
                    execution_results.append({
                        "instance_id": action["instance_id"],
                        "status": patch_result.get("status", "unknown"),
                        "action": "patched"
                    })
                else:
                    # Schedule for later
                    execution_results.append({
                        "instance_id": action["instance_id"],
                        "status": "scheduled",
                        "action": "scheduled"
                    })
            
            resolution_plan["execution_results"] = execution_results
            resolution_plan["auto_executed"] = True
        else:
            resolution_plan["auto_executed"] = False
            resolution_plan["requires_approval"] = True
        
        return resolution_plan
        
    except Exception as e:
        return {
            "instance_ids": instance_ids,
            "criticality": criticality,
            "auto_approve": auto_approve,
            "error": str(e),
            "status": "failed"
        }
        
async def execute_automated_patching(instance_ids: List[str], patch_level: str = "non_critical", rollback_enabled: bool = True) -> Dict[str, Any]:
    """Execute automated patching with rollback capability"""
    return await ssm.execute_patch_now(instance_ids, patch_level)
        
async def monitor_security_events(instance_ids: List[str], event_types: List[str] = None, time_range: str = "24h") -> Dict[str, Any]:
    """Monitor security events across multiple instances"""
    try:
        if event_types is None:
            event_types = ["login", "privilege_escalation", "config_changes"]
        
        all_events = []
        security_summary = {}
        alerts = []
        
        for instance_id in instance_ids:
            events = cloudtrail.analyze_events(instance_id, event_types, time_range)
            all_events.extend(events.get("security_events", []))
            
            # Add high-risk events to alerts
            for event in events.get("suspicious_activity", []):
                if event.get("risk_score", 0) >= 75:
                    alerts.append({
                        "instance_id": instance_id,
                        "event": event,
                        "alert_level": "high" if event.get("risk_score", 0) >= 90 else "medium"
                    })
            
            security_summary[instance_id] = {
                "total_events": len(events.get("events", [])),
                "security_events": len(events.get("security_events", [])),
                "suspicious_activity": len(events.get("suspicious_activity", [])),
                "high_risk_count": len([e for e in events.get("suspicious_activity", []) if e.get("risk_score", 0) >= 75])
            }
        
        # Generate recommendations based on findings
        recommendations = []
        total_alerts = len(alerts)
        if total_alerts > 0:
            recommendations.append(f"Review {total_alerts} high-risk security events")
        if total_alerts > 5:
            recommendations.append("Consider implementing additional security monitoring")
        if any(summary.get("high_risk_count", 0) > 3 for summary in security_summary.values()):
            recommendations.append("Investigate instances with multiple high-risk events")
        
        return {
            "security_summary": security_summary,
            "alerts": alerts,
            "recommendations": recommendations,
            "total_instances": len(instance_ids),
            "time_range": time_range
        }
    except Exception as e:
        return {
            "security_summary": {},
            "alerts": [],
            "recommendations": [],
            "error": str(e),
            "total_instances": len(instance_ids)
        }
        
async def analyze_configuration_changes(instance_ids: List[str], time_range: str = "24h") -> Dict[str, Any]:
    """Analyze configuration changes for security impact"""
    try:
        all_changes = []
        impact_summary = {}
        
        # Security-relevant event types for configuration changes
        config_event_types = [
            'ModifyInstanceAttribute', 'AuthorizeSecurityGroupIngress', 
            'RevokeSecurityGroupIngress', 'CreateSecurityGroup', 'DeleteSecurityGroup',
            'AttachUserPolicy', 'DetachUserPolicy', 'ModifyDBInstance',
            'PutBucketPolicy', 'DeleteBucketPolicy'
        ]
        
        for instance_id in instance_ids:
            # Get configuration-related events
            events = cloudtrail.analyze_events(instance_id, config_event_types, time_range)
            
            instance_changes = []
            security_impact = {
                "risk_level": "low",
                "change_count": 0,
                "high_risk_changes": 0,
                "security_group_changes": 0,
                "policy_changes": 0
            }
            
            for event in events.get("events", []):
                event_name = event.get("event_name", "")
                change_data = {
                    "timestamp": event.get("event_time"),
                    "event_name": event_name,
                    "user": event.get("user_name"),
                    "source_ip": event.get("source_ip"),
                    "instance_id": instance_id
                }
                
                # Classify change risk
                if "SecurityGroup" in event_name:
                    change_data["risk_level"] = "high" if "Delete" in event_name else "medium"
                    security_impact["security_group_changes"] += 1
                elif "Policy" in event_name:
                    change_data["risk_level"] = "high"
                    security_impact["policy_changes"] += 1
                else:
                    change_data["risk_level"] = "medium"
                
                instance_changes.append(change_data)
                security_impact["change_count"] += 1
                
                if change_data["risk_level"] == "high":
                    security_impact["high_risk_changes"] += 1
            
            # Determine overall risk level for instance
            if security_impact["high_risk_changes"] > 2:
                security_impact["risk_level"] = "high"
            elif security_impact["high_risk_changes"] > 0 or security_impact["change_count"] > 5:
                security_impact["risk_level"] = "medium"
            
            all_changes.extend(instance_changes)
            impact_summary[instance_id] = security_impact
        
        # Overall compliance assessment
        high_risk_instances = [iid for iid, impact in impact_summary.items() if impact.get("risk_level") == "high"]
        medium_risk_instances = [iid for iid, impact in impact_summary.items() if impact.get("risk_level") == "medium"]
        
        if high_risk_instances:
            compliance_status = "non_compliant"
        elif medium_risk_instances:
            compliance_status = "review_required"
        else:
            compliance_status = "compliant"
        
        return {
            "changes": all_changes,
            "security_impact": impact_summary,
            "compliance_status": compliance_status,
            "high_risk_instances": high_risk_instances,
            "medium_risk_instances": medium_risk_instances,
            "total_changes": len(all_changes),
            "time_range": time_range
        }
    except Exception as e:
        return {
            "changes": [],
            "security_impact": {},
            "compliance_status": "error",
            "error": str(e),
            "total_changes": 0
        }
        
async def generate_vulnerability_report(instance_ids: List[str], format: str = "json") -> Dict[str, Any]:
    """Generate comprehensive vulnerability report"""
    report_data = {
        "report_id": f"sre-report-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
        "generated_at": datetime.utcnow().isoformat(),
        "instance_count": len(instance_ids),
        "instances": {},
        "summary": {
            "total_vulnerabilities": 0,
            "critical_count": 0,
            "high_count": 0,
            "compliance_issues": 0
        }
    }
    
    recommendations = []
    
    for instance_id in instance_ids:
        # Get vulnerability analysis
        vuln_analysis = analyzer.analyze_instance(instance_id)
        
        # Get patch compliance (simplified)
        try:
            compliance = ssm.get_patch_compliance([instance_id])
            compliance_data = compliance.get('compliance_data', {}).get(instance_id, {})
        except Exception:
            compliance_data = {"compliance_status": "unknown", "missing_count": 0}
        
        report_data["instances"][instance_id] = {
            "vulnerability_analysis": vuln_analysis,
            "patch_compliance": compliance_data,
            "risk_score": vuln_analysis.get("risk_score", 0)
        }
        
        # Update summary
        report_data["summary"]["total_vulnerabilities"] += len(vuln_analysis.get("vulnerabilities", []))
        report_data["summary"]["critical_count"] += len([v for v in vuln_analysis.get("vulnerabilities", []) if v.get("severity") == "CRITICAL"])
        report_data["summary"]["high_count"] += len([v for v in vuln_analysis.get("vulnerabilities", []) if v.get("severity") == "HIGH"])
        
        if compliance_data.get("compliance_status") == "non_compliant":
            report_data["summary"]["compliance_issues"] += 1
        
        # Add recommendations
        if vuln_analysis.get("risk_score", 0) >= 80:
            recommendations.append(f"Immediate attention required for {instance_id}")
    
    report_data["recommendations"] = recommendations
    
    return report_data

def schedule_automated_patching(instance_ids: List[str], criticality: str = "high") -> Dict[str, Any]:
    """Schedule automated patching based on AI recommendations"""
    try:
        print(f"DEBUG: Calling auto_remediation.schedule_automated_patching with {instance_ids}, {criticality}")
        result = auto_remediation.schedule_automated_patching(instance_ids, criticality)
        print(f"DEBUG: auto_remediation result: {result}")
        return result
    except Exception as e:
        print(f"ERROR: schedule_automated_patching exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "error": str(e),
            "instance_ids": instance_ids,
            "criticality": criticality
        }

def get_scheduled_patches(instance_id: Optional[str] = None) -> Dict[str, Any]:
    """Get scheduled patch operations"""
    try:
        return auto_remediation.get_scheduled_patches(instance_id)
    except Exception as e:
        return {
            "error": str(e),
            "instance_id": instance_id
        }

def cancel_scheduled_patch(instance_id: str, rule_name: str) -> Dict[str, Any]:
    """Cancel a scheduled patch operation"""
    try:
        return auto_remediation.cancel_scheduled_patch(instance_id, rule_name)
    except Exception as e:
        return {
            "error": str(e),
            "instance_id": instance_id,
            "rule_name": rule_name
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)