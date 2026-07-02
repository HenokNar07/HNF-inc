# HNF, inc.

Mean-variance portfolio analysis: real Markowitz math, explained in plain
language. This repo is being built bottom-up: **math engine first** (this
stage), then a FastAPI wrapper, then a React front end.

## Stage 1: math engine (`math_engine/`)

A standalone, UI-free Python package. No FastAPI, no React, no LLM calls --
just the deterministic computation, verifiable against a tool like Portfolio
Visualizer before anything is built on top of it.

### Module layout

| File | Responsibility |
|---|---|
| `data.py` | Fetch adjusted close prices (yfinance), resample to monthly returns. Always pulls SPY alongside requested tickers, for beta. |
| `risk_free.py` | 3-month T-bill rate from FRED, hardcoded fallback if `FRED_API_KEY` isn't set. |
| `stats.py` | Annualized mean/covariance, portfolio return/variance/Sharpe, per-asset beta. |
| `optimize.py` | Efficient frontier, max Sharpe, min variance -- hand-rolled `scipy.optimize.minimize` (SLSQP), not a black-box library, so the constrained QP is visible. |
| `types.py` | Pydantic models for the output -- doubles as the future FastAPI response schema. |
| `pipeline.py` | `run_mvo(...)`, the one function that wires everything together and handles edge cases (single ticker, invalid ticker, bad weight sums, infeasible weight caps). |

### Setup

```bash
cd portfolio-frontier
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .          # so `import math_engine` works from anywhere
cp .env.example .env      # optional: add FRED_API_KEY for a live risk-free rate
```

### Run the tests

```bash
pytest                 # fast, offline tests only (25 tests) -- run this constantly
pytest -m network       # + 1 integration test that hits yfinance/FRED for real
```

What's actually being checked (see `tests/test_optimize.py`,
`tests/test_stats.py`):
- Two-asset portfolio variance matches the textbook closed-form formula
  (`w1^2*v1 + w2^2*v2 + 2*w1*w2*cov12`), independent of the matrix computation.
- Two-asset min-variance-at-target-return matches the closed-form weight formula.
- All optimizer outputs sum to 1 and are long-only (>= 0).
- The max-Sharpe portfolio has the best Sharpe ratio of any point on the frontier
  (the actual optimality condition, not just "it's on the curve").
- The global min-variance portfolio has the lowest std dev of any frontier point.
- Beta recovery on synthetic data with a known, exact beta.
- Edge cases: single ticker, invalid ticker, mismatched lengths, duplicate
  tickers, weights that don't sum to 100, negative/zero weights, infeasible
  max-weight caps.

### Run the sample portfolio

```bash
python scripts/run_sample.py
# or with your own portfolio:
python scripts/run_sample.py --tickers VOO,AAPL,BND --weights 40,35,25 --years 5
```

This prints per-asset stats, the risk-free rate, your portfolio's stats, the
max-Sharpe and min-variance portfolios, a sample of frontier points, and the
correlation matrix -- everything you need to cross-check against Portfolio
Visualizer's Efficient Frontier tool (same tickers/weights/period, arithmetic
mean returns). The script's docstring has the exact comparison steps.

## Key architectural decisions

- **Arithmetic annualization** (`monthly_mean * 12`, `monthly_cov * 12`),
  not geometric compounding. Markowitz optimization needs the mean/variance
  of the *return distribution*, which is what arithmetic annualization gives
  you -- geometric (CAGR) annualization would understate variance's role and
  isn't what Portfolio Visualizer's frontier tool uses either.
- **scipy.optimize.minimize (SLSQP), not PyPortfolioOpt.** Every constrained
  QP in `optimize.py` is the textbook formulation, solved numerically. Slower
  to write than calling a library function, but the math is auditable line by
  line -- which matters for a product whose entire pitch is explaining the
  math.
- **Frontier target-return range is solved, not guessed.** Without a
  max-weight cap, the achievable return range for a long-only portfolio is
  exactly `[min(mu), max(mu)]` (100% in the worst/best single asset). *With*
  a cap (e.g. no asset above 40%), those extremes become infeasible -- you
  literally cannot reach them under the constraints. `_achievable_return_range`
  in `optimize.py` solves two tiny LPs (via `scipy.optimize.linprog`) to find
  the true achievable range first, then traces the frontier within it. This
  was caught during manual verification (see below): the naive `[min(mu),
  max(mu)]` version treated ~40% of frontier points as solver failures, when
  really they were points outside the feasible region entirely.
- **Weight normalization is forgiving.** Input weights can be fractions
  (`[0.4, 0.35, 0.25]`) or percentages (`[40, 35, 25]`), and don't need to sum
  exactly to 1/100 -- they get normalized with a warning. A user's weights
  adding up to 97% due to a typo shouldn't hard-fail the request.
- **Long-only + optional max-weight cap by default**, because naive
  mean-variance optimization on sample estimates is well known to produce
  extreme, unstable weights (100% in whatever asset had the best trailing
  return). Comments in `optimize.py` note where a shrinkage estimator
  (Ledoit-Wolf) or Black-Litterman priors could slot in later to address the
  underlying estimation-error problem, rather than just capping its symptoms.
- **All financial numbers are deterministic**, produced here with no LLM
  involvement. `types.py`/`pipeline.py` exist specifically so the future AI
  explanation layer receives already-computed numbers to narrate, never asked
  to produce or estimate one itself.

## Verified against Portfolio Visualizer

Sample portfolio (40% VOO / 35% AAPL / 25% BND, 5y monthly lookback) --
compare your own Portfolio Visualizer run's per-asset arithmetic mean/std
dev, correlation matrix, and tangency portfolio weights against this repo's
`python scripts/run_sample.py` output. Expect agreement within a few tens of
basis points (data vendor / exact date-window differences); large
discrepancies mean something's wrong and should be tracked down before
moving on to the FastAPI layer.

## Stage 2: FastAPI backend (`backend/`)

A thin HTTP wrapper -- no math lives here, everything is a call-through to
`math_engine`. Structure:

| File | Responsibility |
|---|---|
| `app/main.py` | App setup, CORS, and exception handlers that map math_engine's domain errors to clean HTTP status codes. |
| `app/routers/analyze.py` | `POST /api/analyze` -- calls `run_mvo`, returns `MVOResult` directly as the response model. |
| `app/routers/explain.py` | `POST /api/explain` -- takes back exactly what `/api/analyze` returned, fills in a fixed prose template with those numbers. |
| `app/explain_template.py` | The narration logic. No external API call -- deterministic Python string formatting, gated by the same "never invent a number" rule as before. |
| `app/schemas.py` | Request models. Response models reuse `math_engine.types` directly. |
| `app/config.py` | Env var reads (CORS origins, ticker limits). |
| `app/rate_limit.py` | Per-IP rate limits on `/api/analyze` and `/api/explain` (20/minute each), so the API can't be hammered into abusing yfinance or burning CPU. |

Error mapping (registered in `main.py`): any `ValueError` (covers
`InsufficientAssetsError` and `TickerDataError`, both subclasses) -> 400;
`OptimizationError` -> 500. Pydantic request validation failures (e.g.
missing required fields) are handled by FastAPI itself as 422, before your
code even runs -- that's why "single ticker" is a 400 (a valid request that
fails business rules) but "missing `weights` field" is a 422 (the request
itself is malformed).

### Why `/api/explain` isn't backed by an LLM

The original plan (and an earlier version of this codebase) had `/api/explain`
call the Claude API to narrate the computed numbers. It worked, and it was
genuinely cheap (a fraction of a cent per call) -- but it added a real
dependency: an API key to manage, a billing account to cap, a third-party
service that could change pricing or behavior, and a vendor relationship
outside this project's control. For a feature that only needs to narrate
three or four numbers in a fixed structure -- "here's your Sharpe ratio,
here's the gap, here's which weights would change" -- a template covers the
same ground without any of that. `explain_template.py` fills in fixed prose
with the same numbers an LLM version would have received, deterministically,
for free, with zero external dependency. If a future version needs genuinely
open-ended narration (not just filling in a fixed structure), an LLM would
be the right tool again -- this isn't a permanent rejection of using one,
just a recognition that this particular feature didn't need one.

### Setup & run

```bash
cd backend
source ../.venv/bin/activate     # same venv as math_engine
pip install -r ../requirements.txt
uvicorn app.main:app --reload --port 8000
# interactive docs: http://localhost:8000/docs
```

### Tests

```bash
cd backend
pytest                 # offline: health check, error-path status codes, explain-template output
pytest -m network       # + real yfinance calls
```

### A real bug this layer caught

`math_engine.data.fetch_adjusted_close` originally built a yfinance `period=`
string like `f"{lookback_years}y"`. That works if `lookback_years` is an
`int` (`"5y"`) but not if it's a `float` -- and the FastAPI request schema
declares `lookback_years: float`, so any JSON request produces `5.0`, giving
`"5.0y"`, which yfinance's `period=` shorthand rejects outright (it only
accepts a fixed enum: `1y`, `2y`, `5y`, ...). The math engine's own tests and
scripts never caught this because they always passed a plain `int`. Fixed by
switching to explicit `start`/`end` dates instead of the `period=` shorthand
-- more precise anyway, and now fractional lookbacks (e.g. 2.5 years) work
too. This is exactly the kind of bug that only shows up once a real caller
(the API, with its typed JSON schema) exercises the code differently than
your own test suite does.

## Stage 3: React front end (`frontend/`)

Vite + React + TypeScript, Tailwind for styling, Recharts for the frontier
chart. No business logic here -- every number displayed comes verbatim from
`/api/analyze` or `/api/explain`; the frontend's only job is layout and
presentation.

| File | Responsibility |
|---|---|
| `src/App.tsx` | Top-level state (holdings, lookback years) and the three-part layout (top bar / main panel / sidebar). |
| `src/components/HoldingsInput.tsx` | Ticker+weight rows, CSV upload, lookback selector, submit button, inline error/warning display. |
| `src/components/FrontierChart.tsx` | The centerpiece: frontier curve, capital allocation line, max-Sharpe dot, user's dot, dashed gap line -- all as separate Recharts series sharing one coordinate system. |
| `src/components/WhatThisMeans.tsx`, `SharpeComparison.tsx`, `OptimalWeightsBar.tsx` | The three sidebar cards. |
| `src/hooks/useAnalyze.ts`, `useExplain.ts` | Thin state wrappers (loading/error/data) around the two API calls -- no caching/global state library, this app doesn't need one yet. |
| `src/api/client.ts`, `types.ts` | Fetch wrapper + hand-mirrored TypeScript types matching `backend/app/schemas.py` / `math_engine/types.py`. |

Design tokens (colors, chart semantics) live in `src/index.css` as CSS
custom properties, mapped to Tailwind utilities in `tailwind.config.cjs` --
so a future Figma-driven reskin means editing values in one place, not
hunting through components.

### Setup & run

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173 -- requires the backend running on :8000
npm run build     # production build, also does the TypeScript check
```

### Environment notes (things that broke and why)

This machine had no Node.js, no package manager, and no `~/.claude/launch.json`
preview config at the start of this stage -- all set up as part of this build
(nvm -> Node LTS -> `npm create vite@latest`). Two bugs came up during setup
that are worth knowing about if the dev server ever misbehaves again:

1. **Vite 8's default bundler (Rolldown) hung indefinitely** during dependency
   pre-bundling in this environment (`[optimizer] bundling dependencies...`
   never completed, pegging a CPU core). `npm create vite@latest` picked up
   Vite 8 since it's now the default on npm, but Vite 8's Rolldown-based
   dependency optimizer is new and apparently doesn't work reliably in this
   sandboxed environment. Fixed by pinning to **Vite 6** (`package.json`
   `devDependencies.vite: "^6"`), which uses the older, battle-tested esbuild
   pre-bundler. If `npm run dev` ever hangs again at "bundling dependencies,"
   check the installed Vite major version first.
2. **Tailwind's utility classes silently didn't apply** (only the base/reset
   CSS loaded) even though `tailwind.config.cjs` looked correct. Root cause:
   Tailwind v3's own config/content-glob resolution uses `process.cwd()`,
   which is *not necessarily* this project's directory -- whatever spawns the
   dev server (an editor task runner, this session's preview tool, etc.) may
   have a different working directory. Vite's own `--root` flag doesn't fix
   this because Tailwind's config search is independent of Vite. Fixed by
   making both the Tailwind config path (in `postcss.config.js`) and the
   `content` globs (in `tailwind.config.cjs`) absolute, anchored to
   `__dirname`, instead of relying on relative-path auto-discovery. If
   Tailwind classes ever stop applying again, check for a `content option
   missing/empty` or `No utility classes were detected` warning in the dev
   server log first -- that's this exact failure mode.

### Manually verified in a real browser

Ran the sample portfolio (40% VOO / 35% AAPL / 25% BND) through the full UI:
holdings form -> loading state -> chart renders with correct frontier curve,
CAL, and both dots (colors confirmed programmatically:
`rgb(22,163,74)` green for max-Sharpe, `rgb(234,88,12)` orange for the
user's portfolio) -> Sharpe comparison and optimal-weights bar chart match
the backend's numbers exactly -> clicking "Explain this to me" renders the
templated explanation instantly, no API key or setup required. Production
build (`npm run build`) also verified clean, with Tailwind's compiled CSS
output (11.26 kB) confirming the utility-class fix actually took effect,
not just in dev mode.

## What's left

- Wire `FRED_API_KEY` for a live risk-free rate (currently falls back
  gracefully to a hardcoded approximate rate without it).
- Deployment: Vercel (frontend) + Railway (backend), per the original spec --
  not attempted yet, local dev only so far.
- Optional: code-split the frontend bundle (Recharts+d3 pushes the JS bundle
  to ~600 kB); shrinkage estimators / Black-Litterman in `optimize.py`, per
  the comments already in that file.
