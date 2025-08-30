# Lambda function for Slack bot
resource "aws_lambda_function" "slack_bot" {
  function_name    = "${var.project_name}-slack-bot"
  role            = aws_iam_role.sre_lambda_role.arn
  handler         = "slack_lambda.handler"
  runtime         = "python3.11"
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size
  
  filename         = "${path.module}/../bots/slack_lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/../bots/slack_lambda.zip")

  environment {
    variables = {
      DYNAMODB_TABLE    = aws_dynamodb_table.sre_operations.name
      S3_BUCKET         = aws_s3_bucket.sre_artifacts.bucket
      BEDROCK_MODEL_ID  = var.bedrock_model_id
      SLACK_SECRET_ARN  = aws_secretsmanager_secret.slack_token.arn
      MCP_SERVER_URL    = "http://${aws_lb.sre_alb.dns_name}"
    }
  }

  depends_on = [aws_cloudwatch_log_group.lambda_slack_logs]

  tags = local.common_tags
}

# Lambda function for Teams bot
resource "aws_lambda_function" "teams_bot" {
  function_name    = "${var.project_name}-teams-bot"
  role            = aws_iam_role.sre_lambda_role.arn
  handler         = "index.handler"
  runtime         = "python3.11"
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size
  
  filename         = "${path.module}/placeholder.zip"

  environment {
    variables = {
      DYNAMODB_TABLE     = aws_dynamodb_table.sre_operations.name
      S3_BUCKET          = aws_s3_bucket.sre_artifacts.bucket
      BEDROCK_MODEL_ID   = var.bedrock_model_id
      TEAMS_SECRET_ARN   = aws_secretsmanager_secret.teams_webhook.arn
      # MCP_SERVER_URL will be configured post-deployment
    }
  }

  depends_on = [aws_cloudwatch_log_group.lambda_teams_logs]

  tags = local.common_tags
}

# Lambda function for scheduled vulnerability scans
resource "aws_lambda_function" "vulnerability_scanner" {
  function_name    = "${var.project_name}-vuln-scanner"
  role            = aws_iam_role.sre_lambda_role.arn
  handler         = "index.handler"
  runtime         = "python3.11"
  timeout         = 300  # 5 minutes for scanning
  memory_size     = 1024
  
  filename         = "${path.module}/placeholder.zip"

  environment {
    variables = {
      DYNAMODB_TABLE    = aws_dynamodb_table.sre_operations.name
      S3_BUCKET         = aws_s3_bucket.sre_artifacts.bucket
      BEDROCK_MODEL_ID  = var.bedrock_model_id
      SLACK_SECRET_ARN  = aws_secretsmanager_secret.slack_token.arn
      TEAMS_SECRET_ARN  = aws_secretsmanager_secret.teams_webhook.arn
    }
  }

  depends_on = [aws_cloudwatch_log_group.lambda_scanner_logs]

  tags = local.common_tags
}

# CloudWatch Log Groups for Lambda functions
resource "aws_cloudwatch_log_group" "lambda_slack_logs" {
  name              = "/aws/lambda/${var.project_name}-slack-bot"
  retention_in_days = 7

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "lambda_teams_logs" {
  name              = "/aws/lambda/${var.project_name}-teams-bot"
  retention_in_days = 7

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "lambda_scanner_logs" {
  name              = "/aws/lambda/${var.project_name}-vuln-scanner"
  retention_in_days = 7

  tags = local.common_tags
}

# EventBridge rule for scheduled vulnerability scans
resource "aws_cloudwatch_event_rule" "vulnerability_scan_schedule" {
  name                = "${var.project_name}-vuln-scan-schedule"
  description         = "Trigger vulnerability scan every 24 hours"
  schedule_expression = "rate(24 hours)"

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "vulnerability_scan_target" {
  rule      = aws_cloudwatch_event_rule.vulnerability_scan_schedule.name
  target_id = "VulnerabilityScanTarget"
  arn       = aws_lambda_function.vulnerability_scanner.arn
}

resource "aws_lambda_permission" "allow_eventbridge_vuln_scan" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.vulnerability_scanner.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.vulnerability_scan_schedule.arn
}