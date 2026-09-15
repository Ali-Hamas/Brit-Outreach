import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Brit Outreach System"
    API_V1_STR: str = "/api/v1"
    
    # Database - defaults to SQLite (no install needed)
    DATABASE_URL: str = "sqlite:///./brit_outreach.db"

    # Redis Connection (optional - in-memory fallback if not available)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: Optional[str] = None

    # Third Party API Keys & CRM
    APOLLO_API_KEY: Optional[str] = None
    HUBSPOT_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    BRITCRM_API_URL: str = "https://truecrm.online/api/mcp"
    BRITCRM_BEARER_TOKEN: Optional[str] = None

    # Social Listening APIs
    REDDIT_CLIENT_ID: Optional[str] = None
    REDDIT_CLIENT_SECRET: Optional[str] = None
    REDDIT_USER_AGENT: str = "BritOutreach/1.0"
    GOOGLE_CUSTOM_SEARCH_API_KEY: Optional[str] = None
    GOOGLE_CSE_ID: Optional[str] = None
    GOOGLE_PLACES_API_KEY: Optional[str] = None
    GOOGLE_PAGESPEED_API_KEY: Optional[str] = None
    BUILTWITH_API_KEY: Optional[str] = None

    # Company Info for Outreach
    COMPANY_NAME: str = "Britsync AI"
    COMPANY_SENDER_NAME: str = "the Britsync AI team"

    # Tracking Host
    BASE_TRACKING_URL: str = "http://localhost:8000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def __init__(self, **values):
        super().__init__(**values)
        if not self.REDIS_URL:
            self.REDIS_URL = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

settings = Settings()
