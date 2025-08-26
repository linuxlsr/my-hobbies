"""Configuration Settings for SRE Operations Assistant"""

import os
from typing import Dict, Any


class Settings:
    """Application settings and configuration"""
    
    # AWS Configuration
    AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
    AWS_PROFILE = os.getenv("AWS_PROFILE", "default")
    
    # Bedrock Configuration
    BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "amazon.titan-text-premier-v1:0")
    BEDROCK_REGION = os.getenv("BEDROCK_REGION", "us-west-2")
    
    # MCP Server Configuration
    MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST", "localhost")
    MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8000"))
    
    # Database Configuration
    DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "sre-operations-history")
    S3_BUCKET = os.getenv("S3_BUCKET", "sre-operations-artifacts")
    
    # Chat Bot Configuration
    SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
    SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
    SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "#sre-alerts")
    
    TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL")
    
    # Vulnerability Management
    VULNERABILITY_CHECK_INTERVAL = int(os.getenv("VULNERABILITY_CHECK_INTERVAL", "86400"))  # 24 hours
    CRITICAL_ALERT_THRESHOLD = float(os.getenv("CRITICAL_ALERT_THRESHOLD", "9.0"))  # CVSS score
    
    # Patch Management
    PATCH_WINDOW_HOURS = os.getenv("PATCH_WINDOW_HOURS", "02:00-04:00")
    AUTO_PATCH_NON_CRITICAL = os.getenv("AUTO_PATCH_NON_CRITICAL", "true").lower() == "true"
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def get_aws_config(cls) -> Dict[str, Any]:
        """Get AWS configuration dictionary"""
        return {
            "region_name": cls.AWS_REGION,
            "profile_name": cls.AWS_PROFILE
        }
    
    @classmethod
    def get_bedrock_config(cls) -> Dict[str, Any]:
        """Get Bedrock configuration dictionary"""
        return {
            "model_id": cls.BEDROCK_MODEL_ID,
            "region_name": cls.BEDROCK_REGION,
            "model_type": "titan"
        }
    
    @classmethod
    def validate_required_settings(cls) -> bool:
        """Validate that all required settings are present"""
        required = [
            cls.SLACK_BOT_TOKEN,
            cls.TEAMS_WEBHOOK_URL,
            cls.DYNAMODB_TABLE,
            cls.S3_BUCKET
        ]
        
        missing = [setting for setting in required if not setting]
        
        if missing:
            print(f"Missing required settings: {missing}")
            return False
        
        return True