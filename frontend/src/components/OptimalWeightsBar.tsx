import { Bar, BarChart, LabelList, ResponsiveContainer, XAxis, YAxis } from "recharts";

interface OptimalWeightsBarProps {
  weights: Record<string, number>;
}

export function OptimalWeightsBar({ weights }: OptimalWeightsBarProps) {
  const data = Object.entries(weights)
    .map(([ticker, weight]) => ({ ticker, weight: weight * 100 }))
    .sort((a, b) => b.weight - a.weight);

  const height = Math.max(data.length * 36, 90);

  return (
    <div className="rounded-2xl border border-border bg-card p-6">
      <h2 className="mb-1 text-base font-semibold text-ink">Optimal weights</h2>
      <p className="mb-4 text-xs text-ink-muted">
        The mathematically optimal (max Sharpe) allocation under Markowitz assumptions.
      </p>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} layout="vertical" margin={{ top: 0, right: 28, bottom: 0, left: 8 }}>
          <XAxis
            type="number"
            domain={[0, 100]}
            tickFormatter={(v: number) => `${v}%`}
            stroke="var(--color-ink-muted)"
            fontSize={12}
          />
          <YAxis
            type="category"
            dataKey="ticker"
            stroke="var(--color-ink-muted)"
            fontSize={12}
            width={56}
          />
          <Bar dataKey="weight" fill="var(--color-primary)" radius={[0, 6, 6, 0]} barSize={18}>
            <LabelList
              dataKey="weight"
              position="right"
              formatter={(value) => `${Number(value).toFixed(0)}%`}
              fill="var(--color-ink-muted)"
              fontSize={12}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
