# Get current AWS account ID and region
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Route53 zone - update this to your domain
data "aws_route53_zone" "main" {
  name = var.domain_name
}
