#!/bin/bash
set -e

echo "🚀 PowerballAI Deployment Script"
echo "================================"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Run 'aws configure' first."
    exit 1
fi

# Get AWS account ID and region
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_REGION:-us-west-2}
ECR_REPO="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/powerball-ai"

echo "📊 AWS Account: $AWS_ACCOUNT_ID"
echo "🌍 Region: $AWS_REGION"
echo ""

# Step 1: Initialize Terraform
echo "1️⃣ Initializing Terraform..."
terraform init

# Step 2: Plan deployment
echo "2️⃣ Planning Terraform deployment..."
terraform plan -out=tfplan

# Step 3: Apply infrastructure
echo "3️⃣ Applying Terraform configuration..."
terraform apply tfplan

# Get ECR repository URL
ECR_URL=$(terraform output -raw ecr_repository_url)
echo "📦 ECR Repository: $ECR_URL"

# Step 4: Build and push Docker image
echo "4️⃣ Building and pushing Docker image..."
cd ..

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URL

# Build image
docker build -t powerball-ai .

# Tag and push
docker tag powerball-ai:latest $ECR_URL:latest
docker push $ECR_URL:latest

# Step 5: Update ECS service
echo "5️⃣ Updating ECS service..."
cd terraform

CLUSTER_NAME=$(terraform output -raw ecs_cluster_name)
SERVICE_NAME=$(terraform output -raw ecs_service_name)

aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service $SERVICE_NAME \
    --force-new-deployment \
    --region $AWS_REGION

echo ""
echo "✅ Deployment complete!"
echo "🌐 Application URL: $(terraform output -raw application_url)"
echo "📊 Monitor logs: aws logs tail $(terraform output -raw cloudwatch_log_group) --follow"
echo ""
echo "⏳ Wait 2-3 minutes for the service to become healthy"