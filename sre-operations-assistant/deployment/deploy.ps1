# PowerShell deployment script for Windows

param(
    [string]$Region = "us-west-2",
    [string]$Environment = "dev",
    [switch]$SkipBuild
)

Write-Host "SRE Operations Assistant Deployment Script" -ForegroundColor Green
Write-Host "Region: $Region" -ForegroundColor Yellow
Write-Host "Environment: $Environment" -ForegroundColor Yellow

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Blue

# Check AWS CLI
try {
    aws --version | Out-Null
    Write-Host "✓ AWS CLI found" -ForegroundColor Green
} catch {
    Write-Host "✗ AWS CLI not found. Please install AWS CLI." -ForegroundColor Red
    exit 1
}

# Check Terraform
try {
    terraform version | Out-Null
    Write-Host "✓ Terraform found" -ForegroundColor Green
} catch {
    Write-Host "✗ Terraform not found. Please install Terraform." -ForegroundColor Red
    exit 1
}

# Check Docker
try {
    docker --version | Out-Null
    Write-Host "✓ Docker found" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker not found. Please install Docker." -ForegroundColor Red
    exit 1
}

# Build deployment packages
if (-not $SkipBuild) {
    Write-Host "Building deployment packages..." -ForegroundColor Blue
    
    # Create Lambda packages
    $functions = @("slack_bot", "teams_bot", "vulnerability_scanner")
    
    foreach ($func in $functions) {
        Write-Host "Creating package for $func..." -ForegroundColor Yellow
        
        # Create temp directory
        $tempDir = New-TemporaryFile | ForEach-Object { Remove-Item $_; New-Item -ItemType Directory -Path $_ }
        
        # Copy files
        Copy-Item -Recurse -Path "src\*" -Destination $tempDir
        Copy-Item -Recurse -Path "config\*" -Destination $tempDir
        Copy-Item -Recurse -Path "bots\*" -Destination $tempDir -ErrorAction SilentlyContinue
        
        # Install dependencies
        pip install -r requirements.txt -t $tempDir
        
        # Create zip
        $zipPath = "deployment\$func.zip"
        Compress-Archive -Path "$tempDir\*" -DestinationPath $zipPath -Force
        
        # Cleanup
        Remove-Item -Recurse -Force $tempDir
        
        Write-Host "✓ Package created: $zipPath" -ForegroundColor Green
    }
    
    # Build Docker image
    Write-Host "Building Docker image..." -ForegroundColor Blue
    docker build -t sre-ops-assistant:latest .
    Write-Host "✓ Docker image built" -ForegroundColor Green
}

# Deploy with Terraform
Write-Host "Deploying infrastructure with Terraform..." -ForegroundColor Blue

Set-Location infrastructure

# Initialize Terraform
terraform init

# Plan deployment
Write-Host "Creating Terraform plan..." -ForegroundColor Yellow
terraform plan -var="aws_region=$Region" -var="environment=$Environment"

# Confirm deployment
$confirm = Read-Host "Do you want to proceed with deployment? (y/N)"
if ($confirm -eq "y" -or $confirm -eq "Y") {
    # Apply Terraform
    terraform apply -var="aws_region=$Region" -var="environment=$Environment" -auto-approve
    
    Write-Host "Deployment completed!" -ForegroundColor Green
    Write-Host "Check Terraform outputs for important URLs and resource names." -ForegroundColor Yellow
} else {
    Write-Host "Deployment cancelled." -ForegroundColor Yellow
}

Set-Location ..

Write-Host "Script completed!" -ForegroundColor Green