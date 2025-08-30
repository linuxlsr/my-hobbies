# SRE Operations Assistant - Terraform Infrastructure

This directory contains Terraform configuration to deploy the SRE Operations Assistant to AWS.

## Prerequisites

1. **AWS CLI configured** with appropriate permissions
2. **Terraform >= 1.5.0** installed
3. **AWS Account** with Bedrock access enabled

## Required AWS Permissions

The deploying user/role needs permissions for:
- IAM (roles, policies)
- Lambda (functions, permissions)
- ECS (clusters, services, tasks)
- ECR (repositories)
- API Gateway (APIs, deployments)
- DynamoDB (tables)
- S3 (buckets)
- Secrets Manager (secrets)
- CloudWatch (logs, alarms, dashboards)
- EventBridge (rules)
- VPC (networking resources)
- Budgets (cost monitoring)

## Quick Start

1. **Copy variables file:**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. **Edit terraform.tfvars:**
   ```bash
   # Required
   aws_region = "us-west-2"
   environment = "dev"
   
   # Optional (can be set later)
   slack_bot_token = "xoxb-your-token"
   teams_webhook_url = "https://your-webhook"
   ```

3. **Initialize and deploy:**
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

## Architecture Overview

### Core Components
- **ECS Cluster:** Runs MCP server container
- **Lambda Functions:** Slack bot, Teams bot, vulnerability scanner
- **API Gateway:** Webhook endpoints for chat integrations
- **DynamoDB:** Operations history storage
- **S3:** Artifacts and logs storage

### Security
- **IAM Roles:** Least privilege access for all components
- **Secrets Manager:** Secure storage for API tokens
- **VPC:** Isolated networking for ECS tasks
- **Security Groups:** Network access controls

### Monitoring
- **CloudWatch Dashboard:** Centralized metrics view
- **CloudWatch Alarms:** Error rate and resource monitoring
- **Cost Budget:** Monthly spend tracking ($100 limit)
- **SNS Alerts:** Notification system

## Post-Deployment Steps

1. **Configure Secrets (if not done during deployment):**
   ```bash
   aws secretsmanager put-secret-value \
     --secret-id sre-ops-assistant/slack-token \
     --secret-string "xoxb-your-slack-token"
   
   aws secretsmanager put-secret-value \
     --secret-id sre-ops-assistant/teams-webhook \
     --secret-string "https://your-teams-webhook-url"
   ```

2. **Build and push container image:**
   ```bash
   # Get ECR login
   aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-west-2.amazonaws.com
   
   # Build and push (from project root)
   docker build -t sre-ops-assistant .
   docker tag sre-ops-assistant:latest <account-id>.dkr.ecr.us-west-2.amazonaws.com/sre-ops-assistant:latest
   docker push <account-id>.dkr.ecr.us-west-2.amazonaws.com/sre-ops-assistant:latest
   ```

3. **Configure Slack App:**
   - Use the Slack webhook URL from Terraform outputs
   - Set up slash commands pointing to the API Gateway endpoint

4. **Configure Teams Integration:**
   - Use the Teams webhook URL from Terraform outputs
   - Set up incoming webhook in Teams

## Outputs

After deployment, Terraform provides:
- API Gateway URLs for webhooks
- ECR repository URL for container images
- Resource names and ARNs
- CloudWatch dashboard URL

## Cost Estimation

Expected monthly costs:
- **Lambda:** $5-15 (based on usage)
- **ECS Fargate:** $10-20 (1 task, 0.25 vCPU, 0.5GB RAM)
- **Bedrock:** $10-30 (Titan Text Premier usage)
- **Other services:** $5-15 (DynamoDB, S3, CloudWatch, etc.)

**Total:** $30-80/month

## Cleanup

To destroy all resources:
```bash
terraform destroy
```

**Note:** This will delete all data in DynamoDB and S3. Export any important data first.

## Troubleshooting

### Common Issues

1. **Bedrock Access:** Ensure Bedrock is enabled in your AWS account and region
2. **ECR Push:** Make sure Docker is installed and you're authenticated to ECR
3. **Lambda Deployment:** Ensure deployment packages exist in `../deployment/` directory
4. **VPC Limits:** Check AWS account limits for VPCs and subnets

### Logs

- **Lambda logs:** CloudWatch `/aws/lambda/<function-name>`
- **ECS logs:** CloudWatch `/ecs/sre-ops-assistant`
- **API Gateway logs:** Enable in API Gateway console if needed