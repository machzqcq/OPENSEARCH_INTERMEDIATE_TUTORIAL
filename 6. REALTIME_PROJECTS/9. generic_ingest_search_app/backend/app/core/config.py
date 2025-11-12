"""
Configuration management using Pydantic settings
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "Generic Ingest & Search API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # OpenSearch
    OPENSEARCH_HOST: str = "opensearch"
    OPENSEARCH_PORT: int = 9200
    OPENSEARCH_USERNAME: str = "admin"
    OPENSEARCH_PASSWORD: str = "Developer@123"
    OPENSEARCH_USE_SSL: bool = True
    OPENSEARCH_VERIFY_CERTS: bool = False
    
    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://frontend:3000"
    ]
    
    # Authentication (simple token-based for demo)
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Demo users (in production, use proper user database)
    DEMO_USERS: dict = {
        "admin": {
            "username": "admin",
            "password": "admin123",  # In production: hashed password
            "email": "admin@example.com"
        },
        "user": {
            "username": "user",
            "password": "user123",
            "email": "user@example.com"
        }
    }
    
    # File upload
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: List[str] = [".csv", ".xlsx", ".jsonl"]
    UPLOAD_DIR: str = "/tmp/uploads"
    
    # Embedding models to pre-deploy
    EMBEDDING_MODELS: List[dict] = [
        {
            "name": "all-MiniLM-L6-v2",
            "model_name": "huggingface/sentence-transformers/all-MiniLM-L6-v2",
            "version": "1.0.1",
            "dimension": 384,
            "description": "Fast and efficient for general semantic search"
        },
        {
            "name": "all-mpnet-base-v2",
            "model_name": "huggingface/sentence-transformers/all-mpnet-base-v2",
            "version": "1.0.1",
            "dimension": 768,
            "description": "Higher quality embeddings, slower but more accurate"
        }
    ]
    
    # OpenAI Configuration (for Plan-Execute-Reflect agent)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
