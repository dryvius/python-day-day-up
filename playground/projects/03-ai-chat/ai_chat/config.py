"""Environment-backed application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SYSTEM_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "system.md"


def load_system_prompt() -> str:
    """Load the versioned default prompt."""

    return DEFAULT_SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()


class Settings(BaseSettings):
    """Runtime settings with safe FakeLLM defaults."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "PythonDayDayUp AI Chat"
    llm_mode: str = "fake"
    model_name: str = "fake-chat-v1"
    system_prompt: str = Field(default_factory=load_system_prompt)
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: SecretStr | None = None
    llm_timeout_seconds: float = Field(default=20.0, gt=0)
    llm_max_retries: int = Field(default=2, ge=0, le=5)
    context_budget_chars: int = Field(default=4000, ge=256)
    max_history_messages: int = Field(default=12, ge=2)
    stream_chunk_chars: int = Field(default=8, ge=1, le=256)
    heartbeat_seconds: float = Field(default=15.0, gt=0)


@lru_cache
def get_settings() -> Settings:
    """Return process-wide settings."""

    return Settings()
