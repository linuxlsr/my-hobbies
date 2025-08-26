variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-west-2"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "sre-ops-assistant"
}

variable "bedrock_model_id" {
  description = "Bedrock model ID to use"
  type        = string
  default     = "amazon.titan-text-premier-v1:0"
}

variable "slack_bot_token" {
  description = "Slack bot token (stored in Secrets Manager)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "teams_webhook_url" {
  description = "Teams webhook URL (stored in Secrets Manager)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "lambda_memory_size" {
  description = "Memory size for Lambda functions"
  type        = number
  default     = 512
}

variable "lambda_timeout" {
  description = "Timeout for Lambda functions in seconds"
  type        = number
  default     = 30
}