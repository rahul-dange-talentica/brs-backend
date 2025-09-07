# BRS Backend - AWS Deployment Script for Windows
# This script helps deploy the BRS backend to a new AWS account

param(
    [Parameter(Mandatory=$true)]
    [string]$DomainName,
    
    [Parameter(Mandatory=$false)]
    [string]$CertificateArn = "",
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-east-1",
    
    [Parameter(Mandatory=$false)]
    [string]$ProjectName = "brs"
)

# Colors for output
$ErrorColor = "Red"
$SuccessColor = "Green"
$InfoColor = "Cyan"
$WarningColor = "Yellow"

function Write-Info($message) {
    Write-Host "[INFO] $message" -ForegroundColor $InfoColor
}

function Write-Success($message) {
    Write-Host "[SUCCESS] $message" -ForegroundColor $SuccessColor
}

function Write-Warning($message) {
    Write-Host "[WARNING] $message" -ForegroundColor $WarningColor
}

function Write-Error($message) {
    Write-Host "[ERROR] $message" -ForegroundColor $ErrorColor
}

function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    $prerequisites = @(
        @{Name="AWS CLI"; Command="aws --version"},
        @{Name="Terraform"; Command="terraform version"},
        @{Name="kubectl"; Command="kubectl version --client"},
        @{Name="Docker"; Command="docker --version"}
    )
    
    $allGood = $true
    foreach ($prereq in $prerequisites) {
        try {
            Invoke-Expression $prereq.Command | Out-Null
            Write-Success "$($prereq.Name) is available"
        }
        catch {
            Write-Error "$($prereq.Name) is not available"
            $allGood = $false
        }
    }
    
    if (-not $allGood) {
        Write-Error "Please install missing prerequisites before continuing"
        exit 1
    }
}

function Test-AWSCredentials {
    Write-Info "Checking AWS credentials..."
    
    try {
        $identity = aws sts get-caller-identity --output json | ConvertFrom-Json
        Write-Success "AWS credentials configured for account: $($identity.Account)"
        return $identity.Account
    }
    catch {
        Write-Error "AWS credentials not configured or expired"
        Write-Info "Please run: aws configure"
        exit 1
    }
}

function New-TerraformBackend {
    param([string]$AccountId)
    
    Write-Info "Setting up Terraform backend..."
    
    $bucketName = "$ProjectName-terraform-state-$(Get-Random -Minimum 1000 -Maximum 9999)"
    $tableName = "$ProjectName-terraform-locks"
    
    Write-Info "Creating S3 bucket: $bucketName"
    aws s3 mb "s3://$bucketName" --region $Region
    
    Write-Info "Enabling S3 bucket versioning..."
    aws s3api put-bucket-versioning --bucket $bucketName --versioning-configuration Status=Enabled
    
    Write-Info "Creating DynamoDB table: $tableName"
    aws dynamodb create-table `
        --table-name $tableName `
        --attribute-definitions AttributeName=LockID,AttributeType=S `
        --key-schema AttributeName=LockID,KeyType=HASH `
        --billing-mode PAY_PER_REQUEST `
        --region $Region
    
    Write-Success "Terraform backend created successfully"
    return @{Bucket=$bucketName; Table=$tableName}
}

function New-SSLCertificate {
    param([string]$Domain)
    
    if ($CertificateArn -eq "") {
        Write-Info "Creating SSL certificate for domain: $Domain"
        
        $certOutput = aws acm request-certificate `
            --domain-name $Domain `
            --validation-method DNS `
            --region $Region `
            --output json | ConvertFrom-Json
        
        $certArn = $certOutput.CertificateArn
        Write-Success "Certificate requested: $certArn"
        Write-Warning "IMPORTANT: You must validate this certificate in AWS Console before proceeding"
        Write-Warning "Go to AWS Console -> Certificate Manager -> Validate the DNS record"
        
        $response = Read-Host "Press Enter when certificate is validated, or type 'skip' to continue without SSL"
        if ($response -eq "skip") {
            return ""
        }
        
        return $certArn
    }
    else {
        Write-Info "Using provided certificate: $CertificateArn"
        return $CertificateArn
    }
}

function Update-TerraformConfig {
    param(
        [string]$AccountId,
        [hashtable]$Backend,
        [string]$CertArn
    )
    
    Write-Info "Updating Terraform configuration..."
    
    # Update backend configuration
    $backendConfig = @"
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
    bucket = "$($Backend.Bucket)"
    key    = "production/terraform.tfstate"
    region = "$Region"
    
    dynamodb_table = "$($Backend.Table)"
    encrypt        = true
  }
}
"@
    
    $backendConfig | Out-File -FilePath "terraform\versions.tf" -Encoding UTF8
    
    # Create terraform.tfvars
    $tfvarsConfig = @"
aws_region = "$Region"
project_name = "$ProjectName"
environment = "production"
certificate_arn = "$CertArn"
domain_name = "$DomainName"
rds_instance_class = "db.t3.micro"
eks_node_instance_types = ["t3.medium"]
"@
    
    $tfvarsConfig | Out-File -FilePath "terraform\terraform.tfvars" -Encoding UTF8
    
    Write-Success "Terraform configuration updated"
}

function Deploy-Infrastructure {
    Write-Info "Deploying infrastructure with Terraform..."
    
    Set-Location terraform
    
    Write-Info "Initializing Terraform..."
    terraform init
    
    Write-Info "Validating Terraform configuration..."
    terraform validate
    
    Write-Info "Planning infrastructure deployment..."
    terraform plan -var-file="terraform.tfvars"
    
    $response = Read-Host "Do you want to deploy this infrastructure? (yes/no)"
    if ($response -ne "yes") {
        Write-Warning "Infrastructure deployment cancelled"
        Set-Location ..
        return $false
    }
    
    Write-Info "Applying Terraform configuration (this will take 10-15 minutes)..."
    terraform apply -var-file="terraform.tfvars" -auto-approve
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Terraform deployment failed"
        Set-Location ..
        return $false
    }
    
    Write-Success "Infrastructure deployed successfully!"
    
    # Get outputs
    $outputs = terraform output -json | ConvertFrom-Json
    
    Set-Location ..
    return $outputs
}

function Update-KubeConfig {
    param([string]$ClusterName)
    
    Write-Info "Configuring kubectl for EKS cluster..."
    
    aws eks update-kubeconfig --region $Region --name $ClusterName
    
    Write-Info "Testing kubectl connection..."
    kubectl get nodes
    
    Write-Success "kubectl configured successfully"
}

function Build-DockerImage {
    param([string]$AccountId)
    
    Write-Info "Building Docker image..."
    
    docker build -t brs-backend:latest .
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker build failed"
        return $false
    }
    
    Write-Info "Logging into ECR..."
    aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin "$AccountId.dkr.ecr.$Region.amazonaws.com"
    
    $ecrUrl = "$AccountId.dkr.ecr.$Region.amazonaws.com/$ProjectName-backend"
    
    Write-Info "Tagging and pushing image to ECR..."
    docker tag brs-backend:latest "$ecrUrl:latest"
    docker push "$ecrUrl:latest"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker push failed"
        return $false
    }
    
    Write-Success "Docker image built and pushed successfully"
    return $true
}

function Update-KubernetesManifests {
    param([string]$AccountId)
    
    Write-Info "Updating Kubernetes manifests..."
    
    # Update deployment.yaml
    (Get-Content k8s\deployment.yaml -Raw) -replace '<AWS_ACCOUNT_ID>', $AccountId -replace '<REGION>', $Region | 
        Set-Content k8s\deployment.yaml -NoNewline
    
    # Update rbac.yaml
    (Get-Content k8s\rbac.yaml -Raw) -replace 'ACCOUNT_ID', $AccountId | 
        Set-Content k8s\rbac.yaml -NoNewline
    
    # Update migration files
    (Get-Content k8s\migration-job.yaml -Raw) -replace '<AWS_ACCOUNT_ID>', $AccountId -replace '<REGION>', $Region | 
        Set-Content k8s\migration-job.yaml -NoNewline
    
    Write-Success "Kubernetes manifests updated"
}

function Deploy-Application {
    Write-Info "Deploying application to Kubernetes..."
    
    # Apply manifests in order
    Write-Info "Creating namespace..."
    kubectl apply -f k8s\namespace.yaml
    
    Write-Info "Setting up RBAC..."
    kubectl apply -f k8s\rbac.yaml
    
    Write-Info "Creating secrets..."
    kubectl apply -f k8s\secrets.yaml
    
    Write-Info "Running database migration..."
    kubectl apply -f k8s\migration-job.yaml
    kubectl wait --for=condition=complete --timeout=600s job/brs-migration -n brs-production
    
    Write-Info "Deploying application..."
    kubectl apply -f k8s\deployment.yaml
    kubectl apply -f k8s\service.yaml
    kubectl apply -f k8s\ingress.yaml
    kubectl apply -f k8s\hpa.yaml
    
    Write-Info "Waiting for deployment to be ready..."
    kubectl rollout status deployment/brs-backend -n brs-production --timeout=600s
    
    Write-Success "Application deployed successfully!"
}

function Test-Deployment {
    Write-Info "Testing deployment..."
    
    # Check pods
    Write-Info "Pod status:"
    kubectl get pods -n brs-production
    
    # Check services
    Write-Info "Service status:"
    kubectl get svc -n brs-production
    
    # Check ingress
    Write-Info "Ingress status:"
    kubectl get ingress -n brs-production
    
    # Port forward and test
    Write-Info "Testing health endpoint..."
    Start-Job -Name "PortForward" -ScriptBlock {
        kubectl port-forward svc/brs-backend-service 8080:80 -n brs-production
    } | Out-Null
    
    Start-Sleep -Seconds 5
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8080/health" -TimeoutSec 10
        Write-Success "Health check passed: $($response.message)"
    }
    catch {
        Write-Warning "Health check failed (this might be normal if load balancer is still starting)"
    }
    finally {
        Stop-Job -Name "PortForward" -ErrorAction SilentlyContinue
        Remove-Job -Name "PortForward" -ErrorAction SilentlyContinue
    }
}

function Show-Summary {
    param([object]$TerraformOutputs)
    
    Write-Success "=== DEPLOYMENT COMPLETE ==="
    Write-Host ""
    Write-Info "Your BRS backend has been deployed successfully!"
    Write-Host ""
    Write-Info "Access Information:"
    Write-Host "- Health Check: http://localhost:8080/health (via port-forward)"
    Write-Host "- API Documentation: http://localhost:8080/docs (via port-forward)"
    Write-Host "- Domain: https://$DomainName (after DNS configuration)"
    Write-Host ""
    Write-Info "Next Steps:"
    Write-Host "1. Configure DNS: Point $DomainName to the ALB endpoint"
    Write-Host "2. Wait for SSL certificate validation (if not done already)"
    Write-Host "3. Test the production endpoint: https://$DomainName/health"
    Write-Host ""
    Write-Info "Useful Commands:"
    Write-Host "- View pods: kubectl get pods -n brs-production"
    Write-Host "- View logs: kubectl logs -f deployment/brs-backend -n brs-production"
    Write-Host "- Port forward: kubectl port-forward svc/brs-backend-service 8080:80 -n brs-production"
    Write-Host ""
    Write-Warning "Estimated Monthly Cost: ~$175 (less with AWS free tier)"
}

# Main execution
function Main {
    Write-Info "Starting BRS Backend AWS Deployment"
    Write-Info "Domain: $DomainName"
    Write-Info "Region: $Region"
    Write-Host ""
    
    # Step 1: Check prerequisites
    Test-Prerequisites
    
    # Step 2: Check AWS credentials
    $accountId = Test-AWSCredentials
    
    # Step 3: Setup Terraform backend
    $backend = New-TerraformBackend -AccountId $accountId
    
    # Step 4: Setup SSL certificate
    $certArn = New-SSLCertificate -Domain $DomainName
    
    # Step 5: Update Terraform configuration
    Update-TerraformConfig -AccountId $accountId -Backend $backend -CertArn $certArn
    
    # Step 6: Deploy infrastructure
    $outputs = Deploy-Infrastructure
    if (-not $outputs) {
        Write-Error "Infrastructure deployment failed"
        exit 1
    }
    
    # Step 7: Configure kubectl
    Update-KubeConfig -ClusterName $outputs.cluster_name.value
    
    # Step 8: Build and push Docker image
    $buildSuccess = Build-DockerImage -AccountId $accountId
    if (-not $buildSuccess) {
        Write-Error "Docker build/push failed"
        exit 1
    }
    
    # Step 9: Update Kubernetes manifests
    Update-KubernetesManifests -AccountId $accountId
    
    # Step 10: Deploy application
    Deploy-Application
    
    # Step 11: Test deployment
    Test-Deployment
    
    # Step 12: Show summary
    Show-Summary -TerraformOutputs $outputs
}

# Run the main function
Main

