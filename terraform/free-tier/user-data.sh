#!/bin/bash
set -e  # Exit on any error

# Enhanced logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a /var/log/brs-setup.log
}

# Error handling function
handle_error() {
    log "ERROR: $1"
    log "Setup failed at line $2"
    exit 1
}

# Set up error trap
trap 'handle_error "Script failed" $LINENO' ERR

log "=== BRS Backend Setup Started ==="
log "Instance ID: $(curl -s http://169.254.169.254/latest/meta-data/instance-id || echo 'unknown')"
log "Region: $(curl -s http://169.254.169.254/latest/meta-data/placement/region || echo 'unknown')"

# Update system
log "Updating system packages..."
yum update -y || handle_error "Failed to update system" $LINENO
log "System update completed"

# Install Docker
log "Installing Docker..."
yum install -y docker || handle_error "Failed to install Docker" $LINENO
systemctl start docker || handle_error "Failed to start Docker" $LINENO
systemctl enable docker || handle_error "Failed to enable Docker" $LINENO
usermod -a -G docker ec2-user || handle_error "Failed to add ec2-user to docker group" $LINENO
log "Docker installation completed"

# Install AWS CLI v2
log "Installing AWS CLI v2..."
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" || handle_error "Failed to download AWS CLI" $LINENO
unzip awscliv2.zip || handle_error "Failed to unzip AWS CLI" $LINENO
./aws/install || handle_error "Failed to install AWS CLI" $LINENO
rm -rf aws awscliv2.zip
log "AWS CLI installation completed"

# Verify AWS CLI access
log "Verifying AWS CLI access..."
aws sts get-caller-identity || handle_error "AWS CLI not working - check IAM role" $LINENO
log "AWS CLI access verified"

# Configure AWS region
aws configure set region ${aws_region}
log "AWS region configured: ${aws_region}"

# Create application directory
log "Creating application directory..."
mkdir -p /opt/brs-backend || handle_error "Failed to create app directory" $LINENO
chown ec2-user:ec2-user /opt/brs-backend || handle_error "Failed to set directory ownership" $LINENO
log "Application directory created"

# Install jq for JSON parsing (needed for Secrets Manager)
log "Installing jq for JSON parsing..."
yum install -y jq || handle_error "Failed to install jq" $LINENO
log "jq installed successfully"

# Get secrets from AWS Secrets Manager
log "Retrieving secrets from AWS Secrets Manager..."
SECRETS_JSON=$(aws secretsmanager get-secret-value --secret-id brs/production/secrets --region ${aws_region} --query SecretString --output text) || handle_error "Failed to retrieve secrets" $LINENO
DATABASE_URL=$(echo "$SECRETS_JSON" | jq -r '.["database-url"]') || handle_error "Failed to parse database URL" $LINENO
JWT_SECRET=$(echo "$SECRETS_JSON" | jq -r '.["jwt-secret"]') || handle_error "Failed to parse JWT secret" $LINENO
log "Secrets retrieved successfully"

# Create environment file
log "Creating environment file..."
cat > /opt/brs-backend/.env << EOF
DATABASE_URL=$DATABASE_URL
SECRET_KEY=$JWT_SECRET
ENVIRONMENT=production
AWS_REGION=${aws_region}
LOG_LEVEL=INFO
ENABLE_METRICS=true
TRUSTED_HOSTS_STR=localhost,127.0.0.1,${elastic_ip},*.brs.example.com
AWS_SECRETS_MANAGER=true
EOF

if [ ! -f /opt/brs-backend/.env ]; then
    handle_error "Failed to create environment file" $LINENO
fi

chown ec2-user:ec2-user /opt/brs-backend/.env || handle_error "Failed to set env file ownership" $LINENO
log "Environment file created"

# ECR Login
log "Logging into ECR..."
aws ecr get-login-password --region ${aws_region} | docker login --username AWS --password-stdin ${ecr_repository_url} || handle_error "Failed to login to ECR" $LINENO
log "ECR login successful"

# Try to pull Docker image (optional during infrastructure setup)
log "Attempting to pull Docker image..."
if docker pull ${ecr_repository_url}:latest; then
    log "Docker image pulled successfully"
    IMAGE_AVAILABLE=true
else
    log "WARNING: Docker image not available yet - this is expected during initial infrastructure setup"
    log "The application service will be created but not started until image is deployed"
    IMAGE_AVAILABLE=false
fi

# jq already installed earlier for Secrets Manager parsing

# Create systemd service for the application
log "Creating systemd service..."
cat > /etc/systemd/system/brs-backend.service << 'EOF'
[Unit]
Description=BRS Backend Application
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/brs-backend
ExecStartPre=-/usr/bin/docker stop brs-backend
ExecStartPre=-/usr/bin/docker rm brs-backend
ExecStart=/usr/bin/docker run --name brs-backend --rm -p 80:8000 --env-file /opt/brs-backend/.env ${ecr_repository_url}:latest
ExecStop=/usr/bin/docker stop brs-backend
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

if [ ! -f /etc/systemd/system/brs-backend.service ]; then
    handle_error "Failed to create systemd service file" $LINENO
fi
log "Systemd service file created"

# Enable the service and start only if image is available
log "Enabling BRS backend service..."
systemctl daemon-reload || handle_error "Failed to reload systemd" $LINENO
systemctl enable brs-backend || handle_error "Failed to enable service" $LINENO

if [ "$IMAGE_AVAILABLE" = true ]; then
    log "Starting BRS backend service..."
    systemctl start brs-backend || handle_error "Failed to start service" $LINENO
    log "BRS backend service started"
else
    log "Skipping service start - Docker image not available"
    log "Use 'sudo /opt/brs-backend/deploy.sh' to deploy and start the service later"
fi

# Test health endpoint only if service was started
if [ "$IMAGE_AVAILABLE" = true ]; then
    log "Waiting for service to be ready..."
    sleep 30
    
    log "Testing health endpoint..."
    for i in {1..10}; do
        if curl -f http://localhost/health > /dev/null 2>&1; then
            log "Health check passed!"
            break
        fi
        log "Health check attempt $i failed, retrying..."
        sleep 10
        if [ $i -eq 10 ]; then
            log "WARNING: Health check failed after 10 attempts"
            log "Service logs:"
            journalctl -u brs-backend --no-pager -n 20
            log "Container logs:"
            docker logs brs-backend --tail 20 || true
        fi
    done
else
    log "Skipping health check - service not started"
fi

# Install CloudWatch agent for monitoring (optional)
log "Installing CloudWatch agent..."
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm || handle_error "Failed to download CloudWatch agent" $LINENO
rpm -U ./amazon-cloudwatch-agent.rpm || handle_error "Failed to install CloudWatch agent" $LINENO
rm -f ./amazon-cloudwatch-agent.rpm
log "CloudWatch agent installed"

# Create startup script for manual deployment
log "Creating deployment script..."
cat > /opt/brs-backend/deploy.sh << 'EOF'
#!/bin/bash
set -e

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "Pulling latest image..."
aws ecr get-login-password --region ${aws_region} | docker login --username AWS --password-stdin ${ecr_repository_url}
docker pull ${ecr_repository_url}:latest

log "Restarting service..."
systemctl restart brs-backend

log "Waiting for service to be ready..."
sleep 15

log "Testing health endpoint..."
curl -f http://localhost/health

log "Deployment complete!"
EOF

chmod +x /opt/brs-backend/deploy.sh || handle_error "Failed to make deploy script executable" $LINENO
chown ec2-user:ec2-user /opt/brs-backend/deploy.sh || handle_error "Failed to set deploy script ownership" $LINENO
log "Deployment script created"

# Create CloudWatch configuration
log "Creating CloudWatch configuration..."
mkdir -p /opt/aws/amazon-cloudwatch-agent/etc
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'EOF'
{
    "logs": {
        "logs_collected": {
            "files": {
                "collect_list": [
                    {
                        "file_path": "/var/log/brs-setup.log",
                        "log_group_name": "/aws/ec2/brs-backend/setup",
                        "log_stream_name": "{instance_id}",
                        "timestamp_format": "%Y-%m-%d %H:%M:%S"
                    }
                ]
            }
        }
    },
    "metrics": {
        "namespace": "BRS/Backend",
        "metrics_collected": {
            "cpu": {
                "measurement": [
                    "cpu_usage_idle",
                    "cpu_usage_iowait",
                    "cpu_usage_user",
                    "cpu_usage_system"
                ],
                "metrics_collection_interval": 60
            },
            "disk": {
                "measurement": [
                    "used_percent"
                ],
                "metrics_collection_interval": 60,
                "resources": [
                    "*"
                ]
            },
            "mem": {
                "measurement": [
                    "mem_used_percent"
                ],
                "metrics_collection_interval": 60
            }
        }
    }
}
EOF
log "CloudWatch configuration created"

# Final status check
log "Final status check..."
log "Docker status: $(systemctl is-active docker)"
log "BRS backend status: $(systemctl is-active brs-backend)"
log "Running containers:"
docker ps

log "=== BRS Backend Setup Completed Successfully ==="
log "Application should be available at: http://${elastic_ip}"
log "Health check: http://${elastic_ip}/health"
log "API docs: http://${elastic_ip}/docs"
log "Setup log location: /var/log/brs-setup.log"