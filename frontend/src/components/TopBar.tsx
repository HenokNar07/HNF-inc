export function TopBar() {
  return (
    <header className="sticky top-0 z-10 flex items-center justify-between border-b border-border bg-card px-6 py-4">
      <div className="flex items-center gap-2.5">
        <span className="h-6 w-6 rounded-md bg-primary" aria-hidden="true" />
        <span className="text-base text-ink">
          HNF, inc. <span className="font-semibold">Portfolio Lens</span>{" "}
          <span className="text-ink-muted">(Beta)</span>
        </span>
      </div>
      <span className="rounded-md border border-border bg-input px-3 py-1.5 text-[11px] font-medium uppercase tracking-wider text-ink-muted">
        Educational tool &middot; not financial advice
      </span>
    </header>
  );
}
