import json
from urllib.parse import parse_qs

def resolve_instance_identifier(identifier):
    """Resolve Name tag or instance ID to actual instance ID"""
    import boto3
    
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

def handle_async_scan(event):
    """Handle async vulnerability scan and send delayed response"""
    import urllib.request
    import os
    
    instance_identifier = event.get('instance_id')
    response_url = event.get('response_url')
    
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
            result_text = f'🔍 Analysis complete for: {display_name or "all instances"} ({instance_id})\n{summary}\nCritical: {critical} | High: {high} | Total: {total}'
            
    except Exception as e:
        result_text = f'❌ Scan failed: {str(e)[:100]}'
    
    # Send delayed response to Slack
    delayed_payload = json.dumps({
        'text': result_text,
        'response_type': 'in_channel'
    })
    
    delayed_req = urllib.request.Request(
        response_url,
        data=delayed_payload.encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(delayed_req, timeout=10):
            pass
    except Exception as e:
        print(f"Failed to send delayed response: {e}")
    
    return {'statusCode': 200}

def handle_async_patch_now(event):
    """Handle async patch execution and send delayed response"""
    import urllib.request
    import os
    
    instance_identifier = event.get('instance_id')
    response_url = event.get('response_url')
    
    # Resolve Name tag to instance ID
    instance_id = resolve_instance_identifier(instance_identifier) if instance_identifier else None
    
    try:
        alb_url = os.environ.get('MCP_SERVER_URL')
        if not alb_url:
            raise Exception('MCP_SERVER_URL environment variable not set')
        
        payload = json.dumps({
            "method": "execute_patch_now",
            "params": {"instance_ids": [instance_id], "patch_level": "non_critical"}
        })
        
        req = urllib.request.Request(
            f"{alb_url}/mcp",
            data=payload.encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            display_name = instance_identifier if instance_identifier != instance_id else instance_id
            if data.get('status') == 'success':
                result_text = f'🔧 Patch execution complete for: {display_name} ({instance_id})\nCommand ID: {data.get("command_id")}\nStatus: {data.get("message")}'
            else:
                result_text = f'❌ Patch execution failed for: {display_name} ({instance_id})\nError: {data.get("error", "Unknown error")}'
            
    except Exception as e:
        result_text = f'❌ Patch execution failed: {str(e)[:100]}'
    
    # Send delayed response to Slack
    delayed_payload = json.dumps({
        'text': result_text,
        'response_type': 'in_channel'
    })
    
    delayed_req = urllib.request.Request(
        response_url,
        data=delayed_payload.encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(delayed_req, timeout=10):
            pass
    except Exception as e:
        print(f"Failed to send delayed response: {e}")
    
    return {'statusCode': 200}

def handle_async_patch_status(event):
    """Handle async patch status check and send delayed response"""
    import urllib.request
    import os
    
    instance_identifier = event.get('instance_id')
    response_url = event.get('response_url')
    
    # Resolve Name tag to instance ID
    instance_id = resolve_instance_identifier(instance_identifier) if instance_identifier else None
    
    try:
        alb_url = os.environ.get('MCP_SERVER_URL')
        if not alb_url:
            raise Exception('MCP_SERVER_URL environment variable not set')
        
        payload = json.dumps({
            "method": "check_patch_compliance",
            "params": {"instance_ids": [instance_id] if instance_id else []}
        })
        
        req = urllib.request.Request(
            f"{alb_url}/mcp",
            data=payload.encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            display_name = instance_identifier if instance_identifier != instance_id else instance_id
            if data.get('status') == 'success':
                if instance_id:
                    compliance_data = data.get('compliance_data', {})
                    instance_data = compliance_data.get(instance_id, {})
                    
                    if instance_data.get('status') == 'no_data':
                        result_text = f'📋 Patch status for: {display_name} ({instance_id})\n⚠️ No patch data available - instance may need SSM agent setup or initial scan\n💡 Try running: /sre-patch-now {instance_identifier} to trigger patching'
                    elif instance_data.get('compliance_status') == 'unknown':
                        result_text = f'📋 Patch status for: {display_name} ({instance_id})\n⚠️ Patch status unknown - may need initial scan\n💡 Use /sre-vuln-check {instance_identifier} to see vulnerabilities'
                    else:
                        status_emoji = '✅' if instance_data.get('compliance_status') == 'compliant' else '⚠️'
                        result_text = f'📋 Patch status for: {display_name} ({instance_id})\n{status_emoji} Compliance: {instance_data.get("compliance_status", "unknown")}\nMissing: {instance_data.get("missing_count", 0)} | Installed: {instance_data.get("installed_count", 0)}'
                else:
                    summary = data.get('summary', {})
                    result_text = f'📋 Patch status summary:\nTotal instances: {summary.get("total_instances", 0)}\nCompliant: {summary.get("compliant_count", 0)} | Non-compliant: {summary.get("non_compliant_count", 0)}'
            else:
                result_text = f'❌ Patch status check failed\nError: {data.get("error", "Unknown error")}'
            
    except Exception as e:
        display_name = instance_identifier if instance_identifier else 'all instances'
        result_text = f'❌ Patch status check failed for {display_name}: {str(e)[:100]}\n💡 Instance may not have SSM agent or proper IAM role'
    
    # Send delayed response to Slack
    delayed_payload = json.dumps({
        'text': result_text,
        'response_type': 'in_channel'
    })
    
    delayed_req = urllib.request.Request(
        response_url,
        data=delayed_payload.encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(delayed_req, timeout=10):
            pass
    except Exception as e:
        print(f"Failed to send delayed response: {e}")
    
    return {'statusCode': 200}

def handle_async_metrics(event):
    """Handle async metrics check and send delayed response"""
    import urllib.request
    import os
    
    instance_identifier = event.get('instance_id')
    response_url = event.get('response_url')
    
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
                result_text = f'❌ Metrics failed for {display_name}: {data["error"][:100]}'
            else:
                metrics = data.get('metrics', {})
                cpu = metrics.get('CPUUtilization', {})
                net_in = metrics.get('NetworkIn', {})
                net_out = metrics.get('NetworkOut', {})
                
                lines = [f'📊 Metrics for: {display_name} ({instance_id})']
                
                if cpu.get('average') is not None:
                    lines.append(f'CPU: {cpu["average"]:.1f}% avg, {cpu.get("maximum", 0):.1f}% max')
                
                if net_in.get('average') is not None:
                    net_in_mb = net_in['average'] / 1024 / 1024
                    lines.append(f'Network In: {net_in_mb:.2f} MB/s avg')
                
                if net_out.get('average') is not None:
                    net_out_mb = net_out['average'] / 1024 / 1024
                    lines.append(f'Network Out: {net_out_mb:.2f} MB/s avg')
                
                if len(lines) == 1:
                    lines.append('⚠️ No metric data available - may need CloudWatch agent')
                
                result_text = '\n'.join(lines)
            
    except Exception as e:
        display_name = instance_identifier if instance_identifier else 'instance'
        result_text = f'❌ Metrics check failed for {display_name}: {str(e)[:100]}'
    
    # Send delayed response to Slack
    delayed_payload = json.dumps({
        'text': result_text,
        'response_type': 'in_channel'
    })
    
    delayed_req = urllib.request.Request(
        response_url,
        data=delayed_payload.encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(delayed_req, timeout=10):
            pass
    except Exception as e:
        print(f"Failed to send delayed response: {e}")
    
    return {'statusCode': 200}

def handler(event, context):
    # Handle async vulnerability scan
    if event.get('async_scan'):
        return handle_async_scan(event)
    
    # Handle async patch execution
    if event.get('async_patch_now'):
        return handle_async_patch_now(event)
    
    # Handle async patch status
    if event.get('async_patch_status'):
        return handle_async_patch_status(event)
    
    # Handle async metrics
    if event.get('async_metrics'):
        return handle_async_metrics(event)
    
    # Handle async patch scheduling
    if event.get('async_schedule_patch'):
        return handle_async_schedule_patch(event)
    
    try:
        body = event.get('body', '')
        
        if body and 'command=' in body:
            parsed = parse_qs(body)
            command = parsed.get('command', [''])[0]
            text = parsed.get('text', [''])[0]
            
            if command == '/sre-vuln-check':
                import boto3
                
                instance_id = text.strip() if text else None
                response_url = parsed.get('response_url', [''])[0]
                
                # Invoke this same Lambda function asynchronously for processing
                lambda_client = boto3.client('lambda')
                async_payload = {
                    'async_scan': True,
                    'instance_id': instance_id,
                    'response_url': response_url
                }
                
                try:
                    response = lambda_client.invoke(
                        FunctionName=context.function_name,
                        InvocationType='Event',  # Async
                        Payload=json.dumps(async_payload)
                    )
                    print(f"Async invoke response: {response}")
                except Exception as e:
                    print(f"Failed to invoke async: {e}")
                    return {
                        'statusCode': 200,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({
                            'response_type': 'ephemeral',
                            'text': f'❌ dispatch_failed: {str(e)}'
                        })
                    }
                
                # Return immediate acknowledgment
                result_text = f'🔍 Vulnerability scan started for: {instance_id or "all instances"}\n⏳ Processing... results will appear shortly'
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'response_type': 'in_channel',
                        'text': result_text
                    })
                }
            
            elif command == '/sre-patch-now':
                import boto3
                
                instance_id = text.strip() if text else None
                response_url = parsed.get('response_url', [''])[0]
                
                if not instance_id:
                    return {
                        'statusCode': 200,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({
                            'response_type': 'ephemeral',
                            'text': '❌ Instance ID required. Usage: /sre-patch-now i-1234567890abcdef0'
                        })
                    }
                
                # Invoke async processing for patching
                lambda_client = boto3.client('lambda')
                async_payload = {
                    'async_patch_now': True,
                    'instance_id': instance_id,
                    'response_url': response_url
                }
                
                try:
                    lambda_client.invoke(
                        FunctionName=context.function_name,
                        InvocationType='Event',
                        Payload=json.dumps(async_payload)
                    )
                except Exception as e:
                    print(f"Failed to invoke async patching: {e}")
                
                result_text = f'🔧 Patch execution started for: {instance_id}\n⏳ Patching... results will appear shortly'
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'response_type': 'in_channel',
                        'text': result_text
                    })
                }
            
            elif command == '/sre-patch-status':
                import boto3
                
                instance_id = text.strip() if text else None
                response_url = parsed.get('response_url', [''])[0]
                
                # Invoke async processing for patch status
                lambda_client = boto3.client('lambda')
                async_payload = {
                    'async_patch_status': True,
                    'instance_id': instance_id,
                    'response_url': response_url
                }
                
                try:
                    lambda_client.invoke(
                        FunctionName=context.function_name,
                        InvocationType='Event',
                        Payload=json.dumps(async_payload)
                    )
                except Exception as e:
                    print(f"Failed to invoke async patch status: {e}")
                
                result_text = f'📋 Patch status check started for: {instance_id or "all instances"}\n⏳ Checking... results will appear shortly'
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'response_type': 'in_channel',
                        'text': result_text
                    })
                }
            
            elif command == '/sre-metrics':
                import boto3
                
                instance_identifier = text.strip() if text else None
                response_url = parsed.get('response_url', [''])[0]
                
                if not instance_identifier:
                    return {
                        'statusCode': 200,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({
                            'response_type': 'ephemeral',
                            'text': '❌ Instance ID required. Usage: /sre-metrics centos-db'
                        })
                    }
                
                # Invoke async processing for metrics
                lambda_client = boto3.client('lambda')
                async_payload = {
                    'async_metrics': True,
                    'instance_id': instance_identifier,
                    'response_url': response_url
                }
                
                try:
                    lambda_client.invoke(
                        FunctionName=context.function_name,
                        InvocationType='Event',
                        Payload=json.dumps(async_payload)
                    )
                except Exception as e:
                    print(f"Failed to invoke async metrics: {e}")
                
                result_text = f'📊 Metrics check started for: {instance_identifier}\n⏳ Gathering performance data... results will appear shortly'
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'response_type': 'in_channel',
                        'text': result_text
                    })
                }
            
            elif command == '/sre-schedule-patch':
                import boto3
                
                instance_identifier = text.strip() if text else None
                response_url = parsed.get('response_url', [''])[0]
                
                if not instance_identifier:
                    return {
                        'statusCode': 200,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({
                            'response_type': 'ephemeral',
                            'text': '❌ Instance ID required. Usage: /sre-schedule-patch centos-db'
                        })
                    }
                
                # Invoke async processing for patch scheduling
                lambda_client = boto3.client('lambda')
                async_payload = {
                    'async_schedule_patch': True,
                    'instance_id': instance_identifier,
                    'response_url': response_url
                }
                
                try:
                    lambda_client.invoke(
                        FunctionName=context.function_name,
                        InvocationType='Event',
                        Payload=json.dumps(async_payload)
                    )
                except Exception as e:
                    print(f"Failed to invoke async schedule patch: {e}")
                
                result_text = f'🤖 AI patch scheduling started for: {instance_identifier}\n⏳ Analyzing vulnerabilities and optimal windows... results will appear shortly'
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'response_type': 'in_channel',
                        'text': result_text
                    })
                }
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'text': 'Command not recognized'})
        }
        
    except Exception as e:
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'text': f'Error: {str(e)}'})
        }