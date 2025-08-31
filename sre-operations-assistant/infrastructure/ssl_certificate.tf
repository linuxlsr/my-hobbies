# SSL Certificate for HTTPS
resource "aws_acm_certificate" "sre_ops_ssl" {
  domain_name               = "sre-ops.threemoonsnetwork.net"
  subject_alternative_names = ["*.sre-ops.threemoonsnetwork.net"]
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "SRE Operations SSL Certificate"
  }
}

# Certificate validation records
resource "aws_route53_record" "ssl_cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.sre_ops_ssl.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.aws_route53_zone.threemoonsnetwork.zone_id
}

# Certificate validation
resource "aws_acm_certificate_validation" "sre_ops_ssl" {
  certificate_arn         = aws_acm_certificate.sre_ops_ssl.arn
  validation_record_fqdns = [for record in aws_route53_record.ssl_cert_validation : record.fqdn]
}