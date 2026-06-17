import Link from "next/link";
import { getDashboardStats } from "@/lib/api";

async function LiveStats() {
  try {
    const stats = await getDashboardStats();
    const crore = (v: number) => {
      const r = v / 100;
      return r >= 1e7 ? `₹${(r / 1e7).toFixed(0)}Cr` : `₹${(r / 1e5).toFixed(0)}L`;
    };
    return (
      <div style={{ display: "flex", gap: 40, flexWrap: "wrap", justifyContent: "center" }}>
        {[
          { label: "Tenders Analysed", value: stats.total_tenders_scanned.toLocaleString("en-IN") },
          { label: "Suspicious Value", value: crore(stats.suspicious_value) },
          { label: "Anomalies Detected", value: stats.new_anomalies_today.toLocaleString("en-IN") + "+" },
          { label: "Corruption Patterns", value: "10" },
        ].map(({ label, value }) => (
          <div key={label} style={{ textAlign: "center" }}>
            <div className="mono" style={{ fontSize: 26, fontWeight: 700, color: "var(--accent-red)" }}>{value}</div>
            <div style={{ fontSize: 10, color: "var(--text-muted)", letterSpacing: "0.08em", textTransform: "uppercase", marginTop: 4 }}>{label}</div>
          </div>
        ))}
      </div>
    );
  } catch {
    return null;
  }
}

const PATTERNS = [
  { name: "Single Bid", desc: "One vendor, no competition" },
  { name: "Rushed Timeline", desc: "Bid window under 3 days" },
  { name: "Bid Splitting", desc: "Awards split to dodge limits" },
  { name: "Inflated Pricing", desc: "Statistical price outliers" },
  { name: "Shell Vendor", desc: "Newly registered, instant winner" },
  { name: "Director Overlap", desc: "Shared directors across bidders" },
  { name: "Spec Tailoring", desc: "Requirements written for one vendor" },
  { name: "Post-Award Inflation", desc: "Price rises after contract award" },
  { name: "Geo Mismatch", desc: "Vendor state vs. delivery mismatch" },
  { name: "Repeat Monopoly", desc: "Same vendor wins repeatedly" },
];

const STEPS = [
  { n: "01", title: "Scrape", desc: "Daily automated scraping of GeM and CPPP portals. 600+ tenders processed per cycle." },
  { n: "02", title: "Detect", desc: "10 rule-based and ML anomaly detectors run against every tender. Risk scored 0–100." },
  { n: "03", title: "Report", desc: "Claude AI generates investigation briefs with RTI questions and recommended actions." },
];

export default async function LandingPage() {
  return (
    <div style={{ background: "var(--bg-base)", minHeight: "100vh", color: "var(--text-primary)" }}>
      {/* Nav */}
      <nav style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "18px 48px", borderBottom: "1px solid var(--border-subtle)", position: "sticky", top: 0, background: "var(--bg-base)", zIndex: 100 }}>
        <span style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 14, color: "var(--accent-red)", letterSpacing: "0.08em" }}>PROCUREWATCH</span>
        <div style={{ display: "flex", gap: 24, alignItems: "center" }}>
          <Link href="/pricing" style={{ fontSize: 12, color: "var(--text-muted)", textDecoration: "none" }}>Pricing</Link>
          <Link href="/api-docs" style={{ fontSize: 12, color: "var(--text-muted)", textDecoration: "none" }}>API</Link>
          <Link href="/dashboard" style={{ fontSize: 12, color: "var(--text-primary)", background: "var(--accent-red)", padding: "7px 16px", borderRadius: 2, textDecoration: "none", fontWeight: 600 }}>Open App</Link>
        </div>
      </nav>

      {/* Hero */}
      <section style={{ padding: "96px 48px 80px", maxWidth: 900, margin: "0 auto", textAlign: "center" }}>
        <div className="mono" style={{ fontSize: 10, color: "var(--accent-red)", letterSpacing: "0.16em", marginBottom: 20 }}>
          GOVERNMENT PROCUREMENT INTELLIGENCE
        </div>
        <h1 style={{ fontSize: "clamp(28px, 5vw, 52px)", fontWeight: 700, lineHeight: 1.1, margin: "0 0 24px", fontFamily: "'Space Grotesk', sans-serif" }}>
          AI That Detects Corruption in<br />
          <span style={{ color: "var(--accent-red)" }}>Government Procurement</span>
        </h1>
        <p style={{ fontSize: 16, color: "var(--text-muted)", lineHeight: 1.7, marginBottom: 36, maxWidth: 600, margin: "0 auto 36px" }}>
          Automated analysis of ₹40L crore in Indian public tenders.
          Zero government cooperation required.
        </p>
        <div style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
          <Link href="/dashboard" style={{ background: "var(--accent-red)", color: "#fff", padding: "12px 28px", borderRadius: 2, textDecoration: "none", fontSize: 13, fontWeight: 700, letterSpacing: "0.06em" }}>
            START FREE
          </Link>
          <Link href="/reports" style={{ background: "var(--bg-elevated)", color: "var(--text-secondary)", padding: "12px 28px", borderRadius: 2, border: "1px solid var(--border-subtle)", textDecoration: "none", fontSize: 13, fontWeight: 600 }}>
            VIEW DEMO REPORTS
          </Link>
        </div>
      </section>

      {/* Live stats */}
      <section style={{ borderTop: "1px solid var(--border-subtle)", borderBottom: "1px solid var(--border-subtle)", padding: "32px 48px", background: "var(--bg-surface)" }}>
        <LiveStats />
      </section>

      {/* How it works */}
      <section style={{ padding: "80px 48px", maxWidth: 900, margin: "0 auto" }}>
        <div className="mono" style={{ fontSize: 10, color: "var(--text-muted)", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 40, textAlign: "center" }}>How It Works</div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 24 }}>
          {STEPS.map(({ n, title, desc }) => (
            <div key={n} style={{ padding: "24px", border: "1px solid var(--border-subtle)", borderRadius: 4, background: "var(--bg-surface)" }}>
              <div className="mono" style={{ fontSize: 28, fontWeight: 700, color: "var(--border-active)", marginBottom: 12 }}>{n}</div>
              <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 8, fontFamily: "'Space Grotesk', sans-serif" }}>{title}</div>
              <div style={{ fontSize: 12, color: "var(--text-muted)", lineHeight: 1.6 }}>{desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Corruption patterns */}
      <section style={{ padding: "0 48px 80px", maxWidth: 900, margin: "0 auto" }}>
        <div className="mono" style={{ fontSize: 10, color: "var(--text-muted)", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 24 }}>10 Corruption Patterns Detected</div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 8 }}>
          {PATTERNS.map(({ name, desc }) => (
            <div key={name} style={{ padding: "14px 16px", border: "1px solid var(--border-subtle)", borderRadius: 2, background: "var(--bg-surface)" }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text-primary)", marginBottom: 4 }}>{name}</div>
              <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* For journalists */}
      <section style={{ background: "var(--bg-surface)", borderTop: "1px solid var(--border-subtle)", borderBottom: "1px solid var(--border-subtle)", padding: "64px 48px" }}>
        <div style={{ maxWidth: 640, margin: "0 auto", textAlign: "center" }}>
          <div className="mono" style={{ fontSize: 10, color: "var(--accent-red)", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 16 }}>Built For</div>
          <h2 style={{ fontSize: 24, fontWeight: 700, margin: "0 0 16px", fontFamily: "'Space Grotesk', sans-serif" }}>Journalists, RTI Activists, and NGOs</h2>
          <p style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.7, marginBottom: 28 }}>
            Every investigation brief includes targeted RTI questions under the Right to Information Act 2005,
            evidence summaries ready to publish, and recommended actions for follow-up.
          </p>
          <div style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
            <Link href="/pricing" style={{ background: "none", border: "1px solid var(--accent-red)", color: "var(--accent-red)", padding: "10px 22px", borderRadius: 2, textDecoration: "none", fontSize: 12, fontWeight: 700 }}>
              SEE PLANS
            </Link>
            <Link href="/api-docs" style={{ background: "none", border: "1px solid var(--border-subtle)", color: "var(--text-secondary)", padding: "10px 22px", borderRadius: 2, textDecoration: "none", fontSize: 12 }}>
              API ACCESS
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer style={{ padding: "32px 48px", borderTop: "1px solid var(--border-subtle)", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
        <span className="mono" style={{ fontSize: 10, color: "var(--text-muted)" }}>
          PROCUREWATCH — Data: Public domain (GeM, CPPP) — Not affiliated with any government entity
        </span>
        <div style={{ display: "flex", gap: 20 }}>
          {[["Dashboard", "/dashboard"], ["Pricing", "/pricing"], ["API Docs", "/api-docs"], ["Alerts", "/alerts"]].map(([label, href]) => (
            <Link key={href} href={href} style={{ fontSize: 11, color: "var(--text-muted)", textDecoration: "none" }}>{label}</Link>
          ))}
        </div>
      </footer>
    </div>
  );
}