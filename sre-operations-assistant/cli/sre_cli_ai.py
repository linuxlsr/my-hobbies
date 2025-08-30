#!/usr/bin/env python3
"""AI-Powered SRE CLI using LLM for natural language processing"""

import click
import requests
from rich.console import Console
from llm_parser import LLMParser

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

def execute_command(endpoint: str, parsed_cmd: dict):
    """Execute the parsed command"""
    command = parsed_cmd['command']
    instance_ids = parsed_cmd['instance_ids']
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
            console.print(f"[bold blue]📊 Getting metrics for {instance_id} ({time_range})...[/bold blue]")
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
                    for metric_name, metric_info in metrics_data.items():
                        if isinstance(metric_info, dict) and 'average' in metric_info:
                            avg = metric_info['average']
                            unit = '%' if 'CPU' in metric_name else 'bytes' if 'Network' in metric_name else ''
                            console.print(f"  [cyan]{metric_name}[/cyan]: {avg:.2f}{unit} (avg)")
            else:
                console.print(f"[red]✗ Error: {response.status_code}[/red]")
        
        else:
            console.print(f"[yellow]Command '{command}' not implemented yet[/yellow]")
    
    except Exception as e:
        console.print(f"[red]✗ Request failed: {e}[/red]")

@click.group()
def cli():
    """AI-Powered SRE Operations Assistant"""
    pass

@cli.command()
@click.argument('query', nargs=-1)
def ask(query):
    """Ask anything in natural language using AI!
    
    Examples:
      sre ask check vulnerabilities for i-00f20fbd7c0075d1d
      sre ask show me cpu performance for i-123 over the last hour
      sre ask what security events happened on i-456 yesterday
    """
    if not query:
        console.print("[yellow]Usage: sre ask <your question>[/yellow]")
        return
    
    query_text = ' '.join(query)
    console.print(f"[cyan]🤖 AI Processing: {query_text}[/cyan]")
    
    # Parse with LLM
    parser = LLMParser()
    parsed = parser.parse_command(query_text)
    
    console.print(f"[dim]Understood: {parsed['command']} for {parsed['instance_ids']} ({parsed['confidence']:.1f} confidence)[/dim]")
    
    if parsed['confidence'] < 0.5:
        console.print("[yellow]⚠ Low confidence in understanding. Please be more specific.[/yellow]")
        if parsed.get('llm_error'):
            console.print(f"[dim]Debug: {parsed['llm_error']}[/dim]")
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
    
    execute_command(endpoint, parsed)

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
• Analyze network traffic for i-789 this week
• Any suspicious activity on i-abc recently?
                """)
            else:
                console.print(f"[cyan]🤖 AI Processing...[/cyan]")
                parsed = parser.parse_command(user_input)
                
                if parsed['method'] == 'llm':
                    console.print(f"[dim]AI understood: {parsed['command']} for {parsed['instance_ids']} ({parsed['confidence']:.1f} confidence)[/dim]")
                else:
                    console.print(f"[yellow]Using fallback parsing (AI unavailable)[/yellow]")
                
                if parsed['confidence'] >= 0.5:
                    if parsed.get('needs_instance_id'):
                        console.print("[yellow]⚠ I understand you want to check vulnerabilities, but I need an instance ID.[/yellow]")
                        console.print("Try: 'check vulnerabilities for i-00f20fbd7c0075d1d'")
                    else:
                        execute_command(endpoint, parsed)
                else:
                    console.print("[yellow]⚠ Please be more specific about what you want to do.[/yellow]")
                    if parsed.get('llm_error'):
                        console.print(f"[dim]Debug: {parsed['llm_error']}[/dim]")
                
        except KeyboardInterrupt:
            break
    
    console.print("[bold green]Goodbye![/bold green]")

if __name__ == "__main__":
    cli()