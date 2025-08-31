# API Key for authentication
resource "random_password" "sre_api_key" {
  length  = 32
  special = true
}

resource "aws_secretsmanager_secret" "sre_api_key" {
  name        = "sre-ops-api-key-v2"
  description = "API key for SRE Operations Assistant"
}

resource "aws_secretsmanager_secret_version" "sre_api_key" {
  secret_id     = aws_secretsmanager_secret.sre_api_key.id
  secret_string = random_password.sre_api_key.result
}