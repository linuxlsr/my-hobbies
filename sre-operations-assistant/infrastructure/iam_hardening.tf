# IAM Security Hardening

# Least privilege IAM role for ECS tasks
resource "aws_iam_role" "ecs_task_role_hardened" {
  name = "sre-ops-ecs-task-role-hardened"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Environment = "dev"
    Project     = "sre-operations-assistant"
  }
}

# Minimal policy for SRE operations
resource "aws_iam_policy" "sre_minimal_policy" {
  name        = "sre-ops-minimal-policy"
  description = "Minimal permissions for SRE operations"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "inspector2:ListFindings",
          "inspector2:GetFindings",
          "ec2:DescribeInstances",
          "cloudwatch:GetMetricStatistics",
          "cloudwatch:ListMetrics",
          "ssm:DescribeInstanceInformation",
          "ssm:GetCommandInvocation",
          "ssm:ListCommandInvocations"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:RequestedRegion" = "us-west-2"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.sre_api_key.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_minimal" {
  role       = aws_iam_role.ecs_task_role_hardened.name
  policy_arn = aws_iam_policy.sre_minimal_policy.arn
}

# Lambda execution role with minimal permissions
resource "aws_iam_role" "lambda_role_hardened" {
  name = "sre-ops-lambda-role-hardened"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Environment = "dev"
    Project     = "sre-operations-assistant"
  }
}

resource "aws_iam_policy" "lambda_minimal_policy" {
  name        = "sre-ops-lambda-minimal-policy"
  description = "Minimal permissions for Lambda functions"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:us-west-2:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.sre_api_key.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_minimal" {
  role       = aws_iam_role.lambda_role_hardened.name
  policy_arn = aws_iam_policy.lambda_minimal_policy.arn
}

# API Gateway resource policy (using rest_api_policy)
resource "aws_api_gateway_rest_api_policy" "sre_api_policy" {
  rest_api_id = aws_api_gateway_rest_api.sre_api.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = "*"
        Action = "execute-api:Invoke"
        Resource = "${aws_api_gateway_rest_api.sre_api.execution_arn}/*"
        Condition = {
          StringEquals = {
            "aws:SourceIp" = [
              "0.0.0.0/0"  # Consider restricting to specific IP ranges
            ]
          }
        }
      }
    ]
  })
}