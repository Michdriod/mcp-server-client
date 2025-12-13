"""
Application configuration using Pydantic Settings.
Loads environment variables from .env file.
"""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Database Configuration
    database_url: str = Field(..., description="PostgreSQL connection URL")
    database_pool_size: int = Field(default=20, description="Connection pool size")
    database_max_overflow: int = Field(default=40, description="Max overflow connections")
    database_pool_timeout: int = Field(default=30, description="Pool timeout in seconds")
    
    # Redis Configuration
    redis_url: str = Field(..., description="Redis connection URL")
    redis_max_connections: int = Field(default=50, description="Max Redis connections")
    
    # LLM API Configuration (Groq, OpenAI, etc.)
    groq_api_key: str = Field(..., description="Groq API key for LLM")
    llm_model: str = Field(
        default="llama-3.3-70b-versatile",
        description="LLM model to use for SQL generation (format: provider:model-name)"
    )
    
    # Query Configuration
    query_timeout_seconds: int = Field(default=30, description="Query execution timeout")
    max_query_results: int = Field(default=1000, description="Maximum rows returned")
    query_cache_ttl_seconds: int = Field(default=300, description="Query cache TTL")
    
    # Security Configuration
    jwt_secret_key: str = Field(..., description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_access_token_expire_minutes: int = Field(default=60, description="Token expiration")
    
    # Celery Configuration
    celery_broker_url: str = Field(..., description="Celery broker URL")
    celery_result_backend: str = Field(..., description="Celery result backend URL")
    
    # Email Configuration
    email_smtp_host: str = Field(default="smtp.gmail.com", description="SMTP server host")
    email_smtp_port: int = Field(default=587, description="SMTP server port")
    email_use_tls: bool = Field(default=True, description="Use TLS for SMTP")
    email_username: str | None = Field(default=None, description="SMTP username")
    email_password: str | None = Field(default=None, description="SMTP password")
    email_from: str = Field(default="noreply@queryassistant.com", description="From email address")
    email_from_name: str | None = Field(default=None, description="Display name for email sender")
    email_from_address: str | None = Field(default=None, description="Email address for sender")
    
    # MCP Server Configuration
    mcp_server_host: str = Field(default="0.0.0.0", description="MCP server host")
    mcp_server_port: int = Field(default=8000, description="MCP server port")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    logfire_token: str | None = Field(default=None, description="Logfire API token")
    
    # Rate Limiting
    rate_limit_per_user_per_hour: int = Field(default=100, description="Rate limit per user")
    
    # Environment
    environment: str = Field(default="development", description="Environment name")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment.lower() == "development"


# Global settings instance
settings = Settings()
