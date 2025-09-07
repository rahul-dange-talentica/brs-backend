# BRS Backend - Complete AWS Deployment Guide

This guide walks you through creating a new AWS account and deploying the BRS backend service from scratch.

## 📋 Prerequisites

- ✅ Terraform v1.13.1 (installed)
- ✅ AWS CLI v2.25.7 (installed)
- ✅ kubectl v1.32.3 (installed)
- ✅ Docker Desktop (for building images)
- 💳 Credit card for AWS account setup

## Step 1: Create New AWS Account

### 1.1 Account Creation
1. Go to [AWS Console](https://aws.amazon.com/)
2. Click "Create an AWS Account"
3. Enter your email address and choose an account name
4. Complete the registration process:
   - Contact information
   - Payment information (credit card)
   - Identity verification (phone/SMS)
   - Select support plan (Basic - Free is fine for now)

### 1.2 Initial Security Setup
After account creation, immediately secure your account:

1. **Enable MFA on Root Account**:
   - Go to IAM → Users → root user
   - Security credentials → Assign MFA device
   - Use authenticator app (Google Authenticator, etc.)

2. **Create IAM Admin User**:
   - Go to IAM → Users → Add user
   - Username: `brs-admin`
   - Access type: ✅ Programmatic access, ✅ AWS Management Console access
   - Permissions: Attach existing policy → `AdministratorAccess`
   - Download CSV with credentials (save securely!)

## Step 2: Configure AWS CLI

### 2.1 Configure Credentials
```powershell
# Configure AWS CLI with your admin user credentials
aws configure

# Enter when prompted:
# AWS Access Key ID: [from downloaded CSV]
# AWS Secret Access Key: [from downloaded CSV]
# Default region name: us-east-1
# Default output format: json
```

### 2.2 Verify Setup
```powershell
# Test your AWS connection
aws sts get-caller-identity

# Should return your account ID and user ARN
```

## Step 3: Domain and SSL Certificate Setup

### 3.1 Domain Requirements
You'll need a domain name for SSL certificates. Options:

**Option A: Use a Domain You Own**
- Point DNS to AWS later
- Example: `api.yourdomain.com`

**Option B: Buy Domain in AWS Route53**
- Go to Route53 → Registered domains
- Search and purchase a domain
- Example: `your-brs-app.com`

**Option C: Use Temporary Self-Signed (Testing Only)**
- Skip SSL setup for now
- Use HTTP only (not recommended for production)

### 3.2 Create SSL Certificate (Required for Production)
```powershell
# Create certificate in AWS Certificate Manager
aws acm request-certificate \
    --domain-name "api.yourdomain.com" \
    --validation-method DNS \
    --region us-east-1

# Note the certificate ARN from the output
# Example: arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012
```

### 3.3 Validate Certificate
1. Go to AWS Console → Certificate Manager
2. Find your certificate
3. Click "Create record in Route 53" (if using Route53) OR
4. Add the DNS validation record to your domain provider

## Step 4: Prepare Infrastructure Deployment

### 4.1 Update Terraform Configuration
```powershell
# Navigate to your project
cd C:\Users\RahulD\Documents\codebase\rahul-dange-talentica\brs-backend

# Create terraform variables file
# Copy and paste this into: terraform\terraform.tfvars
```

Create `terraform\terraform.tfvars`:
```hcl
aws_region = "us-east-1"
project_name = "brs"
environment = "production"

# Replace with your actual certificate ARN
certificate_arn = "arn:aws:acm:us-east-1:YOUR_ACCOUNT_ID:certificate/YOUR_CERT_ID"

# Replace with your domain
domain_name = "api.yourdomain.com"

# Optional: Customize instance sizes
rds_instance_class = "db.t3.micro"  # Free tier eligible
eks_node_instance_types = ["t3.medium"]
```

### 4.2 Create S3 Backend for Terraform State
```powershell
# Create unique bucket name
$bucketName = "brs-terraform-state-$(Get-Random)"
echo "Using bucket: $bucketName"

# Create S3 bucket for terraform state
aws s3 mb "s3://$bucketName" --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning --bucket $bucketName --versioning-configuration Status=Enabled

# Create DynamoDB table for state locking
aws dynamodb create-table `
    --table-name brs-terraform-locks `
    --attribute-definitions AttributeName=LockID,AttributeType=S `
    --key-schema AttributeName=LockID,KeyType=HASH `
    --billing-mode PAY_PER_REQUEST `
    --region us-east-1
```

### 4.3 Update Backend Configuration
Update `terraform\versions.tf`:
```hcl
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.4"
    }
  }
  
  backend "s3" {
    bucket = "YOUR_ACTUAL_BUCKET_NAME"  # Replace with $bucketName from above
    key    = "production/terraform.tfstate"
    region = "us-east-1"
    
    dynamodb_table = "brs-terraform-locks"
    encrypt        = true
  }
}
```

## Step 5: Deploy Infrastructure

### 5.1 Initialize Terraform
```powershell
cd terraform

# Initialize terraform with your backend
terraform init

# Validate configuration
terraform validate
```

### 5.2 Plan Infrastructure
```powershell
# Review what will be created
terraform plan -var-file="terraform.tfvars"

# This will show you:
# - VPC with subnets
# - EKS cluster
# - RDS database
# - ECR repository
# - Security groups
# - IAM roles
```

### 5.3 Deploy Infrastructure
```powershell
# Deploy infrastructure (takes 10-15 minutes)
terraform apply -var-file="terraform.tfvars"

# Type 'yes' when prompted
```

### 5.4 Save Important Outputs
```powershell
# Get important information
terraform output

# Save these values:
# - cluster_name
# - ecr_repository_url
# - rds_instance_endpoint
```

## Step 6: Configure kubectl for EKS

### 6.1 Update kubeconfig
```powershell
# Configure kubectl to use your EKS cluster
aws eks update-kubeconfig --region us-east-1 --name brs-cluster

# Verify connection
kubectl get nodes
```

## Step 7: Build and Deploy Application

### 7.1 Build Docker Image
```powershell
# Build the application image
docker build -t brs-backend:latest .

# Get ECR login command
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Tag and push image
$accountId = (aws sts get-caller-identity --query Account --output text)
$ecrUrl = "$accountId.dkr.ecr.us-east-1.amazonaws.com/brs-backend"

docker tag brs-backend:latest "$ecrUrl:latest"
docker push "$ecrUrl:latest"
```

### 7.2 Update Kubernetes Manifests
```powershell
# Update manifests with your account ID
$accountId = (aws sts get-caller-identity --query Account --output text)

# Update k8s manifests (replace placeholders)
(Get-Content k8s\deployment.yaml) -replace '<AWS_ACCOUNT_ID>', $accountId -replace '<REGION>', 'us-east-1' | Set-Content k8s\deployment.yaml
(Get-Content k8s\rbac.yaml) -replace 'ACCOUNT_ID', $accountId | Set-Content k8s\rbac.yaml
```

### 7.3 Deploy to Kubernetes
```powershell
# Apply manifests in order
kubectl apply -f k8s\namespace.yaml
kubectl apply -f k8s\rbac.yaml
kubectl apply -f k8s\secrets.yaml

# Run database migration
kubectl apply -f k8s\migration-job.yaml
kubectl wait --for=condition=complete --timeout=600s job/brs-migration -n brs-production

# Deploy application
kubectl apply -f k8s\deployment.yaml
kubectl apply -f k8s\service.yaml
kubectl apply -f k8s\ingress.yaml
kubectl apply -f k8s\hpa.yaml

# Wait for deployment
kubectl rollout status deployment/brs-backend -n brs-production
```

## Step 8: Verify Deployment

### 8.1 Check Application Status
```powershell
# Check pods
kubectl get pods -n brs-production

# Check services
kubectl get svc -n brs-production

# Check ingress
kubectl get ingress -n brs-production

# Get load balancer URL
kubectl get ingress brs-backend-ingress -n brs-production -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

### 8.2 Test Health Endpoints
```powershell
# Port forward to test locally
kubectl port-forward svc/brs-backend-service 8080:80 -n brs-production

# In another terminal/browser, test:
# http://localhost:8080/health
# http://localhost:8080/docs
```

## Step 9: Configure DNS (Production)

### 9.1 Point Domain to Load Balancer
1. Get ALB hostname: `kubectl get ingress brs-backend-ingress -n brs-production`
2. Create CNAME record in your DNS provider:
   - Name: `api` (for api.yourdomain.com)
   - Value: ALB hostname (e.g., `k8s-brsproduction-brsbacke-xxxxx.us-east-1.elb.amazonaws.com`)

### 9.2 Verify SSL Certificate
- Wait 5-10 minutes for DNS propagation
- Visit `https://api.yourdomain.com/health`
- Should show SSL certificate and API response

## Step 10: Monitor and Maintain

### 10.1 Monitor Application
- **Health Check**: `https://api.yourdomain.com/health`
- **Detailed Health**: `https://api.yourdomain.com/api/v1/monitoring/health/detailed`
- **API Docs**: `https://api.yourdomain.com/docs`

### 10.2 Check AWS Costs
- Go to AWS Console → Billing & Cost Management
- Set up billing alerts for cost monitoring

### 10.3 Scale if Needed
```powershell
# Scale application
kubectl scale deployment brs-backend --replicas=5 -n brs-production

# Auto-scaling is already configured (2-10 replicas)
```

## 🎯 Expected Costs (Estimated Monthly)

- **EKS Cluster**: ~$75/month
- **EC2 Instances** (t3.medium x2): ~$60/month
- **RDS** (db.t3.micro): ~$15/month (free tier for first year)
- **ALB**: ~$20/month
- **Data Transfer**: ~$5-10/month
- **Total**: ~$175/month (less with free tier)

## 🆘 Troubleshooting

### Common Issues:

1. **Certificate Not Validating**:
   - Check DNS records in Certificate Manager
   - Ensure domain ownership verification

2. **Pods Not Starting**:
   ```powershell
   kubectl describe pod POD_NAME -n brs-production
   kubectl logs POD_NAME -n brs-production
   ```

3. **Database Connection Issues**:
   - Check security groups
   - Verify secrets in AWS Secrets Manager

4. **Load Balancer Not Working**:
   - Check ALB controller installation
   - Verify ingress annotations

## 🎉 Success!

If everything is working:
- ✅ Your BRS backend is running on AWS EKS
- ✅ Auto-scaling is configured
- ✅ SSL/TLS is working
- ✅ Database is set up with backups
- ✅ Monitoring is available

Your API will be available at: `https://api.yourdomain.com`

## 🔄 CI/CD Setup (Optional)

To enable automatic deployments:

1. **GitHub Secrets**: Add to your repository:
   - `AWS_ACCESS_KEY_ID`: Your AWS access key
   - `AWS_SECRET_ACCESS_KEY`: Your AWS secret key

2. **Push to Main**: Any push to main branch will trigger deployment

3. **Infrastructure Changes**: Changes to `terraform/` folder will update infrastructure

---

**Need Help?** 
- Check the logs: `kubectl logs -f deployment/brs-backend -n brs-production`
- Monitor health: `https://api.yourdomain.com/api/v1/monitoring/health/detailed`
- AWS Console: Check EKS, RDS, and ALB status

