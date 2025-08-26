"""AWS Service Integrations"""

import boto3
from typing import List, Dict, Any
from datetime import datetime, timedelta


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
                
                print(f"DEBUG: Page {page_count}: {len(page_findings)} findings, total so far: {len(all_findings)}")
                
                next_token = response.get('nextToken')
                if not next_token:
                    break
                    
                # Safety break to prevent infinite loops
                if page_count > 50:
                    print(f"DEBUG: Breaking after {page_count} pages")
                    break
            
            findings = all_findings
            print(f"DEBUG: Final total findings: {len(findings)}")
            
            # Count by severity
            critical_count = sum(1 for f in findings if f.get('severity') == 'CRITICAL')
            high_count = sum(1 for f in findings if f.get('severity') == 'HIGH')
            medium_count = sum(1 for f in findings if f.get('severity') == 'MEDIUM')
            low_count = sum(1 for f in findings if f.get('severity') == 'LOW')
            
            print(f"DEBUG: Severity counts - Critical: {critical_count}, High: {high_count}, Medium: {medium_count}, Low: {low_count}")
            
            # Debug: Check first few findings structure
            print(f"DEBUG: Sample findings structure:")
            for i, f in enumerate(findings[:3]):
                print(f"  Finding {i}: severity={f.get('severity')}, title={f.get('title', 'No title')[:50]}")
            
            # Debug: Check if there are findings without severity
            no_severity = [f for f in findings if not f.get('severity')]
            print(f"DEBUG: Findings without severity: {len(no_severity)}")
            
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
            # Parse time range
            end_time = datetime.utcnow()
            if time_range.endswith('h'):
                hours = int(time_range[:-1])
                start_time = end_time - timedelta(hours=hours)
            elif time_range.endswith('d'):
                days = int(time_range[:-1])
                start_time = end_time - timedelta(days=days)
            else:
                start_time = end_time - timedelta(hours=24)  # Default 24h
            
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
                        Period=3600,  # 1 hour periods
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
                            
                            # Simple anomaly detection (values > 2 std dev from mean)
                            if len(averages) > 3:
                                import statistics
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
                MaxItems=50
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
                    not source_ip.startswith('10.') and not source_ip.startswith('172.') and not source_ip.startswith('192.168.'),  # External IP
                    'Console' not in event.get('UserAgent', '')
                ]
                
                if sum(suspicious_indicators) >= 2:
                    suspicious_activity.append({
                        **event_data,
                        'risk_factors': suspicious_indicators,
                        'risk_score': sum(suspicious_indicators) * 25  # 0-100 scale
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