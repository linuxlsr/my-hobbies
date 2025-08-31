# Route53 hosted zone data source
data "aws_route53_zone" "threemoonsnetwork" {
  name         = "threemoonsnetwork.net"
  private_zone = false
}