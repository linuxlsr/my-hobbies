# API Gateway for Slack and Teams webhooks
resource "aws_api_gateway_rest_api" "sre_api" {
  name        = "${var.project_name}-api"
  description = "API Gateway for SRE Operations Assistant webhooks"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = local.common_tags
}

# Slack webhook resource
resource "aws_api_gateway_resource" "slack_webhook" {
  rest_api_id = aws_api_gateway_rest_api.sre_api.id
  parent_id   = aws_api_gateway_rest_api.sre_api.root_resource_id
  path_part   = "slack"
}

resource "aws_api_gateway_method" "slack_post" {
  rest_api_id   = aws_api_gateway_rest_api.sre_api.id
  resource_id   = aws_api_gateway_resource.slack_webhook.id
  http_method   = "POST"
  authorization = "NONE"
}

# OPTIONS method for CORS
resource "aws_api_gateway_method" "slack_options" {
  rest_api_id   = aws_api_gateway_rest_api.sre_api.id
  resource_id   = aws_api_gateway_resource.slack_webhook.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "slack_options_integration" {
  rest_api_id = aws_api_gateway_rest_api.sre_api.id
  resource_id = aws_api_gateway_resource.slack_webhook.id
  http_method = aws_api_gateway_method.slack_options.http_method
  type        = "MOCK"
  
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "slack_options_response" {
  rest_api_id = aws_api_gateway_rest_api.sre_api.id
  resource_id = aws_api_gateway_resource.slack_webhook.id
  http_method = aws_api_gateway_method.slack_options.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "slack_options_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.sre_api.id
  resource_id = aws_api_gateway_resource.slack_webhook.id
  http_method = aws_api_gateway_method.slack_options.http_method
  status_code = aws_api_gateway_method_response.slack_options_response.status_code
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'POST,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

resource "aws_api_gateway_integration" "slack_integration" {
  rest_api_id = aws_api_gateway_rest_api.sre_api.id
  resource_id = aws_api_gateway_resource.slack_webhook.id
  http_method = aws_api_gateway_method.slack_post.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.slack_bot.invoke_arn
}

# Teams webhook resource
resource "aws_api_gateway_resource" "teams_webhook" {
  rest_api_id = aws_api_gateway_rest_api.sre_api.id
  parent_id   = aws_api_gateway_rest_api.sre_api.root_resource_id
  path_part   = "teams"
}

resource "aws_api_gateway_method" "teams_post" {
  rest_api_id   = aws_api_gateway_rest_api.sre_api.id
  resource_id   = aws_api_gateway_resource.teams_webhook.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "teams_integration" {
  rest_api_id = aws_api_gateway_rest_api.sre_api.id
  resource_id = aws_api_gateway_resource.teams_webhook.id
  http_method = aws_api_gateway_method.teams_post.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.teams_bot.invoke_arn
}

# API Gateway deployment
resource "aws_api_gateway_deployment" "sre_api_deployment" {
  depends_on = [
    aws_api_gateway_integration.slack_integration,
    aws_api_gateway_integration.teams_integration,
    aws_api_gateway_integration.slack_options_integration
  ]

  rest_api_id = aws_api_gateway_rest_api.sre_api.id
  
  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.slack_webhook.id,
      aws_api_gateway_method.slack_post.id,
      aws_api_gateway_integration.slack_integration.id,
      aws_lambda_function.slack_bot.source_code_hash,
      timestamp()
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

# API Gateway stage
resource "aws_api_gateway_stage" "sre_api_stage" {
  deployment_id = aws_api_gateway_deployment.sre_api_deployment.id
  rest_api_id   = aws_api_gateway_rest_api.sre_api.id
  stage_name    = var.environment

  tags = local.common_tags
}

# Lambda permissions for API Gateway
resource "aws_lambda_permission" "allow_api_gateway_slack" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.slack_bot.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.sre_api.execution_arn}/*/*/*"
}

resource "aws_lambda_permission" "allow_api_gateway_teams" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.teams_bot.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.sre_api.execution_arn}/*/*"
}

# API Gateway usage plan and API key
resource "aws_api_gateway_usage_plan" "sre_usage_plan" {
  name = "${var.project_name}-usage-plan"

  api_stages {
    api_id = aws_api_gateway_rest_api.sre_api.id
    stage  = aws_api_gateway_stage.sre_api_stage.stage_name
  }

  quota_settings {
    limit  = 1000
    period = "DAY"
  }

  throttle_settings {
    rate_limit  = 10
    burst_limit = 20
  }

  tags = local.common_tags
}