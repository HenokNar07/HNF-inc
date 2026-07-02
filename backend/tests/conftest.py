import os
import sys

# backend/app is a plain (non-installed) package -- make sure `backend/` is on
# sys.path regardless of where pytest's cwd/rootdir ends up, so `import app.main`
# works the same way it does when uvicorn runs from the backend/ directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402 -- must follow the sys.path fixup above


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """The Limiter's counters are process-global, not per-test. Without this,
    a test that deliberately exhausts the limit (or just runs late in a long
    session) can 429 every test that runs after it, regardless of test
    order -- reset before every test so each one starts with a clean bucket.
    """
    from app.rate_limit import limiter

    limiter.reset()
