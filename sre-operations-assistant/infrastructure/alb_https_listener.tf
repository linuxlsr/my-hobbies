# Get existing ALB
data "aws_lb" "existing_alb" {
  name = "sre-ops-assistant-alb"
}

# Create new target group for HTTPS
resource "aws_lb_target_group" "https_tg" {
  name        = "sre-ops-https-tg-v2"
  port        = 8000
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = data.aws_lb.existing_alb.vpc_id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }
}

# Add HTTPS listener
resource "aws_lb_listener" "https_listener" {
  load_balancer_arn = data.aws_lb.existing_alb.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate_validation.sre_ops_ssl.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.https_tg.arn
  }
}