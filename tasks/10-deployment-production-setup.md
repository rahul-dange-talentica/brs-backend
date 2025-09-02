# Task 10: Deployment & Production Setup

**Phase**: 3 - Quality & Deployment  
**Sequence**: 10  
**Priority**: Critical  
**Estimated Effort**: 12-15 hours  
**Dependencies**: All previous tasks (01-09)

---

## Objective

Set up complete production deployment infrastructure using Docker, Kubernetes, and AWS services according to technical PRD specifications, ensuring scalability, security, and reliability for the BRS backend service.

## Scope

- Docker containerization with multi-stage builds
- Kubernetes deployment configuration for AWS EKS
- AWS infrastructure setup (RDS, ECR, ALB, VPC)
- Production environment configuration and secrets management
- CI/CD pipeline for automated deployment
- Monitoring, logging, and alerting setup
- Database migration and backup strategies
- Security hardening and SSL/TLS configuration

## Technical Requirements

### AWS Infrastructure (from Technical PRD)
- **Container**: Docker with multi-stage builds
- **Orchestration**: Amazon EKS (Elastic Kubernetes Service)  
- **Load Balancer**: AWS Application Load Balancer (ALB)
- **Database Hosting**: Amazon RDS for PostgreSQL
- **Container Registry**: Amazon ECR
- **Secrets Management**: AWS Secrets Manager

### Performance & Reliability
- **Performance**: API response time < 500ms (95th percentile)
- **Availability**: 99% uptime during business hours
- **Scalability**: Support 100 concurrent users without degradation
- **Security**: Zero critical security vulnerabilities

## Acceptance Criteria

### ✅ Docker Containerization
- [ ] Multi-stage Dockerfile optimized for production
- [ ] Container size optimized (<500MB)
- [ ] Non-root user for security
- [ ] Health checks configured
- [ ] Environment-specific configurations

### ✅ Kubernetes Configuration
- [ ] Deployment manifests for EKS
- [ ] Service and Ingress configuration
- [ ] ConfigMaps for environment variables
- [ ] Secrets for sensitive data
- [ ] Resource limits and requests defined
- [ ] Horizontal Pod Autoscaler (HPA) configured

### ✅ AWS Infrastructure
- [ ] VPC with public/private subnets
- [ ] RDS PostgreSQL with Multi-AZ deployment
- [ ] ECR repository for container images
- [ ] ALB with SSL/TLS termination
- [ ] EKS cluster with worker nodes
- [ ] IAM roles and policies configured

### ✅ Security & Secrets
- [ ] AWS Secrets Manager integration
- [ ] Database credentials secured
- [ ] JWT secrets in AWS Secrets Manager
- [ ] SSL/TLS certificates configured
- [ ] Security groups and NACLs configured
- [ ] Container vulnerability scanning

### ✅ Monitoring & Logging
- [ ] Application logs centralized (CloudWatch)
- [ ] Performance monitoring setup
- [ ] Health check endpoints monitored
- [ ] Alerting for critical issues
- [ ] Database performance monitoring

## Implementation Details

### Multi-stage Dockerfile
```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Configure poetry
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev --no-interaction --no-ansi

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes Deployment (k8s/deployment.yaml)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: brs-backend
  namespace: brs-production
  labels:
    app: brs-backend
    version: v1.0.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app: brs-backend
  template:
    metadata:
      labels:
        app: brs-backend
        version: v1.0.0
    spec:
      containers:
      - name: brs-backend
        image: <AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/brs-backend:latest
        ports:
        - containerPort: 8000
          protocol: TCP
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: brs-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: brs-secrets
              key: jwt-secret
        - name: ENVIRONMENT
          value: "production"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        securityContext:
          runAsNonRoot: true
          runAsUser: 1001
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: false
---
apiVersion: v1
kind: Service
metadata:
  name: brs-backend-service
  namespace: brs-production
spec:
  selector:
    app: brs-backend
  ports:
  - name: http
    port: 80
    targetPort: 8000
    protocol: TCP
  type: ClusterIP
```

### Kubernetes Ingress with ALB (k8s/ingress.yaml)
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: brs-backend-ingress
  namespace: brs-production
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS":443}]'
    alb.ingress.kubernetes.io/ssl-redirect: '443'
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:region:account:certificate/cert-id
    alb.ingress.kubernetes.io/healthcheck-path: /health
    alb.ingress.kubernetes.io/healthcheck-interval-seconds: '30'
    alb.ingress.kubernetes.io/healthy-threshold-count: '2'
    alb.ingress.kubernetes.io/unhealthy-threshold-count: '3'
spec:
  rules:
  - host: api.brs.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: brs-backend-service
            port:
              number: 80
```

### Horizontal Pod Autoscaler (k8s/hpa.yaml)
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: brs-backend-hpa
  namespace: brs-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: brs-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
```

### AWS Infrastructure as Code (terraform/main.tf)
```hcl
provider "aws" {
  region = var.aws_region
}

# VPC and Networking
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  
  name = "brs-vpc"
  cidr = "10.0.0.0/16"
  
  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  
  enable_nat_gateway = true
  enable_vpn_gateway = false
  enable_dns_hostnames = true
  enable_dns_support = true
  
  tags = {
    Environment = "production"
    Project = "brs"
  }
}

# EKS Cluster
module "eks" {
  source = "terraform-aws-modules/eks/aws"
  
  cluster_name    = "brs-cluster"
  cluster_version = "1.27"
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  
  node_groups = {
    main = {
      desired_capacity = 2
      max_capacity     = 10
      min_capacity     = 2
      
      instance_types = ["t3.medium"]
      
      k8s_labels = {
        Environment = "production"
        Application = "brs-backend"
      }
    }
  }
  
  tags = {
    Environment = "production"
    Project = "brs"
  }
}

# RDS PostgreSQL
resource "aws_db_instance" "brs_db" {
  identifier = "brs-database"
  
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.micro"
  
  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type         = "gp2"
  storage_encrypted    = true
  
  db_name  = "brs_production"
  username = "brs_admin"
  password = random_password.db_password.result
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.brs.name
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  multi_az = true
  
  skip_final_snapshot = false
  final_snapshot_identifier = "brs-db-final-snapshot"
  
  tags = {
    Environment = "production"
    Project = "brs"
  }
}

# ECR Repository
resource "aws_ecr_repository" "brs_backend" {
  name                 = "brs-backend"
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {
    scan_on_push = true
  }
  
  tags = {
    Environment = "production"
    Project = "brs"
  }
}

# Secrets Manager
resource "aws_secretsmanager_secret" "brs_secrets" {
  name = "brs/production/secrets"
  
  tags = {
    Environment = "production"
    Project = "brs"
  }
}

resource "aws_secretsmanager_secret_version" "brs_secrets" {
  secret_id = aws_secretsmanager_secret.brs_secrets.id
  secret_string = jsonencode({
    database-url = "postgresql://${aws_db_instance.brs_db.username}:${random_password.db_password.result}@${aws_db_instance.brs_db.endpoint}/${aws_db_instance.brs_db.db_name}"
    jwt-secret   = random_password.jwt_secret.result
  })
}
```

### GitHub Actions CI/CD (.github/workflows/deploy.yml)
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]
  workflow_dispatch:

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: brs-backend
  EKS_CLUSTER_NAME: brs-cluster

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: brs_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install Poetry
      uses: snok/install-poetry@v1
    
    - name: Install dependencies
      run: poetry install
    
    - name: Run tests
      run: poetry run pytest --cov=app --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.AWS_REGION }}
    
    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1
    
    - name: Build, tag, and push image to Amazon ECR
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        IMAGE_TAG: ${{ github.sha }}
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:latest .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
    
    - name: Update kubeconfig
      run: |
        aws eks update-kubeconfig --name $EKS_CLUSTER_NAME --region $AWS_REGION
    
    - name: Deploy to EKS
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        IMAGE_TAG: ${{ github.sha }}
      run: |
        sed -i "s|<AWS_ACCOUNT_ID>|${{ steps.login-ecr.outputs.registry }}|g" k8s/deployment.yaml
        sed -i "s|latest|$IMAGE_TAG|g" k8s/deployment.yaml
        kubectl apply -f k8s/
        kubectl rollout status deployment/brs-backend -n brs-production
```

### Production Configuration (app/config.py)
```python
import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    database_url: str
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    
    # CORS
    allowed_origins: List[str] = ["https://brs.example.com"]
    
    # Environment
    environment: str = "production"
    debug: bool = False
    
    # AWS
    aws_region: str = "us-east-1"
    aws_secrets_manager: bool = True
    
    # Monitoring
    enable_metrics: bool = True
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Load secrets from AWS Secrets Manager in production
        if self.aws_secrets_manager and self.environment == "production":
            self._load_aws_secrets()
    
    def _load_aws_secrets(self):
        import boto3
        import json
        
        client = boto3.client('secretsmanager', region_name=self.aws_region)
        
        try:
            response = client.get_secret_value(SecretId='brs/production/secrets')
            secrets = json.loads(response['SecretString'])
            
            self.database_url = secrets.get('database-url', self.database_url)
            self.secret_key = secrets.get('jwt-secret', self.secret_key)
        except Exception as e:
            print(f"Failed to load secrets from AWS: {e}")

settings = Settings()
```

## Testing

### Infrastructure Testing
- [ ] Docker container builds successfully
- [ ] Container security scan passes
- [ ] Kubernetes manifests validate
- [ ] Health checks respond correctly
- [ ] Load balancer routing works

### Performance Testing
- [ ] Load testing with 100 concurrent users
- [ ] Response time under 500ms (95th percentile)
- [ ] Auto-scaling triggers work correctly
- [ ] Database performance under load

### Security Testing
- [ ] Container vulnerability scanning
- [ ] Network security group validation
- [ ] SSL/TLS certificate validation
- [ ] Secrets are properly secured

## Deployment Commands

### Build and Push Container
```bash
# Build Docker image
docker build -t brs-backend:latest .

# Tag for ECR
docker tag brs-backend:latest <account>.dkr.ecr.<region>.amazonaws.com/brs-backend:latest

# Push to ECR
docker push <account>.dkr.ecr.<region>.amazonaws.com/brs-backend:latest
```

### Deploy to Kubernetes
```bash
# Apply all manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n brs-production
kubectl get services -n brs-production
kubectl get ingress -n brs-production

# Check logs
kubectl logs -f deployment/brs-backend -n brs-production
```

### Database Migration
```bash
# Run migration job
kubectl create job --from=cronjob/brs-migration migrate-$(date +%s) -n brs-production
```

## Definition of Done

- [ ] Docker containers building and running successfully
- [ ] AWS infrastructure deployed via Terraform
- [ ] EKS cluster operational with application deployed
- [ ] RDS PostgreSQL database configured and accessible
- [ ] Load balancer routing traffic correctly
- [ ] SSL/TLS certificates configured
- [ ] Auto-scaling working correctly
- [ ] Monitoring and alerting functional
- [ ] CI/CD pipeline deploying successfully
- [ ] Performance requirements met
- [ ] Security hardening completed
- [ ] Documentation updated with deployment procedures

## Next Steps

After completion:
- Production environment is fully operational
- Application is accessible at https://api.brs.example.com
- Monitoring and alerting provide operational visibility
- CI/CD enables continuous deployment
- Infrastructure is scalable and maintainable

## Notes

- Monitor costs and optimize resource usage
- Set up backup and disaster recovery procedures
- Implement log aggregation and analysis
- Plan for certificate renewal automation
- Create operational runbooks for common tasks
- Set up staging environment for testing
