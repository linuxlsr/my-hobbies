# SRE Operations Assistant

An AI-powered Site Reliability Engineering assistant that provides comprehensive AWS infrastructure monitoring, vulnerability scanning, and operational insights through multiple interfaces.

## 🚀 Features

- **🔍 Vulnerability Scanning** - AWS Inspector integration for security assessments
- **📊 Infrastructure Monitoring** - CloudWatch metrics and EC2 instance monitoring  
- **🤖 AI-Powered Chat Interface** - Natural language queries for operational tasks
- **💬 Slack/Teams Integration** - Bot interfaces for team collaboration
- **🔒 Enterprise Security** - WAF protection, rate limiting, and audit logging
- **📱 Multiple Access Methods** - CLI, Web API, and chat bots

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Slack/Teams   │    │   CLI Client     │    │   Web Browser   │
│      Bots       │    │                  │    │                 │
└─────────┬───────┘    └─────────┬────────┘    └─────────┬───────┘
          │                      │                       │
          └──────────────────────┼───────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │     API Gateway         │
                    │   (Rate Limited)        │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Application Load      │
                    │   Balancer + WAF        │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   ECS Fargate Tasks     │
                    │   (HTTPS Endpoints)     │
                    └────────────┬────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
┌─────────▼───────┐    ┌─────────▼───────┐    ┌─────────▼───────┐
│ AWS Inspector   │    │ AWS CloudWatch  │    │ AWS Systems     │
│                 │    │                 │    │ Manager         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Quick Start

### Prerequisites
- AWS CLI configured with appropriate permissions
- Terraform >= 1.0
- Python 3.8+
- Docker (for local development)

### 1. Deploy Infrastructure
```bash
# Prepare Lambda deployment packages
cd bots
zip -r slack_bot.zip slack_lambda.py
zip -r teams_bot.zip teams_lambda.py
zip -r patch_executor.zip patch_executor.py

# Deploy infrastructure
cd ../infrastructure
terraform init
terraform plan
terraform apply
```

### 2. Use the CLI
```bash
cd cli
python3 sre_cli.py chat
```

### 3. Test the API
```bash
curl https://sre-ops.your-domain.com/health
```

## 📖 Usage Guide

### CLI Commands
```bash
# Interactive chat mode
python3 sre_cli.py chat

# Direct queries
python3 sre_cli.py ask "scan all vulnerabilities"
python3 sre_cli.py ask "show CPU metrics for your-instance-name"
python3 sre_cli.py ask "list all instances"

# Configuration
python3 sre_cli.py config
python3 sre_cli.py config --remote-url https://your-endpoint.com
```

### Slack Integration
Use these slash commands in Slack:
- `/sre scan all` - Run vulnerability scan
- `/sre status` - Get infrastructure status
- `/sre metrics your-instance-name` - Get instance metrics

### API Endpoints
- `GET /health` - Health check
- `POST /chat` - Natural language queries
- `GET /instances` - List EC2 instances
- `GET /vulnerabilities` - Get vulnerability findings

## 🔧 Configuration

### Environment Variables
```bash
AWS_REGION=us-west-2
AWS_PROFILE=your-profile
SRE_API_ENDPOINT=https://sre-ops.your-domain.com
```

### CLI Configuration
The CLI stores configuration in `~/.sre-cli/config.json`:
```json
{
  "mode": "remote",
  "local_endpoint": "http://localhost:8000",
  "remote_endpoint": "https://sre-ops.your-domain.com"
}
```

## 🔒 Security Features

- **WAF Protection** - Blocks common attacks and malicious traffic
- **Rate Limiting** - 100 requests/second, 10,000/day quota
- **TLS Encryption** - All traffic encrypted with valid SSL certificates
- **API Authentication** - API keys and resource-based policies
- **Audit Logging** - CloudTrail integration for compliance
- **Least Privilege IAM** - Minimal permissions for all components

## 📊 Monitoring & Alerts

### CloudWatch Alarms
- High error rate detection
- WAF blocked requests monitoring
- Infrastructure health checks

### SNS Notifications
Subscribe to `sre-ops-security-alerts` topic for security events.

## 🧪 Testing

```bash
# Run structural tests
terraform apply

# Run functional tests
terraform apply

# Test CLI commands
terraform apply
```

## 📁 Project Structure

```
sre-operations-assistant/
├── cli/                    # Command-line interface
├── bots/                   # Slack and Teams bot Lambda functions
├── infrastructure/         # Terraform infrastructure code
├── tests/                  # Test suites
├── docs/                   # Additional documentation
└── README.md              # This file
```

## 🚨 Troubleshooting

See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for common issues and solutions.

## 🏗️ Architecture Details

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed system design.

## 🔧 Development

See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for development setup and contribution guidelines.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For issues and questions:
- Create an issue in this repository
- Check the troubleshooting guide
- Review CloudWatch logs for errors

---

**Built with ❤️ for Site Reliability Engineering**