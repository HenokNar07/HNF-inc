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

function EmptyStateCard({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-[200px] items-center justify-center rounded-2xl border border-dashed border-border bg-card p-6 text-center text-sm text-ink-muted">
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
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_360px]">
          <div className="flex flex-col gap-6">
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
              <EmptyStateCard>
                Enter your holdings above and click "Analyze portfolio" to see your efficient
                frontier.
              </EmptyStateCard>
            )}
          </div>

          <aside className="flex flex-col gap-6">
            {result ? (
              <>
                <WhatThisMeans
                  explanation={explainState.explanation}
                  loading={explainState.loading}
                  error={explainState.error}
                  onExplain={() => explainState.explain(result)}
                />
                <SharpeComparison
                  currentSharpe={result.current_portfolio.sharpe_ratio}
                  optimalSharpe={result.max_sharpe.sharpe_ratio}
                />
                <OptimalWeightsBar weights={result.max_sharpe.weights} />
              </>
            ) : (
              <EmptyStateCard>
                Your results, explained in plain English, will show up here.
              </EmptyStateCard>
            )}
          </aside>
        </div>
      </main>
    </div>
  );
}

export default App;
