from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path


BACKEND_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    # OpenAI Configuration
    openai_api_key: str
    openai_base_url: str = "https://openrouter.ai/api/v1"
    requesty_api_key: str = ""
    requesty_base_url: str = "https://router.requesty.ai/v1"

    # Model Configurations
    default_tailor_model: str = "google/gemma-4-31b-it:free"
    keyword_extraction_model: str = "deepseek/deepseek-chat-v3-0324:free"
    match_analysis_model: str = "deepseek/deepseek-chat-v3-0324:free"
    outreach_model: str = "google/gemma-4-31b-it:free"
    requesty_tailor_model: str = "google/gemma-4-31b-it"
    requesty_auxiliary_model: str = "nvidia/nemotron-3-ultra-550b-a55b"

    # Database Configuration
    chroma_db_path: str = "./chroma_db"

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # CORS Configuration
    allowed_origins: List[str] = [
        "http://localhost:5173", "http://localhost:3000"]

    # Rate Limiting
    rate_limit_per_minute: int = 60

    # File Upload Configuration
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: List[str] = [".tex"]

    class Config:
        env_file = str(BACKEND_ENV_FILE)
        case_sensitive = False


settings = Settings()
