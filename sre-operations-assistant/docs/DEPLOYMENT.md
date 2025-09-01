# Deployment Guide

## Prerequisites

1. **AWS Account Setup**
   - AWS CLI configured with appropriate permissions
   - Terraform installed (>= 1.5.0)
   - Python 3.11+ installed

2. **Required AWS Services**
   - EC2 instances with Inspector v2 enabled
   - CloudWatch and CloudTrail configured
   - Systems Manager for patch management

## Environment Setup

1. **Clone and Install**
   ```bash
   cd ai_practice/sre-operations-assistant
   pip install -r requirements.txt
   ```

2. **Environment Variables**
   ```bash
   export AWS_REGION=us-west-2
   export BEDROCK_MODEL_ID=amazon.titan-text-premier-v1:0
   export SLACK_BOT_TOKEN=xoxb-your-token
   export TEAMS_WEBHOOK_URL=https://your-webhook-url
   export DYNAMODB_TABLE=sre-operations-history
   export S3_BUCKET=sre-operations-artifacts
   ```

## Infrastructure Deployment

1. **Prepare Lambda Packages**
   ```bash
   # Create Lambda deployment packages
   cd bots
   zip -r slack_bot.zip slack_lambda.py
   zip -r teams_bot.zip teams_lambda.py
   zip -r patch_executor.zip patch_executor.py
   
   # Move to infrastructure folder
   mv *.zip ../infrastructure/
   ```

2. **Deploy with Terraform**
   ```bash
   cd infrastructure
   terraform init
   terraform plan
   terraform apply
   ```

## Post-Deployment Steps

1. **Configure Secrets**
   ```bash
   # List secrets to get exact ARNs
   aws secretsmanager list-secrets --query "SecretList[?contains(Name, 'slack-token')].{Name:Name,ARN:ARN}"
   aws secretsmanager list-secrets --query "SecretList[?contains(Name, 'teams-webhook')].{Name:Name,ARN:ARN}"
   
   # Set secret values (use actual ARNs from above)
   aws secretsmanager put-secret-value --secret-id "arn:aws:secretsmanager:us-west-2:ACCOUNT:secret:sre-ops-assistant/sre-slack-token-SUFFIX" --secret-string "xoxb-your-token"
   aws secretsmanager put-secret-value --secret-id "arn:aws:secretsmanager:us-west-2:ACCOUNT:secret:sre-ops-assistant/sre-teams-webhook-SUFFIX" --secret-string "https://your-webhook-url"
   ```

2. **Build and Push Docker Image**
   ```bash
   # Get ECR repository URL
   aws ecr describe-repositories --repository-names sre-ops-assistant --query "repositories[0].repositoryUri" --output text
   
   # Login to ECR
   aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin $(aws ecr describe-repositories --repository-names sre-ops-assistant --query "repositories[0].repositoryUri" --output text | cut -d'/' -f1)
   
   # Build and push
   docker build -t sre-operations-assistant .
   docker tag sre-operations-assistant:latest $(aws ecr describe-repositories --repository-names sre-ops-assistant --query "repositories[0].repositoryUri" --output text):latest
   docker push $(aws ecr describe-repositories --repository-names sre-ops-assistant --query "repositories[0].repositoryUri" --output text):latest
   ```

3. **Update ECS Service**
   ```bash
   # Force ECS service to deploy the new image
   aws ecs update-service --cluster sre-ops-assistant-cluster --service sre-ops-assistant-mcp-server --force-new-deployment
   
   # Check deployment status
   aws ecs describe-services --cluster sre-ops-assistant-cluster --services sre-ops-assistant-mcp-server --query "services[0].deployments[0].{Status:status,RunningCount:runningCount,DesiredCount:desiredCount}"
   ```

4. **Deploy Lambda Functions**
   ```bash
   # Package Lambda functions
   cd bots
   zip -r slack_bot.zip slack_lambda.py
   zip -r teams_bot.zip teams_lambda.py
   zip -r patch_executor.zip patch_executor.py
   
   # Move to infrastructure folder for terraform
   mv *.zip ../infrastructure/
   cd ../infrastructure
   
   # Deploy via terraform (Lambda functions will use these zip files)
   terraform apply -target=aws_lambda_function.slack_bot -target=aws_lambda_function.teams_bot
   ```

2. **Test CLI Tool**
   ```bash
   python cli/sre_cli.py --help
   python cli/sre_cli.py vulnerabilities --instance-id i-1234567
   ```

3. **Configure Chat Bots**
   - Add Slack bot to workspace
   - Configure Teams webhook
   - Test with `/sre-vuln-check` command

## Verification

1. **Health Check**
   ```bash
   curl http://localhost:8000/health
   ```

2. **MCP Connection Test**
   ```bash
   python cli/sre_cli.py interactive
   > analyze vulnerabilities for all instances
   ```

3. **Bot Integration Test**
   - Send `/sre-vuln-check` in Slack
   - Verify Teams notifications

## Monitoring Setup

1. **CloudWatch Dashboards**
   - MCP server metrics
   - Function execution times
   - Error rates

2. **Alerts Configuration**
   - Critical vulnerability detection
   - System health monitoring
   - Cost threshold alerts

## Troubleshooting

- **MCP Server Issues**: Check logs in CloudWatch
- **Permission Errors**: Verify IAM roles and policies
- **Bot Integration**: Validate tokens and webhook URLs
- **Performance**: Monitor Lambda cold starts and memory usage

## Budget Monitoring

Expected monthly costs: $30-85
- Monitor via AWS Cost Explorer
- Set up billing alerts at $50 and $75