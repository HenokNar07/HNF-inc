interface WhatThisMeansProps {
  explanation: string | null;
  loading: boolean;
  error: string | null;
  onExplain: () => void;
}

export function WhatThisMeans({ explanation, loading, error, onExplain }: WhatThisMeansProps) {
  return (
    <div className="rounded-2xl border border-border bg-card p-6">
      <h2 className="mb-3 text-base font-semibold text-ink">What this means</h2>

      {explanation ? (
        <div className="space-y-3 text-sm leading-relaxed text-ink">
          {explanation
            .split(/\n\n+/)
            .filter(Boolean)
            .map((paragraph) => (
              <p key={paragraph.slice(0, 24)}>{paragraph}</p>
            ))}
        </div>
      ) : (
        <p className="text-sm text-ink-muted">
          Get a plain-English breakdown of where your portfolio sits relative to the frontier,
          what the Sharpe ratio gap means, and why the optimal weights differ from yours.
        </p>
      )}

      {error && (
        <p className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      <button
        type="button"
        onClick={onExplain}
        disabled={loading}
        className="mt-4 w-full rounded-lg border border-primary px-4 py-2 text-sm font-medium text-primary transition-colors hover:bg-primary-soft disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? "Thinking..." : explanation ? "Regenerate explanation" : "Explain this to me"}
      </button>
    </div>
  );
}
