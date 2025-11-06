from pydantic_settings import BaseSettings # type: ignore
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Chatbot API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour
    RESET_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour
    
    # SendGrid
    SENDGRID_API_KEY: str
    FROM_EMAIL: str
    
    # Google Gemini
    GEMINI_API_KEY: str
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_TYPES: list = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

