#!/bin/bash
# Quick deployment script for ECS update

echo "🔄 Quick ECS deployment with CloudTrail fix..."

# Build and push updated container
docker build -t sre-operations-assistant:latest .
docker tag sre-operations-assistant:latest -.dkr.ecr.us-west-2.amazonaws.com/sre-operations-assistant:latest
docker push -.dkr.ecr.us-west-2.amazonaws.com/sre-operations-assistant:latest

# Force ECS service update
aws ecs update-service \
    --cluster sre-ops-assistant-cluster \
    --service sre-ops-assistant-mcp-server \
    --force-new-deployment \
    --region us-west-2

echo "✅ Deployment initiated. Check ECS console for status."
