# Security Guidelines

## Environment Variables

This application uses environment variables for sensitive configuration. Never commit these values to version control.

### Required Environment Variables

```bash
# Domain configuration
export POWERBALL_SITE_NAME="your-domain.com"

# AWS configuration  
export AWS_REGION="us-west-2"
export AWS_ACCOUNT_ID="<your-aws-account-id>"
```

### Setup Instructions

1. Copy the environment template:
   ```bash
   cp env.template .env
   ```

2. Edit `.env` with your actual values
3. Source the environment:
   ```bash
   source .env
   ```

## AWS Security

- Use IAM roles with minimal required permissions
- Enable CloudTrail logging
- Use VPC with private subnets for sensitive resources
- Enable WAF protection for public endpoints
- Regularly rotate access keys

## Application Security

- All external traffic uses HTTPS
- Rate limiting enabled via WAF
- Input validation on all API endpoints
- Non-root container user
- Security headers enabled

## Deployment Security

- Never commit AWS credentials
- Use environment-specific configurations
- Review all Terraform changes before applying
- Enable resource tagging for cost tracking
- Use least-privilege IAM policies