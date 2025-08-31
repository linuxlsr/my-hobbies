#!/usr/bin/env python3
import os

# Files to remove - temporary and fix scripts
files_to_remove = [
    'read_networking.py',       # Temporary script
    'placeholder.py',           # Temporary file
    'placeholder.zip',          # Temporary file
    'patch_executor.zip',       # Old zip file
    'check_resources.sh',       # Temporary script
    'remove_duplicates.txt',    # Temporary file
    'tfplan',                   # Old plan file
    'fix_drift.tf',             # Fix script
    'fix_https_certificate.tf', # Fix script
    'fix_state_drift.tf',       # Fix script
    'disable_http_service.tf',  # Comment-only file
    'vpc_data.tf',              # Comment-only file
    'alb_https_rule.tf',        # Comment-only file
    'ssl_only.tf'               # Temporary file
]

# Remove files
for file in files_to_remove:
    if os.path.exists(file):
        os.remove(file)
        print(f"✅ Removed {file}")
    else:
        print(f"ℹ️  {file} not found")

print("\n🧹 Infrastructure cleanup complete!")
print("📁 Kept essential terraform files only")