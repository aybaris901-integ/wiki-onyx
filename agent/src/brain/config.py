"""Environment-driven settings. Everything has a working default so the demo runs with zero config."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = AGENT_DIR.parent


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


@dataclass
class Settings:
    demo_data_dir: Path = field(default_factory=lambda: Path(_env("DEMO_DATA_DIR") or REPO_DIR / "demo-data"))
    chroma_dir: Path = field(default_factory=lambda: Path(_env("CHROMA_DIR") or AGENT_DIR / ".chroma"))
    repo_slug: str = field(default_factory=lambda: _env("REPO_SLUG", "aybaris901-integ/wiki-onyx"))
    repo_branch: str = field(default_factory=lambda: _env("REPO_BRANCH", "company-brain"))
    openrouter_api_key: str = field(default_factory=lambda: _env("OPENROUTER_API_KEY"))
    openrouter_model: str = field(default_factory=lambda: _env("OPENROUTER_MODEL", "anthropic/claude-sonnet-4.5"))
    anthropic_api_key: str = field(default_factory=lambda: _env("ANTHROPIC_API_KEY"))
    anthropic_model: str = field(default_factory=lambda: _env("ANTHROPIC_MODEL", "claude-sonnet-4-5"))
    onyx_url: str = field(default_factory=lambda: _env("ONYX_URL").rstrip("/"))
    onyx_api_key: str = field(default_factory=lambda: _env("ONYX_API_KEY"))
    embed_model: str = field(default_factory=lambda: _env("EMBED_MODEL", "all-MiniLM-L6-v2"))
    port: int = field(default_factory=lambda: int(_env("PORT", "8000")))
    rate_limit_per_minute: int = field(default_factory=lambda: int(_env("RATE_LIMIT_PER_MINUTE", "10")))
    llm_timeout_s: float = 20.0

    @property
    def llm_name(self) -> str:
        if self.openrouter_api_key:
            return f"openrouter/{self.openrouter_model}"
        if self.anthropic_api_key:
            return f"anthropic/{self.anthropic_model}"
        return "extractive"

    def blob_url(self, repo_path: str) -> str:
        return f"https://github.com/{self.repo_slug}/blob/{self.repo_branch}/{repo_path.lstrip('/')}"


settings = Settings()
