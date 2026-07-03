interface OptimalWeightsBarProps {
  weights: Record<string, number>;
}

export function OptimalWeightsBar({ weights }: OptimalWeightsBarProps) {
  const data = Object.entries(weights)
    .map(([ticker, weight]) => ({ ticker, weight: weight * 100 }))
    .sort((a, b) => b.weight - a.weight);

  return (
    <div>
      <h2 className="text-lg text-ink">Optimal weights (max Sharpe)</h2>
      <div className="mt-4 flex flex-col gap-3">
        {data.map(({ ticker, weight }) => (
          <div key={ticker} className="flex items-center gap-3">
            <span className="w-14 shrink-0 text-sm text-ink">{ticker}</span>
            <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-input">
              <div
                className="h-full rounded-full bg-primary"
                style={{ width: `${Math.max(weight, 2)}%` }}
              />
            </div>
            <span className="w-10 shrink-0 text-right text-sm text-ink-muted">
              {weight.toFixed(0)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
