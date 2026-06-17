"use client";

import { TopBar } from "@/components/layout/TopBar";
import { Copy, Check } from "lucide-react";
import { useState } from "react";

function Code({ children }: { children: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <div style={{ position: "relative", background: "var(--bg-elevated)", border: "1px solid var(--border-subtle)", borderRadius: 2, padding: "14px 16px", marginTop: 8 }}>
      <pre style={{ margin: 0, fontSize: 11, color: "var(--text-secondary)", fontFamily: "JetBrains Mono, monospace", whiteSpace: "pre-wrap", wordBreak: "break-all" }}>{children}</pre>
      <button
        onClick={async () => { await navigator.clipboard.writeText(children); setCopied(true); setTimeout(() => setCopied(false), 1500); }}
        style={{ position: "absolute", top: 8, right: 8, background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer" }}
      >
        {copied ? <Check size={12} /> : <Copy size={12} />}
      </button>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 40 }}>
      <div style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", letterSpacing: "0.1em", textTransform: "uppercase", paddingBottom: 8, borderBottom: "1px solid var(--border-subtle)", marginBottom: 16 }}>
        {title}
      </div>
      {children}
    </div>
  );
}

function Endpoint({ method, path, desc, response }: { method: string; path: string; desc: string; response: string }) {
  const color = method === "GET" ? "var(--accent-green)" : method === "POST" ? "var(--accent-amber)" : "var(--accent-red)";
  return (
    <div style={{ marginBottom: 20, padding: "14px 16px", border: "1px solid var(--border-subtle)", borderRadius: 2, background: "var(--bg-surface)" }}>
      <div style={{ display: "flex", gap: 10, alignItems: "baseline", marginBottom: 6 }}>
        <span className="mono" style={{ fontSize: 10, fontWeight: 700, color, minWidth: 40 }}>{method}</span>
        <span className="mono" style={{ fontSize: 12, color: "var(--text-primary)" }}>{path}</span>
      </div>
      <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 8 }}>{desc}</div>
      <Code>{response}</Code>
    </div>
  );
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function ApiDocsPage() {
  return (
    <div>
      <TopBar title="API Documentation" subtitle="Programmatic access for media and NGOs" />

      <div style={{ padding: "32px", maxWidth: 820, display: "flex", flexDirection: "column", gap: 0 }}>

        <Section title="Authentication">
          <p style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.65, marginBottom: 12 }}>
            All write endpoints and report generation require an API key. Pass it in the <code className="mono" style={{ fontSize: 11, padding: "1px 5px", background: "var(--bg-elevated)", borderRadius: 2 }}>X-API-Key</code> header.
            Free accounts include 10 reports/month. Pro accounts have unlimited access.
          </p>
          <Code>{`# Register for a free API key
curl -X POST ${API_BASE}/auth/register \\
  -H "Content-Type: application/json" \\
  -d '{"email": "you@example.com"}'

# Response: {"api_key": "pw_...", "email": "...", "plan": "free"}

# Use your key
curl ${API_BASE}/reports \\
  -H "X-API-Key: pw_your_key_here"`}</Code>
        </Section>

        <Section title="Rate Limits">
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                {["Plan", "Reports/month", "API calls/day"].map(h => (
                  <th key={h} style={{ textAlign: "left", padding: "6px 10px", fontSize: 9, color: "var(--text-muted)", letterSpacing: "0.07em", textTransform: "uppercase" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[["Free", "10", "100"], ["Pro", "Unlimited", "10,000"], ["Enterprise", "Unlimited", "Unlimited"]].map(([plan, reports, calls]) => (
                <tr key={plan} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                  <td style={{ padding: "8px 10px", fontWeight: 600 }}>{plan}</td>
                  <td className="mono" style={{ padding: "8px 10px", color: "var(--text-muted)" }}>{reports}</td>
                  <td className="mono" style={{ padding: "8px 10px", color: "var(--text-muted)" }}>{calls}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>

        <Section title="Tenders">
          <Endpoint method="GET" path="/tenders" desc="List tenders with optional filters: ministry, state, risk_min, risk_max, anomaly_type, date_from, date_to, page, limit" response={`GET /tenders?risk_min=70&limit=5

{
  "tenders": [
    {
      "id": "uuid",
      "gem_id": "GEMF10794...",
      "title": "Road Construction Materials",
      "ministry": "Ministry of Road Transport",
      "state": "Maharashtra",
      "value": 831212631158,
      "risk_score": 100,
      "anomaly_flags": ["inflated_pricing", "single_bid"],
      "vendor_name": "ABC Infrastructure Ltd"
    }
  ],
  "total": 610,
  "page": 1,
  "limit": 5
}`} />
        </Section>

        <Section title="Anomalies">
          <Endpoint method="GET" path="/anomalies" desc="List detected anomalies sorted by parent tender risk score. Filters: type, severity, ministry, date_from" response={`GET /anomalies?type=single_bid&severity=critical

{
  "anomalies": [
    {
      "id": "uuid",
      "type": "single_bid",
      "severity": "critical",
      "evidence": {"bid_count": 1, "value_rupees": 83121263.0},
      "tender_title": "...",
      "ministry": "...",
      "risk_score": 100
    }
  ],
  "total": 215
}`} />
        </Section>

        <Section title="Reports (AI Investigation Briefs)">
          <Endpoint method="POST" path="/reports/generate" desc="Generate an AI investigation brief for selected tenders. Requires X-API-Key." response={`POST /reports/generate
X-API-Key: pw_your_key

{"tender_ids": ["uuid1", "uuid2"], "report_type": "full"}

# Response (immediate):
{"report_id": "uuid", "status": "generating"}

# Poll status:
GET /reports/{report_id}
{"status": "ready", "title": "Investigation Brief: ...", "sections": {...}}`} />

          <Endpoint method="GET" path="/reports/{id}/stream" desc="SSE stream of Claude generation. Connect via EventSource for live typewriter output while report generates." response={`const es = new EventSource('/reports/{id}/stream');
es.addEventListener('chunk', e => console.log(e.data));
es.addEventListener('done', () => es.close());`} />

          <Endpoint method="GET" path="/export/reports/{id}/pdf" desc="Download PDF version of a completed report. Returns application/pdf." response={`curl ${API_BASE}/export/reports/{id}/pdf \\
  --output report.pdf`} />
        </Section>

        <Section title="Vendors">
          <Endpoint method="GET" path="/vendors/{id}" desc="Full vendor profile with win rate, contract history, director network" response={`{
  "id": "uuid",
  "name": "Vendor Name",
  "gstin": "27AABC...",
  "win_rate": 12.5,
  "total_wins": 8,
  "total_value": 4200000000,
  "risk_level": "high",
  "director_network": {...}
}`} />
        </Section>

        <Section title="Alerts">
          <Endpoint method="POST" path="/alerts/subscribe" desc="Subscribe to anomaly alerts via email when new detections match your criteria" response={`POST /alerts/subscribe

{
  "ministries": ["Ministry of Defence", "Ministry of Health"],
  "keywords": ["ventilator", "CCTV"],
  "email": "journalist@thewire.in"
}

{"alert_id": "uuid"}`} />
        </Section>

        <Section title="Dashboard Stats">
          <Endpoint method="GET" path="/dashboard/stats" desc="Aggregate statistics: flagged counts, suspicious value, ministry risk breakdown, state heatmap" response={`{
  "flagged_this_month": 47,
  "suspicious_value": 6234500000000,
  "new_anomalies_today": 12,
  "total_tenders_scanned": 610,
  "top_risky_ministries": [...],
  "state_risk_map": [...]
}`} />
        </Section>

      </div>
    </div>
  );
}
