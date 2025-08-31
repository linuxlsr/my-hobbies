# SRE Slack Bot User Guide

The SRE Slack Bot provides instant access to vulnerability management, system monitoring, and automated remediation directly from Slack.

## Available Commands

### 🔍 Vulnerability Management

#### `/vuln-check <instance>`
Check vulnerabilities for a specific instance.
```
/vuln-check centos-db
/vuln-check i-02cda701eb446f378
```

#### `/report`
Generate comprehensive vulnerability report for all running instances.
```
/report
```
Shows: Total vulnerabilities, critical/high counts, risk assessment

### 📊 System Monitoring

#### `/metrics <instance>`
Get CPU, memory, and network metrics for an instance.
```
/metrics centos-db
/metrics i-03b46c128bd908d70
```
Shows: 24-hour averages and maximums

#### `/health`
Check overall system health status.
```
/health
```
Shows: Instance counts by state, running instances list

#### `/patch-status <instance>`
Check patch compliance status.
```
/patch-status centos-db
```

### 🔒 Security Operations

#### `/security-events [instance]`
Monitor security events and suspicious activities.
```
/security-events centos-db    # Specific instance
/security-events              # All instances
```
Shows: High-risk alerts, login attempts, privilege escalation

### 🤖 Automated Remediation

#### `/schedule-patch <instance>`
AI-powered patch scheduling with vulnerability resolution.
```
/schedule-patch centos-db
```
Features:
- Analyzes vulnerabilities and system telemetry
- Finds optimal maintenance windows
- Creates EventBridge automation rules
- Shows specific CVEs to be patched
- Provides risk scoring and confidence levels

#### `/show-patches [instance]`
View scheduled patch operations.
```
/show-patches centos-db       # Specific instance
/show-patches                 # All instances
```
Shows: Scheduled times, criticality levels, EventBridge rules

#### `/patch-now <instance>`
Execute immediate patching (use with caution).
```
/patch-now centos-db
```

## Instance Identification

The bot supports both instance IDs and Name tags:
- **Instance ID**: `i-02cda701eb446f378`
- **Name tag**: `centos-db`, `web-server-01`

## Response Types

- **Immediate**: Quick acknowledgment that processing started
- **Delayed**: Detailed results appear shortly after (usually 10-30 seconds)
- **In-channel**: Results visible to everyone
- **Ephemeral**: Error messages visible only to you

## Best Practices

### Daily Operations
1. Start with `/health` to check system status
2. Use `/report` for vulnerability overview
3. Check `/security-events` for suspicious activity
4. Use `/metrics` for performance troubleshooting

### Vulnerability Management
1. Run `/report` to identify critical issues
2. Use `/vuln-check` for detailed instance analysis
3. Schedule remediation with `/schedule-patch`
4. Monitor progress with `/show-patches`

### Emergency Response
1. `/security-events` - Check for active threats
2. `/vuln-check` - Assess vulnerability exposure
3. `/patch-now` - Emergency patching (if needed)
4. `/metrics` - Monitor system impact

## Command Examples

### Morning Health Check
```
/health
/report
/security-events
```

### Instance Investigation
```
/vuln-check web-server-01
/metrics web-server-01
/security-events web-server-01
```

### Patch Management Workflow
```
/report                           # Identify issues
/schedule-patch web-server-01     # Plan remediation
/show-patches                     # Verify schedules
```

## Troubleshooting

### Common Issues
- **"Instance not found"**: Check Name tag spelling or use instance ID
- **"No data available"**: Instance may need CloudWatch agent or SSM agent
- **"Dispatch failed"**: Contact admin - Lambda function issue

### Getting Help
- Use exact instance names or IDs
- Commands work with both running and stopped instances
- Most commands support both specific instances and "all instances"
- Results appear in 10-30 seconds for complex operations

## Integration Notes

- **EventBridge**: Scheduled patches create EventBridge rules
- **CloudWatch**: Metrics require CloudWatch agent on instances  
- **SSM**: Patching requires Systems Manager agent
- **Inspector**: Vulnerability data from AWS Inspector v2

## Security

- All commands log to CloudWatch for audit
- Patch operations require manual approval by default
- Security events are monitored and alerted
- No sensitive data is stored in Slack messages