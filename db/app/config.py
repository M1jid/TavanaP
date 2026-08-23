"""
Application configuration settings
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Database settings
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    
    # Test database settings
    test_postgres_db: str = "test_db"
    test_postgres_host: str = "localhost"
    
    # Environment
    testing: bool = False
    debug: bool = False
    
    # Application settings
    app_name: str = "Database Service"
    app_version: str = "1.0.0"
    
    # API settings
    api_prefix: str = ""
    
    @property
    def database_url(self) -> str:
        """Get the database URL based on environment"""
        if self.testing:
            return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.test_postgres_host}/{self.test_postgres_db}"
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def test_database_url(self) -> str:
        """Get the test database URL"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.test_postgres_host}/{self.test_postgres_db}"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings() 