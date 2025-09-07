#!/bin/bash

# Deploy BRS Backend Application to AWS Free Tier Infrastructure

set -e  # Exit on any error

# Configuration
REGION="${1:-us-east-1}"
FORCE="${2:-false}"
PROJECT_NAME="brs"
REPOSITORY_NAME="${PROJECT_NAME}-backend-free"
IMAGE_TAG="latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
write_log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

write_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" >&2
}

write_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

# Help function
show_help() {
    echo "Usage: $0 [REGION] [FORCE]"
    echo ""
    echo "Deploy BRS Backend Application to AWS Free Tier Infrastructure"
    echo ""
    echo "Arguments:"
    echo "  REGION    AWS region (default: us-east-1)"
    echo "  FORCE     Force rebuild image (true/false, default: false)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Deploy to us-east-1, skip build if image exists"
    echo "  $0 us-west-2          # Deploy to us-west-2"
    echo "  $0 us-east-1 true     # Force rebuild and deploy"
    echo ""
    echo "Prerequisites:"
    echo "  - AWS CLI installed and configured"
    echo "  - Docker installed and running"
    echo "  - SSH key configured at ~/.ssh/brs-key"
    echo "  - Terraform infrastructure deployed"
}

# Check for help
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_help
    exit 0
fi

# Validate prerequisites
write_log "Checking prerequisites..."

if ! command -v aws &> /dev/null; then
    write_error "AWS CLI not found. Please install AWS CLI."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    write_error "Docker not found. Please install Docker."
    exit 1
fi

if ! command -v terraform &> /dev/null; then
    write_error "Terraform not found. Please install Terraform."
    exit 1
fi

if [[ ! -f ~/.ssh/brs-key ]]; then
    write_error "SSH key not found at ~/.ssh/brs-key"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    write_error "Docker is not running. Please start Docker."
    exit 1
fi

# Get account ID and ECR repository URL
write_log "Getting AWS account information..."

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null) || {
    write_error "Failed to get AWS account information. Check your AWS credentials."
    exit 1
}

ECR_URL="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPOSITORY_NAME}"
write_log "Account ID: ${ACCOUNT_ID}"
write_log "ECR Repository: ${ECR_URL}"

# Check if image already exists (unless force rebuild)
SKIP_BUILD=false
if [[ "$FORCE" != "true" ]]; then
    write_log "Checking if image already exists..."
    
    if aws ecr describe-images --repository-name "$REPOSITORY_NAME" --region "$REGION" --query 'imageDetails[?imageTag!=null]' --output json &> /dev/null; then
        IMAGES=$(aws ecr describe-images --repository-name "$REPOSITORY_NAME" --region "$REGION" --query 'imageDetails[?imageTag!=null]' --output json)
        IMAGE_COUNT=$(echo "$IMAGES" | jq length)
        
        if [[ "$IMAGE_COUNT" -gt 0 ]]; then
            write_log "Image already exists in ECR. Use 'force' parameter to rebuild."
            SKIP_BUILD=true
        else
            write_log "No images found in ECR. Building new image."
        fi
    else
        write_log "Repository empty or error checking. Building new image."
    fi
else
    write_log "Force rebuild requested."
fi

# Build and push Docker image
if [[ "$SKIP_BUILD" != "true" ]]; then
    write_log "Building Docker image..."
    IMAGE_NAME="${ECR_URL}:${IMAGE_TAG}"
    
    if ! docker build -t "$IMAGE_NAME" .; then
        write_error "Docker build failed"
        exit 1
    fi
    write_log "Docker image built successfully"

    write_log "Logging into ECR..."
    if ! aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$ECR_URL"; then
        write_error "ECR login failed"
        exit 1
    fi
    write_log "ECR login successful"

    write_log "Pushing image to ECR..."
    if ! docker push "$IMAGE_NAME"; then
        write_error "Docker push failed"
        exit 1
    fi
    write_log "Image pushed successfully to ECR"
fi

# Get EC2 instance IP
write_log "Getting EC2 instance information..."

if [[ ! -d "terraform/free-tier" ]]; then
    write_error "Terraform directory not found. Please ensure you're in the project root."
    exit 1
fi

cd terraform/free-tier
ELASTIC_IP=$(terraform output -raw elastic_ip 2>/dev/null) || {
    write_error "Failed to get EC2 instance IP from Terraform output"
    cd ../..
    exit 1
}
cd ../..

write_log "EC2 Instance IP: ${ELASTIC_IP}"

# Deploy to EC2 instance
write_log "Deploying application to EC2 instance..."
if ! ssh -i ~/.ssh/brs-key -o StrictHostKeyChecking=no -o ConnectTimeout=30 ec2-user@"$ELASTIC_IP" "sudo /opt/brs-backend/deploy.sh"; then
    write_error "Deployment script failed"
    write_log "Check the application logs on the EC2 instance:"
    write_log "  ssh -i ~/.ssh/brs-key ec2-user@${ELASTIC_IP}"
    write_log "  sudo journalctl -u brs-backend -f"
    exit 1
fi
write_log "Application deployed successfully"

# Test deployment
write_log "Testing deployment..."
sleep 10

HEALTH_URL="http://${ELASTIC_IP}/health"
write_log "Testing health endpoint..."

if curl -f -s -m 30 "$HEALTH_URL" > /dev/null; then
    RESPONSE=$(curl -s -m 30 "$HEALTH_URL")
    write_log "Health check passed! Application is running."
    echo "$RESPONSE"
    write_log "Application URL: http://${ELASTIC_IP}"
    write_log "API Documentation: http://${ELASTIC_IP}/docs"
else
    write_error "Health check failed"
    write_log "Check the application logs on the EC2 instance:"
    write_log "  ssh -i ~/.ssh/brs-key ec2-user@${ELASTIC_IP}"
    write_log "  sudo journalctl -u brs-backend -f"
    write_log "  docker logs brs-backend"
    exit 1
fi

write_log "Deployment process completed!"

# Summary
echo ""
write_log "=== DEPLOYMENT SUMMARY ==="
write_log "Region: ${REGION}"
write_log "Repository: ${REPOSITORY_NAME}"
write_log "Image: ${IMAGE_TAG}"
write_log "Instance IP: ${ELASTIC_IP}"
write_log "Application: http://${ELASTIC_IP}"
write_log "API Docs: http://${ELASTIC_IP}/docs"
echo ""
