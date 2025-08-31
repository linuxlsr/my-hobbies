#!/bin/bash

# Deploy Secure SRE Operations Assistant Infrastructure

set -e

echo "🔒 Deploying Secure SRE Operations Assistant"
echo "============================================"

# Check if domain exists in Route53
echo "🌐 Checking Route53 domain..."
aws route53 list-hosted-zones --query "HostedZones[?Name=='threemoonsnetwork.net.']" --output table

if [ $? -ne 0 ]; then
    echo "❌ Route53 domain threemoonsnetwork.net not found"
    echo "Please ensure the domain is registered and hosted in Route53"
    exit 1
fi

# Navigate to infrastructure directory
cd ../infrastructure

# Initialize Terraform
echo "🔧 Initializing Terraform..."
terraform init

# Plan the secure deployment
echo "📋 Planning secure infrastructure..."
terraform plan -out=secure.tfplan

# Ask for confirmation
echo ""
echo "🚨 SECURITY DEPLOYMENT PLAN"
echo "This will deploy:"
echo "  ✅ SSL Certificate for sre-ops.threemoonsnetwork.net"
echo "  ✅ WAF with rate limiting and geo-blocking"
echo "  ✅ HTTPS-only ALB with HTTP redirect"
echo "  ✅ API key authentication"
echo "  ✅ Security monitoring and alerts"
echo ""
read -p "Continue with deployment? (y/N): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

# Apply the secure configuration
echo "🚀 Deploying secure infrastructure..."
terraform apply secure.tfplan

# Get the API key
echo "🔑 Retrieving API key..."
API_KEY=$(aws secretsmanager get-secret-value --secret-id sre-ops-api-key --query SecretString --output text | jq -r .api_key)

# Build and deploy the updated Docker image with security middleware
echo "🐳 Building secure Docker image..."
cd ../

# Update Dockerfile to include security middleware
cat > Dockerfile.secure << EOF
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Set environment variables
ENV PYTHONPATH=/app
ENV REQUIRE_API_KEY=true

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "uvicorn", "src.mcp_server:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Build and push the secure image
echo "📦 Building and pushing secure Docker image..."
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin $(aws ecr describe-repositories --repository-names sre-mcp-server --query 'repositories[0].repositoryUri' --output text | cut -d'/' -f1)

REPO_URI=$(aws ecr describe-repositories --repository-names sre-mcp-server --query 'repositories[0].repositoryUri' --output text)

docker build -f Dockerfile.secure -t $REPO_URI:secure .
docker push $REPO_URI:secure

# Update ECS service to use the secure image
echo "🔄 Updating ECS service..."
aws ecs update-service --cluster sre-ops-cluster --service sre-mcp-server-secure --force-new-deployment

# Wait for deployment to complete
echo "⏳ Waiting for deployment to complete..."
aws ecs wait services-stable --cluster sre-ops-cluster --services sre-mcp-server-secure

# Test the secure endpoint
echo "🧪 Testing secure endpoint..."
sleep 30

echo "Testing HTTPS endpoint..."
curl -k -H "X-API-Key: $API_KEY" https://sre-ops.threemoonsnetwork.net/health

echo ""
echo "Testing HTTP redirect..."
curl -I http://sre-ops.threemoonsnetwork.net/health

echo ""
echo "✅ Secure deployment completed!"
echo ""
echo "🔗 Secure API URL: https://sre-ops.threemoonsnetwork.net"
echo "🔑 API Key: $API_KEY"
echo "📊 WAF Dashboard: https://console.aws.amazon.com/wafv2/homev2/web-acls"
echo "📈 CloudWatch Metrics: https://console.aws.amazon.com/cloudwatch/"
echo ""
echo "⚠️  IMPORTANT: Save the API key securely!"
echo "⚠️  Update your CLI and Slack bot configurations with the new URL and API key"