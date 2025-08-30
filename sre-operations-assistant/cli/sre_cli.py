#!/usr/bin/env python3
"""MCP-Powered CLI for SRE Operations - Updated with Core Functions"""

import click
import asyncio
import requests
from rich.console import Console
from rich.table import Table
from typing import List, Optional
import boto3

console = Console()

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
@click.option('--metrics', '-m', default='CPUUtilization,NetworkIn,NetworkOut', help='Comma-separated metric names')
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
def interactive():
    """Start interactive MCP-powered mode"""
    console.print("[bold green]SRE Assistant Interactive Mode[/bold green]")
    console.print("Type 'exit' to quit, 'help' for commands")
    
    # Get endpoint once at startup
    endpoint = get_mcp_endpoint()
    if not endpoint:
        console.print("[red]✗ MCP server not accessible. Exiting.[/red]")
        return
    
    while True:
        try:
            user_input = console.input("\n[bold cyan]sre>[/bold cyan] ")
            
            if user_input.lower() in ['exit', 'quit']:
                break
            elif user_input.lower() == 'help':
                console.print("""
Available commands:
- analyze vulnerabilities for <instance-id>
- scan all instances
- find patch windows for <instance-id>
- schedule patches for <criticality>
- check security events for <time-range>
- get cloudwatch metrics for <instance-id>
- analyze cloudtrail events for <instance-id>
- check config changes for <instance-id>
                """)
            else:
                console.print(f"[yellow]Processing: {user_input}[/yellow]")
                
                # Parse natural language input
                if "vulnerabilities" in user_input.lower() and "for" in user_input.lower():
                    # Extract instance ID
                    parts = user_input.split()
                    instance_id = None
                    for part in parts:
                        if part.startswith('i-'):
                            instance_id = part
                            break
                    
                    if instance_id:
                        try:
                            response = requests.post(f"{endpoint}/mcp", json={
                                "method": "get_inspector_findings",
                                "params": {"instance_id": instance_id, "severity": "all"}
                            }, timeout=30)
                            
                            if response.status_code == 200:
                                data = response.json()
                                console.print(f"[green]✓ Analysis complete for {instance_id}[/green]")
                                console.print(f"Summary: {data.get('summary', 'No summary available')}")
                                console.print(f"Total findings: {data.get('total_count', 0)}")
                                console.print(f"Critical: {data.get('critical_count', 0)}, High: {data.get('high_count', 0)}")
                            else:
                                console.print(f"[red]✗ Server error: {response.status_code}[/red]")
                                console.print(f"Response: {response.text}")
                        except Exception as e:
                            console.print(f"[red]✗ Request failed: {e}[/red]")
                    else:
                        console.print("[red]✗ No instance ID found in input[/red]")
                
                elif "scan all" in user_input.lower() or "all instances" in user_input.lower():
                    try:
                        response = requests.post(f"{endpoint}/mcp", json={
                            "method": "get_inspector_findings",
                            "params": {"instance_id": None, "severity": "all"}
                        }, timeout=60)
                        
                        if response.status_code == 200:
                            data = response.json()
                            console.print(f"[green]✓ Region-wide scan complete[/green]")
                            console.print(f"Summary: {data.get('summary', 'No summary available')}")
                            console.print(f"Total findings: {data.get('total_count', 0)}")
                            console.print(f"Critical: {data.get('critical_count', 0)}, High: {data.get('high_count', 0)}")
                        else:
                            console.print(f"[red]✗ Server error: {response.status_code}[/red]")
                            console.print(f"Response: {response.text}")
                    except Exception as e:
                        console.print(f"[red]✗ Request failed: {e}[/red]")
                
                elif "patch now" in user_input.lower() or "execute patch" in user_input.lower():
                    # Extract instance ID for immediate patching
                    parts = user_input.split()
                    instance_id = None
                    for part in parts:
                        if part.startswith('i-'):
                            instance_id = part
                            break
                    
                    if instance_id:
                        try:
                            response = requests.post(f"{endpoint}/mcp", json={
                                "method": "execute_patch_now",
                                "params": {"instance_ids": [instance_id], "patch_level": "non_critical"}
                            }, timeout=30)
                            
                            if response.status_code == 200:
                                data = response.json()
                                if data.get('status') == 'success':
                                    console.print(f"[green]✓ Patch command sent to {instance_id}[/green]")
                                    console.print(f"Command ID: {data.get('command_id')}")
                                else:
                                    console.print(f"[red]✗ Patch failed: {data.get('error')}[/red]")
                            else:
                                console.print(f"[red]✗ Server error: {response.status_code}[/red]")
                        except Exception as e:
                            console.print(f"[red]✗ Request failed: {e}[/red]")
                    else:
                        console.print("[red]✗ No instance ID found in input[/red]")
                
                elif "patch status" in user_input.lower():
                    # Extract instance ID for patch status
                    parts = user_input.split()
                    instance_id = None
                    for part in parts:
                        if part.startswith('i-'):
                            instance_id = part
                            break
                    
                    if instance_id:
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
                                    console.print(f"Missing: {instance_data.get('missing_count', 0)}, Installed: {instance_data.get('installed_count', 0)}")
                                else:
                                    console.print(f"[red]✗ Failed: {data.get('error')}[/red]")
                            else:
                                console.print(f"[red]✗ Server error: {response.status_code}[/red]")
                        except Exception as e:
                            console.print(f"[red]✗ Request failed: {e}[/red]")
                    else:
                        console.print("[red]✗ No instance ID found in input[/red]")
                
                elif "patch window" in user_input.lower():
                    # Extract instance ID for patch window analysis
                    parts = user_input.split()
                    instance_id = None
                    for part in parts:
                        if part.startswith('i-'):
                            instance_id = part
                            break
                    
                    if instance_id:
                        try:
                            response = requests.post(f"{endpoint}/mcp", json={
                                "method": "analyze_optimal_patch_window",
                                "params": {"instance_id": instance_id, "days_ahead": 7}
                            }, timeout=30)
                            
                            if response.status_code == 200:
                                data = response.json()
                                console.print(f"[green]✓ Patch window analysis complete[/green]")
                                console.print(f"Instance: {data.get('instance_id', instance_id)}")
                                console.print(f"Status: {data.get('status', 'Analysis complete')}")
                            else:
                                console.print(f"[red]✗ Server error: {response.status_code}[/red]")
                                console.print(f"Response: {response.text}")
                        except Exception as e:
                            console.print(f"[red]✗ Request failed: {e}[/red]")
                    else:
                        console.print("[red]✗ No instance ID found in input[/red]")
                
                else:
                    console.print("[yellow]Command not recognized. Try 'analyze vulnerabilities for i-xxxxx' or 'find patch windows for i-xxxxx'[/yellow]")

                
        except KeyboardInterrupt:
            break
    
    console.print("[bold green]Goodbye![/bold green]")


if __name__ == "__main__":
    cli()