import { useState } from "react";
import { TopBar } from "./components/TopBar";
import { HoldingsInput } from "./components/HoldingsInput";
import type { HoldingRow } from "./components/HoldingsInput";
import { FrontierChart } from "./components/FrontierChart";
import { WhatThisMeans } from "./components/WhatThisMeans";
import { SharpeComparison } from "./components/SharpeComparison";
import { OptimalWeightsBar } from "./components/OptimalWeightsBar";
import { useAnalyze } from "./hooks/useAnalyze";
import { useExplain } from "./hooks/useExplain";

const SAMPLE_HOLDINGS: HoldingRow[] = [
  { id: crypto.randomUUID(), ticker: "VOO", weight: "40" },
  { id: crypto.randomUUID(), ticker: "AAPL", weight: "35" },
  { id: crypto.randomUUID(), ticker: "BND", weight: "25" },
];

function EmptyState({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-[200px] items-center justify-center rounded-md border border-dashed border-border p-6 text-center text-sm text-ink-muted">
      {children}
    </div>
  );
}

function App() {
  const [holdings, setHoldings] = useState<HoldingRow[]>(SAMPLE_HOLDINGS);
  const [lookbackYears, setLookbackYears] = useState(5);

  const { result, loading, error, analyze } = useAnalyze();
  const warnings = result?.warnings ?? [];
  const explainState = useExplain();

  const handleAnalyze = () => {
    explainState.reset();
    analyze({
      tickers: holdings.map((h) => h.ticker.trim().toUpperCase()),
      weights: holdings.map((h) => Number(h.weight)),
      lookback_years: lookbackYears,
    });
  };

  return (
    <div className="min-h-screen bg-surface">
      <TopBar />
      <main className="mx-auto max-w-7xl px-6 py-8">
        <div className="grid grid-cols-1 gap-10 lg:grid-cols-[1fr_380px]">
          <div className="flex flex-col gap-10 lg:border-r lg:border-border lg:pr-10">
            <HoldingsInput
              holdings={holdings}
              onHoldingsChange={setHoldings}
              lookbackYears={lookbackYears}
              onLookbackYearsChange={setLookbackYears}
              onSubmit={handleAnalyze}
              loading={loading}
              error={error}
              warnings={warnings}
            />
            {result ? (
              <FrontierChart result={result} />
            ) : (
              <EmptyState>
                Enter your holdings above and click "Analyze" to see your efficient frontier.
              </EmptyState>
            )}
          </div>

          <aside className="flex flex-col gap-8">
            {result ? (
              <>
                <WhatThisMeans explanation={explainState.explanation} error={explainState.error} />
                <SharpeComparison
                  currentSharpe={result.current_portfolio.sharpe_ratio}
                  optimalSharpe={result.max_sharpe.sharpe_ratio}
                />
                <OptimalWeightsBar weights={result.max_sharpe.weights} />
                <button
                  type="button"
                  onClick={() => explainState.explain(result)}
                  disabled={explainState.loading}
                  className="w-full rounded-md border border-primary px-4 py-3 text-sm font-medium text-primary transition-colors hover:bg-primary-soft disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {explainState.loading
                    ? "Thinking..."
                    : explainState.explanation
                      ? "Regenerate explanation"
                      : "Explain this to me"}
                </button>
              </>
            ) : (
              <EmptyState>Your results, explained in plain English, will show up here.</EmptyState>
            )}
          </aside>
        </div>
      </main>
    </div>
  );
}

export default App;
