"""Bedrock Model Abstractions for Different Foundation Models"""

import json
import boto3
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class BedrockModelInterface(ABC):
    """Abstract interface for Bedrock foundation models"""
    
    @abstractmethod
    def generate_response(self, prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """Generate response from the model"""
        pass
    
    @abstractmethod
    def format_request_body(self, prompt: str, max_tokens: int) -> Dict[str, Any]:
        """Format request body for the specific model"""
        pass
    
    @abstractmethod
    def extract_response_text(self, response_body: Dict[str, Any]) -> str:
        """Extract text from model response"""
        pass


class TitanTextModel(BedrockModelInterface):
    """Amazon Titan Text Premier model implementation"""
    
    def __init__(self, model_id: str = "amazon.titan-text-premier-v1:0"):
        self.model_id = model_id
        self.bedrock = boto3.client('bedrock-runtime')
    
    def format_request_body(self, prompt: str, max_tokens: int) -> Dict[str, Any]:
        """Format request for Titan Text model"""
        return {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": max_tokens,
                "temperature": 0.1,
                "topP": 0.9,
                "stopSequences": []
            }
        }
    
    def extract_response_text(self, response_body: Dict[str, Any]) -> str:
        """Extract text from Titan response"""
        results = response_body.get('results', [])
        if results:
            return results[0].get('outputText', '')
        return ''
    
    def generate_response(self, prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """Generate response from Titan model"""
        try:
            body = self.format_request_body(prompt, max_tokens)
            
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            return self.extract_response_text(response_body)
            
        except Exception as e:
            print(f"Error calling Titan model: {e}")
            return None


class NovaModel(BedrockModelInterface):
    """Amazon Nova model implementation"""
    
    def __init__(self, model_id: str = "amazon.nova-micro-v1:0"):
        self.model_id = model_id
        self.bedrock = boto3.client('bedrock-runtime')
    
    def format_request_body(self, prompt: str, max_tokens: int) -> Dict[str, Any]:
        """Format request for Nova model"""
        return {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ],
            "inferenceConfig": {
                "max_new_tokens": max_tokens,
                "temperature": 0.1,
                "top_p": 0.9
            }
        }
    
    def extract_response_text(self, response_body: Dict[str, Any]) -> str:
        """Extract text from Nova response"""
        output = response_body.get('output', {})
        message = output.get('message', {})
        content = message.get('content', [])
        if content:
            return content[0].get('text', '')
        return ''
    
    def generate_response(self, prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """Generate response from Nova model"""
        try:
            body = self.format_request_body(prompt, max_tokens)
            
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            return self.extract_response_text(response_body)
            
        except Exception as e:
            print(f"Error calling Nova model: {e}")
            return None


class BedrockModelFactory:
    """Factory for creating appropriate Bedrock model instances"""
    
    @staticmethod
    def create_model(model_id: str) -> BedrockModelInterface:
        """Create model instance based on model ID"""
        if "titan" in model_id.lower():
            return TitanTextModel(model_id)
        elif "nova" in model_id.lower():
            return NovaModel(model_id)
        else:
            # Default to Titan
            return TitanTextModel(model_id)
    
    @staticmethod
    def get_available_models() -> Dict[str, str]:
        """Get list of available on-demand models"""
        return {
            "titan-text-premier": "amazon.titan-text-premier-v1:0",
            "titan-text-express": "amazon.titan-text-express-v1",
            "nova-micro": "amazon.nova-micro-v1:0",
            "nova-lite": "amazon.nova-lite-v1:0",
            "nova-pro": "amazon.nova-pro-v1:0"
        }