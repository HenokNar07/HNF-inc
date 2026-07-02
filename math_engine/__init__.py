"""Mean-variance portfolio analysis math engine.

Pipeline: data.py (prices) -> stats.py (mu/cov/beta) -> optimize.py (frontier/max Sharpe)
-> pipeline.py (orchestration, produces JSON-ready output for the API layer).

Nothing in this package touches an LLM. All numbers here are deterministic.
"""
