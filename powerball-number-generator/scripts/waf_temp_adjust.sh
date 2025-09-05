#!/bin/bash
set -e

echo "🛡️ Temporarily adjusting WAF for load testing"

AWS_REGION="us-west-2"

# Get WAF ACL ID
WAF_ID=$(aws wafv2 list-web-acls --scope REGIONAL --region $AWS_REGION --query 'WebACLs[?Name==`powerball-waf`].Id' --output text)

if [ -z "$WAF_ID" ]; then
    echo "❌ WAF not found"
    exit 1
fi

echo "📋 Current WAF configuration:"
aws wafv2 get-web-acl --scope REGIONAL --id $WAF_ID --region $AWS_REGION --query 'WebACL.Rules[?Name==`RateLimitRule`].Statement.RateBasedStatement.Limit' --output text

echo ""
echo "🔧 To temporarily increase rate limit for testing:"
echo "1. Go to AWS Console > WAF & Shield"
echo "2. Edit 'powerball-waf' > Rules"
echo "3. Edit 'RateLimitRule'"
echo "4. Change limit from 2000 to 10000 (temporary)"
echo "5. Run load test"
echo "6. Change back to 2000 when done"
echo ""
echo "⚠️  REMEMBER: Change it back after testing!"