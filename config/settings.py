"""
config/settings.py

Centralised configuration loaded from environment variables.
All constants, thresholds, and external URLs live here — never in source files.
"""

import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class Settings:
    """
    Application-wide settings loaded from environment variables at startup.

    Using a dataclass makes settings testable and injectable rather than
    relying on scattered os.getenv() calls throughout the codebase.
    """

    # ── OpenRouter ────────────────────────────────────────────────────────────
    openrouter_api_keys: List[str] = field(default_factory=list)
    openrouter_model: str = "meta-llama/llama-3.2-3b-instruct:free"
    openrouter_base_url: str = "https://openrouter.ai/api/v1/chat/completions"
    openrouter_http_referer: str = "https://github.com/ai-code-reviewer"
    openrouter_app_title: str = "GitHub AI Code Reviewer"

    # ── GitHub ────────────────────────────────────────────────────────────────
    github_token: str = ""
    github_api_base: str = "https://api.github.com"
    pr_number: int = 0
    repo_owner: str = ""
    repo_name: str = ""

    # ── Slack ─────────────────────────────────────────────────────────────────
    slack_webhook_url: str = ""

    # ── Agent thresholds ──────────────────────────────────────────────────────
    risk_threshold: int = 50
    max_diff_tokens: int = 12000

    def __post_init__(self) -> None:
        """Load all values from environment variables after dataclass init."""
        # Collect the three rotating API keys (skip any that are unset)
        raw_keys = [
            os.getenv("OPENROUTER_API_KEY_1", ""),
            os.getenv("OPENROUTER_API_KEY_2", ""),
            os.getenv("OPENROUTER_API_KEY_3", ""),
        ]
        self.openrouter_api_keys = [k for k in raw_keys if k]

        self.openrouter_model = os.getenv(
            "OPENROUTER_MODEL", self.openrouter_model
        )
        self.openrouter_base_url = os.getenv(
            "OPENROUTER_BASE_URL", self.openrouter_base_url
        )
        self.openrouter_http_referer = os.getenv(
            "OPENROUTER_HTTP_REFERER", self.openrouter_http_referer
        )
        self.openrouter_app_title = os.getenv(
            "OPENROUTER_APP_TITLE", self.openrouter_app_title
        )

        self.github_token = os.getenv("GITHUB_TOKEN", "")
        self.github_api_base = os.getenv("GITHUB_API_BASE", self.github_api_base)

        # PR context injected by GitHub Actions environment
        try:
            self.pr_number = int(os.getenv("PR_NUMBER", "0"))
        except ValueError:
            self.pr_number = 0

        self.repo_owner = os.getenv("REPO_OWNER", "")
        self.repo_name = os.getenv("REPO_NAME", "")

        self.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")

        try:
            self.risk_threshold = int(os.getenv("RISK_THRESHOLD", "50"))
        except ValueError:
            self.risk_threshold = 50

        try:
            self.max_diff_tokens = int(os.getenv("MAX_DIFF_TOKENS", "12000"))
        except ValueError:
            self.max_diff_tokens = 12000

    def validate(self) -> None:
        """
        Raise ValueError if any critical setting is missing.

        Called at agent startup so failures are loud and immediate rather
        than surfacing deep inside a network call.
        """
        missing: List[str] = []

        if not self.openrouter_api_keys:
            missing.append(
                "OPENROUTER_API_KEY_1 / OPENROUTER_API_KEY_2 / OPENROUTER_API_KEY_3 "
                "(at least one required)"
            )
        if not self.github_token:
            missing.append("GITHUB_TOKEN")
        if not self.pr_number:
            missing.append("PR_NUMBER")
        if not self.repo_owner:
            missing.append("REPO_OWNER")
        if not self.repo_name:
            missing.append("REPO_NAME")

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )


# Module-level singleton — import this everywhere instead of instantiating again
settings = Settings()
