"""Configuration management for the research assistant."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Environment-driven application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    app_name: str = "Autonomous Research Assistant"
    app_env: str = "development"

    groq_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    llm_provider: str = "groq"
    llm_model: str = "llama-3.1-8b-instant"
    llm_temperature: float = 0.1
    llm_enabled: bool = True

    search_max_results: int = 5
    search_timeout: int = 30
    similarity_threshold: float = 0.7

    data_dir: Path = Field(default_factory=lambda: BASE_DIR / "data")
    knowledge_db_path: Path = Field(default_factory=lambda: BASE_DIR / "data" / "knowledge_db")
    embedding_model: str = "all-MiniLM-L6-v2"

    log_level: str = "INFO"
    log_file: Path = Field(default_factory=lambda: BASE_DIR / "logs" / "app.log")

    streamlit_port: int = 8501

    @property
    def active_llm_api_key(self) -> Optional[str]:
        if self.llm_provider.lower() == "groq":
            return self.groq_api_key
        if self.llm_provider.lower() == "openai":
            return self.openai_api_key
        return None


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.knowledge_db_path.mkdir(parents=True, exist_ok=True)
settings.log_file.parent.mkdir(parents=True, exist_ok=True)
