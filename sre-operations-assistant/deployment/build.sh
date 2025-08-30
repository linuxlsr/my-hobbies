#!/bin/bash

# Build script for SRE Operations Assistant deployment packages

set -e

echo "Building deployment packages..."

# Create deployment directory
mkdir -p deployment

# Function to create Lambda deployment package
create_lambda_package() {
    local function_name=$1
    local source_dir=$2
    
    echo "Creating package for $function_name..."
    
    # Create temporary directory
    temp_dir=$(mktemp -d)
    
    # Copy source files
    cp -r $source_dir/* $temp_dir/
    cp -r src/ $temp_dir/
    cp -r config/ $temp_dir/
    
    # Install dependencies
    pip install -r requirements.txt -t $temp_dir/
    
    # Create zip file
    cd $temp_dir
    zip -r ../deployment/${function_name}.zip .
    cd - > /dev/null
    
    # Cleanup
    rm -rf $temp_dir
    
    echo "Package created: deployment/${function_name}.zip"
}

# Create Lambda packages
create_lambda_package "slack_bot" "bots"
create_lambda_package "teams_bot" "bots"
create_lambda_package "vulnerability_scanner" "src"

echo "All deployment packages created successfully!"

# Build Docker image for ECS
echo "Building Docker image..."
docker build -t sre-ops-assistant:latest .

echo "Build complete!"
echo ""
echo "Next steps:"
echo "1. Push Docker image to ECR"
echo "2. Deploy with Terraform: cd infrastructure && terraform apply"