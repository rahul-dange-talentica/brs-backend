variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "brs"
}

variable "ssh_public_key" {
  description = "SSH public key for EC2 access"
  type        = string
  # Generate with: ssh-keygen -t rsa -b 2048 -f ~/.ssh/brs-key
  # Then copy the content of ~/.ssh/brs-key.pub
}

