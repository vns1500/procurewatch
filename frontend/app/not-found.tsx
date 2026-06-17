import Link from "next/link";

export default function NotFound() {
  return (
    <div style={{ padding: "80px 32px", display: "flex", flexDirection: "column", gap: 16, alignItems: "flex-start" }}>
      <span className="mono" style={{ fontSize: 10, color: "var(--accent-red)", letterSpacing: "0.12em" }}>404</span>
      <h1 style={{ fontSize: 22, fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>Page not found</h1>
      <p style={{ fontSize: 13, color: "var(--text-muted)", margin: 0 }}>The page you are looking for does not exist or has been moved.</p>
      <Link href="/dashboard" style={{ fontSize: 12, color: "var(--accent-red)", textDecoration: "none" }}>
        Return to dashboard →
      </Link>
    </div>
  );
}
