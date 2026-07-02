# HNF, inc.

Real mean-variance (Markowitz) portfolio analysis, explained in plain
English. Enter your holdings, see where your portfolio sits on the
efficient frontier, and find the mathematically optimal allocation for
the same assets -- with a sidebar that explains what all of it means, no
finance background required.

> **Educational tool -- not financial advice.** Nothing in this app is a
> recommendation to buy, sell, or hold anything. It shows you what the math
> says under a specific set of assumptions; what you do with that is up to
> you (and ideally a real financial advisor for anything that matters).

## What it does

1. You enter your tickers and weights (or upload a CSV).
2. It pulls real historical price data and computes the efficient frontier
   for those exact assets -- the curve of best-possible risk/return
   combinations you can get by mixing them.
3. It plots your current portfolio against that curve, alongside the
   mathematically optimal (max Sharpe ratio) allocation.
4. It explains the result in plain language -- what the Sharpe ratio gap
   means, and why the optimal weights differ from yours.

Every number on screen comes from real, deterministic computation
(`numpy`/`scipy`, not a language model). Nothing is AI-generated or
estimated; the math is the same math you'd get running the same portfolio
through a tool like Portfolio Visualizer.

## Getting started

Nothing here requires an account, API key, or sign-up of any kind --
price data (Yahoo Finance) and the risk-free rate (the U.S. Treasury's own
public API) are both free and keyless. You need Python 3.9+ and Node.js
18+ installed.

First, get the code:

```bash
git clone https://github.com/HenokNar07/HNF-inc.git
cd HNF-inc
```

Everything below assumes your terminal is inside that `HNF-inc` folder --
if a command says "no such file or directory," that's almost always why.

Two things need to run at once: the backend (does the math) and the
frontend (the app you actually look at).

### 1. Backend

```bash
cd backend
python3 -m venv ../.venv
source ../.venv/bin/activate
pip install -r ../requirements.txt
pip install -e ..
uvicorn app.main:app --reload --port 8000
```

Leave this running. Interactive API docs at `http://localhost:8000/docs`.

### 2. Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` -- that's the app.

## How it's built

| Folder | What's in it |
|---|---|
| `math_engine/` | The actual math: price fetching, annualized returns/covariance, the efficient frontier, max-Sharpe and min-variance portfolios. Pure Python (`pandas`/`numpy`/`scipy`), no framework, fully unit tested. |
| `backend/` | A FastAPI wrapper around `math_engine` -- two endpoints (`/api/analyze`, `/api/explain`), input validation, rate limiting, CORS. |
| `frontend/` | React + Vite + Tailwind + Recharts. Holdings input, the frontier chart, and the explanation sidebar. |

## Running the tests

```bash
# from the repo root
pytest                  # math engine, offline
pytest -m network        # + tests that hit real market data

cd backend
pytest                  # backend, offline
pytest -m network        # + tests that hit real market data
```

## A note on the math

- Expected returns and covariance are annualized arithmetically (monthly
  mean/covariance times 12), which is the standard convention for
  mean-variance inputs -- it'll read a little higher than a compounded
  (CAGR) return, and that's expected.
- The frontier and max-Sharpe portfolio are long-only by default, with an
  optional cap on how much any single asset can hold (40% by default) --
  naive mean-variance optimization on sample data is well known to produce
  extreme, unstable weights without one.
- The risk-free rate used for the Sharpe ratio comes from the U.S.
  Treasury's average interest rate on Treasury Bills, refreshed on every
  request; if that request ever fails, the app falls back to a hardcoded
  approximate rate rather than breaking, and tells you which one it used.
