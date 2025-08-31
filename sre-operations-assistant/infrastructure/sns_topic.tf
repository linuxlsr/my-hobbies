# SNS Topic for security alerts
resource "aws_sns_topic" "alerts" {
  name = "sre-ops-security-alerts"
}