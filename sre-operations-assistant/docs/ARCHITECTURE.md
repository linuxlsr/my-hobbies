# Architecture Documentation

## 🏗️ System Overview

The SRE Operations Assistant is a cloud-native, microservices-based system designed for high availability, security, and scalability.

## 🎯 Design Principles

- **Security First** - All traffic encrypted, WAF protected, least privilege access
- **High Availability** - Multi-AZ deployment, auto-scaling, health checks
- **Observability** - Comprehensive logging, monitoring, and alerting
- **Scalability** - Containerized services, load balancing, auto-scaling
- **Cost Optimization** - Serverless where appropriate, right-sized resources

## 🏛️ Architecture Layers

### 1. Presentation Layer
```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Slack Bot     │  │   Teams Bot     │  │   CLI Client    │
│   (Lambda)      │  │   (Lambda)      │  │   (Python)      │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

**Components:**
- **Slack Bot**: AWS Lambda function handling Slack slash commands
- **Teams Bot**: AWS Lambda function for Microsoft Teams integration  
- **CLI Client**: Python-based command-line interface

**Technologies:**
- AWS Lambda (Serverless compute)
- Python 3.8+ runtime
- Slack SDK / Microsoft Graph API

### 2. API Gateway Layer
```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Rate Limit  │  │ API Keys    │  │ Request Validation  │ │
│  │ 100 req/sec │  │ Auth        │  │ & Transformation    │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Rate limiting (100 req/sec, 10K/day)
- API key authentication
- Request/response transformation
- CORS handling
- CloudWatch integration

### 3. Load Balancer & Security Layer
```
┌─────────────────────────────────────────────────────────────┐
│                Application Load Balancer                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │    WAF      │  │ SSL/TLS     │  │ Health Checks       │ │
│  │ Protection  │  │ Termination │  │ & Routing           │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Security Features:**
- AWS WAF with managed rule sets
- SSL/TLS termination with ACM certificates
- Security groups restricting access
- DDoS protection via AWS Shield

### 4. Application Layer
```
┌─────────────────────────────────────────────────────────────┐
│                    ECS Fargate Cluster                     │
│  ┌─────────────────┐              ┌─────────────────────┐  │
│  │ HTTPS Service   │              │ Auto Scaling        │  │
│  │ (2 tasks)       │◄────────────►│ 1-10 tasks         │  │
│  │ Port 8000       │              │ CPU/Memory based    │  │
│  └─────────────────┘              └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Container Specifications:**
- **Image**: Custom Python application
- **CPU**: 256 CPU units (0.25 vCPU)
- **Memory**: 512 MB
- **Network**: awsvpc mode with public IPs
- **Health Check**: `/health` endpoint

### 5. Data & Integration Layer
```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ AWS Inspector   │  │ AWS CloudWatch  │  │ AWS Systems     │
│ Vulnerability   │  │ Metrics &       │  │ Manager         │
│ Scanning        │  │ Logging         │  │ Patch Mgmt      │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

**AWS Service Integrations:**
- **Inspector**: Vulnerability assessments
- **CloudWatch**: Metrics, logs, and alarms
- **Systems Manager**: Instance management and patching
- **EC2**: Instance monitoring and management
- **CloudTrail**: API audit logging

## 🌐 Network Architecture

### VPC Configuration
```
┌─────────────────────────────────────────────────────────────┐
│                        VPC                                  │
│  ┌─────────────────┐              ┌─────────────────────┐  │
│  │ Public Subnet   │              │ Public Subnet       │  │
│  │ us-west-2a      │              │ us-west-2b          │  │
│  │ 10.0.X.X/24     │              │ 10.0.X.X/24         │  │
│  └─────────────────┘              └─────────────────────┘  │
│           │                                   │             │
│  ┌─────────────────┐              ┌─────────────────────┐  │
│  │ Internet        │              │ Internet            │  │
│  │ Gateway         │              │ Gateway             │  │
│  └─────────────────┘              └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Network Details:**
- **VPC CIDR**: 10.0.X.X/16
- **Availability Zones**: us-west-2a, us-west-2b
- **Public Subnets**: For ALB and ECS tasks with public IPs
- **Internet Gateway**: Direct internet access
- **Route Tables**: Public routing to IGW

### Security Groups
```
ALB Security Group (sg-xxxxxxxxxxxxxxxxx)
├── Inbound: Port 80 (HTTP) from 0.0.0.0/0
├── Inbound: Port 443 (HTTPS) from 0.0.0.0/0
└── Outbound: All traffic

ECS Security Group (sg-xxxxxxxxxxxxxxxxx)  
├── Inbound: Port 8000 from ALB Security Group
└── Outbound: All traffic
```

## 🔒 Security Architecture

### Defense in Depth
```
Internet → WAF → ALB → Security Groups → ECS Tasks → IAM Roles
```

**Security Layers:**
1. **WAF**: Blocks malicious requests, rate limiting
2. **ALB**: SSL termination, security groups
3. **Security Groups**: Network-level firewall rules
4. **ECS Tasks**: Container isolation, least privilege
5. **IAM Roles**: Fine-grained permissions

### Certificate Management
```
┌─────────────────────────────────────────────────────────────┐
│                    SSL Certificate                         │
│  ┌─────────────────┐              ┌─────────────────────┐  │
│  │ ACM Certificate │              │ Route53 Validation  │  │
│  │ *.threemoons... │◄────────────►│ DNS Records         │  │
│  │ Auto-renewal    │              │ CNAME validation    │  │
│  └─────────────────┘              └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Secrets Management
```
┌─────────────────────────────────────────────────────────────┐
│                 AWS Secrets Manager                        │
│  ┌─────────────────┐              ┌─────────────────────┐  │
│  │ API Keys        │              │ Database Creds      │  │
│  │ Encrypted       │              │ Auto-rotation       │  │
│  │ Versioned       │              │ Fine-grained access │  │
│  └─────────────────┘              └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Monitoring & Observability

### Logging Architecture
```
Application Logs → CloudWatch Logs → Log Insights → Dashboards
     │
     ├── ECS Task Logs (/ecs/sre-ops-assistant)
     ├── Lambda Logs (/aws/lambda/sre-*)  
     ├── ALB Access Logs (S3)
     └── WAF Logs (CloudWatch)
```

### Metrics & Alarms
```
┌─────────────────────────────────────────────────────────────┐
│                    CloudWatch Metrics                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ Application     │  │ Infrastructure  │  │ Security    │ │
│  │ - Response time │  │ - CPU/Memory    │  │ - WAF blocks│ │
│  │ - Error rates   │  │ - Network I/O   │  │ - Failed    │ │
│  │ - Request count │  │ - Disk usage    │  │   requests  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Alerting Flow
```
Metric Threshold → CloudWatch Alarm → SNS Topic → Email/Slack
```

## 🚀 Deployment Architecture

### Infrastructure as Code
```
┌─────────────────────────────────────────────────────────────┐
│                      Terraform                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ Core Infra      │  │ Security        │  │ Monitoring  │ │
│  │ - VPC/Subnets   │  │ - WAF/SG        │  │ - CW Alarms │ │
│  │ - ALB/ECS       │  │ - IAM Roles     │  │ - SNS Topics│ │
│  │ - Route53       │  │ - Certificates  │  │ - Dashboards│ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### CI/CD Pipeline (Future)
```
Git Push → Build → Test → Security Scan → Deploy → Monitor
```

## 📈 Scalability Considerations

### Horizontal Scaling
- **ECS Auto Scaling**: CPU/Memory based scaling (1-10 tasks)
- **ALB**: Automatic scaling for traffic distribution
- **API Gateway**: Serverless, scales automatically

### Vertical Scaling
- **ECS Task Size**: Can increase CPU/Memory per task
- **Lambda Memory**: Adjustable from 128MB to 10GB

### Performance Optimization
- **Connection Pooling**: Reuse AWS service connections
- **Caching**: In-memory caching for frequent queries
- **Async Processing**: Non-blocking I/O operations

## 🔄 Data Flow

### Request Flow
```
1. User Request → API Gateway/ALB
2. Authentication & Rate Limiting
3. WAF Security Filtering  
4. Load Balancer Routing
5. ECS Task Processing
6. AWS Service Integration
7. Response Assembly
8. Response Delivery
```

### Monitoring Data Flow
```
1. Application Metrics → CloudWatch
2. Log Aggregation → CloudWatch Logs
3. Alarm Evaluation → CloudWatch Alarms
4. Notification → SNS → Email/Slack
5. Audit Trail → CloudTrail → S3
```

## 🎯 Future Architecture Enhancements

### Multi-Region Deployment
- Cross-region replication
- Global load balancing
- Disaster recovery

### Microservices Decomposition
- Separate vulnerability scanning service
- Dedicated metrics service
- Independent notification service

### Advanced Security
- AWS Config for compliance
- GuardDuty for threat detection
- Security Hub for centralized security

This architecture provides a solid foundation for a production-ready SRE Operations Assistant with enterprise-grade security, monitoring, and scalability.