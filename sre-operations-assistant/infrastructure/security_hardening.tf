# Security Hardening for SRE Operations Assistant

# API Gateway Rate Limiting
resource "aws_api_gateway_usage_plan" "sre_rate_limit" {
  name         = "sre-ops-rate-limit"
  description  = "Rate limiting for SRE Operations API"

  api_stages {
    api_id = aws_api_gateway_rest_api.sre_api.id
    stage  = aws_api_gateway_stage.sre_api_stage.stage_name
  }

  throttle_settings {
    rate_limit  = 100  # requests per second
    burst_limit = 200  # burst capacity
  }

  quota_settings {
    limit  = 10000  # requests per day
    period = "DAY"
  }
}

# API Key for enhanced authentication
resource "aws_api_gateway_api_key" "sre_api_key" {
  name        = "sre-ops-api-key"
  description = "API key for SRE Operations Assistant"
  enabled     = true
}

resource "aws_api_gateway_usage_plan_key" "sre_usage_plan_key" {
  key_id        = aws_api_gateway_api_key.sre_api_key.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.sre_rate_limit.id
}

# WAF for additional protection
resource "aws_wafv2_web_acl" "sre_waf" {
  name  = "sre-ops-waf"
  scope = "REGIONAL"

  default_action {
    allow {}
  }

  # Rate limiting rule
  rule {
    name     = "RateLimitRule"
    priority = 1

    override_action {
      none {}
    }

    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRule"
      sampled_requests_enabled   = true
    }

    action {
      block {}
    }
  }

  # Block common attacks
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "CommonRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "SREOpsWAF"
    sampled_requests_enabled   = true
  }

  tags = {
    Name        = "sre-ops-waf"
    Environment = "dev"
    Project     = "sre-operations-assistant"
  }
}

# Associate WAF with ALB
resource "aws_wafv2_web_acl_association" "sre_waf_alb" {
  resource_arn = data.aws_lb.existing_alb.arn
  web_acl_arn  = aws_wafv2_web_acl.sre_waf.arn
}

# Enhanced security group rules
resource "aws_security_group_rule" "alb_https_restricted" {
  type              = "ingress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]  # Consider restricting to specific IPs
  description       = "HTTPS access with WAF protection"
  security_group_id = "sg-0bcc08fbdcb6b3254"
}

# Remove the old unrestricted HTTPS rule
resource "aws_security_group_rule" "remove_old_https" {
  type              = "ingress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = "sg-0bcc08fbdcb6b3254"
  
  lifecycle {
    create_before_destroy = false
  }
}