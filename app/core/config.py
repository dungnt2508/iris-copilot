"""
Core configuration for the application
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional
from dotenv import load_dotenv

# Get the project root directory (rag-bot-backend)
current_file = Path(__file__)
project_root = current_file.parent.parent.parent  # Go up from app/core/config.py to rag-bot-backend

# Load .env file manually before creating settings
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file)
    print(f"✅ Loaded .env from: {env_file}")
    
    # Clean environment variables (remove trailing spaces)
    for key, value in os.environ.items():
        if isinstance(value, str):
            os.environ[key] = value.strip()
else:
    print(f"⚠️  .env file not found at: {env_file}")


class AzureADConfig(BaseSettings):
    """Azure AD configuration"""
    
    # Azure AD App Registration settings
    client_id: str = Field(default="", env="AZURE_AD_CLIENT_ID")
    client_secret: str = Field(default="", env="AZURE_AD_CLIENT_SECRET")
    tenant_id: str = Field(default="", env="AZURE_AD_TENANT_ID")
    
    # Redirect URI for OAuth flow
    redirect_uri: str = Field(default="http://localhost:8000/api/v1/azure-ad/callback", env="AZURE_AD_REDIRECT_URI")
    
    # Scopes for Microsoft Graph API
    scopes: list[str] = Field(
        default=[
            "https://graph.microsoft.com/User.Read",
            "https://graph.microsoft.com/User.ReadBasic.All",
            "https://graph.microsoft.com/Group.Read.All",
            "https://graph.microsoft.com/Calendars.Read",
            "https://graph.microsoft.com/Calendars.ReadWrite",
            "https://graph.microsoft.com/Team.ReadBasic.All",
            "https://graph.microsoft.com/Channel.ReadBasic.All",
            "https://graph.microsoft.com/ChannelMessage.Send",
            "https://graph.microsoft.com/ChannelMessage.Read.All"
        ],
        env="AZURE_AD_SCOPES"
    )
    
    # Authority URL
    authority: str = Field(
        default="https://login.microsoftonline.com",
        env="AZURE_AD_AUTHORITY"
    )
    
    # Graph API endpoint
    graph_endpoint: str = Field(
        default="https://graph.microsoft.com/v1.0",
        env="AZURE_AD_GRAPH_ENDPOINT"
    )
    
    # Token cache settings
    cache_ttl: int = Field(default=3600, env="AZURE_AD_CACHE_TTL")  # 1 hour
    
    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields
    )
    
    def is_configured(self) -> bool:
        """Check if Azure AD is properly configured"""
        return bool(self.client_id and self.client_secret and self.tenant_id)


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    database_url: str = Field(default="postgresql+asyncpg://ai_user:ai_password@localhost:5433/iris_v2", env="DATABASE_URL")
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    database_pool_size: int = Field(default=20, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, env="DATABASE_MAX_OVERFLOW")
    database_pool_pre_ping: bool = Field(default=True, env="DATABASE_POOL_PRE_PING")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_pool_size: int = Field(default=10, env="REDIS_POOL_SIZE")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")
    
    # JWT
    secret_key: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Azure AD
    azure_ad: AzureADConfig = Field(default_factory=AzureADConfig)
    
    # Application settings
    app_name: str = Field(default="IRIS RAG Bot", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG", description="Enable debug mode")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # API settings
    api_v1_prefix: str = Field(default="/api/v1", env="API_V1_PREFIX")
    cors_origins: list[str] = Field(default=["*"], env="CORS_ORIGINS")
    
    # OpenAI
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")
    openai_embedding_model: str = Field(default="text-embedding-ada-002", env="OPENAI_EMBEDDING_MODEL")
    openai_max_tokens: int = Field(default=2000, env="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    
    # Azure OpenAI
    use_azure_openai: bool = Field(default=False, env="USE_AZURE_OPENAI")
    azure_openai_api_key: Optional[str] = Field(default=None, env="AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: Optional[str] = Field(default=None, env="AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment: Optional[str] = Field(default=None, env="AZURE_OPENAI_DEPLOYMENT")
    
    # Email
    smtp_host: Optional[str] = Field(default=None, env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_user: Optional[str] = Field(default=None, env="SMTP_USER")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    smtp_from_email: str = Field(default="noreply@iris.ai", env="SMTP_FROM_EMAIL")
    smtp_from_name: str = Field(default="IRIS AI", env="SMTP_FROM_NAME")
    
    # File Storage
    upload_dir: str = Field(default="uploads", env="UPLOAD_DIR")
    max_upload_size: int = Field(default=10 * 1024 * 1024, env="MAX_UPLOAD_SIZE")  # 10MB
    allowed_extensions: list[str] = Field(default=[".pdf", ".docx", ".txt", ".md", ".csv", ".json"], env="ALLOWED_EXTENSIONS")
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_period: int = Field(default=60, env="RATE_LIMIT_PERIOD")
    login_attempts_max: int = Field(default=5, env="LOGIN_ATTEMPTS_MAX")
    login_attempts_window: int = Field(default=900, env="LOGIN_ATTEMPTS_WINDOW")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # Features
    enable_registration: bool = Field(default=True, env="ENABLE_REGISTRATION")
    require_email_verification: bool = Field(default=True, env="REQUIRE_EMAIL_VERIFICATION")
    enable_social_login: bool = Field(default=False, env="ENABLE_SOCIAL_LOGIN")
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    
    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields
    )
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == "production"


# Global settings instance
settings = Settings()
