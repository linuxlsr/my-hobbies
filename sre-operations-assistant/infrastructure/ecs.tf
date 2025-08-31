# ECS Cluster for MCP server
resource "aws_ecs_cluster" "sre_cluster" {
  name = "${var.project_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = local.common_tags
}

# CloudWatch Log Group for ECS
resource "aws_cloudwatch_log_group" "ecs_logs" {
  name              = "/ecs/${var.project_name}"
  retention_in_days = 7

  tags = local.common_tags
}

# ECS Task Definition for MCP server
resource "aws_ecs_task_definition" "mcp_server" {
  family                   = "${var.project_name}-mcp-server"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn           = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "sre-mcp-server"
      image = "${local.account_id}.dkr.ecr.${local.region}.amazonaws.com/${aws_ecr_repository.sre_repo.name}:latest"
      
      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "AWS_REGION"
          value = local.region
        },
        {
          name  = "BEDROCK_MODEL_ID"
          value = var.bedrock_model_id
        },
        {
          name  = "DYNAMODB_TABLE"
          value = aws_dynamodb_table.sre_operations.name
        },
        {
          name  = "S3_BUCKET"
          value = aws_s3_bucket.sre_artifacts.bucket
        }
      ]



      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_logs.name
          "awslogs-region"        = local.region
          "awslogs-stream-prefix" = "sre-mcp-server"
        }
      }

      essential = true
    }
  ])

  tags = local.common_tags
}

# ECS Service for MCP server
resource "aws_ecs_service" "mcp_server" {
  name            = "${var.project_name}-mcp-server"
  cluster         = aws_ecs_cluster.sre_cluster.id
  task_definition = aws_ecs_task_definition.mcp_server.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.public_subnet_1.id, aws_subnet.public_subnet_2.id]
    security_groups  = [aws_security_group.ecs_sg.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.sre_tg.arn
    container_name   = "sre-mcp-server"
    container_port   = 8000
  }

  depends_on = [aws_lb_listener.sre_listener]

  tags = local.common_tags
}

# ECR Repository for container images
resource "aws_ecr_repository" "sre_repo" {
  name                 = var.project_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.common_tags
}

# ECR Lifecycle Policy
resource "aws_ecr_lifecycle_policy" "sre_repo_policy" {
  repository = aws_ecr_repository.sre_repo.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 5 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 5
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}