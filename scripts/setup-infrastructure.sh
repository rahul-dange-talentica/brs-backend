#!/bin/bash
set -e

# BRS Infrastructure Setup Script
# This script sets up the initial AWS infrastructure using Terraform

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-brs}"
TERRAFORM_STATE_BUCKET="${PROJECT_NAME}-terraform-state-bucket"
TERRAFORM_LOCKS_TABLE="${PROJECT_NAME}-terraform-locks"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    local deps=("aws" "terraform")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log_error "$dep is not installed or not in PATH"
            exit 1
        fi
    done
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured. Run 'aws configure' first."
        exit 1
    fi
    
    log_success "All dependencies are available"
}

create_terraform_backend() {
    log_info "Setting up Terraform backend..."
    
    # Check if S3 bucket exists
    if aws s3 ls "s3://$TERRAFORM_STATE_BUCKET" &> /dev/null; then
        log_warning "S3 bucket $TERRAFORM_STATE_BUCKET already exists"
    else
        log_info "Creating S3 bucket for Terraform state..."
        aws s3 mb "s3://$TERRAFORM_STATE_BUCKET" --region "$AWS_REGION"
        
        # Enable versioning
        aws s3api put-bucket-versioning \
            --bucket "$TERRAFORM_STATE_BUCKET" \
            --versioning-configuration Status=Enabled
        
        # Enable encryption
        aws s3api put-bucket-encryption \
            --bucket "$TERRAFORM_STATE_BUCKET" \
            --server-side-encryption-configuration '{
                "Rules": [
                    {
                        "ApplyServerSideEncryptionByDefault": {
                            "SSEAlgorithm": "AES256"
                        }
                    }
                ]
            }'
        
        log_success "S3 bucket created and configured"
    fi
    
    # Check if DynamoDB table exists
    if aws dynamodb describe-table --table-name "$TERRAFORM_LOCKS_TABLE" &> /dev/null; then
        log_warning "DynamoDB table $TERRAFORM_LOCKS_TABLE already exists"
    else
        log_info "Creating DynamoDB table for Terraform locks..."
        aws dynamodb create-table \
            --table-name "$TERRAFORM_LOCKS_TABLE" \
            --attribute-definitions AttributeName=LockID,AttributeType=S \
            --key-schema AttributeName=LockID,KeyType=HASH \
            --billing-mode PAY_PER_REQUEST \
            --region "$AWS_REGION"
        
        # Wait for table to be active
        aws dynamodb wait table-exists --table-name "$TERRAFORM_LOCKS_TABLE"
        log_success "DynamoDB table created"
    fi
}

setup_certificate() {
    log_info "Setting up SSL certificate..."
    
    local domain_name="${DOMAIN_NAME:-api.brs.example.com}"
    
    log_warning "SSL Certificate Setup Required"
    echo "You need to create an SSL certificate in AWS Certificate Manager (ACM)"
    echo "1. Go to AWS Console -> Certificate Manager"
    echo "2. Request a public certificate for: $domain_name"
    echo "3. Complete domain validation"
    echo "4. Copy the certificate ARN"
    echo
    echo "Example ARN: arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012"
    echo
    read -p "Enter your certificate ARN (or press Enter to skip): " CERT_ARN
    
    if [ -n "$CERT_ARN" ]; then
        echo "export CERTIFICATE_ARN=\"$CERT_ARN\"" >> .env.terraform
        log_success "Certificate ARN saved to .env.terraform"
    else
        log_warning "Certificate ARN not provided. You'll need to provide it during Terraform apply."
    fi
}

initialize_terraform() {
    log_info "Initializing Terraform..."
    
    cd terraform
    
    # Update backend configuration
    cat > backend.tf << EOF
terraform {
  backend "s3" {
    bucket = "$TERRAFORM_STATE_BUCKET"
    key    = "production/terraform.tfstate"
    region = "$AWS_REGION"
    
    dynamodb_table = "$TERRAFORM_LOCKS_TABLE"
    encrypt        = true
  }
}
EOF
    
    # Initialize Terraform
    terraform init
    
    # Validate configuration
    terraform validate
    
    log_success "Terraform initialized successfully"
    
    cd ..
}

plan_infrastructure() {
    log_info "Planning infrastructure deployment..."
    
    cd terraform
    
    # Source environment variables if available
    if [ -f "../.env.terraform" ]; then
        source ../.env.terraform
    fi
    
    # Create terraform.tfvars file
    cat > terraform.tfvars << EOF
aws_region = "$AWS_REGION"
project_name = "$PROJECT_NAME"
environment = "production"
certificate_arn = "${CERTIFICATE_ARN:-}"
domain_name = "${DOMAIN_NAME:-api.brs.example.com}"
EOF
    
    # Run terraform plan
    terraform plan -var-file="terraform.tfvars"
    
    cd ..
    
    log_success "Infrastructure plan completed"
}

apply_infrastructure() {
    log_info "Applying infrastructure..."
    
    cd terraform
    
    # Apply with auto-approval after confirmation
    echo
    log_warning "This will create AWS resources that may incur charges."
    read -p "Do you want to continue? (yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
        terraform apply -var-file="terraform.tfvars" -auto-approve
        log_success "Infrastructure deployed successfully"
        
        # Display outputs
        echo
        log_info "Infrastructure outputs:"
        terraform output
        
        # Save important outputs
        local cluster_name
        local ecr_url
        cluster_name=$(terraform output -raw cluster_name)
        ecr_url=$(terraform output -raw ecr_repository_url)
        
        cat > ../infrastructure-info.txt << EOF
EKS Cluster: $cluster_name
ECR Repository: $ecr_url
AWS Region: $AWS_REGION

Configure kubectl:
aws eks update-kubeconfig --region $AWS_REGION --name $cluster_name

ECR Login:
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ecr_url
EOF
        
        log_success "Infrastructure information saved to infrastructure-info.txt"
    else
        log_info "Infrastructure deployment cancelled"
    fi
    
    cd ..
}

show_next_steps() {
    echo
    log_success "Infrastructure setup completed!"
    echo "-----------------------------------"
    echo "Next steps:"
    echo "1. Configure kubectl:"
    echo "   aws eks update-kubeconfig --region $AWS_REGION --name brs-cluster"
    echo
    echo "2. Build and deploy application:"
    echo "   ./scripts/deploy.sh deploy"
    echo
    echo "3. Set up CI/CD:"
    echo "   - Add AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY to GitHub secrets"
    echo "   - Push to main branch to trigger deployment"
    echo
    echo "4. Configure domain:"
    echo "   - Point your domain to the ALB endpoint"
    echo "   - Update DNS records"
    echo
    echo "Files created:"
    echo "- terraform/backend.tf"
    echo "- terraform/terraform.tfvars"
    echo "- infrastructure-info.txt"
    echo "- .env.terraform (if certificate ARN was provided)"
    echo "-----------------------------------"
}

# Main execution
main() {
    log_info "Starting BRS infrastructure setup..."
    
    case "${1:-setup}" in
        "backend")
            check_dependencies
            create_terraform_backend
            ;;
        "init")
            check_dependencies
            initialize_terraform
            ;;
        "plan")
            check_dependencies
            plan_infrastructure
            ;;
        "apply")
            check_dependencies
            apply_infrastructure
            show_next_steps
            ;;
        "setup")
            check_dependencies
            create_terraform_backend
            setup_certificate
            initialize_terraform
            plan_infrastructure
            
            echo
            log_info "Infrastructure is ready to deploy."
            read -p "Do you want to deploy now? (yes/no): " deploy_now
            
            if [ "$deploy_now" = "yes" ]; then
                apply_infrastructure
                show_next_steps
            else
                echo
                log_info "To deploy later, run: $0 apply"
                show_next_steps
            fi
            ;;
        *)
            echo "Usage: $0 [backend|init|plan|apply|setup]"
            echo "  backend - Create S3 bucket and DynamoDB table only"
            echo "  init    - Initialize Terraform only"
            echo "  plan    - Plan infrastructure changes"
            echo "  apply   - Apply infrastructure changes"
            echo "  setup   - Full setup process (default)"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"


