#!/usr/bin/env python3
"""Natural Language Parser for SRE CLI"""

import re
from typing import Dict, List, Optional, Tuple

class NLPParser:
    """Parse natural language commands into structured actions"""
    
    def __init__(self):
        # Instance ID patterns
        self.instance_patterns = [
            r'i-[a-f0-9]{8,17}',  # Standard EC2 instance ID
            r'instance[:\s]+([i-][a-f0-9]{8,17})',
            r'server[:\s]+([i-][a-f0-9]{8,17})'
        ]
        
        # Command patterns with keywords
        self.command_patterns = {
            'vulnerabilities': [
                r'vulnerabilit(y|ies)', r'vuln', r'security issues?', r'cve', r'inspect'
            ],
            'cloudwatch_metrics': [
                r'metrics?', r'cloudwatch', r'cpu', r'memory', r'network', r'performance', r'monitoring'
            ],
            'cloudtrail_events': [
                r'cloudtrail', r'events?', r'logs?', r'audit', r'trail', r'api calls?'
            ],
            'security_events': [
                r'security events?', r'suspicious', r'alerts?', r'threats?', r'intrusion'
            ],
            'config_changes': [
                r'config', r'configuration', r'changes?', r'drift', r'compliance'
            ],
            'patch_status': [
                r'patch', r'patching', r'updates?', r'compliance'
            ]
        }
        
        # Time range patterns
        self.time_patterns = {
            r'(\d+)\s*h(our)?s?': lambda m: f"{m.group(1)}h",
            r'(\d+)\s*d(ay)?s?': lambda m: f"{m.group(1)}d",
            r'last\s*(\d+)\s*h(our)?s?': lambda m: f"{m.group(1)}h",
            r'past\s*(\d+)\s*d(ay)?s?': lambda m: f"{m.group(1)}d",
            r'today': lambda m: "24h",
            r'yesterday': lambda m: "48h",
            r'week': lambda m: "7d"
        }
    
    def extract_instance_ids(self, text: str) -> List[str]:
        """Extract EC2 instance IDs from text"""
        instances = []
        text_lower = text.lower()
        
        # Direct instance ID patterns
        for pattern in self.instance_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            instances.extend(matches)
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(instances))
    
    def extract_time_range(self, text: str) -> str:
        """Extract time range from text"""
        text_lower = text.lower()
        
        for pattern, converter in self.time_patterns.items():
            match = re.search(pattern, text_lower)
            if match:
                return converter(match)
        
        return "24h"  # Default
    
    def identify_command(self, text: str) -> Optional[str]:
        """Identify the command type from natural language"""
        text_lower = text.lower()
        
        # Score each command type
        scores = {}
        for command, keywords in self.command_patterns.items():
            score = 0
            for keyword in keywords:
                if re.search(keyword, text_lower):
                    score += 1
            if score > 0:
                scores[command] = score
        
        # Return command with highest score
        if scores:
            return max(scores, key=scores.get)
        
        return None
    
    def parse_command(self, text: str) -> Dict:
        """Parse natural language into structured command"""
        result = {
            'command': None,
            'instance_ids': [],
            'time_range': '24h',
            'confidence': 0.0,
            'original_text': text
        }
        
        # Extract components
        result['instance_ids'] = self.extract_instance_ids(text)
        result['time_range'] = self.extract_time_range(text)
        result['command'] = self.identify_command(text)
        
        # Calculate confidence
        confidence = 0.0
        if result['command']:
            confidence += 0.5
        if result['instance_ids']:
            confidence += 0.4
        if 'last' in text.lower() or 'past' in text.lower() or any(t in text.lower() for t in ['hour', 'day', 'week']):
            confidence += 0.1
        
        result['confidence'] = min(confidence, 1.0)
        
        return result
    
    def suggest_corrections(self, text: str) -> List[str]:
        """Suggest corrections for unclear commands"""
        suggestions = []
        
        # Check if instance ID is missing
        if not self.extract_instance_ids(text):
            suggestions.append("Add an instance ID (e.g., i-1234567890abcdef0)")
        
        # Check if command is unclear
        if not self.identify_command(text):
            suggestions.append("Be more specific about what you want to do (vulnerabilities, metrics, events, etc.)")
        
        return suggestions

def test_parser():
    """Test the NLP parser"""
    parser = NLPParser()
    
    test_cases = [
        "check vulnerabilities for i-00f20fbd7c0075d1d",
        "show me metrics for i-123456789 last 2 hours",
        "analyze security events on i-abc123def456 past 24 hours",
        "get cloudtrail logs for server i-999888777 today",
        "vuln scan i-00f20fbd7c0075d1d",
        "cpu metrics i-123 last week",
        "config changes yesterday i-456",
        "patch status for i-789"
    ]
    
    for test in test_cases:
        result = parser.parse_command(test)
        print(f"Input: {test}")
        print(f"  Command: {result['command']}")
        print(f"  Instances: {result['instance_ids']}")
        print(f"  Time: {result['time_range']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        print()

if __name__ == "__main__":
    test_parser()