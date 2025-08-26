# Create placeholder Lambda packages for deployment
data "archive_file" "slack_bot_zip" {
  type        = "zip"
  output_path = "${path.module}/placeholder.zip"
  
  source {
    content  = "def handler(event, context): return {'statusCode': 200, 'body': 'Placeholder'}"
    filename = "index.py"
  }
}

data "archive_file" "teams_bot_zip" {
  type        = "zip"
  output_path = "${path.module}/placeholder.zip"
  
  source {
    content  = "def handler(event, context): return {'statusCode': 200, 'body': 'Placeholder'}"
    filename = "index.py"
  }
}

data "archive_file" "scanner_zip" {
  type        = "zip"
  output_path = "${path.module}/placeholder.zip"
  
  source {
    content  = "def handler(event, context): return {'statusCode': 200, 'body': 'Placeholder'}"
    filename = "index.py"
  }
}