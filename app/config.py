"""Application configuration"""

from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    api_title: str = "AI DevOps Team"
    api_version: str = "1.0.0"

    llm_provider: str = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4"
    openai_temperature: float = 0.3
    openai_max_tokens: int = 2000
    openai_timeout: int = 10

    local_llm_model: str = "gpt2"
    local_llm_path: str = ""
    local_llm_url: str = ""
    local_llm_device: str = "cpu"

    investigation_timeout: int = 20
    agent_timeout: int = 10
    retry_attempts: int = 1

    cors_origins: List[str] = ["*"]

    log_level: str = "INFO"

    database_url: str = ""
    redis_url: str = ""

    github_token: str = ""
    github_repo: str = ""

    kubernetes_kubeconfig: Optional[str] = None
    kubernetes_namespace: str = "default"

    aws_region: str = ""

    prometheus_url: str = ""
    grafana_url: str = ""
    grafana_api_key: str = ""

    slack_token: str = ""
    slack_channel: str = ""

    env: str = "development"
    debug: bool = True

    class Config:
        """Pydantic settings configuration."""
        env_file = ".env"
        case_sensitive = False


settings = Settings()
