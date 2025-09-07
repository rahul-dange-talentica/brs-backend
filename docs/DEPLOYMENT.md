# BRS Backend - Production Deployment Guide

This document provides comprehensive instructions for deploying the Book Review System (BRS) backend to AWS production environment using Docker, Kubernetes (EKS), and Terraform.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Initial Deployment](#initial-deployment)
4. [CI/CD Pipeline](#cicd-pipeline)
5. [Database Management](#database-management)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)
7. [Troubleshooting](#troubleshooting)
8. [Security Considerations](#security-considerations)

## Prerequisites

### Required Tools

Install the following tools on your local machine:

```bash
# AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Terraform
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

### AWS Prerequisites

1. **AWS Account**: Access to an AWS account with appropriate permissions
2. **IAM User**: Create an IAM user with the following policies:
   - `AmazonEKSClusterPolicy`
   - `AmazonEKSWorkerNodePolicy`
   - `AmazonEKS_CNI_Policy`
   - `AmazonEC2ContainerRegistryFullAccess`
   - `AmazonRDSFullAccess`
   - `SecretsManagerReadWrite`
   - `AmazonVPCFullAccess`

3. **AWS Credentials**: Configure AWS credentials
```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and preferred region
```

4. **Domain Name**: A registered domain name for SSL/TLS certificates
5. **SSL Certificate**: Create an ACM certificate for your domain

## Infrastructure Setup

### 1. Terraform State Backend

Create an S3 bucket and DynamoDB table for Terraform state management:

```bash
# Create S3 bucket for Terraform state
aws s3 mb s3://brs-terraform-state-bucket --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket brs-terraform-state-bucket \
    --versioning-configuration Status=Enabled

# Create DynamoDB table for state locking
aws dynamodb create-table \
    --table-name brs-terraform-locks \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --region us-east-1
```

### 2. Update Terraform Configuration

Edit `terraform/versions.tf` to use your actual S3 bucket:

```hcl
terraform {
  backend "s3" {
    bucket = "your-actual-terraform-state-bucket"
    key    = "production/terraform.tfstate"
    region = "us-east-1"
    
    dynamodb_table = "your-actual-terraform-locks"
    encrypt        = true
  }
}
```

### 3. Deploy Infrastructure

```bash
cd terraform

# Initialize Terraform
terraform init

# Plan the infrastructure
terraform plan -var="certificate_arn=arn:aws:acm:us-east-1:ACCOUNT:certificate/CERT-ID"

# Apply the infrastructure
terraform apply -var="certificate_arn=arn:aws:acm:us-east-1:ACCOUNT:certificate/CERT-ID"
```

**Note**: Replace `ACCOUNT` and `CERT-ID` with your actual AWS account ID and certificate ID.

## Initial Deployment

### 1. Configure kubectl

```bash
# Get cluster name and region from Terraform output
aws eks update-kubeconfig --region us-east-1 --name brs-cluster
```

### 2. Update Kubernetes Manifests

Update the placeholders in Kubernetes manifests with actual values:

```bash
# Get your AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION="us-east-1"

# Update deployment manifest
sed -i "s|<AWS_ACCOUNT_ID>|${AWS_ACCOUNT_ID}|g" k8s/deployment.yaml
sed -i "s|<REGION>|${AWS_REGION}|g" k8s/deployment.yaml

# Update RBAC manifest
sed -i "s|ACCOUNT_ID|${AWS_ACCOUNT_ID}|g" k8s/rbac.yaml
```

### 3. Build and Push Initial Image

```bash
# Build the Docker image
docker build -t brs-backend:latest .

# Tag for ECR
docker tag brs-backend:latest ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/brs-backend:latest

# Login to ECR
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Push to ECR
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/brs-backend:latest
```

### 4. Deploy Application

```bash
# Apply Kubernetes manifests in order
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/secrets.yaml

# Run database migration
kubectl apply -f k8s/migration-job.yaml
kubectl wait --for=condition=complete --timeout=600s job/brs-migration -n brs-production

# Deploy application
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml

# Wait for deployment to be ready
kubectl rollout status deployment/brs-backend -n brs-production
```

### 5. Verify Deployment

```bash
# Check pods
kubectl get pods -n brs-production

# Check services
kubectl get svc -n brs-production

# Check ingress
kubectl get ingress -n brs-production

# Test health endpoint
kubectl port-forward svc/brs-backend-service 8080:80 -n brs-production &
curl http://localhost:8080/health
```

## CI/CD Pipeline

### GitHub Secrets Setup

Configure the following secrets in your GitHub repository:

1. **AWS_ACCESS_KEY_ID**: AWS access key for deployment
2. **AWS_SECRET_ACCESS_KEY**: AWS secret key for deployment

### Workflow Files

The following GitHub Actions workflows are configured:

- **CI Workflow** (`.github/workflows/ci.yml`): Runs on pull requests
  - Code linting and formatting
  - Unit and integration tests
  - Security scanning
  - Docker image build test

- **Deployment Workflow** (`.github/workflows/deploy.yml`): Runs on main branch
  - Full test suite
  - Docker image build and push to ECR
  - Database migration
  - Kubernetes deployment
  - Deployment verification

- **Infrastructure Workflow** (`.github/workflows/infrastructure.yml`): Manages Terraform
  - Infrastructure validation
  - Planning on pull requests
  - Apply on main branch merges

### Manual Deployment

Use the deployment script for manual deployments:

```bash
# Full deployment
./scripts/deploy.sh deploy

# Build and push image only
./scripts/deploy.sh build

# Run migration only
./scripts/deploy.sh migrate

# Verify deployment
./scripts/deploy.sh verify
```

## Database Management

### Migrations

Database migrations are handled by Alembic and deployed via Kubernetes jobs.

**Automatic Migration**: Runs as part of the deployment pipeline.

**Manual Migration**:
```bash
# Create a one-time migration job
kubectl create job --from=cronjob/brs-migration-cronjob migrate-$(date +%s) -n brs-production

# Monitor migration
kubectl logs job/migrate-$(date +%s) -n brs-production -f
```

### Backup Strategy

**Automated Backups**: RDS automatically creates daily backups with 7-day retention.

**Manual Backup**:
```bash
# Create snapshot
aws rds create-db-snapshot \
    --db-instance-identifier brs-database \
    --db-snapshot-identifier brs-manual-snapshot-$(date +%Y%m%d-%H%M%S)
```

**Restore from Backup**:
```bash
# List available snapshots
aws rds describe-db-snapshots --db-instance-identifier brs-database

# Restore from snapshot (creates new instance)
aws rds restore-db-instance-from-db-snapshot \
    --db-instance-identifier brs-database-restored \
    --db-snapshot-identifier snapshot-name
```

## Monitoring and Maintenance

### Health Checks

The application provides several health check endpoints:

- **Basic Health**: `/health`
- **Detailed Health**: `/api/v1/monitoring/health/detailed`
- **Metrics**: `/api/v1/monitoring/metrics`

### Scaling

**Manual Scaling**:
```bash
# Scale deployment
kubectl scale deployment brs-backend --replicas=5 -n brs-production

# Scale database (requires RDS modification)
aws rds modify-db-instance \
    --db-instance-identifier brs-database \
    --db-instance-class db.t3.small \
    --apply-immediately
```

**Auto Scaling**: Horizontal Pod Autoscaler (HPA) is configured to scale based on CPU and memory usage.

### Logs

**Application Logs**:
```bash
# View live logs
kubectl logs -f deployment/brs-backend -n brs-production

# View logs from specific pod
kubectl logs pod-name -n brs-production

# View logs from previous deployment
kubectl logs deployment/brs-backend -n brs-production --previous
```

**Infrastructure Logs**: Available in AWS CloudWatch.

### Updates

**Application Updates**: Handled automatically via CI/CD pipeline on main branch updates.

**Infrastructure Updates**: 
1. Update Terraform configuration
2. Create pull request for review
3. Merge to main branch for automatic apply

**Security Updates**:
```bash
# Update base image
docker build --no-cache -t brs-backend:security-update .

# Deploy with new image tag
kubectl set image deployment/brs-backend brs-backend=ECR_URL:security-update -n brs-production
```

## Troubleshooting

### Common Issues

**1. Pod Not Starting**
```bash
# Check pod status
kubectl describe pod pod-name -n brs-production

# Check logs
kubectl logs pod-name -n brs-production

# Common causes:
# - Image pull errors
# - Configuration errors
# - Resource limits
# - Secret/ConfigMap issues
```

**2. Database Connection Issues**
```bash
# Check secrets
kubectl get secret brs-secrets -n brs-production -o yaml

# Test database connectivity
kubectl exec -it pod-name -n brs-production -- psql $DATABASE_URL -c "SELECT 1;"

# Check RDS status
aws rds describe-db-instances --db-instance-identifier brs-database
```

**3. Ingress Not Working**
```bash
# Check ingress status
kubectl describe ingress brs-backend-ingress -n brs-production

# Check ALB controller logs
kubectl logs -n kube-system deployment/aws-load-balancer-controller

# Check certificate
aws acm describe-certificate --certificate-arn CERTIFICATE_ARN
```

**4. Performance Issues**
```bash
# Check resource usage
kubectl top pods -n brs-production
kubectl top nodes

# Check HPA status
kubectl get hpa -n brs-production

# Scale up if needed
kubectl scale deployment brs-backend --replicas=10 -n brs-production
```

### Emergency Procedures

**Rollback Deployment**:
```bash
# Check rollout history
kubectl rollout history deployment/brs-backend -n brs-production

# Rollback to previous version
kubectl rollout undo deployment/brs-backend -n brs-production

# Rollback to specific revision
kubectl rollout undo deployment/brs-backend --to-revision=2 -n brs-production
```

**Emergency Scaling**:
```bash
# Scale to zero (maintenance mode)
kubectl scale deployment brs-backend --replicas=0 -n brs-production

# Emergency scale up
kubectl scale deployment brs-backend --replicas=20 -n brs-production
```

## Security Considerations

### Network Security

- **VPC**: All resources deployed in private subnets
- **Security Groups**: Restrictive ingress/egress rules
- **NACLs**: Network-level access control

### Application Security

- **Non-root Container**: Application runs as non-root user
- **Read-only Root Filesystem**: Where possible
- **Resource Limits**: CPU and memory limits enforced
- **Secret Management**: Sensitive data stored in AWS Secrets Manager

### Access Control

- **RBAC**: Kubernetes role-based access control
- **IAM**: AWS IAM roles and policies
- **Service Accounts**: Dedicated service accounts for pods

### Data Security

- **Encryption at Rest**: RDS and EBS volumes encrypted
- **Encryption in Transit**: TLS for all communications
- **Backup Encryption**: Automated backups encrypted

### Security Monitoring

- **Container Scanning**: ECR vulnerability scanning enabled
- **Security Audits**: Regular security assessment
- **Log Monitoring**: Centralized logging for security events

### Compliance

- **Data Privacy**: GDPR and privacy regulations compliance
- **Security Standards**: SOC 2 and ISO 27001 alignment
- **Regular Updates**: Security patches and updates

---

## Support and Maintenance

For questions and support:

- **Technical Issues**: Create GitHub issues
- **Security Concerns**: Email security@brs.example.com
- **Documentation**: See `/docs` directory for additional guides

**Maintenance Windows**: Scheduled maintenance occurs during low-traffic hours (2-4 AM UTC).

**Emergency Contact**: Available 24/7 for critical production issues.


