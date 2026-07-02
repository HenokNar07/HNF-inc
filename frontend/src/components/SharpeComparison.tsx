interface SharpeComparisonProps {
  currentSharpe: number;
  optimalSharpe: number;
}

function SharpeBar({
  label,
  value,
  max,
  color,
}: {
  label: string;
  value: number;
  max: number;
  color: string;
}) {
  const widthPct = Math.max((value / max) * 100, 2);
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-sm">
        <span className="text-ink-muted">{label}</span>
        <span className="font-medium text-ink">{value.toFixed(3)}</span>
      </div>
      <div className="h-2 w-full rounded-full bg-surface">
        <div
          className="h-2 rounded-full transition-[width]"
          style={{ width: `${widthPct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

export function SharpeComparison({ currentSharpe, optimalSharpe }: SharpeComparisonProps) {
  const maxSharpe = Math.max(currentSharpe, optimalSharpe, 0.01);
  const gap = optimalSharpe - currentSharpe;

  return (
    <div className="rounded-2xl border border-border bg-card p-6">
      <h2 className="mb-4 text-base font-semibold text-ink">Sharpe ratio</h2>
      <div className="space-y-3">
        <SharpeBar
          label="Yours"
          value={currentSharpe}
          max={maxSharpe}
          color="var(--color-user-portfolio)"
        />
        <SharpeBar
          label="Optimal"
          value={optimalSharpe}
          max={maxSharpe}
          color="var(--color-max-sharpe)"
        />
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
