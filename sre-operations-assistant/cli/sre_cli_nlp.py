#!/usr/bin/env python3
"""Natural Language SRE CLI"""

import click
import requests
from rich.console import Console
import re
from typing import List, Optional

console = Console()

def get_mcp_endpoint():
    """Get MCP server endpoint"""
    for url in ["http://localhost:8000", "http://127.0.0.1:8000"]:
        try:
            response = requests.get(f"{url}/health", timeout=2)
            if response.status_code == 200:
                console.print(f"[green]Connected to local server: {url}[/green]")
                return url
        except:
            continue
    
    # Try ECS
    try:
        import boto3
        ecs = boto3.client('ecs')
        elbv2 = boto3.client('elbv2')
        
        services = ecs.describe_services(
            cluster='sre-ops-assistant-cluster',
            services=['sre-ops-assistant-mcp-server']
        )
        
        if services['services']:
            service = services['services'][0]
            for lb in service.get('loadBalancers', []):
                if 'targetGroupArn' in lb:
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
                            
                            response = requests.get(f"{alb_url}/health", timeout=5)
                            if response.status_code == 200:
                                console.print(f"[green]Connected to ECS service: {alb_url}[/green]")
                                return alb_url
    except Exception as e:
        console.print(f"[yellow]ECS connection failed: {e}[/yellow]")
    
    return None

def extract_instance_id(text: str) -> Optional[str]:
    """Extract instance ID from text"""
    pattern = r'i-[a-f0-9]{8,17}'
    match = re.search(pattern, text)
    return match.group(0) if match else None

def extract_time_range(text: str) -> str:
    """Extract time range from text"""
    text_lower = text.lower()
    
    # Time patterns
    patterns = {
        r'(\d+)\s*h(our)?s?': lambda m: f"{m.group(1)}h",
        r'(\d+)\s*d(ay)?s?': lambda m: f"{m.group(1)}d",
        r'last\s*(\d+)\s*h(our)?s?': lambda m: f"{m.group(1)}h",
        r'past\s*(\d+)\s*d(ay)?s?': lambda m: f"{m.group(1)}d",
        r'today': lambda m: "24h",
        r'yesterday': lambda m: "48h",
        r'week': lambda m: "7d"
    }
    
    for pattern, converter in patterns.items():
        match = re.search(pattern, text_lower)
        if match:
            return converter(match)
    
    return "24h"

def identify_command(text: str) -> Optional[str]:
    """Identify command from natural language"""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ['vuln', 'vulnerabilit', 'security issues', 'cve', 'inspect']):
        return 'vulnerabilities'
    elif any(word in text_lower for word in ['metrics', 'cloudwatch', 'cpu', 'memory', 'network', 'performance']):
        return 'cloudwatch_metrics'
    elif any(word in text_lower for word in ['cloudtrail', 'events', 'logs', 'audit', 'trail', 'api calls']):
        return 'cloudtrail_events'
    elif any(word in text_lower for word in ['security events', 'suspicious', 'alerts', 'threats', 'intrusion']):
        return 'security_events'
    elif any(word in text_lower for word in ['config', 'configuration', 'changes', 'drift', 'compliance', 'changed', 'what changed']):
        return 'config_changes'
    elif any(word in text_lower for word in ['patch', 'patching', 'updates']):
        return 'patch_status'
    
    return None

@click.group()
def cli():
    """SRE Operations Assistant - Natural Language CLI"""
    pass

@cli.command()
@click.argument('query', nargs=-1)
def ask(query):
    """Ask anything in natural language!
    
    Examples:
      sre ask vulnerabilities for i-00f20fbd7c0075d1d
      sre ask cpu metrics i-123 last 2 hours
      sre ask security events i-456 today
    """
    if not query:
        console.print("[yellow]Usage: sre ask <your question>[/yellow]")
        console.print("Examples:")
        console.print("  sre ask vulnerabilities for i-00f20fbd7c0075d1d")
        console.print("  sre ask cpu metrics i-123 last 2 hours")
        console.print("  sre ask security events i-456 today")
        return
    
    query_text = ' '.join(query)
    console.print(f"[cyan]Understanding: {query_text}[/cyan]")
    
    # Parse the query
    instance_id = extract_instance_id(query_text)
    time_range = extract_time_range(query_text)
    command = identify_command(query_text)
    
    if not instance_id:
        console.print("[red]✗ No instance ID found[/red]")
        console.print("Please include an instance ID like i-00f20fbd7c0075d1d")
        return
    
    if not command:
        console.print("[yellow]I'm not sure what you want to do.[/yellow]")
        console.print("Try: vulnerabilities, metrics, events, config changes, etc.")
        return
    
    # Get endpoint
    endpoint = get_mcp_endpoint()
    if not endpoint:
        console.print("[red]✗ MCP server not accessible[/red]")
        return
    
    # Execute command
    try:
        if command == 'vulnerabilities':
            console.print(f"[bold blue]Analyzing vulnerabilities for {instance_id}...[/bold blue]")
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
            console.print(f"[bold blue]Getting metrics for {instance_id} ({time_range})...[/bold blue]")
            response = requests.post(f"{endpoint}/mcp", json={
                "method": "get_ec2_cloudwatch_metrics",
                "params": {
                    "instance_id": instance_id,
                    "metric_names": ["CPUUtilization", "NetworkIn", "NetworkOut"],
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
                    if not metrics_data:
                        console.print("  [yellow]No metrics data available[/yellow]")
                        # Debug: show what we got
                        console.print(f"  [dim]Debug: Response keys: {list(data.keys())}[/dim]")
                    else:
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
                                else:
                                    console.print(f"  [cyan]{metric_name}[/cyan]: {metric_info}")
                            else:
                                console.print(f"  [cyan]{metric_name}[/cyan]: {metric_info}")
                    
                    # Show anomalies if any
                    anomalies = data.get('anomalies', [])
                    if anomalies:
                        console.print(f"\n  [red]⚠ {len(anomalies)} anomalies detected:[/red]")
                        for anomaly in anomalies[:3]:  # Show first 3
                            console.print(f"    {anomaly['metric']}: {anomaly['value']:.2f} at {anomaly['timestamp'][:19]}")
            else:
                console.print(f"[red]✗ Error: {response.status_code}[/red]")
        
        elif command == 'cloudtrail_events':
            console.print(f"[bold blue]Analyzing CloudTrail events for {instance_id} ({time_range})...[/bold blue]")
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
        
        elif command == 'security_events':
            console.print(f"[bold blue]Monitoring security events for {instance_id} ({time_range})...[/bold blue]")
            response = requests.post(f"{endpoint}/mcp", json={
                "method": "monitor_security_events",
                "params": {
                    "instance_ids": [instance_id],
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
                    alerts = len(data.get('alerts', []))
                    console.print(f"  Security alerts: {alerts}")
            else:
                console.print(f"[red]✗ Error: {response.status_code}[/red]")
        
        elif command == 'config_changes':
            console.print(f"[bold blue]Analyzing config changes for {instance_id} ({time_range})...[/bold blue]")
            response = requests.post(f"{endpoint}/mcp", json={
                "method": "analyze_configuration_changes",
                "params": {
                    "instance_ids": [instance_id],
                    "time_range": time_range
                }
            }, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    console.print(f"[red]✗ Error: {data['error']}[/red]")
                else:
                    console.print(f"[green]✓ Configuration analysis complete[/green]")
                    changes = data.get('total_changes', 0)
                    compliance = data.get('compliance_status', 'unknown')
                    console.print(f"  Changes: {changes}, Status: {compliance}")
            else:
                console.print(f"[red]✗ Error: {response.status_code}[/red]")
        
        else:
            console.print(f"[yellow]Command '{command}' recognized but not implemented yet[/yellow]")
    
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")

@cli.command()
def chat():
    """Interactive natural language chat mode"""
    console.print("[bold green]SRE Assistant - Natural Language Chat[/bold green]")
    console.print("Type naturally! Examples:")
    console.print("  • vulnerabilities for i-00f20fbd7c0075d1d")
    console.print("  • cpu metrics i-123 last 2 hours")
    console.print("  • security events i-456 today")
    console.print("Type 'exit' to quit\n")
    
    endpoint = get_mcp_endpoint()
    if not endpoint:
        console.print("[red]✗ MCP server not accessible. Exiting.[/red]")
        return
    
    while True:
        try:
            user_input = console.input("\n[bold cyan]sre> [/bold cyan]")
            
            if user_input.lower() in ['exit', 'quit']:
                break
            elif user_input.lower() == 'help':
                console.print("""
[bold]Natural Language Commands:[/bold]
• vulnerabilities for i-00f20fbd7c0075d1d
• cpu metrics i-123 last 2 hours  
• security events i-456 today
• cloudtrail logs i-789 past week
• config changes i-abc yesterday

[bold]You can also say:[/bold]
• check vulns on i-123
• show me performance for i-456 last day
• any suspicious activity on i-789?
• what changed on i-abc recently?
                """)
            else:
                # Parse and execute
                instance_id = extract_instance_id(user_input)
                time_range = extract_time_range(user_input)
                command = identify_command(user_input)
                
                if not instance_id:
                    console.print("[red]✗ No instance ID found[/red]")
                    console.print("Please include an instance ID like i-00f20fbd7c0075d1d")
                    continue
                
                if not command:
                    console.print("[yellow]I'm not sure what you want to do.[/yellow]")
                    console.print("Try: vulnerabilities, metrics, events, config changes, etc.")
                    continue
                
                # Execute the same logic as ask command
                if command == 'vulnerabilities':
                    try:
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
                    except Exception as e:
                        console.print(f"[red]✗ Request failed: {e}[/red]")
                
                elif command == 'cloudwatch_metrics':
                    try:
                        response = requests.post(f"{endpoint}/mcp", json={
                            "method": "get_ec2_cloudwatch_metrics",
                            "params": {
                                "instance_id": instance_id,
                                "metric_names": ["CPUUtilization", "NetworkIn", "NetworkOut"],
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
                                if not metrics_data:
                                    console.print("  [yellow]No metrics data available[/yellow]")
                                    # Debug: show what we got
                                    console.print(f"  [dim]Debug: Response keys: {list(data.keys())}[/dim]")
                                else:
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
                                            else:
                                                console.print(f"  [cyan]{metric_name}[/cyan]: {metric_info}")
                                        else:
                                            console.print(f"  [cyan]{metric_name}[/cyan]: {metric_info}")
                                
                                # Show anomalies if any
                                anomalies = data.get('anomalies', [])
                                if anomalies:
                                    console.print(f"\n  [red]⚠ {len(anomalies)} anomalies detected:[/red]")
                                    for anomaly in anomalies[:3]:  # Show first 3
                                        console.print(f"    {anomaly['metric']}: {anomaly['value']:.2f} at {anomaly['timestamp'][:19]}")
                        else:
                            console.print(f"[red]✗ Error: {response.status_code}[/red]")
                    except Exception as e:
                        console.print(f"[red]✗ Request failed: {e}[/red]")
                
                else:
                    console.print(f"[yellow]'{command}' recognized but not fully implemented in chat mode yet[/yellow]")
                    console.print(f"Try: python cli/sre_cli_nlp.py ask {user_input}")
                
        except KeyboardInterrupt:
            break
    
    console.print("[bold green]Goodbye![/bold green]")

if __name__ == "__main__":
    cli()