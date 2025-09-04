terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    # }
  # }
# }

provider "aws" {
  region = var.aws_region
# }

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  # }
# }

# Moved to data.tf
  name = "<your-domain.com>"
# }

# VPC and Networking
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "powerball-vpc"
  # }
# }

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "powerball-igw"
  # }
# }

resource "aws_subnet" "public" {
  count = 2

  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index + 1# }.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "powerball-public-${count.index + 1# }"
  # }
# }

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  # }

  tags = {
    Name = "powerball-public-rt"
  # }
# }

resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
# }

# Security Groups
resource "aws_security_group" "alb" {
  name_prefix = "powerball-alb-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  # }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  # }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  # }

  tags = {
    Name = "powerball-alb-sg"
  # }
# }

resource "aws_security_group" "ecs" {
  name_prefix = "powerball-ecs-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5000
    to_port         = 5000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  # }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  # }

  tags = {
    Name = "powerball-ecs-sg"
  # }
# }

# SSL Certificate
resource "aws_acm_certificate" "main" {
  domain_name       = "avarice.<your-domain.com>"
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  # }

  tags = {
    Name = "powerball-cert"
  # }
# }

resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.main.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    # }
  # }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.aws_route53_zone.main.zone_id
# }

resource "aws_acm_certificate_validation" "main" {
  certificate_arn         = aws_acm_certificate.main.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
# }

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "powerball-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = false

  tags = {
    Name = "powerball-alb"
  # }
# }

resource "aws_lb_target_group" "main" {
  name        = "powerball-tg"
  port        = 5000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 60
    matcher             = "200"
    path                = "/ping"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 10
    unhealthy_threshold = 5
  # }

  lifecycle {
    create_before_destroy = true
  # }

  tags = {
    Name = "powerball-tg"
  # }
# }

# HTTPS Listener with security headers
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate_validation.main.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.main.arn
  # }
# }

# HTTP to HTTPS redirect
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    # }
  # }
# }

# Route53 DNS Record
resource "aws_route53_record" "main" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = var.subdomain
  type    = "A"

  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  # }
# }

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "powerball-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  # }

  tags = {
    Name = "powerball-cluster"
  # }
# }

# ECS Task Definition
resource "aws_ecs_task_definition" "main" {
  family                   = "powerball"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.container_cpu
  memory                   = var.container_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn           = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name  = "powerball"
      image = "${aws_ecr_repository.main.repository_url# }:latest"
      
      cpu = var.container_cpu
      memory = var.container_memory
      
      portMappings = [
        {
          containerPort = 5000
          protocol      = "tcp"
        # }
      ]

      environment = [
        {
          name  = "PORT"
          value = "5000"
        # },
        {
          name  = "PYTHONPATH"
          value = "/app/src"
        # }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.main.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
          "awslogs-create-group"  = "true"
        # }
      # }



      essential = true
    # }
  ])

  tags = {
    Name = "powerball-task"
  # }
# }

# ECS Service
resource "aws_ecs_service" "main" {
  name            = "powerball-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.main.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  platform_version = "LATEST"

  network_configuration {
    security_groups  = [aws_security_group.ecs.id]
    subnets          = aws_subnet.public[*].id
    assign_public_ip = true
  # }

  load_balancer {
    target_group_arn = aws_lb_target_group.main.arn
    container_name   = "powerball"
    container_port   = 5000
  # }

  # Wait for load balancer to be ready
  depends_on = [
    aws_lb_listener.https,
    aws_lb_listener.http,
    aws_iam_role_policy_attachment.ecs_execution
  ]



  tags = {
    Name = "powerball-service"
  # }
# }

# ECR Repository
resource "aws_ecr_repository" "main" {
  name                 = "powerball"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  # }

  tags = {
    Name = "powerball-ecr"
  # }
# }

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "main" {
  name              = "/ecs/powerball"
  retention_in_days = 7

  tags = {
    Name = "powerball-logs"
  # }
# }

# WAF for DDoS and attack protection
resource "aws_wafv2_web_acl" "main" {
  name  = "powerball-waf"
  scope = "REGIONAL"

  default_action {
    allow {# }
  # }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "powerball-waf"
    sampled_requests_enabled   = true
  # }

  # Rate limiting rule
  rule {
    name     = "RateLimitRule"
    priority = 1

    action {
      block {# }
    # }

    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      # }
    # }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRule"
      sampled_requests_enabled   = true
    # }
  # }

  # AWS Managed Rules
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 2

    override_action {
      none {# }
    # }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      # }
    # }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "CommonRuleSetMetric"
      sampled_requests_enabled   = true
    # }
  # }

  tags = {
    Name = "powerball-waf"
  # }
# }



