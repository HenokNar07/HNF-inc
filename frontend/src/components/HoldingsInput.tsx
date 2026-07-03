import { useRef } from "react";
import type { ChangeEvent } from "react";
import type { ReturnModel } from "../api/types";

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
  returnModel: ReturnModel;
  onReturnModelChange: (model: ReturnModel) => void;
  onSubmit: () => void;
  loading: boolean;
  error: string | null;
  warnings: string[];
}

const RETURN_MODEL_HELP: Record<ReturnModel, string> = {
  historical:
    "Expected return for each holding is its own historical average return.",
  fama_french:
    "Expected return comes from each holding's exposure to three market risk factors (market, size, value) -- not from macroeconomic forecasts or trend prediction.",
};

export function HoldingsInput({
  holdings,
  onHoldingsChange,
  lookbackYears,
  onLookbackYearsChange,
  returnModel,
  onReturnModelChange,
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
  const isBalanced = Math.abs(weightSum - 100) <= 0.5;
  const canSubmit = holdings.every((row) => row.ticker.trim() !== "" && row.weight !== "");

  return (
    <section>
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl text-ink">Holdings</h2>
          <p className="mt-1 text-sm text-ink-muted">
            Enter ticker symbols and portfolio weights. Weights must sum to 100%.
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2 pt-1 text-xs text-ink-muted">
          <label htmlFor="lookback" className="whitespace-nowrap uppercase tracking-wider">
            Lookback (yrs)
          </label>
          <input
            id="lookback"
            type="number"
            min={1}
            max={30}
            value={lookbackYears}
            onChange={(e) => onLookbackYearsChange(Number(e.target.value))}
            className="w-14 rounded-md border border-border bg-input px-2 py-1 text-ink"
          />
        </div>
      </div>

      <div className="mb-5">
        <span className="text-xs uppercase tracking-wider text-ink-muted">Expected return model</span>
        <div className="mt-2 inline-flex rounded-md border border-border bg-input p-0.5 text-sm">
          <button
            type="button"
            onClick={() => onReturnModelChange("historical")}
            className={`rounded px-3 py-1.5 transition-colors ${
              returnModel === "historical" ? "bg-primary text-black" : "text-ink-muted hover:text-ink"
            }`}
          >
            Historical average
          </button>
          <button
            type="button"
            onClick={() => onReturnModelChange("fama_french")}
            className={`rounded px-3 py-1.5 transition-colors ${
              returnModel === "fama_french" ? "bg-primary text-black" : "text-ink-muted hover:text-ink"
            }`}
          >
            Fama-French 3-factor
          </button>
        </div>
        <p className="mt-2 text-xs text-ink-muted">{RETURN_MODEL_HELP[returnModel]}</p>
      </div>

      <div className="mb-2 grid grid-cols-[1fr_1fr_28px] gap-2 text-xs uppercase tracking-wider text-ink-muted">
        <span>Ticker</span>
        <span>Weight</span>
        <span />
      </div>

      <div className="flex flex-col gap-2">
        {holdings.map((row) => (
          <div key={row.id} className="grid grid-cols-[1fr_1fr_28px] items-center gap-2">
            <input
              type="text"
              placeholder="Ticker"
              value={row.ticker}
              onChange={(e) => updateRow(row.id, { ticker: e.target.value.toUpperCase() })}
              className="rounded-md border border-border bg-input px-3 py-2.5 text-sm uppercase text-ink placeholder:normal-case placeholder:text-ink-muted"
            />
            <div className="relative">
              <input
                type="number"
                placeholder="Weight"
                value={row.weight}
                onChange={(e) => updateRow(row.id, { weight: e.target.value })}
                className="w-full rounded-md border border-border bg-input px-3 py-2.5 pr-7 text-sm text-ink placeholder:text-ink-muted"
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
              className="rounded-md px-1.5 py-2.5 text-ink-muted hover:text-ink disabled:opacity-30"
            >
              &#10005;
            </button>
          </div>
        ))}
      </div>

      <p className={`mt-3 text-sm ${isBalanced ? "text-primary" : "text-ink-muted"}`}>
        {weightSum.toFixed(0)}% total{!isBalanced ? " (will be normalized to 100%)" : ""}
      </p>

      <div className="mt-3 flex items-center gap-4 text-sm">
        <button type="button" onClick={addRow} className="text-primary hover:text-primary-hover">
          + Add holding
        </button>
        <span className="text-ink-muted">
          or{" "}
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="underline hover:text-ink"
          >
            upload a CSV export from your brokerage
          </button>
        </span>
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,text/csv"
          className="hidden"
          onChange={handleCsvUpload}
        />
      </div>

      <button
        type="button"
        onClick={onSubmit}
        disabled={!canSubmit || loading}
        className="mt-5 w-full rounded-md bg-primary px-4 py-3 text-sm font-medium text-black transition-colors hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? "Analyzing..." : "Analyze"}
      </button>

      {error && (
        <p className="mt-3 rounded-md border border-red-900/50 bg-red-950/40 px-3 py-2 text-sm text-red-400">
          {error}
        </p>
      )}
      {warnings.length > 0 && (
        <ul className="mt-3 space-y-1">
          {warnings.map((warning) => (
            <li
              key={warning}
              className="rounded-md border border-amber-900/50 bg-amber-950/40 px-3 py-2 text-sm text-amber-400"
            >
              {warning}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
