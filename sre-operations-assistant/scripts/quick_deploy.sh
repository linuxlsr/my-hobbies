#!/bin/bash
# Quick deployment script for ECS update

echo "🔄 Quick ECS deployment with CloudTrail fix..."

# Check if AWS_ACCOUNT_ID is set
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo "Error: AWS_ACCOUNT_ID environment variable is not set"
    echo "Please set it with: export AWS_ACCOUNT_ID=your-account-id"
    exit 1
fi

# Build and push updated container
docker build -t sre-operations-assistant:latest .
docker tag sre-operations-assistant:latest $AWS_ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/sre-operations-assistant:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/sre-operations-assistant:latest

# Force ECS service update
aws ecs update-service \
    --cluster sre-ops-assistant-cluster \
    --service sre-ops-assistant-mcp-server \
    --force-new-deployment \
    --region us-west-2

echo "✅ Deployment initiated. Check ECS console for status."
