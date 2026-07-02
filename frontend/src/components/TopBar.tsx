export function TopBar() {
  return (
    <header className="sticky top-0 z-10 flex items-center justify-between border-b border-border bg-card/90 px-6 py-4 backdrop-blur">
      <div className="flex items-baseline gap-2">
        <span className="text-lg font-semibold tracking-tight text-ink">Portfolio Lens</span>
        <span className="text-sm text-ink-muted">mean-variance analysis</span>
      </div>
      <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-medium text-amber-800">
        <span aria-hidden="true">&#9432;</span>
        Educational tool, not financial advice
      </span>
    </header>
  );
}
