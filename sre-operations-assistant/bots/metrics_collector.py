#!/usr/bin/env python3
"""Custom metrics collector for SRE Operations Assistant"""

import json
import boto3
import urllib.request
import os
from datetime import datetime
from typing import Dict, Any

def handler(event, context):
    """Lambda handler for collecting custom SRE metrics"""
    
    cloudwatch = boto3.client('cloudwatch')
    mcp_url = os.environ.get('MCP_SERVER_URL')
    namespace = os.environ.get('NAMESPACE', 'SRE/Operations')
    
    if not mcp_url:
        print("MCP_SERVER_URL not configured")
        return {'statusCode': 400, 'body': 'Configuration error'}
    
    try:
        # Collect vulnerability metrics
        vuln_metrics = collect_vulnerability_metrics(mcp_url)
        
        # Collect patch compliance metrics
        patch_metrics = collect_patch_compliance_metrics(mcp_url)
        
        # Collect instance health metrics
        health_metrics = collect_instance_health_metrics(mcp_url)
        
        # Send metrics to CloudWatch
        metrics_data = []
        
        # Vulnerability metrics
        if vuln_metrics:
            metrics_data.extend([
                {
                    'MetricName': 'CriticalVulnerabilities',
                    'Value': vuln_metrics.get('critical_count', 0),
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow()
                },
                {
                    'MetricName': 'HighVulnerabilities', 
                    'Value': vuln_metrics.get('high_count', 0),
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow()
                },
                {
                    'MetricName': 'TotalVulnerabilities',
                    'Value': vuln_metrics.get('total_count', 0),
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow()
                }
            ])
        
        # Patch compliance metrics
        if patch_metrics:
            metrics_data.append({
                'MetricName': 'PatchCompliance',
                'Value': patch_metrics.get('compliance_percentage', 0),
                'Unit': 'Percent',
                'Timestamp': datetime.utcnow()
            })
        
        # Instance health metrics
        if health_metrics:
            metrics_data.extend([
                {
                    'MetricName': 'HealthyInstances',
                    'Value': health_metrics.get('healthy_count', 0),
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow()
                },
                {
                    'MetricName': 'UnhealthyInstances',
                    'Value': health_metrics.get('unhealthy_count', 0),
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow()
                }
            ])
        
        # Send metrics in batches (CloudWatch limit is 20 per call)
        for i in range(0, len(metrics_data), 20):
            batch = metrics_data[i:i+20]
            cloudwatch.put_metric_data(
                Namespace=namespace,
                MetricData=batch
            )
        
        print(f"Successfully sent {len(metrics_data)} metrics to CloudWatch")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Collected {len(metrics_data)} metrics',
                'metrics': [m['MetricName'] for m in metrics_data]
            })
        }
        
    except Exception as e:
        print(f"Error collecting metrics: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def collect_vulnerability_metrics(mcp_url: str) -> Dict[str, Any]:
    """Collect vulnerability metrics from MCP server"""
    try:
        payload = json.dumps({
            "method": "get_inspector_findings",
            "params": {"severity": "all"}
        })
        
        req = urllib.request.Request(
            f"{mcp_url}/mcp",
            data=payload.encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
            
    except Exception as e:
        print(f"Error collecting vulnerability metrics: {e}")
        return {}

def collect_patch_compliance_metrics(mcp_url: str) -> Dict[str, Any]:
    """Collect patch compliance metrics from MCP server"""
    try:
        payload = json.dumps({
            "method": "check_patch_compliance",
            "params": {"instance_ids": []}
        })
        
        req = urllib.request.Request(
            f"{mcp_url}/mcp",
            data=payload.encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            # Calculate compliance percentage
            if 'compliance_summary' in data:
                total = data['compliance_summary'].get('total_instances', 0)
                compliant = data['compliance_summary'].get('compliant_instances', 0)
                if total > 0:
                    data['compliance_percentage'] = (compliant / total) * 100
                else:
                    data['compliance_percentage'] = 100
            
            return data
            
    except Exception as e:
        print(f"Error collecting patch compliance metrics: {e}")
        return {}

def collect_instance_health_metrics(mcp_url: str) -> Dict[str, Any]:
    """Collect instance health metrics"""
    try:
        # Get EC2 instance status
        ec2 = boto3.client('ec2')
        response = ec2.describe_instance_status(IncludeAllInstances=True)
        
        healthy_count = 0
        unhealthy_count = 0
        
        for status in response['InstanceStatuses']:
            instance_status = status.get('InstanceStatus', {}).get('Status', 'unknown')
            system_status = status.get('SystemStatus', {}).get('Status', 'unknown')
            
            if instance_status == 'ok' and system_status == 'ok':
                healthy_count += 1
            else:
                unhealthy_count += 1
        
        return {
            'healthy_count': healthy_count,
            'unhealthy_count': unhealthy_count,
            'total_instances': healthy_count + unhealthy_count
        }
        
    except Exception as e:
        print(f"Error collecting instance health metrics: {e}")
        return {}

if __name__ == "__main__":
    # For local testing
    test_event = {}
    test_context = type('Context', (), {'function_name': 'test'})()
    result = handler(test_event, test_context)
    print(json.dumps(result, indent=2))