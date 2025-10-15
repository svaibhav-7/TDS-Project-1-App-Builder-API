from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "App Builder API"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    
    # GitHub settings
    GITHUB_TOKEN: str = Field(..., env="GITHUB_TOKEN")
    GITHUB_ORG: Optional[str] = os.getenv("GITHUB_ORG")
    
    # LLM settings
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4")
    
    # API settings
    API_PREFIX: str = "/api/v1"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # CORS settings
    CORS_ORIGINS: list = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Initialize settings
settings = Settings()
