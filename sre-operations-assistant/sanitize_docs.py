#!/usr/bin/env python3
"""Sanitize documentation files to remove sensitive information"""

import os
import re

# Sensitive data patterns and their replacements
REPLACEMENTS = {
    # Domain names
    r'threemoonsnetwork\.net': 'your-domain.com',
    r'sre-ops\.threemoonsnetwork\.net': 'sre-ops.your-domain.com',
    
    # AWS Account ID
    r'303655880964': 'YOUR-AWS-ACCOUNT-ID',
    
    # Instance IDs and names
    r'centos-db': 'your-instance-name',
    r'i-[0-9a-f]{17}': 'i-1234567890abcdef0',
    
    # Security Group IDs
    r'sg-[0-9a-f]{17}': 'sg-xxxxxxxxxxxxxxxxx',
    
    # Subnet IDs
    r'subnet-[0-9a-f]{17}': 'subnet-xxxxxxxxxxxxxxxxx',
    
    # VPC IDs
    r'vpc-[0-9a-f]{8,17}': 'vpc-xxxxxxxxx',
    
    # Load Balancer ARNs
    r'arn:aws:elasticloadbalancing:us-west-2:303655880964:loadbalancer/app/sre-ops-assistant-alb/[a-f0-9]+': 'arn:aws:elasticloadbalancing:REGION:YOUR-AWS-ACCOUNT-ID:loadbalancer/app/sre-ops-assistant-alb/LOAD-BALANCER-ID',
    
    # Target Group ARNs
    r'arn:aws:elasticloadbalancing:us-west-2:303655880964:targetgroup/[^/]+/[a-f0-9]+': 'arn:aws:elasticloadbalancing:REGION:YOUR-AWS-ACCOUNT-ID:targetgroup/TARGET-GROUP-NAME/TARGET-GROUP-ID',
    
    # Certificate ARNs
    r'arn:aws:acm:us-west-2:303655880964:certificate/[a-f0-9-]+': 'arn:aws:acm:REGION:YOUR-AWS-ACCOUNT-ID:certificate/CERTIFICATE-ID',
    
    # Route53 Zone IDs
    r'Z3BX20QXDZNSN2': 'YOUR-HOSTED-ZONE-ID',
    
    # API Gateway IDs
    r'316kvw7woh': 'YOUR-API-GATEWAY-ID',
    
    # IP Addresses (private ranges)
    r'10\.0\.[0-9]+\.[0-9]+': '10.0.X.X',
    r'44\.239\.217\.186': 'X.X.X.X',
    r'52\.39\.2\.174': 'X.X.X.X',
    
    # Specific resource names that might be sensitive
    r'sre-ops-assistant-alb-942046254': 'sre-ops-assistant-alb-RANDOM-ID',
    r'DeckynScaling': 'your-sns-topic',
    r'cost-monitoring': 'your-cost-topic',
    r'dynamodb': 'your-dynamodb-topic',
}

def sanitize_file(file_path):
    """Sanitize a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply all replacements
        for pattern, replacement in REPLACEMENTS.items():
            content = re.sub(pattern, replacement, content)
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Sanitized {file_path}")
            return True
        else:
            print(f"ℹ️  No changes needed in {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Sanitize all documentation files"""
    print("🧹 Sanitizing documentation files...")
    print("=" * 50)
    
    # Files to sanitize
    files_to_sanitize = [
        'README.md',
        'docs/TROUBLESHOOTING.md',
        'docs/ARCHITECTURE.md',
        'docs/DEVELOPMENT.md'
    ]
    
    sanitized_count = 0
    
    for file_path in files_to_sanitize:
        if os.path.exists(file_path):
            if sanitize_file(file_path):
                sanitized_count += 1
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print("\n" + "=" * 50)
    print(f"📊 Sanitization complete: {sanitized_count} files modified")
    print("🔒 Sensitive information has been replaced with placeholders")
    
    if sanitized_count > 0:
        print("\n📝 Next steps:")
        print("1. Review the sanitized files")
        print("2. Update any remaining sensitive references")
        print("3. Commit the sanitized documentation")

if __name__ == "__main__":
    main()