output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnets" {
  description = "List of IDs of public subnets"
  value       = aws_subnet.public[*].id
}

output "rds_instance_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "rds_instance_port" {
  description = "RDS instance port"
  value       = aws_db_instance.main.port
}

output "rds_instance_username" {
  description = "RDS instance root username"
  value       = aws_db_instance.main.username
  sensitive   = true
}

output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.main.repository_url
}

output "elastic_ip" {
  description = "Elastic IP for the application"
  value       = aws_eip.app.public_ip
}

output "application_url" {
  description = "Application URL"
  value       = "http://${aws_eip.app.public_ip}"
}

output "ssh_command" {
  description = "SSH command to connect to instances"
  value       = "ssh -i ~/.ssh/brs-key ec2-user@${aws_eip.app.public_ip}"
}

output "database_url" {
  description = "Database connection URL"
  value       = "postgresql://${aws_db_instance.main.username}:${random_password.db_password.result}@${aws_db_instance.main.endpoint}/${aws_db_instance.main.db_name}"
  sensitive   = true
}

output "free_tier_usage" {
  description = "Free tier resource usage"
  value = {
    ec2_hours_used     = "750 hours/month (t3.micro)"
    rds_hours_used     = "750 hours/month (db.t3.micro)"
    rds_storage_used   = "20 GB"
    ecr_storage_limit  = "500 MB"
    estimated_cost     = "$0/month (within free tier limits)"
  }
}

