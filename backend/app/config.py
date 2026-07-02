"""Environment-driven settings, read once at import time.

Kept as plain module-level constants (no pydantic-settings dependency) --
CORS origins are the only thing left to configure here. Everything the app
talks to (yfinance, the Treasury Fiscal Data API) is free and keyless, so
there's nothing to run this app that requires signing up for anything.
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
