# Lambda function for Slack bot
resource "aws_lambda_function" "slack_bot" {
  function_name    = "${var.project_name}-slack-bot"
  role            = aws_iam_role.sre_lambda_role.arn
  handler         = "slack_lambda.handler"
  runtime         = "python3.11"
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size
  
  filename         = data.archive_file.slack_bot_zip.output_path
  source_code_hash = data.archive_file.slack_bot_zip.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE    = aws_dynamodb_table.sre_operations.name
      S3_BUCKET         = aws_s3_bucket.sre_artifacts.bucket
      BEDROCK_MODEL_ID  = var.bedrock_model_id
      SLACK_SECRET_ARN  = aws_secretsmanager_secret.slack_token.arn
      MCP_SERVER_URL    = "https://sre-ops.threemoonsnetwork.net"
    }
  }

  depends_on = [aws_cloudwatch_log_group.lambda_slack_logs]

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
  
  filename         = data.archive_file.scanner_zip.output_path
  source_code_hash = data.archive_file.scanner_zip.output_base64sha256

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

# Lambda function for patch execution
resource "aws_lambda_function" "patch_executor" {
  function_name    = "${var.project_name}-patch-executor"
  role            = aws_iam_role.sre_lambda_role.arn
  handler         = "index.handler"
  runtime         = "python3.11"
  timeout         = 900  # 15 minutes for patching
  memory_size     = 512
  
  filename         = data.archive_file.patch_executor_zip.output_path
  source_code_hash = data.archive_file.patch_executor_zip.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE    = aws_dynamodb_table.sre_operations.name
      S3_BUCKET         = aws_s3_bucket.sre_artifacts.bucket
      SLACK_SECRET_ARN  = aws_secretsmanager_secret.slack_token.arn
    }
  }

  depends_on = [aws_cloudwatch_log_group.lambda_patch_logs]

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "lambda_patch_logs" {
  name              = "/aws/lambda/${var.project_name}-patch-executor"
  retention_in_days = 14

  tags = local.common_tags
}

# Lambda permission for EventBridge patch rules
resource "aws_lambda_permission" "allow_eventbridge_patch" {
  statement_id  = "AllowExecutionFromEventBridgePatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.patch_executor.function_name
  principal     = "events.amazonaws.com"
}