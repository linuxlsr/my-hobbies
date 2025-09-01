# Custom CloudWatch metrics for SRE Operations Assistant

# Lambda function to collect custom metrics
resource "aws_lambda_function" "metrics_collector" {
  function_name    = "${var.project_name}-metrics-collector"
  role            = aws_iam_role.sre_lambda_role.arn
  handler         = "metrics_collector.handler"
  runtime         = "python3.11"
  timeout         = 300
  memory_size     = 512
  
  filename         = "metrics_collector.zip"
  source_code_hash = data.archive_file.metrics_collector_zip.output_base64sha256

  environment {
    variables = {
      MCP_SERVER_URL = "https://sre-ops.threemoonsnetwork.net"
      NAMESPACE      = "SRE/Operations"
    }
  }

  depends_on = [aws_cloudwatch_log_group.lambda_metrics_logs]

  tags = local.common_tags
}

# CloudWatch Log Group for metrics collector
resource "aws_cloudwatch_log_group" "lambda_metrics_logs" {
  name              = "/aws/lambda/${var.project_name}-metrics-collector"
  retention_in_days = 7

  tags = local.common_tags
}

# EventBridge rule for metrics collection
resource "aws_cloudwatch_event_rule" "metrics_collection_schedule" {
  name                = "${var.project_name}-metrics-collection"
  description         = "Collect custom SRE metrics every 5 minutes"
  schedule_expression = "rate(5 minutes)"

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "metrics_collection_target" {
  rule      = aws_cloudwatch_event_rule.metrics_collection_schedule.name
  target_id = "MetricsCollectionTarget"
  arn       = aws_lambda_function.metrics_collector.arn
}

resource "aws_lambda_permission" "allow_eventbridge_metrics" {
  statement_id  = "AllowExecutionFromEventBridgeMetrics"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.metrics_collector.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.metrics_collection_schedule.arn
}

# Custom metric alarms
resource "aws_cloudwatch_metric_alarm" "high_vulnerability_count" {
  alarm_name          = "${var.project_name}-high-vulnerability-count"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "CriticalVulnerabilities"
  namespace           = "SRE/Operations"
  period              = "300"
  statistic           = "Maximum"
  threshold           = "50"
  alarm_description   = "High number of critical vulnerabilities detected"
  alarm_actions       = [aws_sns_topic.sre_alerts.arn]
  treat_missing_data  = "notBreaching"

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "patch_compliance_low" {
  alarm_name          = "${var.project_name}-patch-compliance-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "PatchCompliance"
  namespace           = "SRE/Operations"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "Patch compliance is below acceptable threshold"
  alarm_actions       = [aws_sns_topic.sre_alerts.arn]
  treat_missing_data  = "notBreaching"

  tags = local.common_tags
}