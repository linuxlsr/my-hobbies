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

def handle_async_schedule_patch(event):
    """Handle async patch scheduling and send delayed response"""
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
            "method": "schedule_automated_patching",
            "params": {
                "instance_ids": [instance_id],
                "criticality": "high"
            }
        })
        
        req = urllib.request.Request(
            f"{alb_url}/mcp",
            data=payload.encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req, timeout=60) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            display_name = instance_identifier if instance_identifier != instance_id else instance_id
            
            if data.get('error'):
                result_text = f'❌ Patch scheduling failed for {display_name}: {data["error"][:150]}'
            else:
                schedules = data.get('instance_schedules', [])
                if schedules:
                    schedule = schedules[0]
                    vuln_count = schedule.get('vulnerability_count', 0)
                    risk_score = schedule.get('risk_score', 0)
                    optimal_window = schedule.get('optimal_window', {})
                    window_time = optimal_window.get('recommended_datetime', 'Unknown')
                    confidence = optimal_window.get('confidence_score', 0)
                    duration = schedule.get('estimated_duration', {})
                    total_minutes = duration.get('total_minutes', 0)
                    reasoning = optimal_window.get('reasoning', 'AI-optimized window')
                    
                    risk_emoji = '🔴' if risk_score >= 80 else '🟡' if risk_score >= 60 else '🟢'
                    
                    result_text = f'🤖 AI Patch Schedule & Resolution for: {display_name} ({instance_id})\n'
                    result_text += f'{risk_emoji} Risk Score: {risk_score:.1f} ({vuln_count} vulnerabilities)\n'
                    result_text += f'📅 Scheduled: {window_time}\n'
                    result_text += f'⏱️ Duration: {total_minutes} minutes\n'
                    result_text += f'🧠 Reasoning: {reasoning}\n'
                    result_text += f'🎯 Confidence: {confidence:.0%}\n\n'
                    
                    # Add patch actions summary
                    patch_actions = schedule.get('patch_actions', [])
                    if patch_actions:
                        result_text += f'🔧 REMEDIATION ACTIONS ({len(patch_actions)}):'
                        for action in patch_actions[:3]:  # Show first 3
                            cve_id = action.get('cve_id', 'Unknown')
                            severity = action.get('severity', 'UNKNOWN')
                            severity_emoji = '🔴' if severity == 'CRITICAL' else '🟡' if severity == 'HIGH' else '🟢'
                            result_text += f'\n{severity_emoji} {cve_id} ({severity})'
                        if len(patch_actions) > 3:
                            result_text += f'\n... and {len(patch_actions) - 3} more patches'
                else:
                    result_text = f'✅ Patch scheduling complete for {display_name} but no details available'
            
    except Exception as e:
        display_name = instance_identifier if instance_identifier else 'instance'
        result_text = f'❌ Patch scheduling failed for {display_name}: {str(e)[:100]}'
    
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

def handle_async_report(event):
    """Handle async vulnerability report generation"""
    import urllib.request
    import os
    import boto3
    
    response_url = event.get('response_url')
    
    try:
        # Get all running instances first
        ec2 = boto3.client('ec2')
        response = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
        instance_ids = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_ids.append(instance['InstanceId'])
        
        if not instance_ids:
            result_text = f'📄 Vulnerability Report Summary\n📊 No running instances found'
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
                    result_text = f'❌ Report generation failed: {data["error"][:150]}'
                else:
                    summary = data.get('summary', {})
                    total_vulns = summary.get('total_vulnerabilities', 0)
                    critical = summary.get('critical_count', 0)
                    high = summary.get('high_count', 0)
                    instance_count = len(instance_ids)
                    
                    result_text = f'📄 Vulnerability Report Summary\n'
                    result_text += f'📊 Instances scanned: {instance_count}\n'
                    result_text += f'🔴 Critical: {critical}\n'
                    result_text += f'🟡 High: {high}\n'
                    result_text += f'📊 Total vulnerabilities: {total_vulns}\n\n'
                    
                    if critical > 0:
                        result_text += f'🚨 CRITICAL: {critical} critical vulnerabilities require immediate attention!'
                    elif high > 10:
                        result_text += f'⚠️ HIGH RISK: {high} high-severity vulnerabilities detected'
                    elif total_vulns > 0:
                        result_text += f'📊 MODERATE: {total_vulns} vulnerabilities found, review recommended'
                    else:
                        result_text += f'✅ GOOD: No vulnerabilities detected'
            
    except Exception as e:
        result_text = f'❌ Report generation failed: {str(e)[:100]}'
    
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

def handle_async_health(event):
    """Handle async system health check"""
    import urllib.request
    import os
    import boto3
    
    response_url = event.get('response_url')
    
    try:
        # Get EC2 instance status directly
        ec2 = boto3.client('ec2')
        response = ec2.describe_instances()
        
        running = stopped = pending = terminated = 0
        instances = []
        
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                state = instance['State']['Name']
                if state == 'running':
                    running += 1
                elif state == 'stopped':
                    stopped += 1
                elif state == 'pending':
                    pending += 1
                elif state == 'terminated':
                    terminated += 1
                
                # Get instance name
                name = 'N/A'
                for tag in instance.get('Tags', []):
                    if tag['Key'] == 'Name':
                        name = tag['Value']
                        break
                
                instances.append({
                    'id': instance['InstanceId'],
                    'name': name,
                    'state': state,
                    'type': instance['InstanceType']
                })
        
        total = len(instances)
        
        result_text = f'🏥 System Health\n'
        result_text += f'📊 Total instances: {total}\n'
        result_text += f'🟢 Running: {running}\n'
        result_text += f'🔴 Stopped: {stopped}\n'
        
        if pending > 0:
            result_text += f'🟡 Pending: {pending}\n'
        if terminated > 0:
            result_text += f'⚫ Terminated: {terminated}\n'
        
        # Health assessment
        if running == total and total > 0:
            result_text += f'\n🟢 All instances healthy'
        elif running > 0:
            result_text += f'\n🟡 {running}/{total} instances running'
        else:
            result_text += f'\n🔴 No instances running'
        
        # Show running instances
        running_instances = [i for i in instances if i['state'] == 'running']
        if running_instances:
            result_text += f'\n\nRunning instances:'
            for inst in running_instances[:5]:  # Show first 5
                result_text += f'\n• {inst["name"]} ({inst["id"]})'
            if len(running_instances) > 5:
                result_text += f'\n... and {len(running_instances) - 5} more'
            
    except Exception as e:
        result_text = f'❌ Health check failed: {str(e)[:100]}'
    
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

def handle_async_security_events(event):
    """Handle async security events monitoring"""
    import urllib.request
    import os
    import boto3
    
    instance_identifier = event.get('instance_id')
    response_url = event.get('response_url')
    
    try:
        # Get instance IDs - either specific instance or all running instances
        if instance_identifier:
            instance_id = resolve_instance_identifier(instance_identifier)
            instance_ids = [instance_id] if instance_id else []
        else:
            # Get all running instances
            ec2 = boto3.client('ec2')
            response = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
            instance_ids = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instance_ids.append(instance['InstanceId'])
        
        if not instance_ids:
            result_text = f'🔒 Security Events\n⚠️ No instances found to monitor'
        else:
            alb_url = os.environ.get('MCP_SERVER_URL')
            if not alb_url:
                raise Exception('MCP_SERVER_URL environment variable not set')
            
            payload = json.dumps({
                "method": "monitor_security_events",
                "params": {
                    "instance_ids": instance_ids,
                    "event_types": ["login", "privilege_escalation", "config_changes"],
                    "time_range": "24h"
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
                    result_text = f'❌ Security monitoring failed: {data["error"][:150]}'
                else:
                    alerts = data.get('alerts', [])
                    total_instances = data.get('total_instances', len(instance_ids))
                    
                    result_text = f'🔒 Security Events (24h)\n'
                    result_text += f'📊 Instances monitored: {total_instances}\n'
                    result_text += f'🚨 Security alerts: {len(alerts)}\n\n'
                    
                    if alerts:
                        result_text += f'🚨 HIGH-RISK SECURITY ALERTS:\n'
                        for alert in alerts[:5]:  # Show first 5 alerts
                            instance_id = alert.get('instance_id', 'Unknown')
                            alert_level = alert.get('alert_level', 'unknown')
                            risk_emoji = '🔴' if alert_level == 'high' else '🟡'
                            result_text += f'{risk_emoji} {instance_id}: {alert_level} risk\n'
                        
                        if len(alerts) > 5:
                            result_text += f'... and {len(alerts) - 5} more alerts\n'
                        
                        result_text += f'\n⚠️ Immediate investigation recommended!'
                    else:
                        result_text += f'✅ No high-risk security events detected'
            
    except Exception as e:
        target = instance_identifier if instance_identifier else 'instances'
        result_text = f'❌ Security monitoring failed for {target}: {str(e)[:100]}'
    
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

def handle_async_show_patches(event):
    """Handle async show scheduled patches"""
    import urllib.request
    import os
    
    instance_identifier = event.get('instance_id')
    response_url = event.get('response_url')
    
    # Resolve Name tag to instance ID if provided
    instance_id = resolve_instance_identifier(instance_identifier) if instance_identifier else None
    
    try:
        alb_url = os.environ.get('MCP_SERVER_URL')
        if not alb_url:
            raise Exception('MCP_SERVER_URL environment variable not set')
        
        payload = json.dumps({
            "method": "get_scheduled_patches",
            "params": {
                "instance_id": instance_id
            }
        })
        
        req = urllib.request.Request(
            f"{alb_url}/mcp",
            data=payload.encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            if data.get('error'):
                result_text = f'❌ Failed to get scheduled patches: {data["error"][:150]}'
            else:
                patches = data.get('scheduled_patches', [])
                total_patches = data.get('total_scheduled', len(patches))
                
                display_name = instance_identifier if instance_identifier else "all instances"
                
                result_text = f'📅 Scheduled Patches for: {display_name}\n'
                result_text += f'📊 Total scheduled: {total_patches}\n\n'
                
                if patches:
                    for patch in patches[:5]:  # Show first 5 patches
                        instance_id = patch.get('instance_id', 'Unknown')
                        rule_name = patch.get('rule_name', 'Unknown')
                        scheduled_time = patch.get('scheduled_time', 'Unknown')
                        criticality = patch.get('criticality', 'Unknown')
                        duration = patch.get('estimated_duration', 'Unknown')
                        status = patch.get('status', 'Unknown')
                        vuln_count = patch.get('vulnerability_count', 'Unknown')
                        
                        # Extract info from rule name if available
                        if rule_name != 'Unknown' and 'patch-' in rule_name:
                            parts = rule_name.split('-')
                            if len(parts) >= 4:
                                criticality = parts[2] if parts[2] != 'Unknown' else criticality
                                # Try to parse timestamp from rule name
                                if len(parts) >= 4:
                                    timestamp_part = parts[-1]
                                    if len(timestamp_part) >= 12:
                                        try:
                                            year = timestamp_part[:4]
                                            month = timestamp_part[4:6]
                                            day = timestamp_part[6:8]
                                            hour = timestamp_part[8:10]
                                            minute = timestamp_part[10:12]
                                            scheduled_time = f"{year}-{month}-{day} {hour}:{minute} UTC"
                                        except:
                                            pass
                        
                        # Clean up scheduled time if it's a cron expression
                        if 'cron(' in scheduled_time:
                            scheduled_time = 'EventBridge rule active'
                        
                        criticality_emoji = '🔴' if criticality == 'critical' else '🟡' if criticality == 'high' else '🟢'
                        status_emoji = '✅' if status == 'ENABLED' else '⚠️'
                        
                        result_text += f'{criticality_emoji} {instance_id} ({criticality})\n'
                        result_text += f'  📅 {scheduled_time}\n'
                        result_text += f'  🔴 {vuln_count} vulnerabilities | {status_emoji} {status}\n'
                        result_text += f'  🏷️ Rule: {rule_name}\n\n'
                    
                    if len(patches) > 5:
                        result_text += f'... and {len(patches) - 5} more scheduled patches\n'
                    
                    result_text += f'📝 View in EventBridge console for details'
                else:
                    result_text += f'ℹ️ No scheduled patches found\n💡 Use /schedule-patch to create patch schedules'
            
    except Exception as e:
        display_name = instance_identifier if instance_identifier else 'instances'
        result_text = f'❌ Failed to get scheduled patches for {display_name}: {str(e)[:100]}'
    
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
    
    # Handle async report
    if event.get('async_report'):
        return handle_async_report(event)
    
    # Handle async health
    if event.get('async_health'):
        return handle_async_health(event)
    
    # Handle async security events
    if event.get('async_security_events'):
        return handle_async_security_events(event)
    
    # Handle async show patches
    if event.get('async_show_patches'):
        return handle_async_show_patches(event)
    

    
    try:
        body = event.get('body', '')
        
        if body and 'command=' in body:
            parsed = parse_qs(body)
            command = parsed.get('command', [''])[0]
            text = parsed.get('text', [''])[0]
            
            if command == '/vuln-check':
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
            
            elif command == '/patch-now':
                import boto3
                
                instance_id = text.strip() if text else None
                response_url = parsed.get('response_url', [''])[0]
                
                if not instance_id:
                    return {
                        'statusCode': 200,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({
                            'response_type': 'ephemeral',
                            'text': '❌ Instance ID required. Usage: /patch-now i-1234567890abcdef0'
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
            
            elif command == '/patch-status':
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
            
            elif command == '/metrics':
                import boto3
                
                instance_identifier = text.strip() if text else None
                response_url = parsed.get('response_url', [''])[0]
                
                if not instance_identifier:
                    return {
                        'statusCode': 200,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({
                            'response_type': 'ephemeral',
                            'text': '❌ Instance ID required. Usage: /metrics centos-db'
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
            
            elif command == '/schedule-patch':
                import boto3
                
                instance_identifier = text.strip() if text else None
                response_url = parsed.get('response_url', [''])[0]
                
                if not instance_identifier:
                    return {
                        'statusCode': 200,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({
                            'response_type': 'ephemeral',
                            'text': '❌ Instance ID required. Usage: /schedule-patch centos-db'
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
                
                result_text = f'🤖 AI patch scheduling & resolution started for: {instance_identifier}\n⏳ Analyzing vulnerabilities, creating remediation plan, and finding optimal windows... results will appear shortly'
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'response_type': 'in_channel',
                        'text': result_text
                    })
                }
            
            elif command == '/report':
                import boto3
                
                response_url = parsed.get('response_url', [''])[0]
                
                # Invoke async processing for vulnerability report
                lambda_client = boto3.client('lambda')
                async_payload = {
                    'async_report': True,
                    'response_url': response_url
                }
                
                try:
                    lambda_client.invoke(
                        FunctionName=context.function_name,
                        InvocationType='Event',
                        Payload=json.dumps(async_payload)
                    )
                except Exception as e:
                    print(f"Failed to invoke async report: {e}")
                
                result_text = f'📄 Generating vulnerability report for all instances...\n⏳ Analyzing security posture... results will appear shortly'
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'response_type': 'in_channel',
                        'text': result_text
                    })
                }
            
            elif command == '/health':
                import boto3
                
                response_url = parsed.get('response_url', [''])[0]
                
                # Invoke async processing for status check
                lambda_client = boto3.client('lambda')
                async_payload = {
                    'async_health': True,
                    'response_url': response_url
                }
                
                try:
                    lambda_client.invoke(
                        FunctionName=context.function_name,
                        InvocationType='Event',
                        Payload=json.dumps(async_payload)
                    )
                except Exception as e:
                    print(f"Failed to invoke async health: {e}")
                
                result_text = f'🏥 Checking system health...\n⏳ Gathering instance data... results will appear shortly'
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'response_type': 'in_channel',
                        'text': result_text
                    })
                }
            
            elif command == '/security-events':
                import boto3
                
                instance_identifier = text.strip() if text else None
                response_url = parsed.get('response_url', [''])[0]
                
                # Invoke async processing for security events
                lambda_client = boto3.client('lambda')
                async_payload = {
                    'async_security_events': True,
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
                    print(f"Failed to invoke async security events: {e}")
                
                target = instance_identifier if instance_identifier else "all instances"
                result_text = f'🔒 Security monitoring started for: {target}\n⏳ Analyzing security events... results will appear shortly'
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'response_type': 'in_channel',
                        'text': result_text
                    })
                }
            
            elif command == '/show-patches':
                import boto3
                
                instance_identifier = text.strip() if text else None
                response_url = parsed.get('response_url', [''])[0]
                
                # Invoke async processing for showing scheduled patches
                lambda_client = boto3.client('lambda')
                async_payload = {
                    'async_show_patches': True,
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
                    print(f"Failed to invoke async show patches: {e}")
                
                target = instance_identifier if instance_identifier else "all instances"
                result_text = f'📅 Getting scheduled patches for: {target}\n⏳ Checking patch schedules... results will appear shortly'
                
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