"""FastAPI Server for SRE Operations Assistant"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from aws_services import AWSInspector, AWSCloudWatch, AWSCloudTrail
from systems_manager import AWSSystemsManager
from vulnerability_analyzer import VulnerabilityAnalyzer
from patch_scheduler import PatchScheduler

app = FastAPI(title="SRE Operations Assistant")

# Initialize services
inspector = AWSInspector()
cloudwatch = AWSCloudWatch()
cloudtrail = AWSCloudTrail()
ssm = AWSSystemsManager()
analyzer = VulnerabilityAnalyzer()
scheduler = PatchScheduler()

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
    else:
        raise HTTPException(status_code=400, detail=f"Unknown method: {method}")
    
def get_inspector_findings(instance_id: Optional[str], severity: str = "all") -> Dict[str, Any]:
    """Get Inspector vulnerability findings for EC2 instances"""
    instance_ids = [instance_id] if instance_id else []
    print(f"DEBUG: get_inspector_findings called with instance_id={instance_id}, severity={severity}")
    print(f"DEBUG: instance_ids={instance_ids}")
    result = inspector.get_findings(instance_ids, severity)
    print(f"DEBUG: inspector.get_findings returned: {result.get('summary', 'No summary')}")
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
    """Analyze optimal patching windows using CloudWatch metrics and GenAI"""
    try:
        analysis_results = {}
        recommendations = []
        
        for instance_id in instance_ids:
            # Get 14 days of CloudWatch metrics
            metrics_data = cloudwatch.get_metrics(
                instance_id, 
                ["CPUUtilization", "NetworkIn", "NetworkOut"], 
                "14d"
            )
            
            # Analyze patterns using GenAI
            pattern_analysis = _analyze_usage_patterns(instance_id, metrics_data)
            
            analysis_results[instance_id] = {
                "metrics_summary": {
                    "avg_cpu": metrics_data.get("metrics", {}).get("CPUUtilization", {}).get("average", 0),
                    "peak_hours": pattern_analysis.get("peak_hours", []),
                    "low_usage_windows": pattern_analysis.get("low_usage_windows", [])
                },
                "recommended_window": pattern_analysis.get("optimal_window", "Sunday 2:00 AM"),
                "confidence": pattern_analysis.get("confidence", 0.8),
                "reasoning": pattern_analysis.get("reasoning", "Low usage period identified")
            }
        
        # Generate overall recommendation
        optimal_window = _find_common_window(analysis_results)
        
        return {
            "status": "success",
            "instance_count": len(instance_ids),
            "analysis_period": "14 days",
            "recommended_window": optimal_window.get("window", "Sunday 2:00 AM UTC"),
            "confidence": optimal_window.get("confidence", 0.8),
            "reasoning": optimal_window.get("reasoning", "Analyzed usage patterns across all instances"),
            "estimated_duration": f"{len(instance_ids) * 15} minutes",
            "instance_analysis": analysis_results,
            "patch_level": patch_level
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

def _analyze_usage_patterns(instance_id: str, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
    """Use GenAI to analyze usage patterns and recommend optimal windows"""
    try:
        from bedrock_models import BedrockModelFactory
        
        # Extract key metrics for analysis
        cpu_metrics = metrics_data.get("metrics", {}).get("CPUUtilization", {})
        network_in = metrics_data.get("metrics", {}).get("NetworkIn", {})
        
        avg_cpu = cpu_metrics.get("average", 0)
        max_cpu = cpu_metrics.get("maximum", 0)
        datapoints = len(cpu_metrics.get("datapoints", []))
        
        # Create prompt for GenAI analysis
        prompt = f"""
Analyze the following 14-day CloudWatch metrics for EC2 instance {instance_id} to recommend the optimal maintenance window:

Metrics Summary:
- Average CPU: {avg_cpu:.1f}%
- Peak CPU: {max_cpu:.1f}%
- Data points: {datapoints}
- Network activity: {network_in.get('average', 0):.0f} bytes/sec

Recommend the best maintenance window considering:
1. Lowest resource utilization periods
2. Typical business hours (avoid 9 AM - 5 PM weekdays)
3. Weekend vs weekday preferences
4. Time zone: UTC

Provide response in JSON format:
{{
  "optimal_window": "Day HH:MM AM/PM UTC",
  "confidence": 0.0-1.0,
  "reasoning": "explanation",
  "peak_hours": ["hour ranges"],
  "low_usage_windows": ["recommended windows"]
}}
"""
        
        # Try to use GenAI model
        try:
            model = BedrockModelFactory.create_model("amazon.titan-text-express-v1")
            response = model.generate_response(prompt, max_tokens=500)
            
            if response:
                # Try to parse JSON response
                import json
                return json.loads(response)
        except Exception:
            pass
        
        # Fallback analysis based on simple heuristics
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
        
        return {
            "optimal_window": optimal_window,
            "confidence": confidence,
            "reasoning": reasoning,
            "peak_hours": ["9 AM - 5 PM weekdays"],
            "low_usage_windows": ["Saturday 11 PM - Sunday 6 AM"]
        }
        
    except Exception as e:
        return {
            "optimal_window": "Sunday 2:00 AM UTC",
            "confidence": 0.5,
            "reasoning": f"Default recommendation due to analysis error: {str(e)}",
            "peak_hours": [],
            "low_usage_windows": []
        }

def _find_common_window(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """Find the best common maintenance window across all instances"""
    try:
        # Collect all recommended windows
        windows = []
        total_confidence = 0
        
        for instance_id, analysis in analysis_results.items():
            windows.append(analysis.get("recommended_window", "Sunday 2:00 AM UTC"))
            total_confidence += analysis.get("confidence", 0.5)
        
        # Simple logic: if most instances recommend Sunday early morning, use that
        sunday_count = sum(1 for w in windows if "Sunday" in w and ("2:00" in w or "3:00" in w or "4:00" in w))
        
        if sunday_count >= len(windows) * 0.6:  # 60% consensus
            return {
                "window": "Sunday 2:00 AM UTC",
                "confidence": min(total_confidence / len(windows), 0.95),
                "reasoning": f"Consensus recommendation based on {sunday_count}/{len(windows)} instances favoring Sunday early morning"
            }
        else:
            return {
                "window": "Saturday 11:00 PM UTC",
                "confidence": min(total_confidence / len(windows), 0.8),
                "reasoning": "Alternative weekend window to accommodate mixed usage patterns"
            }
            
    except Exception:
        return {
            "window": "Sunday 2:00 AM UTC",
            "confidence": 0.7,
            "reasoning": "Default safe maintenance window"
        }

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
                    schedule_result = scheduler.schedule_remediation([action["instance_id"]], criticality, False)
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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)