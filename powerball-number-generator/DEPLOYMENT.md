# PowerballAI Predictor - Deployment Guide

## Quick Start

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run local development server
bash scripts/run_local.sh
# Or manually:
cd web && uvicorn app:app --host 0.0.0.0 --port 5000 --reload
```

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build manually
docker build -t powerball .
docker run -p 5000:5000 -v $(pwd)/data:/app/data powerball
```

## CLI Usage

### Basic Commands
```bash
# Initialize data
python3 cli/powerball_cli.py update-data

# Check system status
python3 cli/powerball_cli.py status

# Generate predictions
python3 cli/powerball_cli.py predict --tickets 5

# Analyze patterns
python3 cli/powerball_cli.py analyze

# Generate portfolio
python3 cli/powerball_cli.py portfolio --tickets 10
```

### Advanced Usage
```bash
# Different strategies
python3 cli/powerball_cli.py predict --strategy frequency_based
python3 cli/powerball_cli.py predict --strategy gap_based
python3 cli/powerball_cli.py predict --strategy monte_carlo

# Export to CSV
python3 cli/powerball_cli.py predict --tickets 10 --format csv > predictions.csv

# Detailed analysis
python3 cli/powerball_cli.py analyze --format detailed
```

## Web Interface

### Local Access
- URL: http://localhost:5000
- Interactive API docs: http://localhost:5000/docs
- Features: Interactive predictions, visual analysis, real-time updates

### API Endpoints
- `GET /ping` - Simple health check
- `GET /health` - Detailed health status
- `GET /api/status` - System status
- `GET /api/analyze` - Statistical analysis
- `POST /api/predict` - Generate predictions
- `POST /api/update-data` - Update historical data

## AWS ECS Deployment

### Prerequisites
- AWS CLI configured
- Docker installed
- ECR repository created

### Deployment Steps

1. **Build and Push to ECR**
```bash
# Login to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-west-2.amazonaws.com

# Build and tag
docker build -t powerball .
docker tag powerball:latest <account>.dkr.ecr.us-west-2.amazonaws.com/powerball:latest

# Push to ECR
docker push <account>.dkr.ecr.us-west-2.amazonaws.com/powerball:latest
```

2. **Create ECS Task Definition**
```json
{
  "family": "powerball",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::<account>:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "powerball",
      "image": "<account>.dkr.ecr.us-west-2.amazonaws.com/powerball:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/powerball",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

3. **Create ECS Service**
```bash
aws ecs create-service \
  --cluster powerball-cluster \
  --service-name powerball-service \
  --task-definition powerball:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

4. **Setup Application Load Balancer**
- Create ALB with target group pointing to port 5000
- Configure health check on `/api/status`
- Setup SSL certificate for HTTPS

## Environment Variables

### Production Settings
```bash
PORT=5000
PYTHONPATH=/app/src
```

### Optional Configuration
```bash
DB_PATH=data/powerball.db  # Database location
UPDATE_INTERVAL=86400      # Data update interval (seconds)
```

## Monitoring & Maintenance

### Health Checks
- Primary: `/ping` (returns "pong")
- Detailed: `/health` (returns JSON with timestamp)
- System: `/api/status` (database connectivity)
- Expected: HTTP 200 responses
- Frequency: Every 30 seconds

### Data Updates
- Automatic: On container startup
- Manual: POST to `/api/update-data`
- Frequency: Daily recommended

### Logs
- Application logs: stdout/stderr
- Access logs: uvicorn built-in
- AWS: CloudWatch Logs

## Security Considerations

### Production Deployment
- Use HTTPS only
- Implement rate limiting
- Add authentication if needed
- Regular security updates

### Data Protection
- SQLite database is local only
- No sensitive data stored
- Stateless application design

## Troubleshooting

### Common Issues

1. **Database not found**
   - Run: `python3 cli/powerball_cli.py update-data`

2. **Import errors**
   - Check Python path and dependencies
   - Ensure all files are in correct directories

3. **Web interface not loading**
   - Check uvicorn is running on correct port
   - Verify firewall/security group settings
   - Check FastAPI app startup logs

4. **Predictions seem random**
   - Ensure sufficient historical data (200+ drawings)
   - Check data quality in status endpoint

### Performance Optimization
- uvicorn with multiple workers for production
- Enable caching for analysis results
- Optimize database queries
- Use CDN for static assets
- Leverage FastAPI's async capabilities

## Cost Estimation (AWS)

### ECS Fargate
- CPU: 0.25 vCPU = ~$7/month
- Memory: 0.5 GB = ~$3/month
- Data transfer: ~$1/month

### Additional Services
- ALB: ~$16/month
- Route53: ~$0.50/month
- CloudWatch: ~$2/month

**Total: ~$30/month**

## Support & Updates

### Maintenance Schedule
- Data updates: Daily
- Security patches: Weekly
- Feature updates: Monthly

### Backup Strategy
- Database: Included in container image
- Configuration: Version controlled
- No persistent data to backup