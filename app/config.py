from pydantic_settings import BaseSettings


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
    backend_cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    allowed_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Additional Security Settings
    trusted_hosts: list[str] = ["localhost", "127.0.0.1", "testserver", "*.brs.example.com"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
