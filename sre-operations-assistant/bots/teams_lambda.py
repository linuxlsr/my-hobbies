import json
import urllib.request
import urllib.parse
import os
import boto3

def resolve_instance_identifier(identifier):
    """Resolve Name tag or instance ID to actual instance ID"""
    if identifier.startswith('i-'):
        return identifier
    
    # Try to find instance by Name tag
    try:
        ec2 = boto3.client('ec2')
        response = ec2.describe_instances(
            Filters=[
                {'Name': 'tag:Name', 'Values': [identifier]},
                {'Name': 'instance-state-name', 'Values': ['running', 'stopped']}
            ]
        )
        
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                return instance['InstanceId']
        
        return identifier  # Return original if not found
    except Exception:
        return identifier

def send_teams_message(webhook_url, message_data):
    """Send message to Teams webhook"""
    try:
        payload = json.dumps(message_data)
        req = urllib.request.Request(
            webhook_url,
            data=payload.encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status == 200
    except Exception as e:
        print(f"Failed to send Teams message: {e}")
        return False

def handle_async_vuln_check(event):
    """Handle async vulnerability check and send Teams message"""
    instance_identifier = event.get('instance_id')
    webhook_url = event.get('webhook_url')
    
    # Resolve Name tag to instance ID
    instance_id = resolve_instance_identifier(instance_identifier) if instance_identifier else None
    
    try:
        alb_url = os.environ.get('MCP_SERVER_URL')
        if not alb_url:
            raise Exception('MCP_SERVER_URL environment variable not set')
        
        payload = json.dumps({
            "method": "get_inspector_findings",
            "params": {"instance_id": instance_id, "severity": "all"}
        })
        
        req = urllib.request.Request(
            f"{alb_url}/mcp",
            data=payload.encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            summary = data.get('summary', 'No data')
            critical = data.get('critical_count', 0)
            high = data.get('high_count', 0)
            total = data.get('total_count', 0)
            
            display_name = instance_identifier if instance_identifier != instance_id else instance_id
            
            # Create Teams message
            teams_message = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": "D13438" if critical > 0 else "FF6D00" if high > 0 else "00FF00",
                "summary": f"Vulnerability Analysis for {display_name}",
                "sections": [{
                    "activityTitle": f"🔍 Vulnerability Analysis Complete",
                    "activitySubtitle": f"Instance: {display_name} ({instance_id})",
                    "facts": [
                        {"name": "Summary", "value": summary},
                        {"name": "Critical", "value": str(critical)},
                        {"name": "High", "value": str(high)},
                        {"name": "Total", "value": str(total)}
                    ]
                }]
            }
            
    except Exception as e:
        display_name = instance_identifier if instance_identifier else 'instance'
        teams_message = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "D13438",
            "summary": f"Vulnerability scan failed for {display_name}",
            "sections": [{
                "activityTitle": "❌ Vulnerability Scan Failed",
                "activitySubtitle": f"Instance: {display_name}",
                "facts": [
                    {"name": "Error", "value": str(e)[:200]}
                ]
            }]
        }
    
    send_teams_message(webhook_url, teams_message)
    return {'statusCode': 200}

def handle_async_metrics(event):
    """Handle async metrics check and send Teams message"""
    instance_identifier = event.get('instance_id')
    webhook_url = event.get('webhook_url')
    
    # Resolve Name tag to instance ID
    instance_id = resolve_instance_identifier(instance_identifier) if instance_identifier else None
    
    try:
        alb_url = os.environ.get('MCP_SERVER_URL')
        if not alb_url:
            raise Exception('MCP_SERVER_URL environment variable not set')
        
        payload = json.dumps({
            "method": "get_ec2_cloudwatch_metrics",
            "params": {
                "instance_id": instance_id,
                "metric_names": ["CPUUtilization", "NetworkIn", "NetworkOut"],
                "time_range": "24h"
            }
        })
        
        req = urllib.request.Request(
            f"{alb_url}/mcp",
            data=payload.encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            display_name = instance_identifier if instance_identifier != instance_id else instance_id
            
            if data.get('error'):
                teams_message = {
                    "@type": "MessageCard",
                    "@context": "http://schema.org/extensions",
                    "themeColor": "D13438",
                    "summary": f"Metrics failed for {display_name}",
                    "sections": [{
                        "activityTitle": "❌ Metrics Check Failed",
                        "activitySubtitle": f"Instance: {display_name} ({instance_id})",
                        "facts": [
                            {"name": "Error", "value": data['error'][:200]}
                        ]
                    }]
                }
            else:
                metrics = data.get('metrics', {})
                cpu = metrics.get('CPUUtilization', {})
                net_in = metrics.get('NetworkIn', {})
                net_out = metrics.get('NetworkOut', {})
                
                facts = [{"name": "Instance", "value": f"{display_name} ({instance_id})"}]
                
                if cpu.get('average') is not None:
                    facts.append({"name": "CPU Average", "value": f"{cpu['average']:.1f}%"})
                    facts.append({"name": "CPU Maximum", "value": f"{cpu.get('maximum', 0):.1f}%"})
                
                if net_in.get('average') is not None:
                    net_in_mb = net_in['average'] / 1024 / 1024
                    facts.append({"name": "Network In", "value": f"{net_in_mb:.2f} MB/s avg"})
                
                if net_out.get('average') is not None:
                    net_out_mb = net_out['average'] / 1024 / 1024
                    facts.append({"name": "Network Out", "value": f"{net_out_mb:.2f} MB/s avg"})
                
                if len(facts) == 1:
                    facts.append({"name": "Status", "value": "No metric data available - may need CloudWatch agent"})
                
                teams_message = {
                    "@type": "MessageCard",
                    "@context": "http://schema.org/extensions",
                    "themeColor": "0076D7",
                    "summary": f"Metrics for {display_name}",
                    "sections": [{
                        "activityTitle": "📊 Performance Metrics (24h)",
                        "activitySubtitle": "CloudWatch Data",
                        "facts": facts
                    }]
                }
            
    except Exception as e:
        display_name = instance_identifier if instance_identifier else 'instance'
        teams_message = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "D13438",
            "summary": f"Metrics check failed for {display_name}",
            "sections": [{
                "activityTitle": "❌ Metrics Check Failed",
                "activitySubtitle": f"Instance: {display_name}",
                "facts": [
                    {"name": "Error", "value": str(e)[:200]}
                ]
            }]
        }
    
    send_teams_message(webhook_url, teams_message)
    return {'statusCode': 200}

def handle_async_report(event):
    """Handle async vulnerability report generation"""
    webhook_url = event.get('webhook_url')
    
    try:
        # Get all running instances first
        ec2 = boto3.client('ec2')
        response = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
        instance_ids = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_ids.append(instance['InstanceId'])
        
        if not instance_ids:
            teams_message = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": "0076D7",
                "summary": "Vulnerability Report",
                "sections": [{
                    "activityTitle": "📄 Vulnerability Report Summary",
                    "facts": [
                        {"name": "Status", "value": "No running instances found"}
                    ]
                }]
            }
        else:
            alb_url = os.environ.get('MCP_SERVER_URL')
            if not alb_url:
                raise Exception('MCP_SERVER_URL environment variable not set')
            
            payload = json.dumps({
                "method": "generate_vulnerability_report",
                "params": {
                    "instance_ids": instance_ids,
                    "format": "summary"
                }
            })
            
            req = urllib.request.Request(
                f"{alb_url}/mcp",
                data=payload.encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=60) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                if data.get('error'):
                    teams_message = {
                        "@type": "MessageCard",
                        "@context": "http://schema.org/extensions",
                        "themeColor": "D13438",
                        "summary": "Report generation failed",
                        "sections": [{
                            "activityTitle": "❌ Report Generation Failed",
                            "facts": [
                                {"name": "Error", "value": data['error'][:200]}
                            ]
                        }]
                    }
                else:
                    summary = data.get('summary', {})
                    total_vulns = summary.get('total_vulnerabilities', 0)
                    critical = summary.get('critical_count', 0)
                    high = summary.get('high_count', 0)
                    instance_count = len(instance_ids)
                    
                    # Determine color based on severity
                    if critical > 0:
                        color = "D13438"  # Red
                        status = f"🚨 CRITICAL: {critical} critical vulnerabilities require immediate attention!"
                    elif high > 10:
                        color = "FF6D00"  # Orange
                        status = f"⚠️ HIGH RISK: {high} high-severity vulnerabilities detected"
                    elif total_vulns > 0:
                        color = "0076D7"  # Blue
                        status = f"📊 MODERATE: {total_vulns} vulnerabilities found, review recommended"
                    else:
                        color = "00FF00"  # Green
                        status = "✅ GOOD: No vulnerabilities detected"
                    
                    teams_message = {
                        "@type": "MessageCard",
                        "@context": "http://schema.org/extensions",
                        "themeColor": color,
                        "summary": "Vulnerability Report Summary",
                        "sections": [{
                            "activityTitle": "📄 Vulnerability Report Summary",
                            "facts": [
                                {"name": "Instances Scanned", "value": str(instance_count)},
                                {"name": "Critical", "value": str(critical)},
                                {"name": "High", "value": str(high)},
                                {"name": "Total Vulnerabilities", "value": str(total_vulns)},
                                {"name": "Assessment", "value": status}
                            ]
                        }]
                    }
            
    except Exception as e:
        teams_message = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "D13438",
            "summary": "Report generation failed",
            "sections": [{
                "activityTitle": "❌ Report Generation Failed",
                "facts": [
                    {"name": "Error", "value": str(e)[:200]}
                ]
            }]
        }
    
    send_teams_message(webhook_url, teams_message)
    return {'statusCode': 200}

def handler(event, context):
    # Handle async operations
    if event.get('async_vuln_check'):
        return handle_async_vuln_check(event)
    
    if event.get('async_metrics'):
        return handle_async_metrics(event)
    
    if event.get('async_report'):
        return handle_async_report(event)
    
    try:
        # Parse Teams webhook payload
        body = event.get('body', '')
        if isinstance(body, str):
            try:
                webhook_data = json.loads(body)
            except:
                webhook_data = {}
        else:
            webhook_data = body
        
        # Extract command from Teams message
        text = webhook_data.get('text', '')
        
        # Get webhook URL from environment
        webhook_url = os.environ.get('TEAMS_WEBHOOK_URL')
        if not webhook_url:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Teams webhook URL not configured'})
            }
        
        # Parse command
        if text.startswith('/vuln-check'):
            instance_identifier = text.replace('/vuln-check', '').strip()
            
            if not instance_identifier:
                teams_message = {
                    "@type": "MessageCard",
                    "@context": "http://schema.org/extensions",
                    "themeColor": "FF6D00",
                    "summary": "Usage Error",
                    "sections": [{
                        "activityTitle": "❌ Instance ID Required",
                        "facts": [
                            {"name": "Usage", "value": "/vuln-check centos-db"}
                        ]
                    }]
                }
                send_teams_message(webhook_url, teams_message)
                return {'statusCode': 200}
            
            # Invoke async processing
            lambda_client = boto3.client('lambda')
            async_payload = {
                'async_vuln_check': True,
                'instance_id': instance_identifier,
                'webhook_url': webhook_url
            }
            
            try:
                lambda_client.invoke(
                    FunctionName=context.function_name,
                    InvocationType='Event',
                    Payload=json.dumps(async_payload)
                )
            except Exception as e:
                print(f"Failed to invoke async: {e}")
            
            # Send immediate acknowledgment
            teams_message = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": "0076D7",
                "summary": f"Vulnerability scan started for {instance_identifier}",
                "sections": [{
                    "activityTitle": "🔍 Vulnerability Scan Started",
                    "activitySubtitle": f"Instance: {instance_identifier}",
                    "facts": [
                        {"name": "Status", "value": "⏳ Processing... results will appear shortly"}
                    ]
                }]
            }
            
        elif text.startswith('/metrics'):
            instance_identifier = text.replace('/metrics', '').strip()
            
            if not instance_identifier:
                teams_message = {
                    "@type": "MessageCard",
                    "@context": "http://schema.org/extensions",
                    "themeColor": "FF6D00",
                    "summary": "Usage Error",
                    "sections": [{
                        "activityTitle": "❌ Instance ID Required",
                        "facts": [
                            {"name": "Usage", "value": "/metrics centos-db"}
                        ]
                    }]
                }
                send_teams_message(webhook_url, teams_message)
                return {'statusCode': 200}
            
            # Invoke async processing
            lambda_client = boto3.client('lambda')
            async_payload = {
                'async_metrics': True,
                'instance_id': instance_identifier,
                'webhook_url': webhook_url
            }
            
            try:
                lambda_client.invoke(
                    FunctionName=context.function_name,
                    InvocationType='Event',
                    Payload=json.dumps(async_payload)
                )
            except Exception as e:
                print(f"Failed to invoke async: {e}")
            
            # Send immediate acknowledgment
            teams_message = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": "0076D7",
                "summary": f"Metrics check started for {instance_identifier}",
                "sections": [{
                    "activityTitle": "📊 Metrics Check Started",
                    "activitySubtitle": f"Instance: {instance_identifier}",
                    "facts": [
                        {"name": "Status", "value": "⏳ Gathering performance data... results will appear shortly"}
                    ]
                }]
            }
            
        elif text.startswith('/report'):
            # Invoke async processing
            lambda_client = boto3.client('lambda')
            async_payload = {
                'async_report': True,
                'webhook_url': webhook_url
            }
            
            try:
                lambda_client.invoke(
                    FunctionName=context.function_name,
                    InvocationType='Event',
                    Payload=json.dumps(async_payload)
                )
            except Exception as e:
                print(f"Failed to invoke async: {e}")
            
            # Send immediate acknowledgment
            teams_message = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": "0076D7",
                "summary": "Generating vulnerability report for all instances",
                "sections": [{
                    "activityTitle": "📄 Vulnerability Report Generation Started",
                    "facts": [
                        {"name": "Status", "value": "⏳ Analyzing security posture... results will appear shortly"}
                    ]
                }]
            }
            
        else:
            teams_message = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": "0076D7",
                "summary": "Available Commands",
                "sections": [{
                    "activityTitle": "🤖 SRE Operations Assistant",
                    "activitySubtitle": "Available Commands:",
                    "facts": [
                        {"name": "/vuln-check <instance>", "value": "Check vulnerabilities"},
                        {"name": "/metrics <instance>", "value": "Get performance metrics"},
                        {"name": "/report", "value": "Generate vulnerability report"}
                    ]
                }]
            }
        
        send_teams_message(webhook_url, teams_message)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'success'})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }