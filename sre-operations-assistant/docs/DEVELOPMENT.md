# Development Guide

## 🛠️ Development Setup

### Prerequisites
- **Python 3.8+** with pip
- **AWS CLI** configured with appropriate permissions
- **Terraform** >= 1.0
- **Docker** (for local testing)
- **Git** for version control

### Local Development Environment

#### 1. Clone and Setup
```bash
git clone <repository-url>
cd sre-operations-assistant

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit with your values
export AWS_REGION=us-west-2
export AWS_PROFILE=your-profile
export SRE_API_ENDPOINT=http://localhost:8000
```

#### 3. Local Testing
```bash
# Run tests
terraform apply
terraform apply

# Start local development server (if available)
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## 🏗️ Project Structure

```
sre-operations-assistant/
├── cli/                           # Command-line interface
│   ├── sre_cli.py                # Main CLI application
│   └── requirements.txt          # CLI dependencies
├── bots/                         # Chat bot integrations
│   ├── slack_lambda.py           # Slack bot Lambda function
│   ├── teams_lambda.py           # Teams bot Lambda function
│   └── requirements.txt          # Bot dependencies
├── infrastructure/               # Terraform infrastructure
│   ├── main.tf                   # Main configuration
│   ├── variables.tf              # Input variables
│   ├── outputs.tf                # Output values
│   ├── networking.tf             # VPC and networking
│   ├── ecs.tf                    # ECS cluster and services
│   ├── alb.tf                    # Application Load Balancer
│   ├── api_gateway.tf            # API Gateway configuration
│   ├── lambda.tf                 # Lambda functions
│   ├── monitoring.tf             # CloudWatch and SNS
│   ├── security_hardening.tf     # WAF and security
│   ├── security_monitoring.tf    # Security alarms
│   ├── iam_hardening.tf          # IAM roles and policies
│   ├── ssl_certificate.tf        # ACM certificates
│   ├── secrets.tf                # Secrets Manager
│   └── route53_*.tf              # DNS configuration
├── tests/                        # Test suites
│   ├── run_tests.py              # Structural tests
│   ├── functional_tests.py       # Functional tests
│   └── test_cli_commands.py      # CLI command tests
├── docs/                         # Documentation
│   ├── ARCHITECTURE.md           # System architecture
│   ├── TROUBLESHOOTING.md        # Common issues
│   └── DEVELOPMENT.md            # This file
├── README.md                     # Main documentation
├── requirements.txt              # Python dependencies
└── .gitignore                    # Git ignore rules
```

## 🔧 Development Workflow

### 1. Feature Development
```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes
# ... edit files ...

# Test changes
terraform apply
terraform apply

# Commit changes
git add .
git commit -m "Add new feature: description"
git push origin feature/new-feature
```

### 2. Infrastructure Changes
```bash
# Navigate to infrastructure
cd infrastructure

# Plan changes
terraform plan

# Apply changes (development)
terraform apply

# Test infrastructure
curl https://sre-ops.your-domain.com/health
python3 ../tests/functional_tests.py
```

### 3. Testing Strategy
```bash
# Unit tests (structural)
terraform apply

# Integration tests (functional)
terraform apply

# CLI tests
terraform apply

# Manual testing
terraform apply chat
```

## 🧪 Testing Guidelines

### Test Categories

#### 1. Structural Tests (`tests/run_tests.py`)
- File existence checks
- Import validation
- Basic configuration verification

#### 2. Functional Tests (`tests/functional_tests.py`)
- CLI command execution
- API endpoint testing
- End-to-end workflows

#### 3. CLI Tests (`test_cli_commands.py`)
- Command syntax validation
- Natural language processing
- Configuration management

### Writing New Tests
```python
def test_new_feature():
    """Test description"""
    try:
        # Test implementation
        result = your_function()
        if result == expected:
            print("✅ Test passed")
            return True
        else:
            print("❌ Test failed")
            return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False
```

## 🔒 Security Development Practices

### 1. Secrets Management
```python
# ❌ Don't hardcode secrets
api_key = "sk-1234567890abcdef"

# ✅ Use environment variables or AWS Secrets Manager
import os
api_key = os.getenv('API_KEY')

# ✅ Or AWS Secrets Manager
import boto3
secrets = boto3.client('secretsmanager')
secret = secrets.get_secret_value(SecretId='api-key')
```

### 2. Input Validation
```python
# ✅ Always validate inputs
def process_query(query: str) -> str:
    if not query or len(query) > 1000:
        raise ValueError("Invalid query length")
    
    # Sanitize input
    clean_query = query.strip()
    return clean_query
```

### 3. Error Handling
```python
# ✅ Proper error handling
try:
    result = aws_service.call()
except ClientError as e:
    logger.error(f"AWS error: {e}")
    return {"error": "Service temporarily unavailable"}
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return {"error": "Internal error"}
```

## 📦 Dependency Management

### Python Dependencies
```bash
# Add new dependency
pip install new-package

# Update requirements
pip freeze > requirements.txt

# Install from requirements
pip install -r requirements.txt
```

### Terraform Dependencies
```hcl
# Use specific provider versions
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

## 🚀 Deployment Process

### Development Deployment
```bash
# Prepare Lambda packages
cd bots
zip -r slack_bot.zip slack_lambda.py
zip -r teams_bot.zip teams_lambda.py
zip -r patch_executor.zip patch_executor.py

# Deploy infrastructure
cd ../infrastructure
terraform workspace select dev  # or create if needed
terraform plan
terraform apply
```

### Production Deployment (Future)
```bash
# Prepare Lambda packages
cd bots
zip -r slack_bot.zip slack_lambda.py
zip -r teams_bot.zip teams_lambda.py
zip -r patch_executor.zip patch_executor.py

# Deploy infrastructure
cd ../infrastructure
terraform workspace select prod
terraform plan -var-file="prod.tfvars"
terraform apply -var-file="prod.tfvars"
```

## 🔍 Debugging

### Local Debugging
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
terraform apply --verbose ask "status"

# Check logs
tail -f /var/log/sre-ops.log
```

### AWS Debugging
```bash
# Check ECS logs
aws logs describe-log-streams --log-group-name /ecs/sre-ops-assistant

# Check Lambda logs
aws logs describe-log-streams --log-group-name /aws/lambda/sre-slack-bot

# Check CloudTrail
aws logs filter-log-events --log-group-name CloudTrail/SREOpsAuditTrail
```

### Common Debug Commands
```bash
# Test connectivity
curl -v https://sre-ops.your-domain.com/health

# Check DNS resolution
nslookup sre-ops.your-domain.com

# Test SSL certificate
openssl s_client -connect sre-ops.your-domain.com:443

# Check AWS resources
aws elbv2 describe-load-balancers --names sre-ops-assistant-alb
aws ecs describe-services --cluster sre-ops-assistant-cluster
```

## 📝 Code Style Guidelines

### Python Style
- Follow PEP 8
- Use type hints where possible
- Document functions with docstrings
- Use meaningful variable names

```python
def get_vulnerability_findings(instance_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve vulnerability findings for a specific EC2 instance.
    
    Args:
        instance_id: EC2 instance identifier
        
    Returns:
        List of vulnerability findings
        
    Raises:
        ClientError: If AWS API call fails
    """
    # Implementation here
    pass
```

### Terraform Style
- Use consistent naming conventions
- Add descriptions to variables
- Tag all resources
- Use modules for reusable components

```hcl
resource "aws_instance" "example" {
  ami           = var.ami_id
  instance_type = var.instance_type
  
  tags = {
    Name        = "sre-ops-instance"
    Environment = var.environment
    Project     = "sre-operations-assistant"
    ManagedBy   = "terraform"
  }
}
```

## 🤝 Contributing Guidelines

### Pull Request Process
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add/update tests
5. Update documentation
6. Submit pull request

### Code Review Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass
- [ ] Documentation updated
- [ ] Security considerations addressed
- [ ] Performance impact considered
- [ ] Backward compatibility maintained

### Commit Message Format
```
type(scope): description

- feat: new feature
- fix: bug fix
- docs: documentation changes
- style: formatting changes
- refactor: code refactoring
- test: adding tests
- chore: maintenance tasks
```

## 🔧 Development Tools

### Recommended IDE Extensions
- **Python**: Python extension for VS Code
- **Terraform**: HashiCorp Terraform extension
- **AWS**: AWS Toolkit for VS Code
- **YAML**: YAML support for configuration files

### Useful Commands
```bash
# Format Terraform code
terraform fmt -recursive

# Validate Terraform configuration
terraform validate

# Check Python code style
flake8 .

# Format Python code
black .

# Security scan
bandit -r .
```

## 📊 Performance Considerations

### Optimization Tips
- Use connection pooling for AWS services
- Implement caching for frequently accessed data
- Use async/await for I/O operations
- Monitor memory usage in Lambda functions

### Monitoring Development Performance
```bash
# Profile Python code
python3 -m cProfile -o profile.stats your_script.py

# Analyze profile
python3 -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(10)"
```

This development guide provides the foundation for contributing to and maintaining the SRE Operations Assistant project.