# Get existing ECS resources
data "aws_ecs_cluster" "existing_cluster" {
  cluster_name = "sre-ops-assistant-cluster"
}

# Update existing ECS service to use HTTPS target group
resource "aws_ecs_service" "sre_mcp_server_https" {
  name            = "sre-ops-assistant-mcp-server-https"
  cluster         = data.aws_ecs_cluster.existing_cluster.id
  task_definition = aws_ecs_task_definition.mcp_server.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = ["subnet-0c9b5790af6bc8648", "subnet-0e8aa966fda872fc5"]
    security_groups  = ["sg-0207a070d55774e21"]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.https_tg.arn
    container_name   = "sre-mcp-server"
    container_port   = 8000
  }

  depends_on = [aws_lb_listener.https_listener]

  lifecycle {
    create_before_destroy = true
  }
}