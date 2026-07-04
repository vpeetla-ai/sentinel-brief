"""Application settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data"
SNAPSHOT_DIR = DATA_DIR / "snapshots"
REPORT_DIR = DATA_DIR / "reports"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Sentinel Brief"
    environment: str = "development"
    log_level: str = "INFO"

    # API auth — gates POST /runs (costs an LLM call + sends email); unset = open (dev/demo)
    sentinel_api_key: str | None = None

    # LLM (optional — mock summarizer used when unset)
    openai_api_key: str | None = None
    groq_api_key: str | None = None
    llm_model: str = "gpt-4o-mini"

    # Email
    resend_api_key: str | None = None
    brief_recipient_email: str | None = None
    brief_from_email: str = "sentinel@vpeetla.ai"

    # AegisAI gateway
    aegisai_api_base_url: str | None = None
    aegisai_gateway_enabled: bool = False
    aegisai_gateway_fail_open: bool = True

    # Run behavior
    min_delta_items: int = 3
    max_items_per_source: int = 12
    snapshot_dir: Path = SNAPSHOT_DIR
    report_dir: Path = REPORT_DIR
    sources_config_path: Path = ROOT / "config" / "sources.yaml"

    # Observability (optional Langfuse)
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str = "https://cloud.langfuse.com"
    langfuse_enabled: bool = True

    # Scheduler (cron expression for APScheduler if enabled)
    cron_enabled: bool = False
    cron_hour_utc: int = 6


@lru_cache
def get_settings() -> Settings:
    return Settings()
