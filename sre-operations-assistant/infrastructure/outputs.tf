output "api_gateway_url" {
  description = "API Gateway URL for webhooks"
  value       = "https://${aws_api_gateway_rest_api.sre_api.id}.execute-api.${local.region}.amazonaws.com/${var.environment}"
}

output "slack_webhook_url" {
  description = "Slack webhook URL"
  value       = "https://${aws_api_gateway_rest_api.sre_api.id}.execute-api.${local.region}.amazonaws.com/${var.environment}/slack"
}

output "ecr_repository_url" {
  description = "ECR repository URL for container images"
  value       = aws_ecr_repository.sre_repo.repository_url
}

output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = aws_dynamodb_table.sre_operations.name
}

output "s3_bucket_name" {
  description = "S3 bucket name for artifacts"
  value       = aws_s3_bucket.sre_artifacts.bucket
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.sre_cluster.name
}

output "cloudwatch_dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = "https://${local.region}.console.aws.amazon.com/cloudwatch/home?region=${local.region}#dashboards:name=${aws_cloudwatch_dashboard.sre_dashboard.dashboard_name}"
}

output "alb_dns_name" {
  description = "Application Load Balancer DNS name for MCP server access"
  value       = aws_lb.sre_alb.dns_name
}

output "mcp_server_url" {
  description = "MCP server URL via ALB"
  value       = "http://${aws_lb.sre_alb.dns_name}"
}

output "secrets_manager_slack_arn" {
  description = "Secrets Manager ARN for Slack token"
  value       = aws_secretsmanager_secret.slack_token.arn
}

output "secrets_manager_teams_arn" {
  description = "Secrets Manager ARN for Teams webhook"
  value       = aws_secretsmanager_secret.teams_webhook.arn
}

output "lambda_function_names" {
  description = "Lambda function names"
  value = {
    slack_bot            = aws_lambda_function.slack_bot.function_name
    vulnerability_scanner = aws_lambda_function.vulnerability_scanner.function_name
  }
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.sre_vpc.id
}

output "subnet_ids" {
  description = "Subnet IDs"
  value = {
    public_subnet_1 = aws_subnet.public_subnet_1.id
    public_subnet_2 = aws_subnet.public_subnet_2.id
  }
}

output "security_group_ids" {
  description = "Security group IDs"
  value = {
    ecs_sg    = aws_security_group.ecs_sg.id
    lambda_sg = aws_security_group.lambda_sg.id
  }
}