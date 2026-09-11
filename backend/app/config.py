"""
Configuration settings for CheapCart application.
Loaded from environment variables with sensible defaults.
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "CheapCart"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/cheapcart.db"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Parser settings
    CACHE_TTL_HOURS: int = 6  # How long to cache search results
    REQUEST_DELAY_MS: int = 500  # Delay between requests to avoid rate limiting
    MAX_RETRIES: int = 3
    REQUEST_TIMEOUT_SEC: int = 30
    
    # User agent rotation
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
