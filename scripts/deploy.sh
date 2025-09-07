#!/bin/bash
set -e

# BRS Backend Deployment Script
# This script handles the complete deployment process

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
EKS_CLUSTER_NAME="${EKS_CLUSTER_NAME:-brs-cluster}"
ECR_REPOSITORY="${ECR_REPOSITORY:-brs-backend}"
NAMESPACE="brs-production"
IMAGE_TAG="${IMAGE_TAG:-latest}"

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
    
    local deps=("aws" "kubectl" "docker")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log_error "$dep is not installed or not in PATH"
            exit 1
        fi
    done
    
    log_success "All dependencies are available"
}

configure_kubectl() {
    log_info "Configuring kubectl for EKS cluster..."
    aws eks update-kubeconfig --region "$AWS_REGION" --name "$EKS_CLUSTER_NAME"
    log_success "kubectl configured successfully"
}

build_and_push_image() {
    local aws_account_id
    aws_account_id=$(aws sts get-caller-identity --query Account --output text)
    local ecr_registry="${aws_account_id}.dkr.ecr.${AWS_REGION}.amazonaws.com"
    
    log_info "Building Docker image..."
    docker build -t "${ECR_REPOSITORY}:${IMAGE_TAG}" .
    docker tag "${ECR_REPOSITORY}:${IMAGE_TAG}" "${ecr_registry}/${ECR_REPOSITORY}:${IMAGE_TAG}"
    docker tag "${ECR_REPOSITORY}:${IMAGE_TAG}" "${ecr_registry}/${ECR_REPOSITORY}:latest"
    
    log_info "Logging in to ECR..."
    aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ecr_registry"
    
    log_info "Pushing image to ECR..."
    docker push "${ecr_registry}/${ECR_REPOSITORY}:${IMAGE_TAG}"
    docker push "${ecr_registry}/${ECR_REPOSITORY}:latest"
    
    log_success "Image pushed successfully"
}

run_database_migration() {
    local aws_account_id
    aws_account_id=$(aws sts get-caller-identity --query Account --output text)
    
    log_info "Running database migration..."
    
    # Create a temporary migration job manifest
    cat > /tmp/migration-job.yaml << EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: brs-migration-$(date +%s)
  namespace: ${NAMESPACE}
  labels:
    app: brs-backend
    component: migration
    environment: production
spec:
  template:
    metadata:
      labels:
        app: brs-backend
        component: migration
        environment: production
    spec:
      serviceAccountName: brs-service-account
      restartPolicy: Never
      containers:
      - name: migration
        image: ${aws_account_id}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG}
        command: ["alembic", "upgrade", "head"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: brs-secrets
              key: database-url
        - name: ENVIRONMENT
          value: "production"
        - name: AWS_REGION
          value: "${AWS_REGION}"
        - name: AWS_SECRETS_MANAGER
          value: "true"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        securityContext:
          runAsNonRoot: true
          runAsUser: 1001
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: false
          capabilities:
            drop:
            - ALL
      securityContext:
        fsGroup: 1001
  backoffLimit: 3
  activeDeadlineSeconds: 600
EOF
    
    kubectl apply -f /tmp/migration-job.yaml
    
    # Wait for migration to complete
    local job_name
    job_name=$(kubectl get jobs -n "$NAMESPACE" --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}')
    kubectl wait --for=condition=complete --timeout=600s "job/$job_name" -n "$NAMESPACE"
    
    # Check if migration was successful
    if kubectl get job "$job_name" -n "$NAMESPACE" -o jsonpath='{.status.conditions[?(@.type=="Complete")].status}' | grep -q "True"; then
        log_success "Database migration completed successfully"
    else
        log_error "Database migration failed"
        kubectl logs "job/$job_name" -n "$NAMESPACE"
        exit 1
    fi
    
    # Cleanup
    rm -f /tmp/migration-job.yaml
}

deploy_application() {
    local aws_account_id
    aws_account_id=$(aws sts get-caller-identity --query Account --output text)
    
    log_info "Deploying application to Kubernetes..."
    
    # Create temporary directory for processed manifests
    local temp_dir="/tmp/k8s-processed-$(date +%s)"
    mkdir -p "$temp_dir"
    
    # Process manifests
    for file in k8s/*.yaml; do
        if [ -f "$file" ]; then
            local filename
            filename=$(basename "$file")
            sed "s|<AWS_ACCOUNT_ID>|${aws_account_id}|g; \
                 s|<REGION>|${AWS_REGION}|g; \
                 s|latest|${IMAGE_TAG}|g; \
                 s|ACCOUNT_ID|${aws_account_id}|g" \
                 "$file" > "$temp_dir/$filename"
        fi
    done
    
    # Apply manifests in order
    kubectl apply -f "$temp_dir/namespace.yaml"
    kubectl apply -f "$temp_dir/rbac.yaml"
    kubectl apply -f "$temp_dir/secrets.yaml"
    kubectl apply -f "$temp_dir/deployment.yaml"
    kubectl apply -f "$temp_dir/service.yaml"
    kubectl apply -f "$temp_dir/ingress.yaml"
    kubectl apply -f "$temp_dir/hpa.yaml"
    
    # Wait for deployment to be ready
    log_info "Waiting for deployment to be ready..."
    kubectl rollout status deployment/brs-backend -n "$NAMESPACE" --timeout=600s
    
    # Cleanup
    rm -rf "$temp_dir"
    
    log_success "Application deployed successfully"
}

verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check pod status
    log_info "Pod status:"
    kubectl get pods -n "$NAMESPACE" -l app=brs-backend
    
    # Check service
    log_info "Service status:"
    kubectl get svc brs-backend-service -n "$NAMESPACE"
    
    # Check ingress
    log_info "Ingress status:"
    kubectl get ingress brs-backend-ingress -n "$NAMESPACE"
    
    # Wait for pods to be ready
    kubectl wait --for=condition=ready pod -l app=brs-backend -n "$NAMESPACE" --timeout=300s
    
    log_success "Deployment verification completed"
}

show_access_info() {
    log_info "Getting access information..."
    
    local ingress_host
    ingress_host=$(kubectl get ingress brs-backend-ingress -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "Not ready yet")
    
    echo
    log_success "Deployment completed successfully!"
    echo "-----------------------------------"
    echo "Application Details:"
    echo "- Namespace: $NAMESPACE"
    echo "- Image: $ECR_REPOSITORY:$IMAGE_TAG"
    echo "- Load Balancer: $ingress_host"
    echo "- Health Check: https://api.brs.example.com/health"
    echo "- API Documentation: https://api.brs.example.com/docs"
    echo
    echo "Useful commands:"
    echo "- View pods: kubectl get pods -n $NAMESPACE"
    echo "- View logs: kubectl logs -f deployment/brs-backend -n $NAMESPACE"
    echo "- Scale deployment: kubectl scale deployment brs-backend --replicas=5 -n $NAMESPACE"
    echo "-----------------------------------"
}

# Main execution
main() {
    log_info "Starting BRS Backend deployment..."
    
    case "${1:-deploy}" in
        "build")
            check_dependencies
            build_and_push_image
            ;;
        "migrate")
            check_dependencies
            configure_kubectl
            run_database_migration
            ;;
        "deploy")
            check_dependencies
            configure_kubectl
            build_and_push_image
            run_database_migration
            deploy_application
            verify_deployment
            show_access_info
            ;;
        "verify")
            check_dependencies
            configure_kubectl
            verify_deployment
            show_access_info
            ;;
        *)
            echo "Usage: $0 [build|migrate|deploy|verify]"
            echo "  build   - Build and push Docker image"
            echo "  migrate - Run database migration only"
            echo "  deploy  - Full deployment (default)"
            echo "  verify  - Verify existing deployment"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"


