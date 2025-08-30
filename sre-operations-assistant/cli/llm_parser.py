#!/usr/bin/env python3
"""LLM-powered Natural Language Parser for SRE CLI"""

import json
import boto3
from typing import Dict, Any, Optional

class LLMParser:
    """Use AWS Bedrock to parse natural language commands"""
    
    def __init__(self):
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-west-2')
        self.model_id = "amazon.titan-text-express-v1"
    
    def parse_command(self, user_input: str) -> Dict[str, Any]:
        """Parse natural language using Titan"""
        
        prompt = f"""Parse command: "{user_input}"

Return JSON only:

For "scan all" or "all vulns" return: {{"command": "scan_all", "instance_ids": [], "time_range": "24h", "confidence": 0.9}}
For vulnerabilities return: {{"command": "vulnerabilities", "instance_ids": ["i-123"], "time_range": "24h", "confidence": 0.9}}
For metrics return: {{"command": "cloudwatch_metrics", "instance_ids": ["i-123"], "time_range": "24h", "confidence": 0.9}}

JSON:"""

        try:
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": 100,
                        "temperature": 0.0,
                        "topP": 0.1
                    }
                })
            )
            
            result = json.loads(response['body'].read())
            content = result['results'][0]['outputText'].strip()
            
            # Clean up response
            content = content.replace('```json', '').replace('```', '').replace('JSON:', '').strip()
            
            # Find JSON
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_content = content[json_start:json_end]
                parsed = json.loads(json_content)
                
                return {
                    "command": parsed.get("command"),
                    "instance_ids": parsed.get("instance_ids", []),
                    "time_range": parsed.get("time_range", "24h"),
                    "confidence": parsed.get("confidence", 0.8),
                    "original_text": user_input,
                    "method": "llm"
                }
            else:
                # Try to parse the text response directly
                if "scan_all" in content.lower():
                    return {
                        "command": "scan_all",
                        "instance_ids": [],
                        "time_range": "24h",
                        "confidence": 0.8,
                        "original_text": user_input,
                        "method": "llm"
                    }
                raise ValueError(f"No JSON in response: {content}")
                
        except Exception as e:
            # LLM failed, using fallback
            return self._fallback_parse(user_input, str(e))
    
    def _fallback_parse(self, text: str, error: str) -> Dict[str, Any]:
        """Fallback regex parsing if LLM fails"""
        import re
        
        # Basic regex fallback
        instance_match = re.search(r'i-[a-f0-9]{8,17}', text)
        instance_ids = [instance_match.group(0)] if instance_match else []
        
        # Simple command detection
        text_lower = text.lower()
        if any(phrase in text_lower for phrase in ['scan all', 'scan everything', 'check all']):
            command = 'scan_all'
        elif any(word in text_lower for word in ['vuln', 'security', 'cve']) and 'all' not in text_lower:
            command = 'vulnerabilities'
        elif any(word in text_lower for word in ['cpu', 'metrics', 'performance']):
            command = 'cloudwatch_metrics'
        elif any(word in text_lower for word in ['events', 'cloudtrail', 'audit']):
            command = 'cloudtrail_events'
        else:
            command = None
        
        # If command detected but no instance ID, suggest higher confidence for prompting
        confidence = 0.6 if command and not instance_ids else 0.3 if command else 0.1
        
        # scan_all doesn't need instance IDs
        needs_instance_id = command is not None and not instance_ids and command != 'scan_all'
        
        return {
            "command": command,
            "instance_ids": instance_ids,
            "time_range": "24h",
            "confidence": confidence,
            "original_text": text,
            "method": "fallback",
            "llm_error": error,
            "needs_instance_id": needs_instance_id
        }

def test_llm_parser():
    """Test the LLM parser"""
    parser = LLMParser()
    
    test_cases = [
        "check vulnerabilities for i-00f20fbd7c0075d1d",
        "show me cpu metrics for i-123456789 over the last 2 hours",
        "analyze security events on server i-abc123def456 from yesterday",
        "what changed on i-999888777 in the past week?"
    ]
    
    for test in test_cases:
        print(f"Input: {test}")
        result = parser.parse_command(test)
        print(f"  Command: {result['command']}")
        print(f"  Instances: {result['instance_ids']}")
        print(f"  Time: {result['time_range']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Method: {result['method']}")
        print()

if __name__ == "__main__":
    test_llm_parser()