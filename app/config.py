"""Application configuration module.

Reads environment variables safely using python-dotenv and Pydantic.
Never exposes sensitive keys in logs or exceptions.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Base directory for the visibility-engine project
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load .env if present in root
ENV_FILE = PROJECT_ROOT / ".env"
if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE)
else:
    load_dotenv()  # Fallback to standard environment


class Settings(BaseModel):
    """Immutable application settings container."""

    # Application metadata
    app_name: str = Field(
        default=os.getenv("APP_NAME", "IncuBrix Visibility Engine")
    )
    app_env: str = Field(default=os.getenv("APP_ENV", "development"))
    debug: bool = Field(
        default=os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
    )

    # Server config
    host: str = Field(default=os.getenv("HOST", "127.0.0.1"))
    port: int = Field(default=int(os.getenv("PORT", "8001")))
    api_v1_prefix: str = Field(default=os.getenv("API_V1_PREFIX", "/v1"))

    # Logging
    log_level: str = Field(default=os.getenv("LOG_LEVEL", "INFO").upper())

    # Storage paths
    database_url: str = Field(
        default=os.getenv(
            "DATABASE_URL", f"sqlite:///{PROJECT_ROOT / 'data' / 'visibility.db'}"
        )
    )
    data_dir: Path = Field(
        default_factory=lambda: Path(os.getenv("DATA_DIR", PROJECT_ROOT / "data")).resolve()
    )
    evidence_dir: Path = Field(
        default_factory=lambda: Path(
            os.getenv("EVIDENCE_DIR", PROJECT_ROOT / "evidence")
        ).resolve()
    )
    outputs_dir: Path = Field(
        default_factory=lambda: Path(
            os.getenv("OUTPUTS_DIR", PROJECT_ROOT / "outputs")
        ).resolve()
    )

    # Brand tracking
    incubrix_brand_name: str = Field(
        default=os.getenv("INCUBRIX_BRAND_NAME", "IncuBrix")
    )
    incubrix_domains: List[str] = Field(
        default_factory=lambda: [
            d.strip().lower()
            for d in os.getenv("INCUBRIX_DOMAINS", "incubrix.com,app.incubrix.com").split(",")
            if d.strip()
        ]
    )

    # External Search & AI Provider Credentials (Safe defaults, never hardcoded)
    serp_api_key: Optional[str] = Field(default=os.getenv("SERP_API_KEY"))
    serp_api_url: str = Field(
        default=os.getenv("SERP_API_URL", "https://google.serper.dev/search")
    )
    ai_provider_api_key: Optional[str] = Field(default=os.getenv("AI_PROVIDER_API_KEY") or os.getenv("PERPLEXITY_API_KEY"))
    ai_provider_api_url: str = Field(
        default=os.getenv(
            "AI_PROVIDER_API_URL", "https://api.perplexity.ai/chat/completions"
        )
    )
    ai_provider_model: str = Field(
        default=os.getenv("AI_PROVIDER_MODEL", "sonar")
    )

    # Specific AI Assistant Provider Credentials
    openai_api_key: Optional[str] = Field(default=os.getenv("OPENAI_API_KEY"))
    openai_api_url: str = Field(
        default=os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions")
    )
    openai_model: str = Field(default=os.getenv("OPENAI_MODEL", "gpt-4o"))

    gemini_api_key: Optional[str] = Field(default=os.getenv("GEMINI_API_KEY"))
    gemini_api_url: str = Field(
        default=os.getenv(
            "GEMINI_API_URL",
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent",
        )
    )
    gemini_model: str = Field(default=os.getenv("GEMINI_MODEL", "gemini-1.5-pro"))

    claude_api_key: Optional[str] = Field(default=os.getenv("CLAUDE_API_KEY"))
    claude_api_url: str = Field(
        default=os.getenv("CLAUDE_API_URL", "https://api.anthropic.com/v1/messages")
    )
    claude_model: str = Field(default=os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022"))


    # Networking
    http_request_timeout_seconds: float = Field(
        default=float(os.getenv("HTTP_REQUEST_TIMEOUT_SECONDS", "10.0"))
    )

    def ensure_directories(self) -> None:
        """Create required runtime directories if they do not exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    settings = Settings()
    settings.ensure_directories()
    return settings
