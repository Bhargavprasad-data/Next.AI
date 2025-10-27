"""
Configuration settings for Next AI
"""
from pydantic import field_validator
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database Configuration
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "ai_app"
    
    # OpenAI Configuration
    openai_api_key: str = ""  # Set via environment variable OPENAI_API_KEY
    
    # Gemini Configuration
    gemini_api_key: str = ""  # Set via environment variable GEMINI_API_KEY
    
    # JWT Configuration
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    
    # RAG Configuration
    vector_db_path: str = "./vector_store"
    embedding_model: str = "text-embedding-3-small"
    
    @field_validator('cors_origins')
    @classmethod
    def parse_cors_origins(cls, v: str) -> List[str]:
        """Parse comma-separated CORS origins"""
        return [origin.strip() for origin in v.split(',')]
    
    @field_validator('openai_api_key')
    @classmethod
    def validate_openai_key(cls, v: str) -> str:
        if not v or len(v) < 10:
            print("⚠️  Warning: OpenAI API key appears to be invalid or missing")
        return v
    
    @field_validator('gemini_api_key')
    @classmethod
    def validate_gemini_key(cls, v: str) -> str:
        if not v or len(v) < 10:
            print("⚠️  Warning: Gemini API key appears to be invalid or missing")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

