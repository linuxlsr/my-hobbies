# Create Slack bot Lambda package
data "archive_file" "slack_bot_zip" {
  type        = "zip"
  output_path = "${path.module}/slack_bot.zip"
  source_file = "${path.module}/../bots/slack_lambda.py"
  output_file_mode = "0666"
}

data "archive_file" "scanner_zip" {
  type        = "zip"
  output_path = "${path.module}/placeholder.zip"
  
  source {
    content  = "def handler(event, context): return {'statusCode': 200, 'body': 'Placeholder'}"
    filename = "index.py"
  }
}

data "archive_file" "patch_executor_zip" {
  type        = "zip"
  output_path = "${path.module}/patch_executor.zip"
  
  source {
    content  = <<EOF
import boto3
import json

def handler(event, context):
    ssm = boto3.client('ssm')
    instance_id = event.get('instance_id')
    criticality = event.get('criticality', 'high')
    
    try:
        # Execute patch command via SSM
        response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunPatchBaseline',
            Parameters={'Operation': ['Install']}
        )
        return {'statusCode': 200, 'body': json.dumps({'command_id': response['Command']['CommandId']})}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
EOF
    filename = "index.py"
  }
}