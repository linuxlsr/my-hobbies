#!/bin/bash

# Build and deploy script
echo "Building Docker image..."
docker build -t sre-operations-assistant:latest .

# Check if AWS_ACCOUNT_ID is set
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo "Error: AWS_ACCOUNT_ID environment variable is not set"
    echo "Please set it with: export AWS_ACCOUNT_ID=your-account-id"
    exit 1
fi

echo "Tagging for ECR..."
docker tag sre-operations-assistant:latest $AWS_ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/sre-ops-assistant:latest

echo "Logging into ECR..."
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com

echo "Pushing to ECR..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/sre-ops-assistant:latest

echo "Updating ECS service..."
aws ecs update-service --cluster sre-ops-assistant-cluster --service sre-ops-assistant-mcp-server --force-new-deployment --region us-west-2

echo "Deployment complete!"
