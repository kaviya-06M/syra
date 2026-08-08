"""
SYRA Settings
=============
Central configuration object. Loads secrets from .env, provides defaults
for everything else. Every module imports:
    from config import settings
"""

import os
from dotenv import load_dotenv

# Load .env from project root (e:\Syra\.env)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))


class _Settings:
    """Single settings object accessed as `settings.ATTRIBUTE`."""

    # ── Server ────────────────────────────────────────────────────────────
    HOST: str = os.getenv("SYRA_HOST", "127.0.0.1")
    PORT: int = int(os.getenv("SYRA_PORT", "8000"))

    # ── NVIDIA NIM ────────────────────────────────────────────────────────
    NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")
    NVIDIA_BASE_URL: str = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    NVIDIA_MODEL: str = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct")

    # ── LLM Defaults ─────────────────────────────────────────────────────
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "1024"))
    LLM_TOP_P: float = float(os.getenv("LLM_TOP_P", "0.9"))

    # ── Database ──────────────────────────────────────────────────────────
    DB_PATH: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "database", "syra.db"
    )

    # ── Agent ─────────────────────────────────────────────────────────────
    AGENT_POLL_INTERVAL: int = int(os.getenv("AGENT_POLL_INTERVAL", "5"))

    # ── Notifications ─────────────────────────────────────────────────────
    NOTIFY_COOLDOWN_SECONDS: int = int(os.getenv("NOTIFY_COOLDOWN_SECONDS", "300"))
    NOTIFY_MIN_CONFIDENCE: int = int(os.getenv("NOTIFY_MIN_CONFIDENCE", "60"))


# Singleton — every import gets the same instance
settings = _Settings()

# Also expose individual vars for backward compat with llm/provider.py
NVIDIA_API_KEY = settings.NVIDIA_API_KEY
NVIDIA_BASE_URL = settings.NVIDIA_BASE_URL
NVIDIA_MODEL = settings.NVIDIA_MODEL
LLM_TEMPERATURE = settings.LLM_TEMPERATURE
LLM_MAX_TOKENS = settings.LLM_MAX_TOKENS
LLM_TOP_P = settings.LLM_TOP_P
