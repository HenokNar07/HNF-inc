import { useRef } from "react";
import type { ChangeEvent } from "react";

export interface HoldingRow {
  id: string;
  ticker: string;
  weight: string; // kept as text while editing; parsed to number on submit
}

export function emptyRow(): HoldingRow {
  return { id: crypto.randomUUID(), ticker: "", weight: "" };
}

function parseCsv(text: string): HoldingRow[] {
  const rows = text
    .split(/\r?\n/)
    .map((line) => line.split(",").map((cell) => cell.trim()))
    .filter((cells) => cells.length >= 2 && cells[0] !== "");

  // Drop a header row if its second column isn't a number (e.g. "Ticker,Weight").
  const dataRows = rows.length > 0 && Number.isNaN(Number(rows[0][1])) ? rows.slice(1) : rows;

  return dataRows.map(([ticker, weight]) => ({
    id: crypto.randomUUID(),
    ticker: ticker.toUpperCase(),
    weight,
  }));
}

interface HoldingsInputProps {
  holdings: HoldingRow[];
  onHoldingsChange: (holdings: HoldingRow[]) => void;
  lookbackYears: number;
  onLookbackYearsChange: (years: number) => void;
  onSubmit: () => void;
  loading: boolean;
  error: string | null;
  warnings: string[];
}

export function HoldingsInput({
  holdings,
  onHoldingsChange,
  lookbackYears,
  onLookbackYearsChange,
  onSubmit,
  loading,
  error,
  warnings,
}: HoldingsInputProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const updateRow = (id: string, patch: Partial<HoldingRow>) => {
    onHoldingsChange(holdings.map((row) => (row.id === id ? { ...row, ...patch } : row)));
  };

  const removeRow = (id: string) => {
    onHoldingsChange(holdings.filter((row) => row.id !== id));
  };

  const addRow = () => {
    onHoldingsChange([...holdings, emptyRow()]);
  };

  const handleCsvUpload = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    file.text().then((text) => {
      const parsed = parseCsv(text);
      if (parsed.length > 0) onHoldingsChange(parsed);
    });
    event.target.value = ""; // allow re-uploading the same file
  };

  const weightSum = holdings.reduce((sum, row) => sum + (Number(row.weight) || 0), 0);
  const canSubmit = holdings.every((row) => row.ticker.trim() !== "" && row.weight !== "");

  return (
    <section className="rounded-2xl border border-border bg-card p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-base font-semibold text-ink">Your holdings</h2>
        <div className="flex items-center gap-3 text-sm text-ink-muted">
          <label htmlFor="lookback" className="whitespace-nowrap">
            Lookback (years)
          </label>
          <input
            id="lookback"
            type="number"
            min={1}
            max={30}
            value={lookbackYears}
            onChange={(e) => onLookbackYearsChange(Number(e.target.value))}
            className="w-16 rounded-lg border border-border px-2 py-1 text-ink"
          />
        </div>
      </div>

      <div className="flex flex-col gap-2">
        {holdings.map((row) => (
          <div key={row.id} className="flex items-center gap-2">
            <input
              type="text"
              placeholder="Ticker"
              value={row.ticker}
              onChange={(e) => updateRow(row.id, { ticker: e.target.value.toUpperCase() })}
              className="w-28 rounded-lg border border-border px-3 py-2 text-sm uppercase text-ink placeholder:normal-case placeholder:text-ink-muted"
            />
            <div className="relative flex-1 max-w-[140px]">
              <input
                type="number"
                placeholder="Weight"
                value={row.weight}
                onChange={(e) => updateRow(row.id, { weight: e.target.value })}
                className="w-full rounded-lg border border-border px-3 py-2 pr-7 text-sm text-ink placeholder:text-ink-muted"
              />
              <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-sm text-ink-muted">
                %
              </span>
            </div>
            <button
              type="button"
              onClick={() => removeRow(row.id)}
              disabled={holdings.length <= 1}
              aria-label={`Remove ${row.ticker || "row"}`}
              className="rounded-lg px-2 py-2 text-ink-muted hover:bg-surface hover:text-ink disabled:opacity-30"
            >
              &#10005;
            </button>
          </div>
        ))}
      </div>

      <div className="mt-3 flex items-center justify-between">
        <div className="flex gap-2">
          <button
            type="button"
            onClick={addRow}
            className="rounded-lg border border-border px-3 py-1.5 text-sm text-ink hover:bg-surface"
          >
            + Add holding
          </button>
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="rounded-lg border border-border px-3 py-1.5 text-sm text-ink hover:bg-surface"
          >
            Upload CSV
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,text/csv"
            className="hidden"
            onChange={handleCsvUpload}
          />
        </div>
        <span className="text-sm text-ink-muted">
          Total: {weightSum.toFixed(1)}%{Math.abs(weightSum - 100) > 0.5 ? " (will be normalized)" : ""}
        </span>
      </div>

      <button
        type="button"
        onClick={onSubmit}
        disabled={!canSubmit || loading}
        className="mt-4 w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? "Analyzing..." : "Analyze portfolio"}
      </button>

      {error && (
        <p className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}
      {warnings.length > 0 && (
        <ul className="mt-3 space-y-1">
          {warnings.map((warning) => (
            <li
              key={warning}
              className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800"
            >
              {warning}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
