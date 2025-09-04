#!/bin/bash
set -e

echo "🚀 Deploying PowerballAI with FastAPI to AWS ECS"

# Load environment variables
if [ -f "../env.local" ]; then
    source ../env.local
    echo "✅ Loaded configuration from env.local"
else
    echo "❌ Please create env.local from env.template with your AWS account ID and domain"
    exit 1
fi

AWS_REGION="${AWS_REGION:-us-west-2}"
ECR_REPO="${ECR_REPOSITORY:-powerball}"
IMAGE_TAG="fastapi-$(date +%Y%m%d-%H%M%S)"

# Change to project root
cd "$(dirname "$0")/.."

echo "1. Building Docker image with FastAPI..."
docker build -t $ECR_REPO:$IMAGE_TAG .
docker tag $ECR_REPO:$IMAGE_TAG $ECR_REPO:latest

echo "2. Getting ECR login..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

echo "3. Applying Terraform infrastructure..."
cd terraform
terraform init
terraform apply -auto-approve

echo "4. Getting ECR repository URL..."
ECR_URI=$(terraform output -raw ecr_repository_url)
echo "ECR URI: $ECR_URI"

echo "5. Pushing Docker image to ECR..."
docker tag $ECR_REPO:$IMAGE_TAG $ECR_URI:$IMAGE_TAG
docker tag $ECR_REPO:latest $ECR_URI:latest

docker push $ECR_URI:$IMAGE_TAG
docker push $ECR_URI:latest

echo "6. Forcing ECS service deployment..."
aws ecs update-service \
    --cluster powerball-cluster \
    --service powerball-service \
    --force-new-deployment \
    --region $AWS_REGION

echo "7. Monitoring deployment..."
for i in {1..12}; do
    echo "Check $i/12..."
    
    SERVICE_STATUS=$(aws ecs describe-services \
        --cluster powerball-cluster \
        --services powerball-service \
        --region $AWS_REGION \
        --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount,Pending:pendingCount}' \
        --output table)
    
    echo "$SERVICE_STATUS"
    
    RUNNING=$(aws ecs describe-services \
        --cluster powerball-cluster \
        --services powerball-service \
        --region $AWS_REGION \
        --query 'services[0].runningCount' \
        --output text)
    
    if [ "$RUNNING" -gt 0 ]; then
        echo "✅ Service is running!"
        
        # Test the endpoint
        echo "8. Testing deployed application..."
        sleep 15
        
        ENDPOINT="https://${SUBDOMAIN}.${DOMAIN_NAME}"
        
        echo "Testing $ENDPOINT/ping..."
        if curl -f -s "$ENDPOINT/ping" | grep -q "pong"; then
            echo "✅ FastAPI deployment successful!"
            echo "🌐 Application available at: $ENDPOINT"
            exit 0
        else
            echo "⚠️ Service running but endpoint not responding correctly"
            echo "Check target group health in AWS console"
        fi
        break
    fi
    
    sleep 30
done

echo "⚠️ Deployment may still be in progress. Check ECS console for details."
