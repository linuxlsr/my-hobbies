"""
Security middleware for API authentication and rate limiting
"""

import os
import time
import json
import hashlib
from typing import Dict, Optional
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from collections import defaultdict, deque
import boto3
from botocore.exceptions import ClientError

class SecurityMiddleware:
    def __init__(self):
        self.require_api_key = os.getenv("REQUIRE_API_KEY", "false").lower() == "true"
        self.api_key = None
        self.rate_limiter = RateLimiter()
        
        if self.require_api_key:
            self._load_api_key()
    
    def _load_api_key(self):
        """Load API key from AWS Secrets Manager"""
        try:
            secrets_client = boto3.client('secretsmanager')
            response = secrets_client.get_secret_value(SecretId='sre-ops-api-key')
            secret_data = json.loads(response['SecretString'])
            self.api_key = secret_data.get('api_key')
        except ClientError as e:
            print(f"Error loading API key: {e}")
            # Fallback to environment variable for local development
            self.api_key = os.getenv("API_KEY")
    
    async def authenticate_request(self, request: Request) -> bool:
        """Authenticate API request"""
        if not self.require_api_key:
            return True
        
        # Check for API key in header
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            # Check Authorization header
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                api_key = auth_header[7:]
        
        if not api_key or api_key != self.api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key"
            )
        
        return True
    
    async def check_rate_limit(self, request: Request) -> bool:
        """Check rate limiting"""
        client_ip = self._get_client_ip(request)
        
        if not self.rate_limiter.is_allowed(client_ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        return True
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded IP (from ALB)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        return request.client.host if request.client else "unknown"

class RateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 300):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed based on rate limiting"""
        now = time.time()
        client_requests = self.requests[client_id]
        
        # Remove old requests outside the window
        while client_requests and client_requests[0] <= now - self.window_seconds:
            client_requests.popleft()
        
        # Check if under limit
        if len(client_requests) >= self.max_requests:
            return False
        
        # Add current request
        client_requests.append(now)
        return True

# Security headers middleware
class SecurityHeaders:
    @staticmethod
    def add_security_headers(response):
        """Add security headers to response"""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

# Request validation
class RequestValidator:
    @staticmethod
    def validate_mcp_request(request_data: dict) -> bool:
        """Validate MCP request structure"""
        if not isinstance(request_data, dict):
            return False
        
        # Check required fields
        if "method" not in request_data or "params" not in request_data:
            return False
        
        # Validate method name (prevent injection)
        method = request_data["method"]
        if not isinstance(method, str) or not method.replace("_", "").isalnum():
            return False
        
        # Validate params
        params = request_data["params"]
        if not isinstance(params, dict):
            return False
        
        return True
    
    @staticmethod
    def sanitize_instance_id(instance_id: str) -> Optional[str]:
        """Sanitize and validate instance ID"""
        if not isinstance(instance_id, str):
            return None
        
        # AWS instance ID pattern: i-[0-9a-f]{8,17}
        import re
        if re.match(r'^i-[0-9a-f]{8,17}$', instance_id):
            return instance_id
        
        return None

# Audit logging
class AuditLogger:
    def __init__(self):
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        import logging
        logger = logging.getLogger("sre_ops_audit")
        logger.setLevel(logging.INFO)
        
        # CloudWatch handler would be added here in production
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def log_request(self, client_ip: str, method: str, params: dict, success: bool):
        """Log API request for audit purposes"""
        self.logger.info(json.dumps({
            "event": "api_request",
            "client_ip": client_ip,
            "method": method,
            "params_hash": hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()[:16],
            "success": success,
            "timestamp": time.time()
        }))
    
    def log_security_event(self, event_type: str, client_ip: str, details: dict):
        """Log security events"""
        self.logger.warning(json.dumps({
            "event": "security_event",
            "type": event_type,
            "client_ip": client_ip,
            "details": details,
            "timestamp": time.time()
        }))