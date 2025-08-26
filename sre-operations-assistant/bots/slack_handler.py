"""AWS Lambda handler for Slack bot webhook"""

import json
import boto3
import os
from slack_bot import SRESlackBot

def lambda_handler(event, context):
    """Handle Slack webhook events"""
    
    try:
        # Parse Slack event
        body = json.loads(event.get('body', '{}'))
        
        # Handle URL verification challenge
        if body.get('type') == 'url_verification':
            return {
                'statusCode': 200,
                'body': body.get('challenge')
            }
        
        # Handle slash commands
        if 'command' in body:
            bot = SRESlackBot()
            command = body['command']
            channel = body['channel_id']
            text = body.get('text', '')
            
            if command == '/sre-vuln-check':
                result = bot.handle_vulnerability_check(channel, text)
            elif command == '/sre-patch-status':
                result = bot.handle_patch_status(channel, text)
            else:
                result = {'status': 'unknown_command'}
            
            return {
                'statusCode': 200,
                'body': json.dumps(result)
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'ok'})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }