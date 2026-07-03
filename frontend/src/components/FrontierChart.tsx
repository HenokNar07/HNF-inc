import {
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Scatter,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TooltipContentProps } from "recharts";
import type { MVOResult } from "../api/types";

interface Point {
  x: number; // risk, annualized std dev, in percent
  y: number; // expected return, in percent
  label?: string;
}

interface FrontierChartProps {
  result: MVOResult;
}

const LEGEND_ITEMS = [
  { label: "Frontier", color: "var(--color-frontier-line)", dash: false },
  { label: "CAL", color: "var(--color-cal-line)", dash: true },
  { label: "Gap", color: "var(--color-gap-line)", dash: true },
];

function ChartTooltip({ active, payload }: TooltipContentProps) {
  if (!active || !payload || payload.length === 0) return null;
  const point = (payload[0]?.payload ?? {}) as Point;
  return (
    <div className="rounded-md border border-border bg-input px-3 py-2 text-xs shadow-md">
      <p className="font-medium text-ink">
        Risk: {point.x?.toFixed(2)}% &middot; Return: {point.y?.toFixed(2)}%
      </p>
    </div>
  );
}

function PointLabel({ x, y, text }: { x?: number | string; y?: number | string; text: string }) {
  const numX = Number(x);
  const numY = Number(y);
  if (x === undefined || y === undefined || Number.isNaN(numX) || Number.isNaN(numY)) return null;
  return (
    <text x={numX + 10} y={numY + 4} fontSize={12} fill="var(--color-ink-muted)">
      {text}
    </text>
  );
}

export function FrontierChart({ result }: FrontierChartProps) {
  const frontierData: Point[] = result.frontier
    .map((p) => ({ x: p.std_dev * 100, y: p.expected_return * 100 }))
    .sort((a, b) => a.x - b.x);

  const maxSharpePoint: Point = {
    x: result.max_sharpe.std_dev * 100,
    y: result.max_sharpe.expected_return * 100,
    label: "Max Sharpe portfolio",
  };
  const userPoint: Point = {
    x: result.current_portfolio.std_dev * 100,
    y: result.current_portfolio.expected_return * 100,
    label: "Your portfolio",
  };

  // Extend the CAL a bit past the riskiest point on screen so it visibly
  // passes through (and beyond) the tangency portfolio, per the spec.
  const maxX = Math.max(...frontierData.map((p) => p.x), userPoint.x, maxSharpePoint.x);
  const calEndX = maxX * 1.25;
  const riskFreePct = result.risk_free_rate * 100;
  const sharpeSlope = (maxSharpePoint.y - riskFreePct) / maxSharpePoint.x;
  const calData: Point[] = [
    { x: 0, y: riskFreePct },
    { x: calEndX, y: riskFreePct + sharpeSlope * calEndX },
  ];

  const gapData: Point[] = [maxSharpePoint, userPoint];

  return (
    <div>
      <div className="mb-4 flex items-baseline justify-between">
        <h2 className="text-2xl text-ink">Efficient frontier</h2>
        <span className="text-[11px] uppercase tracking-wider text-ink-muted">
          Mean-variance analysis
        </span>
      </div>

      <div className="relative">
        <div className="absolute left-12 top-2 z-10 rounded-md border border-border bg-input px-3 py-2 text-xs">
          {LEGEND_ITEMS.map((item) => (
            <div key={item.label} className="flex items-center gap-2 py-0.5 text-ink-muted">
              <span
                className="inline-block h-0.5 w-4"
                style={{
                  backgroundColor: item.dash ? "transparent" : item.color,
                  borderTop: item.dash ? `1.5px dashed ${item.color}` : undefined,
                }}
              />
              {item.label}
            </div>
          ))}
        </div>

        <ResponsiveContainer width="100%" height={420}>
          <ComposedChart data={frontierData} margin={{ top: 10, right: 40, bottom: 24, left: 8 }}>
            <CartesianGrid stroke="var(--color-border)" strokeDasharray="3 3" />
            <XAxis
              type="number"
              dataKey="x"
              domain={[0, "auto"]}
              tickFormatter={(v: number) => `${v.toFixed(0)}%`}
              stroke="var(--color-ink-muted)"
              fontSize={12}
              label={{
                value: "Risk (annualized volatility)",
                position: "insideBottom",
                offset: -14,
                fill: "var(--color-ink-muted)",
                fontSize: 12,
              }}
            />
            <YAxis
              type="number"
              dataKey="y"
              tickFormatter={(v: number) => `${v.toFixed(0)}%`}
              stroke="var(--color-ink-muted)"
              fontSize={12}
              label={{
                value: "Expected return",
                angle: -90,
                position: "insideLeft",
                fill: "var(--color-ink-muted)",
                fontSize: 12,
              }}
            />
            <Tooltip content={(props) => <ChartTooltip {...props} />} />

            <Line
              data={calData}
              dataKey="y"
              stroke="var(--color-cal-line)"
              strokeWidth={1.5}
              strokeDasharray="5 5"
              dot={false}
              isAnimationActive={false}
              legendType="none"
            />
            <Line
              dataKey="y"
              stroke="var(--color-frontier-line)"
              strokeWidth={2.5}
              dot={false}
              isAnimationActive={false}
              legendType="none"
            />
            <Line
              data={gapData}
              dataKey="y"
              stroke="var(--color-gap-line)"
              strokeWidth={1.5}
              strokeDasharray="4 4"
              dot={false}
              isAnimationActive={false}
              legendType="none"
            />
            <Scatter
              data={[maxSharpePoint]}
              dataKey="y"
              fill="var(--color-max-sharpe)"
              stroke="var(--color-surface)"
              strokeWidth={2}
              r={7}
              label={(props: { x?: number | string; y?: number | string }) => (
                <PointLabel {...props} text="Max Sharpe portfolio" />
              )}
            />
            <Scatter
              data={[userPoint]}
              dataKey="y"
              fill="var(--color-user-portfolio)"
              stroke="var(--color-surface)"
              strokeWidth={2}
              r={7}
              label={(props: { x?: number | string; y?: number | string }) => (
                <PointLabel {...props} text="Your portfolio" />
              )}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
