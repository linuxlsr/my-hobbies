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
            console.print(f"Summary: {data.get('summary', 'No summary')}")
        else:
            console.print(f"[red]✗ Error: {response.status_code}[/red]")
    except Exception as e:
        console.print(f"[red]✗ Connection failed: {e}[/red]")

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

if __name__ == "__main__":
    cli()