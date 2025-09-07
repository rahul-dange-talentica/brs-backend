provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "terraform"
      Tier        = "free"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}

# Random passwords
resource "random_password" "db_password" {
  length      = 32
  special     = true
  # Exclude characters that are invalid for RDS passwords: '/', '@', '"', and spaces
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "random_password" "jwt_secret" {
  length  = 64
  special = true
}

# VPC (Free)
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-vpc-free"
  }
}

# Internet Gateway (Free)
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-igw-free"
  }
}

# Public Subnets (Free - no NAT Gateway needed)
resource "aws_subnet" "public" {
  count = 2

  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-${count.index + 1}-free"
  }
}

# Route Table (Free)
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.project_name}-public-rt-free"
  }
}

resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Security Group for Application (Free)
resource "aws_security_group" "app" {
  name_prefix = "${var.project_name}-app-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Restrict this to your IP in production
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-app-sg-free"
  }
}

# Security Group for RDS (Free)
resource "aws_security_group" "rds" {
  name_prefix = "${var.project_name}-rds-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-rds-sg-free"
  }
}

# RDS Subnet Group (Free)
resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnet-group-free"
  subnet_ids = aws_subnet.public[*].id

  tags = {
    Name = "${var.project_name}-db-subnet-group-free"
  }
}

# RDS PostgreSQL (FREE TIER ELIGIBLE)
resource "aws_db_instance" "main" {
  identifier = "${var.project_name}-database-free"
  
  engine         = "postgres"
  engine_version = "15"
  instance_class = "db.t3.micro"  # FREE TIER
  
  allocated_storage     = 20  # FREE TIER (up to 20GB)
  max_allocated_storage = 20  # Prevent auto-scaling beyond free tier
  storage_type         = "gp2"
  storage_encrypted    = true
  
  db_name  = "${var.project_name}_production"
  username = "${var.project_name}_admin"
  password = random_password.db_password.result
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  multi_az = false  # Single AZ for free tier
  
  skip_final_snapshot = true  # Skip final snapshot for free tier
  
  tags = {
    Name = "${var.project_name}-database-free"
  }
}

# ECR Repository (FREE TIER - 500MB)
resource "aws_ecr_repository" "main" {
  name                 = "${var.project_name}-backend-free"
  image_tag_mutability = "MUTABLE"
  force_delete         = true  # Allow deletion even with images
  
  image_scanning_configuration {
    scan_on_push = true
  }
  
  tags = {
    Name = "${var.project_name}-backend-ecr-free"
  }
}

# Note: Docker image should be pushed separately using deployment scripts
# Infrastructure and application deployment are kept separate for better practices

# AWS Secrets Manager (Free)
resource "aws_secretsmanager_secret" "brs_secrets" {
  name = "brs/production/secrets"
  description = "Secrets for BRS Backend Application"
  
  tags = {
    Name = "${var.project_name}-secrets-free"
  }
}

# AWS Secrets Manager Secret Version (Free)
resource "aws_secretsmanager_secret_version" "brs_secrets" {
  secret_id = aws_secretsmanager_secret.brs_secrets.id
  secret_string = jsonencode({
    database-url = "postgresql://${aws_db_instance.main.username}:${random_password.db_password.result}@${aws_db_instance.main.endpoint}/${aws_db_instance.main.db_name}"
    jwt-secret   = random_password.jwt_secret.result
  })
}

# Key Pair for EC2 (Free)
resource "aws_key_pair" "main" {
  key_name   = "${var.project_name}-key-free"
  public_key = var.ssh_public_key
}

# IAM Role for EC2 Instance (Free)
resource "aws_iam_role" "ec2_role" {
  name = "${var.project_name}-ec2-role-free"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-ec2-role-free"
  }
}

# IAM Policy for ECR and Secrets Manager Access (Free)
resource "aws_iam_policy" "ecr_policy" {
  name = "${var.project_name}-ecr-policy-free"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.brs_secrets.arn
      }
    ]
  })
}

# Attach ECR Policy to Role (Free)
resource "aws_iam_role_policy_attachment" "ecr_policy_attachment" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = aws_iam_policy.ecr_policy.arn
}

# IAM Instance Profile (Free)
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.project_name}-ec2-profile-free"
  role = aws_iam_role.ec2_role.name
}

# EC2 Instance (Free Tier)
resource "aws_instance" "app" {
  ami                     = "ami-0c02fb55956c7d316"  # Amazon Linux 2 (free tier eligible)
  instance_type           = "t3.micro"               # FREE TIER
  subnet_id               = aws_subnet.public[0].id
  vpc_security_group_ids  = [aws_security_group.app.id]
  key_name               = aws_key_pair.main.key_name
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name
  associate_public_ip_address = true

  user_data = templatefile("${path.module}/user-data.sh", {
    ecr_repository_url = aws_ecr_repository.main.repository_url
    database_url       = "postgresql://${aws_db_instance.main.username}:${random_password.db_password.result}@${aws_db_instance.main.endpoint}/${aws_db_instance.main.db_name}"
    jwt_secret         = random_password.jwt_secret.result
    aws_region         = var.aws_region
    elastic_ip         = aws_eip.app.public_ip
  })

  # Explicit dependencies to ensure everything is ready before EC2 starts
  depends_on = [
    aws_iam_role_policy_attachment.ecr_policy_attachment,
    aws_secretsmanager_secret_version.brs_secrets,
    aws_db_instance.main
  ]

  tags = {
    Name = "${var.project_name}-app-free"
  }
}

# Elastic IP for Application (Free - 1 EIP per account)
resource "aws_eip" "app" {
  domain = "vpc"
  
  tags = {
    Name = "${var.project_name}-eip-free"
  }
}

# Associate Elastic IP with EC2 Instance
resource "aws_eip_association" "app" {
  instance_id   = aws_instance.app.id
  allocation_id = aws_eip.app.id
}

# Output database connection string to a local file for easy access
resource "local_file" "database_config" {
  content = templatefile("${path.module}/config.env.template", {
    database_url = "postgresql://${aws_db_instance.main.username}:${random_password.db_password.result}@${aws_db_instance.main.endpoint}/${aws_db_instance.main.db_name}"
    jwt_secret   = random_password.jwt_secret.result
  })
  filename = "${path.module}/../../.env.production"
}
