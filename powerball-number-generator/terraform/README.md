# PowerballAI Terraform Deployment

Secure, cost-optimized AWS deployment for PowerballAI Predictor.

## Architecture

- **Domain**: your-domain.com (HTTPS only)
- **Compute**: ECS Fargate (0.25 vCPU, 512MB RAM)
- **Database**: SQLite in container (lowest cost)
- **Security**: WAF, Security Groups, SSL/TLS
- **Monitoring**: CloudWatch Logs (7-day retention)

## Cost Optimization

- **ECS Fargate**: ~$10/month (minimal resources)
- **ALB**: ~$16/month (required for HTTPS)
- **Route53**: ~$0.50/month
- **WAF**: ~$1/month (basic rules)
- **CloudWatch**: ~$1/month (minimal logs)
- **Total**: ~$28/month

## Security Features

1. **WAF Protection**:
   - Rate limiting (2000 requests/5min per IP)
   - AWS Managed Common Rule Set
   - DDoS protection

2. **Network Security**:
   - VPC with public subnets only (stateless app)
   - Security groups with minimal access
   - HTTPS-only with SSL redirect

3. **Application Security**:
   - Container scanning enabled
   - Minimal IAM permissions
   - No sensitive data storage

## Prerequisites

1. **AWS CLI configured**:
   ```bash
   aws configure
   ```

2. **Terraform installed** (>= 1.0)

3. **Docker installed**

4. **Route53 hosted zone** for `your-domain.com`

## Deployment

### Quick Deploy
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars if needed
chmod +x deploy.sh
./deploy.sh
```

### Manual Deploy
```bash
# 1. Initialize Terraform
terraform init

# 2. Plan deployment
terraform plan

# 3. Apply infrastructure
terraform apply

# 4. Build and push Docker image
ECR_URL=$(terraform output -raw ecr_repository_url)
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin $ECR_URL

cd ..
docker build -t powerball-ai .
docker tag powerball-ai:latest $ECR_URL:latest
docker push $ECR_URL:latest

# 5. Update ECS service
cd terraform
aws ecs update-service \
  --cluster $(terraform output -raw ecs_cluster_name) \
  --service $(terraform output -raw ecs_service_name) \
  --force-new-deployment
```

## Monitoring

### Health Check
```bash
curl https://your-domain.com/api/status
```

### View Logs
```bash
aws logs tail /ecs/powerball-ai --follow
```

### ECS Service Status
```bash
aws ecs describe-services \
  --cluster powerball-ai-cluster \
  --services powerball-ai-service
```

## Updates

### Application Updates
```bash
cd terraform
./deploy.sh  # Rebuilds and redeploys
```

### Infrastructure Updates
```bash
terraform plan
terraform apply
```

## Security Considerations

### Rate Limiting
- 2000 requests per 5 minutes per IP
- Automatic blocking of abusive IPs
- CloudWatch metrics for monitoring

### SSL/TLS
- TLS 1.2 minimum
- Automatic HTTP to HTTPS redirect
- Certificate auto-renewal via ACM

### Container Security
- Image scanning on push
- Minimal base image
- No root privileges
- Read-only filesystem (except /tmp)

## Troubleshooting

### Common Issues

1. **Certificate validation fails**:
   - Ensure Route53 hosted zone exists
   - Check DNS propagation

2. **ECS service won't start**:
   - Check CloudWatch logs
   - Verify security group rules
   - Ensure ECR image exists

3. **High costs**:
   - Monitor CloudWatch usage
   - Adjust log retention
   - Consider spot instances for dev

### Debug Commands
```bash
# Check ECS service events
aws ecs describe-services --cluster powerball-ai-cluster --services powerball-ai-service

# View container logs
aws logs tail /ecs/powerball-ai --follow

# Check ALB target health
aws elbv2 describe-target-health --target-group-arn $(terraform output -raw target_group_arn)

# WAF metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/WAFV2 \
  --metric-name AllowedRequests \
  --dimensions Name=WebACL,Value=powerball-ai-waf \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

## Cleanup

```bash
terraform destroy
```

**Note**: This will delete all resources and data. The SQLite database is ephemeral and will be lost.