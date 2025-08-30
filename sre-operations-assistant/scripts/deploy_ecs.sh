#!/bin/bash
set -e

# Configuration
PROJECT_NAME="sre-operations-assistant"
AWS_REGION="us-west-2"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PROJECT_NAME}"

echo "🚀 Deploying SRE Operations Assistant to ECS"
echo "================================================"

# Step 1: Build Docker image
echo "📦 Building Docker image..."
docker build -t ${PROJECT_NAME}:latest .

# Step 2: Tag for ECR
echo "🏷️  Tagging image for ECR..."
docker tag ${PROJECT_NAME}:latest ${ECR_REPO}:latest

# Step 3: Login to ECR
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REPO}

# Step 4: Push to ECR
echo "⬆️  Pushing image to ECR..."
docker push ${ECR_REPO}:latest

# Step 5: Update ECS service
echo "🔄 Updating ECS service..."
aws ecs update-service \
    --cluster ${PROJECT_NAME}-cluster \
    --service ${PROJECT_NAME}-mcp-server \
    --force-new-deployment \
    --region ${AWS_REGION}

# Step 6: Wait for deployment
echo "⏳ Waiting for deployment to complete..."
aws ecs wait services-stable \
    --cluster ${PROJECT_NAME}-cluster \
    --services ${PROJECT_NAME}-mcp-server \
    --region ${AWS_REGION}

# Step 7: Get service status
echo "📊 Getting service status..."
SERVICE_STATUS=$(aws ecs describe-services \
    --cluster ${PROJECT_NAME}-cluster \
    --services ${PROJECT_NAME}-mcp-server \
    --region ${AWS_REGION} \
    --query 'services[0].deployments[0].status' \
    --output text)

if [ "$SERVICE_STATUS" = "PRIMARY" ]; then
    echo "✅ Deployment successful!"
    
    # Get ALB endpoint
    ALB_DNS=$(aws elbv2 describe-load-balancers \
        --names ${PROJECT_NAME}-alb \
        --region ${AWS_REGION} \
        --query 'LoadBalancers[0].DNSName' \
        --output text 2>/dev/null || echo "ALB not found")
    
    if [ "$ALB_DNS" != "ALB not found" ]; then
        echo "🌐 Service available at: http://${ALB_DNS}"
        echo "🏥 Health check: http://${ALB_DNS}/health"
    fi
else
    echo "❌ Deployment failed with status: $SERVICE_STATUS"
    exit 1
fi

echo "🎉 ECS deployment complete!"