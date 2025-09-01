# Security Monitoring and Alerting

# CloudWatch Log Group for security events
resource "aws_cloudwatch_log_group" "sre_security_logs" {
  name              = "/aws/sre-ops/security"
  retention_in_days = 30

  tags = {
    Environment = "dev"
    Project     = "sre-operations-assistant"
  }
}

# CloudWatch Alarms for security events
resource "aws_cloudwatch_metric_alarm" "high_error_rate" {
  alarm_name          = "sre-ops-high-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "4XXError"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Sum"
  threshold           = "50"
  alarm_description   = "This metric monitors high 4XX error rate"
  alarm_actions       = [aws_sns_topic.sre_security_alerts.arn]

  dimensions = {
    LoadBalancer = data.aws_lb.existing_alb.arn_suffix
  }
}

resource "aws_cloudwatch_metric_alarm" "waf_blocked_requests" {
  alarm_name          = "sre-ops-waf-blocked-requests"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "BlockedRequests"
  namespace           = "AWS/WAFV2"
  period              = "300"
  statistic           = "Sum"
  threshold           = "100"
  alarm_description   = "High number of requests blocked by WAF"
  alarm_actions       = [aws_sns_topic.sre_security_alerts.arn]

  dimensions = {
    WebACL = aws_wafv2_web_acl.sre_waf.name
    Region = "us-west-2"
  }
}

# Use existing SNS topic for alerts
data "aws_sns_topic" "existing_alerts" {
  name = "sre-ops-assistant-alerts"
}

# CloudTrail for API auditing
resource "aws_cloudtrail" "sre_audit_trail" {
  name           = "sre-ops-audit-trail"
  s3_bucket_name = aws_s3_bucket.sre_audit_logs.bucket

  event_selector {
    read_write_type                 = "All"
    include_management_events       = true
    exclude_management_event_sources = []

    data_resource {
      type   = "AWS::S3::Object"
      values = ["${aws_s3_bucket.sre_audit_logs.arn}/*"]
    }
  }

  tags = {
    Environment = "dev"
    Project     = "sre-operations-assistant"
  }
}

# S3 bucket for audit logs
resource "aws_s3_bucket" "sre_audit_logs" {
  bucket        = "sre-ops-audit-logs-${random_id.bucket_suffix.hex}"
  force_destroy = true

  tags = {
    Environment = "dev"
    Project     = "sre-operations-assistant"
  }
}

resource "aws_s3_bucket_versioning" "sre_audit_logs_versioning" {
  bucket = aws_s3_bucket.sre_audit_logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "sre_audit_logs_encryption" {
  bucket = aws_s3_bucket.sre_audit_logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}