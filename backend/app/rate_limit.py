"""Per-IP rate limiting for the endpoints that do real work.

Without this, anyone with the URL can hit /api/analyze in a tight loop and
get our server's IP rate-limited by Yahoo Finance (yfinance is an
unofficial scraper, not a real API, and reacts poorly to bursty traffic).

Limits live here as one shared object so main.py (registers the exception
handler) and each router (applies the per-route decorator) both reference
the same Limiter instance.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# /api/analyze costs a yfinance fetch -- generous enough for a real user
# iterating on their portfolio, tight enough to blunt a scripted loop.
ANALYZE_RATE_LIMIT = "20/minute"

# /api/explain is now a pure template fill (no external API call), so it's
# cheap to serve -- same generous limit as analyze, just to bound compute
# from a scripted loop rather than to guard against any real cost.
EXPLAIN_RATE_LIMIT = "20/minute"
