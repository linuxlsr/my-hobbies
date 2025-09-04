#!/bin/bash
set -e

echo "🧨 Tearing down PowerballAI AWS infrastructure"

cd ../terraform

echo "1. Destroying all Terraform resources..."
terraform destroy -auto-approve

echo "2. Cleaning up any remaining ECR images..."
ECR_REPO_NAME="powerball"
aws ecr describe-repositories --repository-names $ECR_REPO_NAME --region us-west-2 >/dev/null 2>&1 && {
    echo "Deleting ECR images..."
    aws ecr batch-delete-image \
        --repository-name $ECR_REPO_NAME \
        --image-ids imageTag=latest imageTag=debug imageTag=minimal \
        --region us-west-2 || echo "No images to delete"
    
    echo "Deleting ECR repository..."
    aws ecr delete-repository \
        --repository-name $ECR_REPO_NAME \
        --force \
        --region us-west-2 || echo "Repository already deleted"
} || echo "ECR repository doesn't exist"

echo "3. Cleaning up any orphaned resources..."
# Clean up any stuck ECS tasks
aws ecs list-clusters --region us-west-2 --query 'clusterArns[?contains(@, `powerball`)]' --output text | while read CLUSTER_ARN; do
    if [ -n "$CLUSTER_ARN" ]; then
        echo "Cleaning cluster: $CLUSTER_ARN"
        aws ecs list-tasks --cluster $CLUSTER_ARN --region us-west-2 --query 'taskArns' --output text | while read TASK_ARN; do
            if [ -n "$TASK_ARN" ]; then
                aws ecs stop-task --cluster $CLUSTER_ARN --task $TASK_ARN --region us-west-2 || true
            fi
        done
    fi
done

# Clean up log groups
aws logs describe-log-groups --log-group-name-prefix "/ecs/powerball" --region us-west-2 --query 'logGroups[*].logGroupName' --output text | while read LOG_GROUP; do
    if [ -n "$LOG_GROUP" ]; then
        echo "Deleting log group: $LOG_GROUP"
        aws logs delete-log-group --log-group-name "$LOG_GROUP" --region us-west-2 || true
    fi
done

echo "✅ Teardown complete!"
echo ""
echo "If VPC destruction timed out, run: bash scripts/force_cleanup.sh"
echo ""
echo "All AWS resources destroyed:"
echo "- ECS cluster and services"
echo "- Load balancer and target groups"  
echo "- VPC and networking"
echo "- ECR repository and images"
echo "- IAM roles and policies"
echo "- Route53 records"
echo "- SSL certificates"
echo "- CloudWatch logs"