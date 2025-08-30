#!/bin/bash

# Build and deploy script
echo "Building Docker image..."
docker build -t sre-operations-assistant:latest .

echo "Tagging for ECR..."
docker tag sre-operations-assistant:latest -.dkr.ecr.us-west-2.amazonaws.com/sre-ops-assistant:latest

echo "Logging into ECR..."
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin -.dkr.ecr.us-west-2.amazonaws.com

echo "Pushing to ECR..."
docker push -.dkr.ecr.us-west-2.amazonaws.com/sre-ops-assistant:latest

echo "Updating ECS service..."
aws ecs update-service --cluster sre-ops-assistant-cluster --service sre-ops-assistant-mcp-server --force-new-deployment --region us-west-2

echo "Deployment complete!"
