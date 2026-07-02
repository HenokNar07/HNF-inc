"""Environment-driven settings, read once at import time.

Kept as plain module-level constants (no pydantic-settings dependency)
consistent with how math_engine.risk_free reads FRED_API_KEY -- one pattern
for "read this env var, fall back to a sane default" across the codebase.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

# Vite's default dev port. Add more via CORS_ORIGINS="http://a.com,http://b.com".
_default_origins = "http://localhost:5173,http://127.0.0.1:5173"
CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", _default_origins).split(",")
    if origin.strip()
]

FRED_API_KEY = os.environ.get("FRED_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# claude-sonnet-5 balances quality and latency for a short narration task;
# not the reasoning-heaviest model since this is templated explanation, not
# open-ended analysis.
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")
