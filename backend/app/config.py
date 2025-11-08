from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    app_name: str = "Scripture Sync"
    database_url: str = "sqlite+aiosqlite:///./data/scripture.db"
    whisper_model: str = "base"
    max_latency_seconds: float = 2.0
    min_match_score: float = 0.6
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    faiss_index_path: str = "./data/faiss_index.bin"
    
    class Config:
        env_file = ".env"

settings = Settings()
