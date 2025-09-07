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
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
  }
  
  backend "s3" {
    bucket = "brs-terraform-state-free-4804"
    key    = "free-tier/terraform.tfstate"
    region = "us-east-1"
    
    dynamodb_table = "brs-terraform-locks-free"
    encrypt        = true
  }
}
