@echo off
echo Deploying SRE Operations Assistant MCP Server to ECS
echo ================================================

REM Get AWS Account ID
for /f %%i in ('aws sts get-caller-identity --query Account --output text') do set ACCOUNT_ID=%%i
if errorlevel 1 (
    echo Failed to get AWS Account ID
    exit /b 1
)

set PROJECT_NAME=sre-operations-assistant
set REGION=us-west-2
set ECR_REPO=%ACCOUNT_ID%.dkr.ecr.%REGION%.amazonaws.com/%PROJECT_NAME%

echo Building Docker image...
docker build -t %PROJECT_NAME%:latest .
if errorlevel 1 (
    echo Docker build failed
    exit /b 1
)

echo Tagging image for ECR...
docker tag %PROJECT_NAME%:latest %ECR_REPO%:latest

echo Logging into ECR...
aws ecr get-login-password --region %REGION% | docker login --username AWS --password-stdin %ECR_REPO%
if errorlevel 1 (
    echo ECR login failed
    exit /b 1
)

echo Pushing image to ECR...
docker push %ECR_REPO%:latest
if errorlevel 1 (
    echo Docker push failed
    exit /b 1
)

echo Updating ECS service...
aws ecs update-service --cluster %PROJECT_NAME%-cluster --service %PROJECT_NAME%-mcp-server --force-new-deployment --region %REGION%
if errorlevel 1 (
    echo ECS service update failed
    exit /b 1
)

echo Deployment initiated successfully!
echo Check ECS console for deployment status.