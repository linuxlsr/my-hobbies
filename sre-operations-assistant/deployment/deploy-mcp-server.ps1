# PowerShell deployment script for MCP server to ECS
param(
    [string]$Region = "us-west-2",
    [string]$ProjectName = "sre-operations-assistant"
)

Write-Host "🚀 Deploying SRE Operations Assistant MCP Server to ECS" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Yellow

# Get AWS Account ID
$AccountId = (aws sts get-caller-identity --query Account --output text)
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to get AWS Account ID. Please check AWS credentials." -ForegroundColor Red
    exit 1
}

$EcrRepo = "$AccountId.dkr.ecr.$Region.amazonaws.com/$ProjectName"

# Step 1: Build Docker image
Write-Host "📦 Building Docker image..." -ForegroundColor Cyan
docker build -t "${ProjectName}:latest" .
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed" -ForegroundColor Red
    exit 1
}

# Step 2: Tag for ECR
Write-Host "🏷️  Tagging image for ECR..." -ForegroundColor Cyan
docker tag "${ProjectName}:latest" "${EcrRepo}:latest"

# Step 3: Login to ECR
Write-Host "🔐 Logging into ECR..." -ForegroundColor Cyan
$LoginCommand = aws ecr get-login-password --region $Region
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ ECR login failed" -ForegroundColor Red
    exit 1
}
$LoginCommand | docker login --username AWS --password-stdin $EcrRepo

# Step 4: Push to ECR
Write-Host "⬆️  Pushing image to ECR..." -ForegroundColor Cyan
docker push "${EcrRepo}:latest"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker push failed" -ForegroundColor Red
    exit 1
}

# Step 5: Update ECS service
Write-Host "🔄 Updating ECS service..." -ForegroundColor Cyan
aws ecs update-service `
    --cluster "${ProjectName}-cluster" `
    --service "${ProjectName}-mcp-server" `
    --force-new-deployment `
    --region $Region

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ ECS service update failed" -ForegroundColor Red
    exit 1
}

# Step 6: Wait for deployment
Write-Host "⏳ Waiting for deployment to complete..." -ForegroundColor Cyan
aws ecs wait services-stable `
    --cluster "${ProjectName}-cluster" `
    --services "${ProjectName}-mcp-server" `
    --region $Region

# Step 7: Get service status
Write-Host "📊 Getting service status..." -ForegroundColor Cyan
$ServiceStatus = aws ecs describe-services `
    --cluster "${ProjectName}-cluster" `
    --services "${ProjectName}-mcp-server" `
    --region $Region `
    --query 'services[0].deployments[0].status' `
    --output text

if ($ServiceStatus -eq "PRIMARY") {
    Write-Host "✅ Deployment successful!" -ForegroundColor Green
    
    # Get ALB endpoint
    $AlbDns = aws elbv2 describe-load-balancers `
        --names "${ProjectName}-alb" `
        --region $Region `
        --query 'LoadBalancers[0].DNSName' `
        --output text 2>$null
    
    if ($AlbDns -and $AlbDns -ne "None") {
        Write-Host "🌐 Service available at: http://$AlbDns" -ForegroundColor Green
        Write-Host "🏥 Health check: http://$AlbDns/health" -ForegroundColor Green
        Write-Host "🔧 MCP endpoint: http://$AlbDns/mcp" -ForegroundColor Green
    }
} else {
    Write-Host "❌ Deployment failed with status: $ServiceStatus" -ForegroundColor Red
    exit 1
}

Write-Host "🎉 ECS deployment complete!" -ForegroundColor Green