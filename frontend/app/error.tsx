"use client";

export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div style={{ padding: "80px 32px", display: "flex", flexDirection: "column", gap: 16, alignItems: "flex-start" }}>
      <span className="mono" style={{ fontSize: 10, color: "var(--accent-red)", letterSpacing: "0.12em" }}>ERROR</span>
      <h1 style={{ fontSize: 22, fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>Something went wrong</h1>
      <p style={{ fontSize: 13, color: "var(--text-muted)", margin: 0, fontFamily: "JetBrains Mono, monospace" }}>{error.message}</p>
      <button onClick={reset} style={{ fontSize: 12, color: "var(--accent-red)", background: "none", border: "1px solid var(--accent-red)", borderRadius: 2, padding: "6px 14px", cursor: "pointer" }}>
        Try again
      </button>
    </div>
  );
}
