# Deploy BRS Backend Application to AWS Free Tier Infrastructure
param(
    [string]$Region = "us-east-1",
    [switch]$Force
)

# Configuration
$ProjectName = "brs"
$RepositoryName = "$ProjectName-backend-free"
$ImageTag = "latest"

# Functions
function Write-Log {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message" -ForegroundColor Green
}

function Write-Error-Log {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] ERROR: $Message" -ForegroundColor Red
}

# Validate prerequisites
Write-Log "Checking prerequisites..."

if (!(Get-Command "aws" -ErrorAction SilentlyContinue)) {
    Write-Error-Log "AWS CLI not found. Please install AWS CLI."
    exit 1
}

if (!(Get-Command "docker" -ErrorAction SilentlyContinue)) {
    Write-Error-Log "Docker not found. Please install Docker."
    exit 1
}

# Get account ID and ECR repository URL
Write-Log "Getting AWS account information..."
try {
    $AccountId = aws sts get-caller-identity --query Account --output text
    $EcrUrl = "$AccountId.dkr.ecr.$Region.amazonaws.com/$RepositoryName"
    Write-Log "Account ID: $AccountId"
    Write-Log "ECR Repository: $EcrUrl"
} catch {
    Write-Error-Log "Failed to get AWS account information. Check your AWS credentials."
    exit 1
}

# Check if image already exists (unless force rebuild)
if (!$Force) {
    Write-Log "Checking if image already exists..."
    try {
        $Images = aws ecr describe-images --repository-name $RepositoryName --region $Region --query 'imageDetails[?imageTag!=null]' --output json | ConvertFrom-Json
        if ($Images.Count -gt 0) {
            Write-Log "Image already exists in ECR. Use -Force to rebuild."
            $SkipBuild = $true
        } else {
            Write-Log "No images found in ECR. Building new image."
            $SkipBuild = $false
        }
    } catch {
        Write-Log "Repository empty or error checking. Building new image."
        $SkipBuild = $false
    }
} else {
    Write-Log "Force rebuild requested."
    $SkipBuild = $false
}

# Build and push Docker image
if (!$SkipBuild) {
    Write-Log "Building Docker image..."
    $ImageName = "$EcrUrl" + ":" + "$ImageTag"
    docker build -t $ImageName .
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Log "Docker build failed"
        exit 1
    }
    Write-Log "Docker image built successfully"

    Write-Log "Logging into ECR..."
    $EcrToken = aws ecr get-login-password --region $Region
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Log "Failed to get ECR token"
        exit 1
    }
    
    docker login --username AWS --password $EcrToken $EcrUrl
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Log "Docker login failed"
        exit 1
    }
    Write-Log "ECR login successful"

    Write-Log "Pushing image to ECR..."
    docker push $ImageName
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Log "Docker push failed"
        exit 1
    }
    Write-Log "Image pushed successfully to ECR"
}

# Get EC2 instance IP
Write-Log "Getting EC2 instance information..."
try {
    $TerraformOutput = terraform -chdir="terraform/free-tier" output -json | ConvertFrom-Json
    $ElasticIp = $TerraformOutput.elastic_ip.value
    Write-Log "EC2 Instance IP: $ElasticIp"
} catch {
    Write-Error-Log "Failed to get EC2 instance IP from Terraform output"
    exit 1
}

# Deploy to EC2 instance
Write-Log "Deploying application to EC2 instance..."
ssh -i ~/.ssh/brs-key -o StrictHostKeyChecking=no ec2-user@$ElasticIp "sudo /opt/brs-backend/deploy.sh"
if ($LASTEXITCODE -ne 0) {
    Write-Error-Log "Deployment script failed"
    exit 1
}
Write-Log "Application deployed successfully"

# Test deployment
Write-Log "Testing deployment..."
Start-Sleep -Seconds 10

$HealthUrl = "http://$ElasticIp/health"
try {
    $Response = Invoke-WebRequest -Uri $HealthUrl -Method GET -TimeoutSec 30
    if ($Response.StatusCode -eq 200) {
        Write-Log "Health check passed! Application is running."
        Write-Log "Application URL: http://$ElasticIp"
        Write-Log "API Documentation: http://$ElasticIp/docs"
    } else {
        Write-Error-Log "Health check failed. Status code: $($Response.StatusCode)"
    }
} catch {
    Write-Error-Log "Failed to connect to application: $_"
    Write-Log "Check the application logs on the EC2 instance:"
    Write-Log "  ssh -i ~/.ssh/brs-key ec2-user@$ElasticIp"
    Write-Log "  sudo journalctl -u brs-backend -f"
}

Write-Log "Deployment process completed!"
