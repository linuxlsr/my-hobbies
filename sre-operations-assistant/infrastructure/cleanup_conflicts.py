#!/usr/bin/env python3
"""Clean up terraform conflicts and duplicates"""

import os

# Files to remove that are causing conflicts
files_to_remove = [
    'remove_http.tf',              # Temporary file
    'security_hardening.tf',       # Causing many new resources
    'security_monitoring.tf',      # Causing conflicts with SNS topics
    'iam_hardening.tf',           # Adding duplicate IAM resources
    'ssl_certificate.tf',         # Duplicate certificate resources
    'secrets.tf',                 # Duplicate secrets
    'route53_data.tf',            # May be conflicting
]

def main():
    print("🧹 Cleaning up terraform conflicts...")
    
    removed_count = 0
    
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
            print(f"✅ Removed {file}")
            removed_count += 1
        else:
            print(f"ℹ️  {file} not found")
    
    print(f"\n📊 Cleanup complete: {removed_count} files removed")
    print("🔄 Run 'terraform plan' to see clean state")

if __name__ == "__main__":
    main()