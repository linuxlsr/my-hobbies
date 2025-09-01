# Troubleshooting Guide

## 🔧 Common Issues and Solutions

### CLI Issues

#### "Cannot connect in remote mode"
**Problem**: CLI can't reach the remote endpoint
**Solutions**:
```bash
# Check endpoint configuration
terraform apply config

# Test endpoint directly
curl https://sre-ops.your-domain.com/health

# Switch to local mode temporarily
terraform apply chat
# Then type: switch local

# Update endpoint if needed
terraform apply config --remote-url https://your-endpoint.com
```

#### "No such command 'status'"
**Problem**: Using wrong CLI syntax
**Solution**: Use the `ask` command for queries:
```bash
# Wrong
terraform apply status

# Correct
terraform apply ask "status"
terraform apply ask "show me the status"
```

### Infrastructure Issues

#### "Certificate validation failed"
**Problem**: SSL certificate not properly configured
**Solutions**:
```bash
# Check certificate status
aws acm list-certificates --query 'CertificateSummaryList[?DomainName==`sre-ops.your-domain.com`]'

# Check Route53 validation records
aws route53 list-resource-record-sets --hosted-zone-id YOUR-HOSTED-ZONE-ID --query 'ResourceRecordSets[?Type==`CNAME`]'

# Reapply terraform if needed
cd infrastructure
terraform apply -target=aws_acm_certificate.sre_ops_ssl
```

#### "Target group unhealthy"
**Problem**: ECS tasks not passing health checks
**Solutions**:
```bash
# Check target group health
aws elbv2 describe-target-health --target-group-arn arn:aws:elasticloadbalancing:us-west-2:YOUR-AWS-ACCOUNT-ID:targetgroup/sre-ops-https-tg-v2/457819692e233142

# Check ECS service status
aws ecs describe-services --cluster sre-ops-assistant-cluster --services sre-ops-assistant-mcp-server-https

# Restart ECS service if needed
aws ecs update-service --cluster sre-ops-assistant-cluster --service sre-ops-assistant-mcp-server-https --force-new-deployment
```

#### "Security group blocking traffic"
**Problem**: Port 443 not open
**Solutions**:
```bash
# Check security group rules
aws ec2 describe-security-groups --group-ids sg-xxxxxxxxxxxxxxxxx

# Add HTTPS rule if missing
aws ec2 authorize-security-group-ingress --group-id sg-xxxxxxxxxxxxxxxxx --protocol tcp --port 443 --cidr 0.0.0.0/0

# Or apply terraform
cd infrastructure
terraform apply -target=aws_security_group_rule.alb_https_ingress
```

### API Issues

#### "HTTP 503 Service Unavailable"
**Problem**: Backend services not running
**Solutions**:
```bash
# Check ECS service status
aws ecs list-services --cluster sre-ops-assistant-cluster

# Check task health
aws ecs describe-tasks --cluster sre-ops-assistant-cluster --tasks $(aws ecs list-tasks --cluster sre-ops-assistant-cluster --query 'taskArns[0]' --output text)

# Check CloudWatch logs
aws logs describe-log-groups --log-group-name-prefix "/ecs/sre-ops"
```

#### "HTTP 429 Too Many Requests"
**Problem**: Rate limiting triggered
**Solutions**:
```bash
# Check API Gateway usage
aws apigateway get-usage --usage-plan-id $(aws apigateway get-usage-plans --query 'items[0].id' --output text) --key-id your-api-key

# Wait for rate limit reset (1 minute)
# Or increase limits in terraform:
# throttle_settings {
#   rate_limit  = 200  # increase from 100
#   burst_limit = 400  # increase from 200
# }
```

### Slack Bot Issues

#### "Slack commands not responding"
**Problem**: Lambda function or API Gateway issues
**Solutions**:
```bash
# Check Lambda function logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/sre"

# Test API Gateway endpoint
curl -X POST https://your-api-gateway-url/dev/slack -d "text=test"

# Redeploy Lambda function
cd infrastructure
terraform apply -target=aws_lambda_function.slack_bot
```

#### "Invalid SSL certificate" in Slack
**Problem**: Slack can't verify SSL certificate
**Solutions**:
- Ensure certificate is valid and not self-signed
- Check certificate chain is complete
- Verify domain matches certificate

### Performance Issues

#### "Slow response times"
**Problem**: High latency or resource constraints
**Solutions**:
```bash
# Check CloudWatch metrics
aws cloudwatch get-metric-statistics --namespace AWS/ECS --metric-name CPUUtilization --dimensions Name=ServiceName,Value=sre-ops-assistant-mcp-server-https --start-time 2025-01-01T00:00:00Z --end-time 2025-01-01T01:00:00Z --period 300 --statistics Average

# Scale up ECS service if needed
aws ecs update-service --cluster sre-ops-assistant-cluster --service sre-ops-assistant-mcp-server-https --desired-count 3

# Check ALB metrics
aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB --metric-name TargetResponseTime --start-time 2025-01-01T00:00:00Z --end-time 2025-01-01T01:00:00Z --period 300 --statistics Average
```

### Security Issues

#### "WAF blocking legitimate requests"
**Problem**: WAF rules too restrictive
**Solutions**:
```bash
# Check WAF logs
aws wafv2 get-sampled-requests --web-acl-arn $(aws wafv2 list-web-acls --scope REGIONAL --query 'WebACLs[0].ARN' --output text) --rule-metric-name RateLimitRule --scope REGIONAL --time-window StartTime=2025-01-01T00:00:00Z,EndTime=2025-01-01T01:00:00Z --max-items 100

# Temporarily disable WAF rule
aws wafv2 update-web-acl --scope REGIONAL --id your-web-acl-id --default-action Allow={}

# Review and adjust WAF rules in terraform
```

## 🔍 Debugging Commands

### Check Overall System Health
```bash
# Test all endpoints
curl https://sre-ops.your-domain.com/health
terraform apply ask "status"

# Run functional tests
terraform apply
```

### Get System Information
```bash
# Infrastructure status
cd infrastructure
terraform show

# AWS resource status
aws elbv2 describe-load-balancers --names sre-ops-assistant-alb
aws ecs describe-clusters --clusters sre-ops-assistant-cluster
aws acm list-certificates
```

### Log Analysis
```bash
# ECS logs
aws logs describe-log-streams --log-group-name /ecs/sre-ops-assistant

# Lambda logs
aws logs describe-log-streams --log-group-name /aws/lambda/sre-slack-bot

# CloudTrail events
aws logs filter-log-events --log-group-name /aws/cloudtrail/sre-ops-audit-trail --start-time 1640995200000
```

## 📞 Getting Help

1. **Check CloudWatch Logs** - Most issues show up in logs first
2. **Review Terraform State** - `terraform show` reveals current configuration
3. **Test Components Individually** - Isolate the failing component
4. **Check AWS Service Health** - Verify AWS services are operational
5. **Review Recent Changes** - Check git history for recent modifications

## 🚨 Emergency Procedures

### Complete System Restart
```bash
# Restart ECS services
aws ecs update-service --cluster sre-ops-assistant-cluster --service sre-ops-assistant-mcp-server-https --force-new-deployment

# Redeploy Lambda functions
cd infrastructure
terraform apply -target=aws_lambda_function.slack_bot -target=aws_lambda_function.teams_bot
```

### Rollback Infrastructure
```bash
cd infrastructure
git checkout HEAD~1  # Go back one commit
terraform apply
```

### Disable Security Features (Emergency Only)
```bash
# Disable WAF temporarily
aws wafv2 disassociate-web-acl --resource-arn $(aws elbv2 describe-load-balancers --names sre-ops-assistant-alb --query 'LoadBalancers[0].LoadBalancerArn' --output text)

# Remove rate limiting
aws apigateway update-usage-plan --usage-plan-id your-usage-plan-id --patch-ops op=remove,path=/throttle
```

Remember to re-enable security features after resolving the emergency!