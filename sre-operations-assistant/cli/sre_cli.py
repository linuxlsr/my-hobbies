#!/usr/bin/env python3
"""AI-Powered SRE Operations CLI - Consolidated with LLM Natural Language Processing"""

import click
import asyncio
import requests
from rich.console import Console
from rich.table import Table
from typing import List, Optional, Dict, Any
import boto3
import json
import re

console = Console()

class LLMParser:
    """Use AWS Bedrock to parse natural language commands"""
    
    def __init__(self):
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-west-2')
        self.model_id = "amazon.titan-text-express-v1"
    
    def parse_command(self, user_input: str) -> Dict[str, Any]:
        """Parse natural language using Titan"""
        
        # Extract instance ID or name
        instance_match = re.search(r'i-[a-f0-9]{8,17}', user_input)
        instance_id = instance_match.group(0) if instance_match else "none"
        
        # Look for instance names after 'for' keyword
        if instance_id == "none" and ' for ' in user_input.lower():
            parts = user_input.lower().split(' for ')
            if len(parts) > 1:
                # Take the part after 'for' and get the first word
                after_for = parts[1].strip().split()[0]
                if len(after_for) > 2:
                    instance_id = after_for
        
        prompt = f"Parse: '{user_input}'\n\nWhat is the main request? Look for these exact words:\n- If 'cpu' or 'memory' or 'metrics' → cloudwatch_metrics\n- If 'vuln' or 'vulnerabilities' or 'security' → vulnerabilities\n- If 'status' or 'health' → status\n- If 'scan all' → scan_all\n- If 'list' or 'instances' → list\n\nReturn JSON:\n{{\"command\": \"cloudwatch_metrics\", \"instance_ids\": [], \"confidence\": 0.9}}\n\nJSON:"

        try:
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": 100,
                        "temperature": 0.0,
                        "topP": 0.1
                    }
                })
            )
            
            result = json.loads(response['body'].read())
            content = result['results'][0]['outputText'].strip()
            
            # Clean and extract JSON
            content = content.replace('```json', '').replace('```', '').replace('JSON:', '').strip()
            
            # Handle partial JSON like "command": "status"
            if content.startswith('"command"') and ':' in content:
                # Extract just the command part, ignore any trailing text
                command_part = content.split(',')[0]  # Take only first part before comma
                command_value = command_part.split(':')[1].strip().strip('"').strip()
                if command_value:  # Only use if we got a valid command
                    parsed = {"command": command_value, "confidence": 0.9, "instance_ids": []}
                else:
                    raise ValueError(f"Empty command in partial JSON: {content}")
            else:
                # Find complete JSON
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_content = content[json_start:json_end]
                    parsed = json.loads(json_content)
                else:
                    raise ValueError(f"No JSON found: {content}")
            
            # Fix instance IDs based on command
            command = parsed.get("command")
            instance_ids = parsed.get("instance_ids", [])
            
            if command in ['list', 'scan_all'] or (command == 'status' and instance_id == "none"):
                instance_ids = []
            elif instance_id != "none":
                instance_ids = [instance_id]
            elif not instance_ids and instance_id != "none":
                instance_ids = [instance_id]
            
            return {
                "command": parsed.get("command"),
                "instance_ids": instance_ids,
                "time_range": "24h",
                "confidence": parsed.get("confidence", 0.9),
                "original_text": user_input,
                "method": "llm"
            }
                
        except Exception as e:
            console.print(f"[dim]LLM failed, using fallback[/dim]")
            return self._fallback_parse(user_input, str(e))
    
    def _fallback_parse(self, text: str, error: str) -> Dict[str, Any]:
        """Fallback regex parsing if LLM fails"""
        
        # Basic regex fallback
        instance_match = re.search(r'i-[a-f0-9]{8,17}', text)
        instance_ids = [instance_match.group(0)] if instance_match else []
        
        # Simple command detection
        text_lower = text.lower()
        if any(phrase in text_lower for phrase in ['scan all', 'scan everything', 'check all']):
            command = 'scan_all'
        elif any(word in text_lower for word in ['cpu', 'mem', 'memory', 'metrics', 'performance', 'cloudwatch']) and 'all' not in text_lower:
            command = 'cloudwatch_metrics'
        elif any(word in text_lower for word in ['vuln', 'vulns', 'vulnerabilities', 'security', 'cve']) and 'all' not in text_lower:
            command = 'vulnerabilities'
        elif any(word in text_lower for word in ['events', 'cloudtrail', 'audit']):
            command = 'cloudtrail_events'
        elif any(word in text_lower for word in ['list', 'instances']):
            command = 'list'
        elif any(word in text_lower for word in ['status', 'health']):
            command = 'status'
        else:
            command = None
        
        # If command detected but no instance ID, suggest higher confidence for prompting
        confidence = 0.8 if command and instance_ids else 0.6 if command and command == 'scan_all' else 0.3 if command else 0.1
        
        # scan_all, list, and status don't need instance IDs
        needs_instance_id = command is not None and not instance_ids and command not in ['scan_all', 'list', 'status']
        
        return {
            "command": command,
            "instance_ids": instance_ids,
            "time_range": "24h",
            "confidence": confidence,
            "original_text": text,
            "method": "fallback",
            "llm_error": error,
            "needs_instance_id": needs_instance_id
        }

# Get MCP server endpoint
def get_mcp_endpoint():
    # Try localhost first
    for url in ["http://localhost:8000", "http://127.0.0.1:8000"]:
        try:
            response = requests.get(f"{url}/health", timeout=2)
            if response.status_code == 200:
                console.print(f"[green]Connected to local server: {url}[/green]")
                return url
        except:
            continue
    
    # Try ECS service via ALB
    try:
        # Get ALB DNS name from ECS service
        ecs = boto3.client('ecs')
        elbv2 = boto3.client('elbv2')
        
        # Get service details
        services = ecs.describe_services(
            cluster='sre-ops-assistant-cluster',
            services=['sre-ops-assistant-mcp-server']
        )
        
        if services['services']:
            service = services['services'][0]
            # Get load balancer info from service
            for lb in service.get('loadBalancers', []):
                if 'targetGroupArn' in lb:
                    # Get ALB from target group
                    tg_response = elbv2.describe_target_groups(
                        TargetGroupArns=[lb['targetGroupArn']]
                    )
                    if tg_response['TargetGroups']:
                        lb_arn = tg_response['TargetGroups'][0]['LoadBalancerArns'][0]
                        lb_response = elbv2.describe_load_balancers(
                            LoadBalancerArns=[lb_arn]
                        )
                        if lb_response['LoadBalancers']:
                            dns_name = lb_response['LoadBalancers'][0]['DNSName']
                            alb_url = f"http://{dns_name}"
                            
                            # Test ALB endpoint
                            response = requests.get(f"{alb_url}/health", timeout=5)
                            if response.status_code == 200:
                                console.print(f"[green]Connected to ECS service: {alb_url}[/green]")
                                return alb_url
    except Exception as e:
        console.print(f"[yellow]ECS connection failed: {e}[/yellow]")
    
    # Try getting ALB URL from terraform output (if available)
    try:
        import subprocess
        result = subprocess.run(
            ['terraform', 'output', '-raw', 'mcp_server_url'],
            cwd='../infrastructure',
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            alb_url = result.stdout.strip()
            response = requests.get(f"{alb_url}/health", timeout=5)
            if response.status_code == 200:
                console.print(f"[green]Connected via terraform output: {alb_url}[/green]")
                return alb_url
    except Exception:
        pass
    
    return None


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """SRE Operations Assistant CLI - MCP-powered vulnerability management"""
    pass


@cli.command()
@click.option('--instance-id', '-i', help='EC2 instance ID')
@click.option('--severity', '-s', default='all', help='Vulnerability severity filter')
def vulnerabilities(instance_id: Optional[str], severity: str):
    """Get vulnerability findings for EC2 instances"""
    console.print(f"[bold blue]Analyzing vulnerabilities...[/bold blue]")
    
    endpoint = get_mcp_endpoint()
    if not endpoint:
        console.print("[red]✗ MCP server not accessible[/red]")
        return
    
    try:
        response = requests.post(f"{endpoint}/mcp", json={
            "method": "get_inspector_findings",
            "params": {"instance_id": instance_id, "severity": severity}
        }, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            console.print(f"[green]✓ Found {len(data.get('findings', []))} vulnerabilities[/green]")
        else:
            console.print(f"[red]✗ Error: {response.status_code}[/red]")
    except Exception as e:
        console.print(f"[red]✗ Connection failed: {e}[/red]")


@cli.command()
@click.option('--instance-id', '-i', required=True, help='EC2 instance ID')
@click.option('--days', '-d', default=7, help='Days ahead to analyze')
def patch_window(instance_id: str, days: int):
    """Find optimal patching window using GenAI analysis"""
    console.print(f"[bold blue]Analyzing optimal patch windows...[/bold blue]")
    
    endpoint = get_mcp_endpoint()
    if not endpoint:
        console.print("[red]✗ MCP server not accessible[/red]")
        return
    
    try:
        response = requests.post(f"{endpoint}/mcp", json={
            "method": "analyze_optimal_patch_window",
            "params": {"instance_id": instance_id, "days_ahead": days}
        }, timeout=30)
        
        if response.status_code == 200:
            console.print("[green]✓ Optimal windows identified[/green]")
        else:
            console.print(f"[red]✗ Error: {response.status_code}[/red]")
    except Exception as e:
        console.print(f"[red]✗ Connection failed: {e}[/red]")


@cli.command()
@click.option('--instance-id', '-i', required=True, help='EC2 instance ID')
@click.option('--patch-level', default='non_critical', help='Patch level (critical, non_critical, all)')
def patch_now(instance_id: str, patch_level: str):
    """Execute patching on an instance immediately"""
    console.print(f"[bold blue]Executing patches on {instance_id}...[/bold blue]")
    
    endpoint = get_mcp_endpoint()
    if not endpoint:
        console.print("[red]✗ MCP server not accessible[/red]")
        return
    
    try:
        response = requests.post(f"{endpoint}/mcp", json={
            "method": "execute_patch_now",
            "params": {"instance_ids": [instance_id], "patch_level": patch_level}
        }, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                console.print(f"[green]✓ Patch command sent to {instance_id}[/green]")
                console.print(f"Command ID: {data.get('command_id')}")
                console.print(f"Patch Level: {data.get('patch_level')}")
            else:
                console.print(f"[red]✗ Patch failed: {data.get('error', 'Unknown error')}[/red]")
        else:
            console.print(f"[red]✗ Error: {response.status_code}[/red]")
    except Exception as e:
        console.print(f"[red]✗ Connection failed: {e}[/red]")


@cli.command()
@click.option('--instance-id', '-i', required=True, help='EC2 instance ID')
def patch_status(instance_id: str):
    """Check patch compliance status for an instance"""
    console.print(f"[bold blue]Checking patch status for {instance_id}...[/bold blue]")
    
    endpoint = get_mcp_endpoint()
    if not endpoint:
        console.print("[red]✗ MCP server not accessible[/red]")
        return
    
    try:
        response = requests.post(f"{endpoint}/mcp", json={
            "method": "check_patch_compliance",
            "params": {"instance_ids": [instance_id]}
        }, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                compliance_data = data.get('compliance_data', {})
                instance_data = compliance_data.get(instance_id, {})
                
                console.print(f"[green]✓ Patch status for {instance_id}:[/green]")
                console.print(f"Compliance: {instance_data.get('compliance_status', 'unknown')}")
                console.print(f"Missing patches: {instance_data.get('missing_count', 0)}")
                console.print(f"Installed patches: {instance_data.get('installed_count', 0)}")
            else:
                console.print(f"[red]✗ Failed: {data.get('error', 'Unknown error')}[/red]")
        else:
            console.print(f"[red]✗ Error: {response.status_code}[/red]")
    except Exception as e:
        console.print(f"[red]✗ Connection failed: {e}[/red]")


@cli.command()
def status():
    """Show health status of all EC2 instances"""
    console.print(f"[bold blue]Checking instance health...[/bold blue]")
    
    try:
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
                
                instances.append({
                    'id': instance['InstanceId'],
                    'state': state,
                    'type': instance['InstanceType']
                })
        
        # Summary
        total = len(instances)
        console.print(f"[green]✓ Total instances: {total}[/green]")
        console.print(f"  Running: {running}")
        console.print(f"  Stopped: {stopped}")
        if pending > 0:
            console.print(f"  Pending: {pending}")
        if terminated > 0:
            console.print(f"  Terminated: {terminated}")
        
        # Health assessment
        if running == total:
            console.print(f"[green]🟢 All instances healthy[/green]")
        elif running > 0:
            console.print(f"[yellow]🟡 {running}/{total} instances running[/yellow]")
        else:
            console.print(f"[red]🔴 No instances running[/red]")
            
    except Exception as e:
        console.print(f"[red]✗ Error checking status: {e}[/red]")


@cli.command()
def list():
    """List all EC2 instances in the region"""
    console.print(f"[bold blue]Listing EC2 instances...[/bold blue]")
    
    try:
        ec2 = boto3.client('ec2')
        response = ec2.describe_instances()
        
        instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                name = 'N/A'
                for tag in instance.get('Tags', []):
                    if tag['Key'] == 'Name':
                        name = tag['Value']
                        break
                
                instances.append({
                    'id': instance['InstanceId'],
                    'name': name,
                    'state': instance['State']['Name'],
                    'type': instance['InstanceType']
                })
        
        if instances:
            table = Table(title="EC2 Instances")
            table.add_column("Instance ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("State", style="yellow")
            table.add_column("Type", style="blue")
            
            for inst in instances:
                table.add_row(inst['id'], inst['name'], inst['state'], inst['type'])
            
            console.print(table)
            console.print(f"[green]✓ Found {len(instances)} instances[/green]")
        else:
            console.print("[yellow]No instances found[/yellow]")
            
    except Exception as e:
        console.print(f"[red]✗ Error listing instances: {e}[/red]")


@cli.command()
@click.option('--severity', '-s', default='all', help='Vulnerability severity filter')
def scan_all(severity: str):
    """Scan all EC2 instances in the region for vulnerabilities"""
    console.print(f"[bold blue]Scanning all EC2 instances...[/bold blue]")
    
    endpoint = get_mcp_endpoint()
    if not endpoint:
        console.print("[red]X MCP server not accessible[/red]")
        return
    
    try:
        response = requests.post(f"{endpoint}/mcp", json={
            "method": "get_inspector_findings",
            "params": {"instance_id": None, "severity": severity}
        }, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            console.print(f"[green]OK Scan complete[/green]")
            console.print(f"Summary: {data.get('summary', 'No summary available')}")
            console.print(f"Total findings: {data.get('total_count', 0)}")
            console.print(f"Critical: {data.get('critical_count', 0)}, High: {data.get('high_count', 0)}")
        else:
            console.print(f"[red]X Error: {response.status_code}[/red]")
            console.print(f"Response: {response.text}")
    except Exception as e:
        console.print(f"[red]X Connection failed: {e}[/red]")


@cli.command()
@click.option('--instance-id', '-i', required=True, help='EC2 instance ID')
@click.option('--metrics', '-m', default='CPUUtilization,MemoryUtilization,NetworkIn,NetworkOut', help='Comma-separated metric names')
@click.option('--time-range', '-t', default='24h', help='Time range (e.g., 24h, 7d)')
def cloudwatch_metrics(instance_id: str, metrics: str, time_range: str):
    """Get CloudWatch metrics for EC2 instance"""
    console.print(f"[bold blue]Getting CloudWatch metrics for {instance_id}...[/bold blue]")
    
    endpoint = get_mcp_endpoint()
    if not endpoint:
        console.print("[red]✗ MCP server not accessible[/red]")
        return
    
    metric_names = [m.strip() for m in metrics.split(',')]
    
    try:
        response = requests.post(f"{endpoint}/mcp", json={
            "method": "get_ec2_cloudwatch_metrics",
            "params": {
                "instance_id": instance_id,
                "metric_names": metric_names,
                "time_range": time_range
            }
        }, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if "error" in data:
                console.print(f"[red]✗ Error: {data['error']}[/red]")
            else:
                console.print(f"[green]✓ Metrics retrieved for {instance_id}[/green]")
                
                # Display metrics summary
                metrics_data = data.get('metrics', {})
                for metric_name, metric_info in metrics_data.items():
                    if 'average' in metric_info:
                        console.print(f"  {metric_name}: avg={metric_info['average']:.2f}, max={metric_info['maximum']:.2f}")
                    else:
                        console.print(f"  {metric_name}: {metric_info.get('status', 'no data')}")
                
                anomalies = data.get('anomalies', [])
                if anomalies:
                    console.print(f"[yellow]⚠ {len(anomalies)} anomalies detected[/yellow]")
        else:
            console.print(f"[red]✗ Error: {response.status_code}[/red]")
    except Exception as e:
        console.print(f"[red]✗ Connection failed: {e}[/red]")


@cli.command()
@click.option('--instance-id', '-i', required=True, help='EC2 instance ID')
@click.option('--time-range', '-t', default='24h', help='Time range (e.g., 24h, 7d)')
def cloudtrail_events(instance_id: str, time_range: str):
    """Analyze CloudTrail events for security insights"""
    console.print(f"[bold blue]Analyzing CloudTrail events for {instance_id}...[/bold blue]")
    
    endpoint = get_mcp_endpoint()
    if not endpoint:
        console.print("[red]✗ MCP server not accessible[/red]")
        return
    
    try:
        response = requests.post(f"{endpoint}/mcp", json={
            "method": "analyze_cloudtrail_events",
            "params": {
                "instance_id": instance_id,
                "event_types": [],
                "time_range": time_range
            }
        }, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if "error" in data:
                console.print(f"[red]✗ Error: {data['error']}[/red]")
            else:
                console.print(f"[green]✓ CloudTrail analysis complete[/green]")
                
                total_events = len(data.get('events', []))
                security_events = len(data.get('security_events', []))
                suspicious = len(data.get('suspicious_activity', []))
                
                console.print(f"  Total events: {total_events}")
                console.print(f"  Security events: {security_events}")
                console.print(f"  Suspicious activity: {suspicious}")
                
                if suspicious > 0:
                    console.print(f"[yellow]⚠ {suspicious} suspicious activities detected[/yellow]")
        else:
            console.print(f"[red]✗ Error: {response.status_code}[/red]")
    except Exception as e:
        console.print(f"[red]✗ Connection failed: {e}[/red]")


@cli.command()
@click.option('--instance-ids', '-i', required=True, help='Comma-separated EC2 instance IDs')
@click.option('--time-range', '-t', default='24h', help='Time range (e.g., 24h, 7d)')
def security_events(instance_ids: str, time_range: str):
    """Monitor security events across multiple instances"""
    console.print(f"[bold blue]Monitoring security events...[/bold blue]")
    
    endpoint = get_mcp_endpoint()
    if not endpoint:
        console.print("[red]✗ MCP server not accessible[/red]")
        return
    
    instance_list = [i.strip() for i in instance_ids.split(',')]
    
    try:
        response = requests.post(f"{endpoint}/mcp", json={
            "method": "monitor_security_events",
            "params": {
                "instance_ids": instance_list,
                "event_types": ["login", "privilege_escalation", "config_changes"],
                "time_range": time_range
            }
        }, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if "error" in data:
                console.print(f"[red]✗ Error: {data['error']}[/red]")
            else:
                console.print(f"[green]✓ Security monitoring complete[/green]")
                
                alerts = data.get('alerts', [])
                total_instances = data.get('total_instances', 0)
                recommendations = data.get('recommendations', [])
                
                console.print(f"  Instances monitored: {total_instances}")
                console.print(f"  Security alerts: {len(alerts)}")
                
                if alerts:
                    console.print(f"[red]🚨 {len(alerts)} high-risk security alerts![/red]")
                    for alert in alerts[:3]:  # Show first 3 alerts
                        console.print(f"    {alert['instance_id']}: {alert['alert_level']} risk")
                
                if recommendations:
                    console.print("[yellow]Recommendations:[/yellow]")
                    for rec in recommendations:
                        console.print(f"  • {rec}")
        else:
            console.print(f"[red]✗ Error: {response.status_code}[/red]")
    except Exception as e:
        console.print(f"[red]✗ Connection failed: {e}[/red]")


@cli.command()
@click.option('--instance-ids', '-i', required=True, help='Comma-separated EC2 instance IDs')
@click.option('--time-range', '-t', default='24h', help='Time range (e.g., 24h, 7d)')
def config_changes(instance_ids: str, time_range: str):
    """Analyze configuration changes for security impact"""
    console.print(f"[bold blue]Analyzing configuration changes...[/bold blue]")
    
    endpoint = get_mcp_endpoint()
    if not endpoint:
        console.print("[red]✗ MCP server not accessible[/red]")
        return
    
    instance_list = [i.strip() for i in instance_ids.split(',')]
    
    try:
        response = requests.post(f"{endpoint}/mcp", json={
            "method": "analyze_configuration_changes",
            "params": {
                "instance_ids": instance_list,
                "time_range": time_range
            }
        }, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if "error" in data:
                console.print(f"[red]✗ Error: {data['error']}[/red]")
            else:
                console.print(f"[green]✓ Configuration analysis complete[/green]")
                
                total_changes = data.get('total_changes', 0)
                compliance_status = data.get('compliance_status', 'unknown')
                high_risk_instances = data.get('high_risk_instances', [])
                
                console.print(f"  Total changes: {total_changes}")
                console.print(f"  Compliance status: {compliance_status}")
                
                if high_risk_instances:
                    console.print(f"[red]⚠ High-risk instances: {', '.join(high_risk_instances)}[/red]")
                elif compliance_status == "compliant":
                    console.print(f"[green]✓ All instances compliant[/green]")
        else:
            console.print(f"[red]✗ Error: {response.status_code}[/red]")
    except Exception as e:
        console.print(f"[red]✗ Connection failed: {e}[/red]")


@cli.command()
def interactive():
    """Legacy interactive mode (use 'chat' for AI-powered mode)"""
    console.print("[yellow]Note: Use 'sre chat' for AI-powered natural language mode[/yellow]")
    console.print("[bold green]SRE Assistant Interactive Mode[/bold green]")
    console.print("Type 'exit' to quit, 'help' for commands")
    
    endpoint = get_mcp_endpoint()
    if not endpoint:
        console.print("[red]✗ MCP server not accessible. Exiting.[/red]")
        return
    
    while True:
        try:
            user_input = console.input("[bold cyan]sre> [/bold cyan]")
            
            if user_input.lower() in ['exit', 'quit']:
                break
            elif user_input.lower() == 'help':
                console.print("""
Available commands:
- analyze vulnerabilities for <instance-id>
- scan all instances
- get cloudwatch metrics for <instance-id>
- analyze cloudtrail events for <instance-id>
                """)
            else:
                console.print(f"[yellow]Try: sre ask {user_input}[/yellow]")
                
        except KeyboardInterrupt:
            break
    
    console.print("[bold green]Goodbye![/bold green]")


@cli.command()
def test_core_functions():
    """Test all core MCP functions with sample data"""
    console.print("[bold blue]Testing Core MCP Functions[/bold blue]")
    console.print("=" * 50)
    
    endpoint = get_mcp_endpoint()
    if not endpoint:
        console.print("[red]✗ MCP server not accessible[/red]")
        return
    
    # Sample instance ID for testing
    test_instance = "i-1234567890abcdef0"  # Replace with actual instance
    
    tests = [
        {
            "name": "CloudWatch Metrics",
            "method": "get_ec2_cloudwatch_metrics",
            "params": {
                "instance_id": test_instance,
                "metric_names": ["CPUUtilization", "NetworkIn"],
                "time_range": "24h"
            }
        },
        {
            "name": "CloudTrail Events",
            "method": "analyze_cloudtrail_events",
            "params": {
                "instance_id": test_instance,
                "event_types": [],
                "time_range": "24h"
            }
        },
        {
            "name": "Security Events",
            "method": "monitor_security_events",
            "params": {
                "instance_ids": [test_instance],
                "event_types": ["login", "privilege_escalation"],
                "time_range": "24h"
            }
        },
        {
            "name": "Configuration Changes",
            "method": "analyze_configuration_changes",
            "params": {
                "instance_ids": [test_instance],
                "time_range": "24h"
            }
        }
    ]
    
    for test in tests:
        console.print(f"\n[cyan]Testing: {test['name']}[/cyan]")
        try:
            response = requests.post(f"{endpoint}/mcp", json={
                "method": test["method"],
                "params": test["params"]
            }, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    console.print(f"[yellow]⚠ Function error: {data['error']}[/yellow]")
                else:
                    console.print(f"[green]✓ {test['name']} - Success[/green]")
                    
                    # Show key metrics
                    if test["method"] == "get_ec2_cloudwatch_metrics":
                        metrics_count = len(data.get("metrics", {}))
                        anomalies = len(data.get("anomalies", []))
                        console.print(f"    Metrics: {metrics_count}, Anomalies: {anomalies}")
                    elif test["method"] == "analyze_cloudtrail_events":
                        events = len(data.get("events", []))
                        suspicious = len(data.get("suspicious_activity", []))
                        console.print(f"    Events: {events}, Suspicious: {suspicious}")
                    elif test["method"] == "monitor_security_events":
                        alerts = len(data.get("alerts", []))
                        instances = data.get("total_instances", 0)
                        console.print(f"    Instances: {instances}, Alerts: {alerts}")
                    elif test["method"] == "analyze_configuration_changes":
                        changes = data.get("total_changes", 0)
                        compliance = data.get("compliance_status", "unknown")
                        console.print(f"    Changes: {changes}, Status: {compliance}")
            else:
                console.print(f"[red]✗ {test['name']} - HTTP {response.status_code}[/red]")
        except Exception as e:
            console.print(f"[red]✗ {test['name']} - Error: {e}[/red]")
    
    console.print("\n[bold green]Core function testing complete![/bold green]")


@cli.command()
@click.argument('query', nargs=-1)
def ask(query):
    """Ask anything in natural language using AI!
    
    Examples:
      sre ask check vulnerabilities for i-00f20fbd7c0075d1d
      sre ask show me cpu performance for i-123 over the last hour
      sre ask scan all instances for vulnerabilities
    """
    if not query:
        console.print("[yellow]Usage: sre ask <your question>[/yellow]")
        console.print("Examples:")
        console.print("  sre ask check vulnerabilities for i-00f20fbd7c0075d1d")
        console.print("  sre ask cpu metrics i-123 last 2 hours")
        console.print("  sre ask scan all instances")
        return
    
    query_text = ' '.join(query)
    console.print(f"[cyan]🤖 AI Processing: {query_text}[/cyan]")
    
    # Parse with LLM
    parser = LLMParser()
    parsed = parser.parse_command(query_text)
    
    console.print(f"[dim]Understood: {parsed['command']} for {parsed['instance_ids']} ({parsed['confidence']:.1f} confidence)[/dim]")
    
    if parsed['confidence'] < 0.5:
        console.print("[yellow]⚠ Low confidence in understanding. Please be more specific.[/yellow]")
        return
    
    if parsed.get('needs_instance_id'):
        console.print("[yellow]⚠ I understand you want to check vulnerabilities, but I need an instance ID.[/yellow]")
        console.print("Try: 'check vulnerabilities for i-00f20fbd7c0075d1d'")
        return
    
    # Get endpoint and execute
    endpoint = get_mcp_endpoint()
    if not endpoint:
        console.print("[red]✗ MCP server not accessible[/red]")
        return
    
    _execute_ai_command(endpoint, parsed)


def _resolve_instance_identifiers(identifiers: list) -> list:
    """Resolve instance names to IDs"""
    if not identifiers:
        return []
    
    resolved_ids = []
    try:
        ec2 = boto3.client('ec2')
        response = ec2.describe_instances()
        
        # Build name to ID mapping
        name_to_id = {}
        all_instances = {}
        
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                all_instances[instance_id] = instance
                
                # Get name from tags
                for tag in instance.get('Tags', []):
                    if tag['Key'] == 'Name':
                        name_to_id[tag['Value']] = instance_id
                        break
        
        # Resolve each identifier
        for identifier in identifiers:
            if identifier.startswith('i-'):
                # Already an instance ID
                resolved_ids.append(identifier)
            elif identifier in name_to_id:
                # Instance name
                resolved_ids.append(name_to_id[identifier])
            else:
                # Try partial name match
                matches = [name for name in name_to_id.keys() if identifier.lower() in name.lower()]
                for match in matches:
                    resolved_ids.append(name_to_id[match])
    
    except Exception:
        # If resolution fails, return original identifiers
        return identifiers
    
    return resolved_ids

def _execute_ai_command(endpoint: str, parsed_cmd: dict):
    """Execute AI-parsed command"""
    command = parsed_cmd['command']
    instance_ids = _resolve_instance_identifiers(parsed_cmd['instance_ids'])
    time_range = parsed_cmd['time_range']
    
    if command == 'scan_all':
        console.print("[bold blue]🔍 Scanning all instances for vulnerabilities...[/bold blue]")
        response = requests.post(f"{endpoint}/mcp", json={
            "method": "get_inspector_findings",
            "params": {"severity": "all"}
        }, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            console.print(f"[green]✓ Found {len(data.get('findings', []))} total vulnerabilities[/green]")
            console.print(f"Summary: {data.get('summary', 'No summary')}")
        else:
            console.print(f"[red]✗ Error: {response.status_code}[/red]")
        return
    
    if not instance_ids:
        console.print("[red]✗ No instance ID found[/red]")
        return
    
    instance_id = instance_ids[0]  # Use first instance
    
    try:
        if command == 'vulnerabilities':
            console.print(f"[bold blue]🔍 Analyzing vulnerabilities for {instance_id}...[/bold blue]")
            response = requests.post(f"{endpoint}/mcp", json={
                "method": "get_inspector_findings",
                "params": {"instance_id": instance_id, "severity": "all"}
            }, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                console.print(f"[green]✓ Found {len(data.get('findings', []))} vulnerabilities[/green]")
                console.print(f"Summary: {data.get('summary', 'No summary')}")
            else:
                console.print(f"[red]✗ Error: {response.status_code}[/red]")
        
        elif command == 'cloudwatch_metrics':
            # Determine which metrics to request based on original text
            text_lower = parsed_cmd['original_text'].lower()
            if 'cpu' in text_lower and 'mem' not in text_lower and 'network' not in text_lower:
                metric_names = ["CPUUtilization"]
            elif 'mem' in text_lower and 'cpu' not in text_lower and 'network' not in text_lower:
                metric_names = ["MemoryUtilization"]
            elif 'network' in text_lower and 'cpu' not in text_lower and 'mem' not in text_lower:
                metric_names = ["NetworkIn", "NetworkOut"]
            else:
                metric_names = ["CPUUtilization", "MemoryUtilization", "NetworkIn", "NetworkOut"]
            
            console.print(f"[bold blue]📊 Getting metrics for {instance_id} ({time_range})...[/bold blue]")
            response = requests.post(f"{endpoint}/mcp", json={
                "method": "get_ec2_cloudwatch_metrics",
                "params": {
                    "instance_id": instance_id,
                    "metric_names": metric_names,
                    "time_range": time_range
                }
            }, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    console.print(f"[red]✗ Error: {data['error']}[/red]")
                else:
                    console.print(f"[green]✓ Metrics for {instance_id} ({instance_id[-4:]}) - {time_range}[/green]")
                    metrics_data = data.get('metrics', {})
                    for metric_name, metric_info in metrics_data.items():
                        if isinstance(metric_info, dict):
                            if 'status' in metric_info:
                                status = metric_info['status']
                                if status == 'no_data':
                                    console.print(f"  [yellow]{metric_name}[/yellow]: No data available")
                                elif status == 'insufficient_data':
                                    console.print(f"  [yellow]{metric_name}[/yellow]: Insufficient data")
                                elif status == 'error':
                                    console.print(f"  [red]{metric_name}[/red]: Error - {metric_info.get('error', 'Unknown error')}")
                            elif 'average' in metric_info:
                                avg = metric_info['average']
                                max_val = metric_info.get('maximum', 0)
                                min_val = metric_info.get('minimum', 0)
                                trend = metric_info.get('trend', 'stable')
                                datapoints = len(metric_info.get('datapoints', []))
                                
                                # Format units based on metric type
                                if 'CPU' in metric_name:
                                    unit = '%'
                                elif 'Network' in metric_name:
                                    unit = 'bytes'
                                elif 'Disk' in metric_name:
                                    unit = 'ops'
                                else:
                                    unit = ''
                                
                                console.print(f"  [cyan]{metric_name}[/cyan]: {avg:.2f}{unit} (avg)")
                                console.print(f"    Range: {min_val:.2f} - {max_val:.2f}{unit}, Trend: {trend}")
                                console.print(f"    Datapoints: {datapoints}")
                    
                    # Show anomalies if any
                    anomalies = data.get('anomalies', [])
                    if anomalies:
                        console.print(f"\n  [red]⚠ {len(anomalies)} anomalies detected:[/red]")
                        for anomaly in anomalies[:3]:  # Show first 3
                            console.print(f"    {anomaly['metric']}: {anomaly['value']:.2f} at {anomaly['timestamp'][:19]}")
            else:
                console.print(f"[red]✗ Error: {response.status_code}[/red]")
        
        elif command == 'cloudtrail_events':
            console.print(f"[bold blue]📄 Analyzing CloudTrail events for {instance_id} ({time_range})...[/bold blue]")
            response = requests.post(f"{endpoint}/mcp", json={
                "method": "analyze_cloudtrail_events",
                "params": {
                    "instance_id": instance_id,
                    "event_types": [],
                    "time_range": time_range
                }
            }, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    console.print(f"[red]✗ Error: {data['error']}[/red]")
                else:
                    console.print(f"[green]✓ CloudTrail analysis complete[/green]")
                    total_events = len(data.get('events', []))
                    suspicious = len(data.get('suspicious_activity', []))
                    console.print(f"  Events: {total_events}, Suspicious: {suspicious}")
            else:
                console.print(f"[red]✗ Error: {response.status_code}[/red]")
        
        elif command == 'list':
            console.print(f"[bold blue]📋 Listing instances...[/bold blue]")
            ctx = click.Context(list)
            ctx.invoke(list)
        
        elif command == 'status':
            if instance_ids:
                # Individual instance status
                console.print(f"[bold blue]🏥 Checking status for {len(instance_ids)} instance(s)...[/bold blue]")
                try:
                    ec2 = boto3.client('ec2')
                    response = ec2.describe_instances(InstanceIds=instance_ids)
                    
                    for reservation in response['Reservations']:
                        for instance in reservation['Instances']:
                            instance_id = instance['InstanceId']
                            state = instance['State']['Name']
                            instance_type = instance['InstanceType']
                            
                            name = 'N/A'
                            for tag in instance.get('Tags', []):
                                if tag['Key'] == 'Name':
                                    name = tag['Value']
                                    break
                            
                            console.print(f"[green]✓ Instance {instance_id}[/green]")
                            console.print(f"  Name: {name}")
                            console.print(f"  State: {state}")
                            console.print(f"  Type: {instance_type}")
                            
                            if state == 'running':
                                console.print(f"[green]🟢 Instance healthy[/green]")
                            elif state == 'stopped':
                                console.print(f"[yellow]🟡 Instance stopped[/yellow]")
                            else:
                                console.print(f"[red]🔴 Instance in {state} state[/red]")
                            console.print()
                except Exception as e:
                    console.print(f"[red]✗ Error checking instance: {e}[/red]")
            else:
                # Overall status
                console.print(f"[bold blue]🏥 Checking health status...[/bold blue]")
                ctx = click.Context(status)
                ctx.invoke(status)
        
        else:
            console.print(f"[yellow]Command '{command}' not implemented yet[/yellow]")
    
    except Exception as e:
        console.print(f"[red]✗ Request failed: {e}[/red]")


@cli.command()
def chat():
    """Interactive AI-powered chat mode"""
    console.print("[bold green]🤖 AI-Powered SRE Assistant[/bold green]")
    console.print("Speak naturally! The AI will understand your intent.")
    console.print("Type 'exit' to quit")
    
    endpoint = get_mcp_endpoint()
    if not endpoint:
        console.print("[red]✗ MCP server not accessible. Exiting.[/red]")
        return
    
    parser = LLMParser()
    
    while True:
        try:
            user_input = console.input("[bold cyan]sre> [/bold cyan]")
            
            if user_input.lower() in ['exit', 'quit']:
                break
            elif user_input.lower() == 'help':
                console.print("""
[bold]Natural Language Examples:[/bold]
• Check vulnerabilities on i-00f20fbd7c0075d1d
• Show me CPU performance for i-123 over the last 2 hours
• What security events happened on i-456 yesterday?
• Scan all instances for vulnerabilities
• Analyze network traffic for i-789 this week
                """)
            else:
                console.print(f"[cyan]🤖 AI Processing...[/cyan]")
                parsed = parser.parse_command(user_input)
                
                if parsed['method'] == 'llm':
                    console.print(f"[dim]AI understood: {parsed['command']} for {parsed['instance_ids']} ({parsed['confidence']:.1f} confidence)[/dim]")
                else:
                    console.print(f"[yellow]Using fallback parsing (AI unavailable)[/yellow]")
                
                if parsed['confidence'] >= 0.3:
                    if parsed.get('needs_instance_id'):
                        console.print("[yellow]⚠ I understand you want to check vulnerabilities, but I need an instance ID.[/yellow]")
                        console.print("Try: 'check vulnerabilities for i-00f20fbd7c0075d1d'")
                    elif parsed['command'] == 'list':
                        ctx = click.Context(list)
                        ctx.invoke(list)
                    elif parsed['command'] == 'status':
                        if parsed['instance_ids']:
                            _execute_ai_command(endpoint, parsed)
                        else:
                            ctx = click.Context(status)
                            ctx.invoke(status)
                    else:
                        _execute_ai_command(endpoint, parsed)
                else:
                    console.print("[yellow]⚠ Please be more specific about what you want to do.[/yellow]")
                    console.print(f"[dim]Debug: command={parsed.get('command')}, instances={parsed.get('instance_ids')}, confidence={parsed.get('confidence')}[/dim]")
                
        except KeyboardInterrupt:
            break
    
    console.print("[bold green]Goodbye![/bold green]")


if __name__ == "__main__":
    cli()