# DynamoDB table for operations history
resource "aws_dynamodb_table" "sre_operations" {
  name           = "${var.project_name}-operations"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "operation_id"
  range_key      = "timestamp"

  attribute {
    name = "operation_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  attribute {
    name = "instance_id"
    type = "S"
  }

  global_secondary_index {
    name               = "instance-index"
    hash_key           = "instance_id"
    range_key          = "timestamp"
    projection_type    = "ALL"
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-operations-table"
  })
}

# S3 bucket for artifacts and logs
resource "aws_s3_bucket" "sre_artifacts" {
  bucket = "${var.project_name}-artifacts-${local.account_id}"

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-artifacts"
  })
}

resource "aws_s3_bucket_versioning" "sre_artifacts_versioning" {
  bucket = aws_s3_bucket.sre_artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "sre_artifacts_encryption" {
  bucket = aws_s3_bucket.sre_artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "sre_artifacts_lifecycle" {
  bucket = aws_s3_bucket.sre_artifacts.id

  rule {
    id     = "cleanup_old_versions"
    status = "Enabled"

    filter {
      prefix = ""
    }

    expiration {
      days = 90
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

# Secrets Manager for sensitive configuration
resource "aws_secretsmanager_secret" "slack_token" {
  name        = "${var.project_name}/slack-token"
  description = "Slack bot token for SRE operations assistant"

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "slack_token" {
  count         = var.slack_bot_token != "" ? 1 : 0
  secret_id     = aws_secretsmanager_secret.slack_token.id
  secret_string = var.slack_bot_token
}

resource "aws_secretsmanager_secret" "teams_webhook" {
  name        = "${var.project_name}/teams-webhook"
  description = "Teams webhook URL for SRE operations assistant"

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "teams_webhook" {
  count         = var.teams_webhook_url != "" ? 1 : 0
  secret_id     = aws_secretsmanager_secret.teams_webhook.id
  secret_string = var.teams_webhook_url
}