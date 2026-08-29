import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Operating Mode
    MOCK_MODE: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./founder0.db"
    
    # Daytona API
    DAYTONA_API_KEY: Optional[str] = None
    DAYTONA_API_URL: str = "https://app.daytona.io/api"
    DAYTONA_TARGET: str = "us"
    
    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password123"
    
    # Nosana LLM
    NOSANA_API_KEY: Optional[str] = None
    NOSANA_BASE_URL: str = "https://api.nosana.io/v1"
    NOSANA_MODEL_ID: str = "deepseek-coder"
    
    # Fallback LLM
    FALLBACK_LLM_PROVIDER: str = "anthropic"
    FALLBACK_LLM_API_KEY: Optional[str] = None
    FALLBACK_LLM_MODEL: str = "claude-3-5-sonnet-20241022"
    
    # Optional TTS
    TTS_PROVIDER: str = "none"
    TTS_API_KEY: Optional[str] = None
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
