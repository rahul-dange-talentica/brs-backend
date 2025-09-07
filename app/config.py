import os
from pydantic_settings import BaseSettings
from typing import List
from pydantic import field_validator
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = "postgresql://brs_user:brs_password@localhost:5432/brs_dev"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production-this-should-be-a-long-random-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15  # 15 minutes as per PRD requirement
    
    # Application
    app_name: str = "Book Review System API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # CORS
    backend_cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    allowed_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Additional Security Settings
    trusted_hosts_str: str = "localhost,127.0.0.1,testserver,*.brs.example.com"
    trusted_hosts: List[str] = ["localhost", "127.0.0.1", "testserver", "*.brs.example.com"]
    
    # Environment
    environment: str = "development"
    
    # AWS Configuration
    aws_region: str = "us-east-1"
    aws_secrets_manager: bool = False
    
    # Monitoring
    enable_metrics: bool = True
    log_level: str = "INFO"
    

    
    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Parse trusted hosts from string
        if hasattr(self, 'trusted_hosts_str') and self.trusted_hosts_str:
            self.trusted_hosts = [host.strip() for host in self.trusted_hosts_str.split(',') if host.strip()]
        
        # Update CORS origins for production
        if self.environment == "production":
            self.allowed_origins = ["https://brs.example.com"]
            # Don't override trusted_hosts in production if it was set via environment
            if not hasattr(self, 'trusted_hosts_str') or not self.trusted_hosts_str:
                self.trusted_hosts = ["api.brs.example.com", "*.brs.example.com"]
            self.debug = False
            self.aws_secrets_manager = True
        
        # Load secrets from AWS Secrets Manager in production
        if self.aws_secrets_manager and self.environment == "production":
            self._load_aws_secrets()
    
    def _load_aws_secrets(self):
        """Load secrets from AWS Secrets Manager."""
        try:
            import boto3
            import json
            
            client = boto3.client('secretsmanager', region_name=self.aws_region)
            
            response = client.get_secret_value(SecretId='brs/production/secrets')
            secrets = json.loads(response['SecretString'])
            
            # Update configuration with secrets
            if 'database-url' in secrets:
                self.database_url = secrets['database-url']
            if 'jwt-secret' in secrets:
                self.secret_key = secrets['jwt-secret']
                
            logger.info("Successfully loaded secrets from AWS Secrets Manager")
            
        except ImportError:
            logger.warning("boto3 not available, skipping AWS Secrets Manager")
        except Exception as e:
            logger.error(f"Failed to load secrets from AWS Secrets Manager: {e}")
            # Don't raise exception to prevent startup failures in development


settings = Settings()
