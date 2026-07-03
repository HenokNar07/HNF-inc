interface SharpeComparisonProps {
  currentSharpe: number;
  optimalSharpe: number;
}

export function SharpeComparison({ currentSharpe, optimalSharpe }: SharpeComparisonProps) {
  const gap = optimalSharpe - currentSharpe;

  return (
    <div>
      <h2 className="mb-1 text-[11px] uppercase tracking-wider text-ink-muted">Sharpe ratio</h2>
      <div className="mt-3 grid grid-cols-2 gap-3">
        <div className="rounded-md border border-border bg-input px-4 py-3">
          <p className="text-[11px] uppercase tracking-wider text-ink-muted">Yours</p>
          <p className="mt-1 text-2xl text-ink">{currentSharpe.toFixed(2)}</p>
        </div>
        <div className="rounded-md border border-primary/40 bg-primary-soft px-4 py-3">
          <p className="text-[11px] uppercase tracking-wider text-ink-muted">Optimal</p>
          <p className="mt-1 text-2xl text-primary">{optimalSharpe.toFixed(2)}</p>
        </div>
      </div>
      {gap > 0.001 && (
        <p className="mt-3 text-sm text-ink-muted">
          The optimal allocation earns{" "}
          <span className="font-medium text-ink">{gap.toFixed(2)}</span> more Sharpe ratio per
          unit of risk, under Markowitz assumptions.
        </p>
      )}
    </div>
  );
}
