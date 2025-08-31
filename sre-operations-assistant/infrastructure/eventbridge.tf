# EventBridge policy for automated patch scheduling
resource "aws_iam_policy" "eventbridge_policy" {
  name        = "${var.project_name}-eventbridge-policy"
  description = "EventBridge permissions for automated patch scheduling"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "events:PutRule",
          "events:DeleteRule",
          "events:ListRules",
          "events:PutTargets",
          "events:RemoveTargets",
          "events:DescribeRule",
          "events:EnableRule",
          "events:DisableRule"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "sts:GetCallerIdentity"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "lambda:AddPermission",
          "lambda:RemovePermission"
        ]
        Resource = "arn:aws:lambda:${local.region}:${local.account_id}:function:${var.project_name}-*"
      }
    ]
  })

  tags = local.common_tags
}

# Attach EventBridge policy to ECS task role
resource "aws_iam_role_policy_attachment" "ecs_task_eventbridge_policy" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = aws_iam_policy.eventbridge_policy.arn
}