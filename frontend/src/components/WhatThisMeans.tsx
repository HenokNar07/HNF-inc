interface WhatThisMeansProps {
  explanation: string | null;
  error: string | null;
}

export function WhatThisMeans({ explanation, error }: WhatThisMeansProps) {
  return (
    <div>
      <h2 className="text-2xl text-ink">What this means</h2>

      {explanation ? (
        <div className="mt-3 space-y-3 text-sm leading-relaxed text-ink-muted">
          {explanation
            .split(/\n\n+/)
            .filter(Boolean)
            .map((paragraph) => (
              <p key={paragraph.slice(0, 24)}>{paragraph}</p>
            ))}
        </div>
      ) : (
        <p className="mt-3 text-sm text-ink-muted">
          Get a plain-English breakdown of where your portfolio sits relative to the frontier,
          what the Sharpe ratio gap means, and why the optimal weights differ from yours.
        </p>
      )}

      {error && (
        <p className="mt-3 rounded-md border border-red-900/50 bg-red-950/40 px-3 py-2 text-sm text-red-400">
          {error}
        </p>
      )}
    </div>
  );
}
