# SRE CLI Test Suite

## CLI Mode Tests (Direct Commands)

### Basic Commands
```bash
# List instances
sre list

# Status check
sre status

# Scan all vulnerabilities
sre scan-all

# Test core functions
sre test-core-functions
```

### Instance-Specific Commands
```bash
# Vulnerabilities
sre vulnerabilities -i i-00f20fbd7c0075d1d
sre vulnerabilities -i i-03b46c128bd908d70

# CloudWatch metrics
sre cloudwatch-metrics -i i-00f20fbd7c0075d1d
sre cloudwatch-metrics -i i-00f20fbd7c0075d1d -m CPUUtilization
sre cloudwatch-metrics -i centos-db -m MemoryUtilization

# CloudTrail events
sre cloudtrail-events -i i-00f20fbd7c0075d1d
sre cloudtrail-events -i centos-db

# Patch operations
sre patch-status -i i-00f20fbd7c0075d1d
sre patch-window -i i-00f20fbd7c0075d1d
sre patch-now -i i-00f20fbd7c0075d1d --patch-level critical
```

## Ask Mode Tests (Natural Language)

### Basic Queries
```bash
# Status queries
sre ask status
sre ask check health status
sre ask show me the status

# List queries
sre ask list instances
sre ask show all instances
sre ask list all servers
```

### Instance-Specific Queries
```bash
# CPU metrics
sre ask cpu metrics for i-00f20fbd7c0075d1d
sre ask show cpu for centos-db
sre ask cpu performance for 3mn-ami-10

# Memory metrics
sre ask memory metrics for i-00f20fbd7c0075d1d
sre ask show memory for centos-db
sre ask mem usage for NATInstance

# Network metrics
sre ask network metrics for i-00f20fbd7c0075d1d
sre ask show network for centos-db
sre ask network traffic for 3mn-ami-10

# All metrics
sre ask metrics for i-00f20fbd7c0075d1d
sre ask show all metrics for centos-db

# Vulnerabilities
sre ask vulnerabilities for i-00f20fbd7c0075d1d
sre ask show vulns for centos-db
sre ask security scan for 3mn-ami-10
sre ask check security for NATInstance

# Status checks
sre ask status for i-00f20fbd7c0075d1d
sre ask show status for centos-db
sre ask health check for 3mn-ami-10

# Scan all
sre ask scan all instances
sre ask scan everything
sre ask check all vulnerabilities
```

## Chat Mode Tests (Interactive)

### Start chat mode
```bash
sre chat
```

### Test Commands in Chat
```
# Basic commands
status
list instances
scan all

# Instance by ID
cpu metrics for i-00f20fbd7c0075d1d
memory metrics for i-00f20fbd7c0075d1d
network metrics for i-00f20fbd7c0075d1d
vulnerabilities for i-00f20fbd7c0075d1d
status for i-00f20fbd7c0075d1d

# Instance by name
cpu metrics for centos-db
memory metrics for centos-db
network metrics for centos-db
vulnerabilities for centos-db
status for centos-db

# Instance by partial name
cpu metrics for centos
status for NAT
metrics for 3mn

# Natural language variations
show cpu for centos-db
get memory metrics for i-00f20fbd7c0075d1d
check vulnerabilities for 3mn-ami-10
what is the status of centos-db
analyze cpu performance for NATInstance

# Complex queries
show network traffic for centos-db over last 2 hours
check security vulnerabilities for all instances
get cpu and memory metrics for i-00f20fbd7c0075d1d

# Help and exit
help
exit
```

## Expected Behaviors

### Command Parsing
- ✅ CPU/memory/metrics → `cloudwatch_metrics`
- ✅ Vulnerabilities/security/vulns → `vulnerabilities`  
- ✅ Status/health → `status`
- ✅ List/instances → `list`
- ✅ Scan all → `scan_all`

### Instance Resolution
- ✅ Instance IDs (i-00f20fbd7c0075d1d) → Direct use
- ✅ Instance names (centos-db) → Resolve to ID
- ✅ Partial names (centos, NAT, 3mn) → Partial match resolution
- ✅ Multiple matches → Return all matches

### Metric Filtering
- ✅ "cpu metrics" → CPUUtilization only
- ✅ "memory metrics" → MemoryUtilization only  
- ✅ "network metrics" → NetworkIn, NetworkOut
- ✅ "metrics" → All metrics (CPU, Memory, Network)

### Error Handling
- ✅ Invalid instance ID → Error message
- ✅ No instance found → Error message
- ✅ MCP server down → Connection error
- ✅ Low confidence parsing → Fallback or clarification

### Response Quality
- ✅ Rich formatted output with colors
- ✅ Tables for list commands
- ✅ Health indicators (🟢🟡🔴)
- ✅ Anomaly detection alerts
- ✅ Summary statistics

## Performance Tests

### Load Testing
```bash
# Multiple rapid queries
for i in {1..10}; do sre ask status; done
for i in {1..5}; do sre ask cpu metrics for centos-db; done
```

### Timeout Testing
```bash
# Long-running commands
sre scan-all
sre ask scan all instances for vulnerabilities
```

## Edge Cases

### Malformed Queries
```bash
sre ask asdfasdf
sre ask cpu
sre ask for
sre ask metrics for
sre ask status for nonexistent-instance
```

### Ambiguous Queries  
```bash
sre ask show
sre ask check
sre ask metrics
sre ask cpu memory network for centos-db
```

### Special Characters
```bash
sre ask cpu metrics for "centos-db"
sre ask status for i-00f20fbd7c0075d1d,i-03b46c128bd908d70
```