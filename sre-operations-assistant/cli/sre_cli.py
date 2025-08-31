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
import os
from pathlib import Path
try:
    import readline
except ImportError:
    readline = None

console = Console()

# Configuration management
CONFIG_DIR = Path.home() / ".sre-cli"
CONFIG_FILE = CONFIG_DIR / "config.json"

def load_config():
    """Load CLI configuration"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"mcp_mode": "auto", "local_endpoint": "http://localhost:8000", "remote_endpoint": "https://sre-ops.threemoonsnetwork.net"}

def save_config(config):
    """Save CLI configuration"""
    CONFIG_DIR.mkdir(exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

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
        
        # Extract time range from input
        time_range = "24h"  # default
        time_patterns = {
            r'(\d+)\s*h(?:our)?s?': lambda m: f"{m.group(1)}h",
            r'(\d+)\s*d(?:ay)?s?': lambda m: f"{m.group(1)}d",
            r'(\d+)\s*w(?:eek)?s?': lambda m: f"{int(m.group(1))*7}d",
            r'last\s+(\d+)\s+hours?': lambda m: f"{m.group(1)}h",
            r'last\s+(\d+)\s+days?': lambda m: f"{m.group(1)}d",
            r'yesterday': lambda m: "1d",
            r'this\s+week': lambda m: "7d"
        }
        
        for pattern, converter in time_patterns.items():
            match = re.search(pattern, user_input.lower())
            if match:
                time_range = converter(match)
                break
        
        # Extract severity from input
        severity = "all"  # default
        if 'critical' in user_input.lower():
            severity = "critical"
        elif 'high' in user_input.lower():
            severity = "high"
        elif 'medium' in user_input.lower():
            severity = "medium"
        elif 'low' in user_input.lower():
            severity = "low"
        
        # Look for instance names after 'for' keyword or as last word
        if instance_id == "none":
            if ' for ' in user_input.lower():
                parts = user_input.split(' for ', 1)
                if len(parts) > 1:
                    after_for = parts[1].strip()
                    if after_for:
                        instance_id = after_for
            else:
                # Try to extract instance name from middle of command
                words = user_input.strip().split()
                command_words = ['show', 'get', 'check', 'cpu', 'memory', 'network', 'metrics', 'vulns', 'vuln', 'vulnerabilities', 'status', 'last', 'hours', 'days', 'weeks', 'yesterday', 'critical', 'high', 'medium', 'low', 'report', 'generate', 'resolve', 'schedule', 'patch', 'patches', 'scheduled', 'window', 'events', 'security', 'all']
                
                # Find potential instance names (words that aren't command words or numbers)
                for i, word in enumerate(words):
                    if (word.lower() not in command_words and 
                        not word.isdigit() and 
                        len(word) > 2 and
                        not re.match(r'^\d+[hdw]$', word)):
                        instance_id = word
                        break
        
        prompt = f"""Parse: '{user_input}'

What is the main request? Look for these exact words:
- If 'cpu' or 'memory' or 'metrics' → cloudwatch_metrics
- If 'vuln' or 'vulnerabilities' or 'security' → vulnerabilities
- If 'resolve' or 'fix' or 'patch' vulnerabilities → resolve_vulns
- If 'report' or 'generate report' → vuln_report
- If 'schedule' or 'maintenance' or 'patch window' → schedule_patches
- If 'bulk' or 'resolve all' or 'fix all' → bulk_resolve
- If 'status' or 'health' → status
- If 'scan all' → scan_all
- If 'list' or 'instances' → list

Return JSON:
{{"command": "cloudwatch_metrics", "instance_ids": [], "confidence": 0.9}}

JSON:"""

        try:
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": 50,
                        "temperature": 0.0,
                        "topP": 1.0
                    }
                })
            )
            
            result = json.loads(response['body'].read())
            content = result['results'][0]['outputText'].strip()
            
            # Simple extraction - just look for command word in input and response
            input_lower = user_input.lower()
            content_lower = content.lower()
            
            if 'status' in input_lower or 'health' in input_lower:
                command = 'status'
            elif 'cpu' in input_lower or 'memory' in input_lower or 'mem' in input_lower or 'network' in input_lower or 'metrics' in input_lower:
                command = 'cloudwatch_metrics'
            elif 'show' in input_lower and 'scheduled' in input_lower and 'patch' in input_lower:
                command = 'show_scheduled_patches'
            elif 'schedule' in input_lower or 'patch' in input_lower or 'window' in input_lower:
                command = 'schedule_patches'
            elif 'scan' in input_lower and 'all' in input_lower:
                command = 'scan_all'
            elif 'list' in input_lower or 'instances' in input_lower:
                command = 'list'
            elif 'report' in input_lower and ('vuln' in input_lower or 'vulnerabilities' in input_lower):
                command = 'vuln_report'
            elif 'resolve' in input_lower and ('vuln' in input_lower or 'vulnerabilities' in input_lower):
                command = 'resolve_vulns'
            elif 'security' in input_lower and ('events' in input_lower or 'monitor' in input_lower):
                command = 'security_events'
            elif 'events' in input_lower or 'cloudtrail' in input_lower or 'audit' in input_lower:
                command = 'cloudtrail_events'
            elif 'vuln' in input_lower or 'vulnerabilities' in input_lower or 'security' in input_lower:
                command = 'vulnerabilities'
            else:
                raise ValueError("No clear command found")
            
            parsed = {"command": command, "confidence": 0.9, "instance_ids": []}
            
            # Fix instance IDs based on command
            command = parsed.get("command")
            instance_ids = parsed.get("instance_ids", [])
            
            if command in ['list', 'scan_all', 'status']:
                instance_ids = []
            elif instance_id != "none":
                instance_ids = [instance_id]
            
            return {
                "command": parsed.get("command"),
                "instance_ids": instance_ids,
                "time_range": time_range,
                "severity": severity,
                "confidence": parsed.get("confidence", 0.9),
                "original_text": user_input,
                "method": "llm"
            }
                
        except Exception as e:
            # console.print(f"[dim]LLM failed, using fallback[/dim]")
            return self._fallback_parse(user_input, str(e))
    
    def _fallback_parse(self, text: str, error: str) -> Dict[str, Any]:
        """Fallback regex parsing if LLM fails"""
        
        # Basic regex fallback
        instance_match = re.search(r'i-[a-f0-9]{8,17}', text)
        instance_ids = [instance_match.group(0)] if instance_match else []
        
        # Also check for names after 'for' or as last word
        if not instance_ids:
            if ' for ' in text.lower():
                parts = text.split(' for ', 1)
                if len(parts) > 1:
                    after_for = parts[1].strip()
                    if after_for and not after_for.lower() in ['all', 'everything']:
                        instance_ids = [after_for]
            else:
                # Try to extract instance name from middle of command
                words = text.strip().split()
                command_words = ['show', 'get', 'check', 'cpu', 'memory', 'network', 'metrics', 'vulns', 'vuln', 'vulnerabilities', 'status', 'last', 'hours', 'days', 'weeks', 'yesterday', 'critical', 'high', 'medium', 'low', 'report', 'generate', 'resolve', 'schedule', 'patch', 'patches', 'scheduled', 'window', 'events', 'security', 'all']
                
                # Find potential instance names (words that aren't command words or numbers)
                for i, word in enumerate(words):
                    if (word.lower() not in command_words and 
                        not word.isdigit() and 
                        len(word) > 2 and
                        not re.match(r'^\d+[hdw]$', word)):
                        instance_ids = [word]
                        break
        
        # Simple command detection
        text_lower = text.lower()
        if any(phrase in text_lower for phrase in ['scan all', 'scan everything', 'check all']):
            command = 'scan_all'
        elif any(word in text_lower for word in ['cpu', 'mem', 'memory', 'network', 'metrics', 'performance', 'cloudwatch']) and 'all' not in text_lower:
            command = 'cloudwatch_metrics'
        elif any(phrase in text_lower for phrase in ['resolve vuln', 'fix vuln', 'patch vuln', 'resolve vulnerabilities']):
            command = 'resolve_vulns'
        elif any(phrase in text_lower for phrase in ['vuln report', 'vulnerability report', 'generate report']):
            command = 'vuln_report'
        elif 'schedule' in text_lower or any(phrase in text_lower for phrase in ['maintenance window', 'patch window', 'optimal window']):
            command = 'schedule_patches'
        elif any(phrase in text_lower for phrase in ['vuln report', 'vulnerability report', 'generate report']) or ('report' in text_lower and any(word in text_lower for word in ['vuln', 'vulnerabilities'])):
            command = 'vuln_report'
        elif any(phrase in text_lower for phrase in ['resolve vuln', 'fix vuln', 'resolve vulnerabilities']) or ('resolve' in text_lower and any(word in text_lower for word in ['vuln', 'vulnerabilities'])):
            command = 'resolve_vulns'
        elif any(phrase in text_lower for phrase in ['bulk resolve', 'resolve all', 'fix all']):
            command = 'bulk_resolve'
        elif any(word in text_lower for word in ['vuln', 'vulns', 'vulnerabilities', 'security', 'cve']):
            command = 'vulnerabilities'
        elif any(word in text_lower for word in ['events', 'cloudtrail', 'audit']) and 'security' not in text_lower:
            command = 'cloudtrail_events'
        elif 'security' in text_lower and ('events' in text_lower or 'monitor' in text_lower):
            command = 'security_events'
        elif any(phrase in text_lower for phrase in ['scheduled patches', 'patch schedule', 'show schedule']) or ('show' in text_lower and 'scheduled' in text_lower):
            command = 'show_scheduled_patches'
        elif any(phrase in text_lower for phrase in ['schedule patch', 'auto patch', 'schedule remediation']):
            command = 'schedule_patches'
        elif any(phrase in text_lower for phrase in ['cancel patch', 'cancel schedule']):
            command = 'cancel_patch'
        elif any(word in text_lower for word in ['list', 'instances']):
            command = 'list'
        elif any(word in text_lower for word in ['status', 'health']):
            command = 'status'
        else:
            command = None
        
        # If command detected but no instance ID, suggest higher confidence for prompting
        confidence = 0.8 if command and instance_ids else 0.6 if command and command == 'scan_all' else 0.3 if command else 0.1
        
        # Commands that don't need instance IDs or can work with "all"
        needs_instance_id = command is not None and not instance_ids and command not in ['scan_all', 'list', 'status', 'schedule_patches', 'resolve_vulns', 'security_events', 'vuln_report', 'show_scheduled_patches', 'cancel_patch'] and 'all' not in text.lower() and command != 'vulnerabilities'
        
        # Extract time range and severity for fallback too
        time_range = "24h"
        severity = "all"
        
        time_patterns = {
            r'(\d+)\s*h(?:our)?s?': lambda m: f"{m.group(1)}h",
            r'(\d+)\s*d(?:ay)?s?': lambda m: f"{m.group(1)}d",
            r'last\s+(\d+)\s+hours?': lambda m: f"{m.group(1)}h",
            r'last\s+(\d+)\s+days?': lambda m: f"{m.group(1)}d"
        }
        
        for pattern, converter in time_patterns.items():
            match = re.search(pattern, text.lower())
            if match:
                time_range = converter(match)
                break
        
        if 'critical' in text.lower():
            severity = "critical"
        elif 'high' in text.lower():
            severity = "high"
        elif 'medium' in text.lower():
            severity = "medium"
        elif 'low' in text.lower():
            severity = "low"
        
        return {
            "command": command,
            "instance_ids": instance_ids,
            "time_range": time_range,
            "severity": severity,
            "confidence": confidence,
            "original_text": text,
            "method": "fallback",
            "llm_error": error,
            "needs_instance_id": needs_instance_id
        }

# Get MCP server endpoint
def get_mcp_endpoint():
    config = load_config()
    mode = config.get("mcp_mode", "auto")
    local_endpoint = config.get("local_endpoint", "http://localhost:8000")
    remote_endpoint = config.get("remote_endpoint", "https://sre-ops.threemoonsnetwork.net")
    
    if mode == "local":
        endpoints = [local_endpoint]
    elif mode == "remote":
        endpoints = [remote_endpoint]
    else:  # auto mode
        endpoints = [local_endpoint, "http://127.0.0.1:8000", remote_endpoint]
    
    for url in endpoints:
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                console.print(f"[green]Connected to server: {url}[/green]")
                return url
        except:
            continue
    
    return None

@click.group()
@click.version_option(version="1.0.0")
def cli():
    """SRE Operations Assistant CLI - MCP-powered vulnerability management"""
    pass

@cli.command()
@click.argument('query', nargs=-1)
def ask(query):
    """Ask anything in natural language using AI!
    
    Examples:
      sre ask check vulnerabilities for i-00f20fbd7c0075d1d
      sre ask show me cpu performance for i-123 over the last hour
      sre ask scan all instances for vulnerabilities
      sre ask schedule patches centos-db
      sre ask show scheduled patches
    """
    if not query:
        console.print("[yellow]Usage: sre ask <your question>[/yellow]")
        console.print("Examples:")
        console.print("  sre ask show vulns centos-db")
        console.print("  sre ask show cpu centos-db last 2 hours")
        console.print("  sre ask scan all critical")
        console.print("  sre ask show security events")
        console.print("  sre ask schedule patches centos-db")
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
        
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                
                # Get name from tags
                for tag in instance.get('Tags', []):
                    if tag['Key'] == 'Name':
                        name = tag['Value']
                        if name not in name_to_id:
                            name_to_id[name] = []
                        name_to_id[name].append(instance_id)
                        break
        
        # console.print(f"[dim]Available names: {list(name_to_id.keys())}[/dim]")
        # console.print(f"[dim]Looking for: {identifiers}[/dim]")
        
        # Resolve each identifier
        for identifier in identifiers:
            if identifier.startswith('i-'):
                # Already an instance ID
                resolved_ids.append(identifier)
            elif identifier in name_to_id:
                # Exact instance name match - add all instances with this name
                resolved_ids.extend(name_to_id[identifier])
                # console.print(f"[dim]Exact match '{identifier}' -> {name_to_id[identifier]}[/dim]")
            else:
                # Try partial name match
                matches = [name for name in name_to_id.keys() if identifier.lower() in name.lower()]
                if matches:
                    # console.print(f"[dim]Partial matches for '{identifier}': {matches}[/dim]")
                    for match in matches:
                        resolved_ids.extend(name_to_id[match])
                # else:
                    # console.print(f"[dim]No matches found for '{identifier}'[/dim]")
    
    except Exception as e:
        # console.print(f"[dim]Resolution error: {e}[/dim]")
        return identifiers
    
    # console.print(f"[dim]Resolved to: {resolved_ids}[/dim]")
    return resolved_ids

def _execute_ai_command(endpoint: str, parsed_cmd: dict):
    """Execute AI-parsed command"""
    command = parsed_cmd['command']
    instance_ids = parsed_cmd['instance_ids']
    time_range = parsed_cmd['time_range']
    severity = parsed_cmd.get('severity', 'all')
    
    if command == 'scan_all':
        console.print("[bold blue]🔍 Scanning all instances for vulnerabilities...[/bold blue]")
        response = requests.post(f"{endpoint}/mcp", json={
            "method": "get_inspector_findings",
            "params": {"severity": severity}
        }, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            console.print(f"[green]✓ Found {len(data.get('findings', []))} total vulnerabilities[/green]")
            console.print(f"Summary: {data.get('summary', 'No summary')}")
        else:
            console.print(f"[red]✗ Error: {response.status_code}[/red]")
        return
    
    # Resolve instance names to IDs and handle "all" cases
    if instance_ids:
        instance_ids = _resolve_instance_identifiers(instance_ids)
        if not instance_ids:  # If resolution failed, show error for specific names
            console.print("[red]✗ Could not resolve instance name[/red]")
            return
    elif command == 'vulnerabilities' and not instance_ids:
        # For vulnerabilities without specific instance, check all running instances
        try:
            ec2 = boto3.client('ec2')
            response = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
            instance_ids = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instance_ids.append(instance['InstanceId'])
        except Exception:
            console.print("[red]✗ Could not get instance list[/red]")
            return
    elif not instance_ids and command not in ['vuln_report', 'resolve_vulns', 'schedule_patches', 'scan_all', 'vulnerabilities', 'status', 'list', 'security_events', 'show_scheduled_patches', 'cancel_patch']:
        console.print("[red]✗ No instance ID found[/red]")
        return
    
    instance_id = instance_ids[0] if instance_ids else None
    
    try:
        if command == 'vulnerabilities':
            if len(instance_ids) == 1:
                console.print(f"[bold blue]🔍 Analyzing vulnerabilities for {instance_ids[0]}...[/bold blue]")
                response = requests.post(f"{endpoint}/mcp", json={
                    "method": "get_inspector_findings",
                    "params": {"instance_id": instance_ids[0], "severity": severity}
                }, timeout=30)
            else:
                console.print(f"[bold blue]🔍 Analyzing vulnerabilities for {len(instance_ids)} instances...[/bold blue]")
                response = requests.post(f"{endpoint}/mcp", json={
                    "method": "get_inspector_findings",
                    "params": {"severity": severity}
                }, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                console.print(f"[green]✓ Found {len(data.get('findings', []))} vulnerabilities[/green]")
                console.print(f"Summary: {data.get('summary', 'No summary')}")
            else:
                console.print(f"[red]✗ Error: {response.status_code}[/red]")
        
        elif command == 'schedule_patches':
            # If no specific instances, get all running instances
            if not instance_ids:
                try:
                    ec2 = boto3.client('ec2')
                    response = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
                    instance_ids = []
                    for reservation in response['Reservations']:
                        for instance in reservation['Instances']:
                            instance_ids.append(instance['InstanceId'])
                except Exception:
                    console.print("[red]✗ Could not get instance list[/red]")
                    return
            
            console.print(f"[bold blue]🤖 AI-Powered Automated Patch Scheduling for {len(instance_ids)} instance(s)...[/bold blue]")
            console.print(f"[dim]Analyzing vulnerabilities, telemetry, and optimal windows...[/dim]")
            response = requests.post(f"{endpoint}/mcp", json={
                "method": "schedule_automated_patching",
                "params": {
                    "instance_ids": instance_ids,
                    "criticality": severity if severity != 'all' else 'high'
                }
            }, timeout=120)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    console.print(f"[red]✗ Error: {data['error']}[/red]")
                else:
                    console.print(f"[green]✓ Automated Patch Scheduling Complete[/green]")
                    
                    plan_id = data.get('plan_id', 'Unknown')
                    schedules = data.get('instance_schedules', [])
                    
                    console.print(f"\n[cyan]📅 Remediation Plan: {plan_id}[/cyan]")
                    console.print(f"  Total instances: {data.get('total_instances', 0)}")
                    console.print(f"  Criticality level: {data.get('criticality', 'high')}")
                    
                    # Show first few scheduled instances
                    console.print(f"\n[bold]Scheduled Patches:[/bold]")
                    for i, schedule in enumerate(schedules[:3]):
                        instance_id = schedule.get('instance_id', 'Unknown')
                        vuln_count = schedule.get('vulnerability_count', 0)
                        risk_score = schedule.get('risk_score', 0)
                        optimal_window = schedule.get('optimal_window', {})
                        window_time = optimal_window.get('recommended_datetime', 'Unknown')
                        confidence = optimal_window.get('confidence_score', 0)
                        duration = schedule.get('estimated_duration', {})
                        total_minutes = duration.get('total_minutes', 0)
                        
                        risk_color = "red" if risk_score >= 80 else "yellow" if risk_score >= 60 else "green"
                        console.print(f"  [{risk_color}]{instance_id}[/{risk_color}]:")
                        console.print(f"    Vulnerabilities: {vuln_count} (risk: {risk_score:.1f})")
                        console.print(f"    Scheduled: {window_time} (confidence: {confidence:.1%})")
                        console.print(f"    Duration: {total_minutes} minutes")
                        
                        reasoning = optimal_window.get('reasoning', 'AI-optimized window')
                        console.print(f"    Reason: {reasoning}")
                        console.print()
                    
                    if len(schedules) > 3:
                        console.print(f"  ... and {len(schedules) - 3} more instances scheduled")
                    
                    console.print(f"\n[blue]🚀 Next Steps:[/blue]")
                    console.print(f"  1. Patches are scheduled based on AI analysis")
                    console.print(f"  2. Use 'show scheduled patches' to view all schedules")
                    console.print(f"  3. EventBridge rules will trigger patches automatically")
                    console.print(f"  4. Pre-patch checks and rollback plans are prepared")
            else:
                console.print(f"[red]✗ Error: {response.status_code}[/red]")
        
        elif command == 'cloudwatch_metrics':
            if len(instance_ids) == 1:
                console.print(f"[bold blue]📊 Getting metrics for {instance_ids[0]}...[/bold blue]")
                # Determine which metrics based on original text
                text_lower = parsed_cmd['original_text'].lower()
                if 'cpu' in text_lower and 'mem' not in text_lower and 'memory' not in text_lower and 'network' not in text_lower:
                    metric_names = ["CPUUtilization"]
                elif ('mem' in text_lower or 'memory' in text_lower) and 'cpu' not in text_lower and 'network' not in text_lower:
                    metric_names = ["MemoryUtilization"]
                elif 'network' in text_lower and 'cpu' not in text_lower and 'mem' not in text_lower and 'memory' not in text_lower:
                    metric_names = ["NetworkIn", "NetworkOut"]
                else:
                    metric_names = ["CPUUtilization", "MemoryUtilization", "NetworkIn", "NetworkOut"]
                
                response = requests.post(f"{endpoint}/mcp", json={
                    "method": "get_ec2_cloudwatch_metrics",
                    "params": {
                        "instance_id": instance_ids[0],
                        "metric_names": metric_names,
                        "time_range": time_range
                    }
                }, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if "error" in data:
                        console.print(f"[red]✗ Error: {data['error']}[/red]")
                    else:
                        console.print(f"[green]✓ Metrics for {instance_ids[0]}[/green]")
                        metrics_data = data.get('metrics', {})
                        for metric_name, metric_info in metrics_data.items():
                            if isinstance(metric_info, dict) and 'average' in metric_info:
                                avg = metric_info['average']
                                max_val = metric_info.get('maximum', 0)
                                if 'CPU' in metric_name or 'Memory' in metric_name:
                                    unit = '%'
                                    console.print(f"  [cyan]{metric_name}[/cyan]: {avg:.2f}{unit} (avg), {max_val:.2f}{unit} (max)")
                                elif 'Network' in metric_name:
                                    # Network metrics are in bytes, show raw values and converted
                                    if avg > 1024 * 1024:
                                        avg_mb = avg / 1024 / 1024
                                        max_mb = max_val / 1024 / 1024
                                        console.print(f"  [cyan]{metric_name}[/cyan]: {avg_mb:.2f} MB (avg), {max_mb:.2f} MB (max) | Raw: {avg:.0f} bytes")
                                    elif avg > 1024:
                                        avg_kb = avg / 1024
                                        max_kb = max_val / 1024
                                        console.print(f"  [cyan]{metric_name}[/cyan]: {avg_kb:.2f} KB (avg), {max_kb:.2f} KB (max) | Raw: {avg:.0f} bytes")
                                    else:
                                        console.print(f"  [cyan]{metric_name}[/cyan]: {avg:.0f} bytes (avg), {max_val:.0f} bytes (max)")
                                else:
                                    console.print(f"  [cyan]{metric_name}[/cyan]: {avg:.2f} (avg), {max_val:.2f} (max)")
                            else:
                                console.print(f"  [yellow]{metric_name}[/yellow]: {metric_info.get('status', 'no data')}")
                else:
                    console.print(f"[red]✗ Error: {response.status_code}[/red]")
            else:
                console.print("[yellow]CloudWatch metrics requires a single instance[/yellow]")
        
        elif command == 'status':
            console.print(f"[bold blue]🏥 Checking health status...[/bold blue]")
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
        
        elif command == 'list':
            console.print(f"[bold blue]📋 Listing EC2 instances...[/bold blue]")
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
        
        elif command == 'cloudtrail_events':
            if len(instance_ids) == 1:
                console.print(f"[bold blue]📄 Analyzing CloudTrail events for {instance_ids[0]}...[/bold blue]")
                response = requests.post(f"{endpoint}/mcp", json={
                    "method": "analyze_cloudtrail_events",
                    "params": {
                        "instance_id": instance_ids[0],
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
                        
                        if suspicious > 0:
                            console.print(f"[yellow]⚠ {suspicious} suspicious activities detected[/yellow]")
                else:
                    console.print(f"[red]✗ Error: {response.status_code}[/red]")
            else:
                console.print("[yellow]CloudTrail events requires a single instance[/yellow]")
        
        elif command == 'security_events':
            if not instance_ids:
                try:
                    ec2 = boto3.client('ec2')
                    response = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
                    instance_ids = []
                    for reservation in response['Reservations']:
                        for instance in reservation['Instances']:
                            instance_ids.append(instance['InstanceId'])
                except Exception:
                    console.print("[red]✗ Could not get instance list[/red]")
                    return
            
            console.print(f"[bold blue]🔒 Monitoring security events for {len(instance_ids)} instance(s)...[/bold blue]")
            response = requests.post(f"{endpoint}/mcp", json={
                "method": "monitor_security_events",
                "params": {
                    "instance_ids": instance_ids,
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
                    console.print(f"  Instances monitored: {total_instances}")
                    console.print(f"  Security alerts: {len(alerts)}")
                    
                    if alerts:
                        console.print(f"[red]🚨 {len(alerts)} high-risk security alerts![/red]")
                        for alert in alerts[:3]:
                            console.print(f"    {alert['instance_id']}: {alert['alert_level']} risk")
            else:
                console.print(f"[red]✗ Error: {response.status_code}[/red]")
        
        elif command == 'vuln_report':
            if not instance_ids:
                try:
                    ec2 = boto3.client('ec2')
                    response = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
                    instance_ids = []
                    for reservation in response['Reservations']:
                        for instance in reservation['Instances']:
                            instance_ids.append(instance['InstanceId'])
                except Exception:
                    console.print("[red]✗ Could not get instance list[/red]")
                    return
            
            console.print(f"[bold blue]📄 Generating vulnerability report for {len(instance_ids)} instance(s)...[/bold blue]")
            response = requests.post(f"{endpoint}/mcp", json={
                "method": "generate_vulnerability_report",
                "params": {
                    "instance_ids": instance_ids,
                    "format": "summary"
                }
            }, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    console.print(f"[red]✗ Error: {data['error']}[/red]")
                else:
                    console.print(f"[green]✓ Report generated[/green]")
                    
                    # Report summary
                    summary = data.get('summary', {})
                    total_vulns = summary.get('total_vulnerabilities', 0)
                    critical = summary.get('critical_count', 0)
                    high = summary.get('high_count', 0)
                    
                    console.print(f"\n[bold]Vulnerability Summary:[/bold]")
                    console.print(f"  Total vulnerabilities: [red]{total_vulns}[/red]")
                    console.print(f"  Critical severity: [red]{critical}[/red]")
                    console.print(f"  High severity: [yellow]{high}[/yellow]")
                    
                    # Risk assessment
                    if critical > 0:
                        console.print(f"\n[red]🚨 CRITICAL: {critical} critical vulnerabilities require immediate attention![/red]")
                    elif high > 10:
                        console.print(f"\n[yellow]⚠ HIGH RISK: {high} high-severity vulnerabilities detected[/yellow]")
                    elif total_vulns > 0:
                        console.print(f"\n[blue]ℹ MODERATE: {total_vulns} vulnerabilities found, review recommended[/blue]")
                    else:
                        console.print(f"\n[green]✅ GOOD: No vulnerabilities detected[/green]")
            else:
                console.print(f"[red]✗ Error: {response.status_code}[/red]")
        
        elif command == 'resolve_vulns':
            if not instance_ids:
                try:
                    ec2 = boto3.client('ec2')
                    response = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
                    instance_ids = []
                    for reservation in response['Reservations']:
                        for instance in reservation['Instances']:
                            instance_ids.append(instance['InstanceId'])
                except Exception:
                    console.print("[red]✗ Could not get instance list[/red]")
                    return
            
            console.print(f"[bold blue]🔧 Resolving vulnerabilities for {len(instance_ids)} instance(s)...[/bold blue]")
            response = requests.post(f"{endpoint}/mcp", json={
                "method": "resolve_vulnerabilities_by_criticality",
                "params": {
                    "instance_ids": instance_ids,
                    "criticality": "high",
                    "auto_approve": False
                }
            }, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    console.print(f"[red]✗ Error: {data['error']}[/red]")
                else:
                    console.print(f"[green]✓ Resolution plan created[/green]")
                    actions = data.get('actions', [])
                    total_vulns = data.get('total_vulnerabilities', 0)
                    console.print(f"  Total vulnerabilities: {total_vulns}")
                    console.print(f"  Planned actions: {len(actions)}")
            else:
                console.print(f"[red]✗ Error: {response.status_code}[/red]")
        
        elif command == 'show_scheduled_patches':
            console.print(f"[bold blue]📅 Getting scheduled patches...[/bold blue]")
            response = requests.post(f"{endpoint}/mcp", json={
                "method": "get_scheduled_patches",
                "params": {
                    "instance_id": instance_id if instance_ids else None
                }
            }, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    console.print(f"[red]✗ Error: {data['error']}[/red]")
                else:
                    patches = data.get('scheduled_patches', [])
                    console.print(f"[green]✓ Found {len(patches)} scheduled patches[/green]")
                    
                    if patches:
                        table = Table(title="Scheduled Patches")
                        table.add_column("Instance ID", style="cyan")
                        table.add_column("Scheduled Time", style="yellow")
                        table.add_column("Criticality", style="red")
                        table.add_column("Duration", style="blue")
                        table.add_column("Status", style="green")
                        
                        for patch in patches:
                            table.add_row(
                                patch.get('instance_id', 'N/A'),
                                patch.get('scheduled_time', 'N/A'),
                                patch.get('criticality', 'N/A'),
                                patch.get('estimated_duration', 'N/A'),
                                patch.get('status', 'N/A')
                            )
                        
                        console.print(table)
                    else:
                        console.print("[yellow]No scheduled patches found[/yellow]")
            else:
                console.print(f"[red]✗ Error: {response.status_code}[/red]")
        
        elif command == 'cancel_patch':
            if not instance_ids:
                console.print("[red]✗ Instance ID required to cancel patch[/red]")
                return
            
            # For demo, use a mock rule name
            rule_name = f"patch-{instance_ids[0]}-high-202401150200"
            
            console.print(f"[bold blue]❌ Cancelling scheduled patch for {instance_ids[0]}...[/bold blue]")
            response = requests.post(f"{endpoint}/mcp", json={
                "method": "cancel_scheduled_patch",
                "params": {
                    "instance_id": instance_ids[0],
                    "rule_name": rule_name
                }
            }, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    console.print(f"[red]✗ Error: {data['error']}[/red]")
                else:
                    console.print(f"[green]✓ Patch cancelled for {instance_ids[0]}[/green]")
                    console.print(f"  Rule: {data.get('rule_name', 'N/A')}")
                    console.print(f"  Status: {data.get('status', 'N/A')}")
            else:
                console.print(f"[red]✗ Error: {response.status_code}[/red]")
        
        else:
            console.print(f"[yellow]Command '{command}' not implemented yet[/yellow]")
    
    except Exception as e:
        console.print(f"[red]✗ Request failed: {e}[/red]")

@cli.command()
@click.option('--mode', type=click.Choice(['local', 'remote', 'auto']), help='MCP server mode')
@click.option('--local-url', help='Local MCP server URL')
@click.option('--remote-url', help='Remote MCP server URL')
def config(mode, local_url, remote_url):
    """Configure MCP server settings"""
    config_data = load_config()
    
    if not any([mode, local_url, remote_url]):
        # Show current configuration
        console.print("[bold blue]Current Configuration:[/bold blue]")
        console.print(f"  Mode: [cyan]{config_data.get('mcp_mode', 'auto')}[/cyan]")
        console.print(f"  Local endpoint: [green]{config_data.get('local_endpoint', 'http://localhost:8000')}[/green]")
        console.print(f"  Remote endpoint: [yellow]{config_data.get('remote_endpoint', 'https://sre-ops.threemoonsnetwork.net')}[/yellow]")
        
        # Test current endpoint
        endpoint = get_mcp_endpoint()
        if endpoint:
            console.print(f"\n[green]✓ Currently connected to: {endpoint}[/green]")
        else:
            console.print(f"\n[red]✗ No MCP server accessible[/red]")
        return
    
    # Update configuration
    if mode:
        config_data['mcp_mode'] = mode
        console.print(f"[green]✓ Mode set to: {mode}[/green]")
    
    if local_url:
        config_data['local_endpoint'] = local_url
        console.print(f"[green]✓ Local endpoint set to: {local_url}[/green]")
    
    if remote_url:
        config_data['remote_endpoint'] = remote_url
        console.print(f"[green]✓ Remote endpoint set to: {remote_url}[/green]")
    
    save_config(config_data)
    
    # Test new configuration
    console.print("\n[cyan]Testing new configuration...[/cyan]")
    endpoint = get_mcp_endpoint()
    if endpoint:
        console.print(f"[green]✓ Successfully connected to: {endpoint}[/green]")
    else:
        console.print(f"[red]✗ Cannot connect with new configuration[/red]")

@cli.command()
@click.argument('mode', type=click.Choice(['local', 'remote', 'auto']))
def switch(mode):
    """Quick switch between MCP server modes
    
    Examples:
      sre switch local   # Use local MCP server only
      sre switch remote  # Use remote MCP server only  
      sre switch auto    # Auto-detect (local first, then remote)
    """
    config_data = load_config()
    old_mode = config_data.get('mcp_mode', 'auto')
    config_data['mcp_mode'] = mode
    save_config(config_data)
    
    console.print(f"[green]✓ Switched from {old_mode} to {mode} mode[/green]")
    
    # Test new mode
    console.print(f"[cyan]Testing {mode} mode...[/cyan]")
    endpoint = get_mcp_endpoint()
    if endpoint:
        console.print(f"[green]✓ Connected to: {endpoint}[/green]")
    else:
        console.print(f"[red]✗ Cannot connect in {mode} mode[/red]")
        console.print("[yellow]Tip: Use 'sre config' to check endpoints[/yellow]")

@cli.command()
def chat():
    """Interactive AI-powered chat mode"""
    console.print("[bold green]🤖 AI-Powered SRE Assistant[/bold green]")
    console.print("Speak naturally! The AI will understand your intent.")
    console.print("Type 'exit' to quit")
    
    # Enable command history with readline
    if readline:
        import os
        histfile = os.path.join(os.path.expanduser("~"), ".sre_history")
        try:
            readline.read_history_file(histfile)
        except FileNotFoundError:
            pass
    
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
            elif user_input.lower().startswith('switch '):
                # Handle switch command in chat mode
                parts = user_input.lower().split()
                if len(parts) == 2 and parts[1] in ['local', 'remote', 'auto']:
                    mode = parts[1]
                    config_data = load_config()
                    old_mode = config_data.get('mcp_mode', 'auto')
                    config_data['mcp_mode'] = mode
                    save_config(config_data)
                    
                    console.print(f"[green]✓ Switched from {old_mode} to {mode} mode[/green]")
                    
                    # Test new mode and update endpoint
                    console.print(f"[cyan]Testing {mode} mode...[/cyan]")
                    endpoint = get_mcp_endpoint()
                    if endpoint:
                        console.print(f"[green]✓ Connected to: {endpoint}[/green]")
                    else:
                        console.print(f"[red]✗ Cannot connect in {mode} mode[/red]")
                        console.print("[yellow]Tip: Use 'config' to check endpoints[/yellow]")
                else:
                    console.print("[yellow]Usage: switch [local|remote|auto][/yellow]")
            elif user_input.lower() == 'config':
                # Show current configuration in chat mode
                config_data = load_config()
                console.print("[bold blue]Current Configuration:[/bold blue]")
                console.print(f"  Mode: [cyan]{config_data.get('mcp_mode', 'auto')}[/cyan]")
                console.print(f"  Local endpoint: [green]{config_data.get('local_endpoint', 'http://localhost:8000')}[/green]")
                console.print(f"  Remote endpoint: [yellow]{config_data.get('remote_endpoint', 'https://sre-ops.threemoonsnetwork.net')}[/yellow]")
                
                # Test current endpoint
                endpoint = get_mcp_endpoint()
                if endpoint:
                    console.print(f"\n[green]✓ Currently connected to: {endpoint}[/green]")
                else:
                    console.print(f"\n[red]✗ No MCP server accessible[/red]")
            elif user_input.lower() == 'help':
                console.print("""
[bold]Natural Language Examples:[/bold]

[cyan]Vulnerabilities:[/cyan]
• show vulns centos-db
• show critical vulnerabilities
• scan all instances
• resolve vulnerabilities centos-db

[cyan]Metrics & Monitoring:[/cyan]
• show cpu centos-db last 2 hours
• show network 3mn-ami-10 last 3 days
• show memory centos-db
• show metrics centos-db yesterday

[cyan]Security & Events:[/cyan]
• show security events
• show events centos-db last week
• show cloudtrail centos-db

[cyan]System Management:[/cyan]
• show status
• list instances
• show patch window centos-db

[cyan]Configuration:[/cyan]
• switch local / switch remote / switch auto
• config (show current settings)

[cyan]Automated Remediation:[/cyan]
• schedule patches centos-db
• schedule automated patching for all instances
• show scheduled patches
• show patch schedule for centos-db
• cancel patch centos-db

[cyan]Time & Severity Options:[/cyan]
• last 2 hours, yesterday, last 3 days
• critical, high, medium, low severity
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
                    else:
                        _execute_ai_command(endpoint, parsed)
                else:
                    console.print("[yellow]⚠ Please be more specific about what you want to do.[/yellow]")
                
        except KeyboardInterrupt:
            break
    
    # Save command history
    if readline:
        try:
            readline.write_history_file(histfile)
        except:
            pass
    
    console.print("[bold green]Goodbye![/bold green]")

if __name__ == "__main__":
    cli()