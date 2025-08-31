# Route53 A record pointing to existing ALB
resource "aws_route53_record" "sre_ops_domain" {
  zone_id = data.aws_route53_zone.threemoonsnetwork.zone_id
  name    = "sre-ops.threemoonsnetwork.net"
  type    = "A"

  alias {
    name                   = "sre-ops-assistant-alb-942046254.us-west-2.elb.amazonaws.com"
    zone_id                = "Z1H1FL5HABSF5"
    evaluate_target_health = true
  }
}