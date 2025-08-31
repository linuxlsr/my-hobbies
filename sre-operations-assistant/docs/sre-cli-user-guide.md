# SRE CLI User Guide

The SRE CLI provides AI-powered natural language interface for vulnerability management, system monitoring, and automated remediation.

## Installation & Setup

### Configuration
```bash
# Configure MCP server endpoints
sre config --mode auto                    # Auto-detect (local first, then remote)
sre config --mode local                   # Use local server only
sre config --mode remote                  # Use remote server only

# Set custom endpoints
sre config --local-url http://localhost:8000
sre config --remote-url http://your-alb-url.com

# View current configuration
sre config
```

### Quick Mode Switching
```bash
sre switch local     # Switch to local MCP server
sre switch remote    # Switch to remote MCP server  
sre switch auto      # Auto-detect mode
```

## Usage Modes

### 1. Natural Language Mode (`sre ask`)
Ask questions in plain English - AI will understand your intent.

```bash
# Vulnerability Management
sre ask check vulnerabilities for centos-db
sre ask scan all instances for critical vulnerabilities
sre ask show me vulnerabilities for i-00f20fbd7c0075d1d

# Performance Monitoring  
sre ask show cpu performance for centos-db last 2 hours
sre ask show memory usage for web-server yesterday
sre ask show network metrics for centos-db last 3 days

# System Status
sre ask show system status
sre ask list all instances
sre ask show health status

# Security & Events
sre ask show security events
sre ask show cloudtrail events for centos-db last week
sre ask monitor security events for all instances

# Automated Remediation
sre ask schedule patches for centos-db
sre ask show scheduled patches
sre ask resolve vulnerabilities for centos-db
sre ask generate vulnerability report
```

### 2. Interactive Chat Mode (`sre chat`)
Continuous conversation with the AI assistant.

```bash
sre chat
```

**Chat Commands:**
- `switch local/remote/auto` - Change MCP server mode
- `config` - Show current configuration  
- `help` - Show available commands and examples
- `exit` - Quit chat mode

**Chat Examples:**
```
sre> show vulns centos-db
sre> show cpu centos-db last 2 hours  
sre> scan all critical
sre> schedule patches centos-db
sre> switch remote
```

## Natural Language Understanding

### Supported Patterns

#### Instance Identification
- **Instance IDs**: `i-00f20fbd7c0075d1d`
- **Name tags**: `centos-db`, `web-server-01`, `production-api`
- **Partial names**: `centos` (matches `centos-db`)

#### Time Ranges
- `last 2 hours`, `yesterday`, `last 3 days`
- `2h`, `24h`, `7d`, `1w`
- `this week`, `last week`

#### Severity Levels
- `critical`, `high`, `medium`, `low`
- `all` (default)

#### Command Types
- **Vulnerabilities**: `vuln`, `vulnerabilities`, `security`, `cve`
- **Metrics**: `cpu`, `memory`, `network`, `performance`, `metrics`
- **Events**: `events`, `cloudtrail`, `audit`, `security events`
- **Status**: `status`, `health`, `list instances`
- **Remediation**: `schedule`, `patch`, `resolve`, `fix`

## Command Categories

### 🔍 Vulnerability Management

```bash
# Scan specific instance
sre ask check vulnerabilities for centos-db

# Scan all instances  
sre ask scan all instances for vulnerabilities

# Generate comprehensive report
sre ask generate vulnerability report

# Resolve vulnerabilities
sre ask resolve vulnerabilities for centos-db
```

### 📊 Performance Monitoring

```bash
# CPU metrics
sre ask show cpu centos-db last 2 hours

# Memory usage
sre ask show memory web-server yesterday  

# Network performance
sre ask show network centos-db last 3 days

# All metrics
sre ask show metrics centos-db
```

### 🔒 Security Operations

```bash
# Security event monitoring
sre ask show security events

# CloudTrail analysis
sre ask show events centos-db last week

# Configuration change analysis
sre ask analyze config changes last 24 hours
```

### 🏥 System Health

```bash
# Overall system status
sre ask show system status

# List all instances
sre ask list instances

# Health check
sre ask show health status
```

### 🤖 Automated Remediation

```bash
# AI-powered patch scheduling
sre ask schedule patches centos-db

# View scheduled patches
sre ask show scheduled patches

# Show patch schedule for specific instance
sre ask show patch schedule for centos-db

# Cancel scheduled patches
sre ask cancel patch centos-db
```

## Advanced Features

### AI-Powered Patch Scheduling
The CLI uses AI to analyze:
- Vulnerability criticality and CVSS scores
- System telemetry and usage patterns  
- Optimal maintenance windows
- Risk assessment and impact analysis

```bash
sre ask schedule automated patching for all instances
```

Features:
- **Intelligent timing**: Finds low-usage windows
- **Risk scoring**: Prioritizes critical vulnerabilities
- **EventBridge integration**: Creates automated schedules
- **Rollback planning**: Prepares recovery procedures
- **Confidence scoring**: Shows AI confidence levels

### Bulk Operations

```bash
# Scan all instances
sre ask scan all instances for critical vulnerabilities

# Resolve all high-priority vulnerabilities
sre ask resolve all high priority vulnerabilities

# Monitor security across all instances
sre ask monitor security events for all instances
```

## Configuration Management

### MCP Server Modes

- **Auto Mode** (default): Tries local server first, falls back to remote
- **Local Mode**: Uses local development server only
- **Remote Mode**: Uses production ECS deployment only

### Endpoint Configuration
```bash
# View current settings
sre config

# Set endpoints
sre config --local-url http://localhost:8000
sre config --remote-url http://your-production-alb.com

# Quick switching
sre switch local    # Development
sre switch remote   # Production
sre switch auto     # Smart detection
```

## Best Practices

### Daily Operations
```bash
sre ask show system status
sre ask generate vulnerability report  
sre ask show security events
```

### Incident Response
```bash
sre ask show security events for affected-server
sre ask check vulnerabilities for affected-server
sre ask show cpu affected-server last hour
```

### Maintenance Planning
```bash
sre ask generate vulnerability report
sre ask schedule patches for production-servers
sre ask show scheduled patches
```

### Development Workflow
```bash
sre switch local                    # Use local server
sre ask check vulnerabilities for test-instance
sre switch remote                   # Switch to production
sre ask show system status
```

## Troubleshooting

### Common Issues

**"MCP server not accessible"**
```bash
sre config                          # Check current settings
sre switch auto                     # Try auto-detection
```

**"Low confidence in understanding"**
- Be more specific about instance names
- Use exact instance IDs when possible
- Include time ranges and severity levels

**"Could not resolve instance name"**
- Check instance Name tags in AWS console
- Use full instance ID instead
- Verify instance is running

### Debug Information
The CLI shows:
- Confidence levels for AI understanding
- Which MCP server endpoint is being used
- Parsing method (LLM vs fallback)

## Integration Notes

- **AWS Services**: EC2, Inspector, CloudWatch, CloudTrail, SSM
- **AI Models**: Amazon Bedrock Titan for natural language processing
- **Automation**: EventBridge for scheduled operations
- **Monitoring**: CloudWatch for metrics and logging

## Security & Compliance

- All operations are logged to CloudWatch
- No credentials stored locally
- Uses AWS IAM for authentication
- Audit trail for all remediation actions
- Manual approval required for critical operations