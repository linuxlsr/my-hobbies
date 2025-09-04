# PowerballAI Setup Instructions

## Prerequisites
- AWS CLI configured with appropriate permissions
- Docker installed
- Terraform installed
- A registered domain name with Route53 hosted zone

## Setup Steps

1. **Configure Environment**
   ```bash
   cp env.template env.local
   # Edit env.local with your values:
   # - AWS_ACCOUNT_ID: Your 12-digit AWS account ID
   # - DOMAIN_NAME: Your registered domain (e.g., example.com)
   # - SUBDOMAIN: Subdomain for the app (e.g., app)
   ```

2. **Update Terraform Variables**
   ```bash
   cd terraform
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your domain name
   ```

3. **Deploy Infrastructure**
   ```bash
   bash scripts/deploy.sh
   ```

4. **Access Application**
   - Your app will be available at: `https://<subdomain>.<domain>`
   - Example: `https://app.example.com`

## Teardown
```bash
bash scripts/teardown.sh
```

## Security Notes
- All sensitive values are now parameterized
- SSL certificate is automatically provisioned via ACM
- WAF protection is enabled for DDoS mitigation
