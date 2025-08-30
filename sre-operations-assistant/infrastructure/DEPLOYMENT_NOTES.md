# Deployment Notes - Critical Issues Addressed

## ⚠️ **Post-Deployment Steps Required**

### 1. **ECS Service Will Initially Fail**
- **Issue:** ECR repository will be empty after first deployment
- **Solution:** Build and push Docker image immediately after `terraform apply`
- **Commands:**
  ```bash
  # Get ECR URL from terraform output
  ECR_URL=$(terraform output -raw ecr_repository_url)
  
  # Build and push image
  cd ..
  docker build -t sre-ops-assistant .
  docker tag sre-ops-assistant:latest $ECR_URL:latest
  docker push $ECR_URL:latest
  
  # Force ECS service update
  aws ecs update-service --cluster sre-ops-assistant-cluster --service sre-ops-assistant-mcp-server --force-new-deployment
  ```

### 2. **Lambda Functions Need MCP Server URL**
- **Issue:** Lambda functions can't connect to ECS service initially
- **Solution:** Update Lambda environment variables after ECS is running
- **Commands:**
  ```bash
  # Get ECS service details and update Lambda functions
  # This will be automated in future versions
  ```

## 🔧 **Issues Fixed in Configuration:**

### ✅ **ECS Execution Role Permissions**
- Added Secrets Manager permissions for container startup
- ECS tasks can now retrieve Slack/Teams tokens

### ✅ **Lambda Environment Variables**
- Removed invalid MCP_SERVER_URL references
- Functions will deploy successfully

### ✅ **Resource Dependencies**
- Proper dependency ordering for resource creation
- Reduced circular dependency issues

## 📋 **Deployment Order:**

1. **First Apply:** `terraform apply` (ECS service will fail initially)
2. **Build Image:** Push Docker image to ECR
3. **Update Service:** Force ECS service deployment
4. **Configure Secrets:** Add Slack/Teams tokens if not done
5. **Test Functions:** Verify Lambda and ECS integration

## 💡 **Future Improvements:**

- Add null_resource for automatic Docker build
- Implement proper service discovery for Lambda-ECS communication
- Add health checks and auto-recovery mechanisms