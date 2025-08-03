from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # OpenAI Configuration
    openai_api_key: str
    openai_base_url: str = "https://openrouter.ai/api/v1"
    
    # Database Configuration
    chroma_db_path: str = "./chroma_db"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # CORS Configuration
    allowed_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    
    # File Upload Configuration
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: List[str] = [".tex"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
