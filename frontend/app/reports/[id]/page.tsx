"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion, useReducedMotion } from "framer-motion";
import { getReport, exportReportPdf } from "@/lib/api";
import type { ReportDetail, RedFlag } from "@/lib/api";
import { TopBar } from "@/components/layout/TopBar";
import { Download, Copy, Check, ArrowLeft, AlertTriangle } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08 } },
};
const cardVariants = {
  hidden: { opacity: 0, y: 8 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.25, ease: "easeOut" } },
};

function RiskBadge({ level }: { level: string | null }) {
  if (!level) return null;
  const color =
    level === "CRITICAL" ? "var(--accent-red)" :
    level === "HIGH"     ? "var(--accent-amber)" :
                           "var(--accent-green)";
  return (
    <span className="mono" style={{
      fontSize: 10, fontWeight: 700, letterSpacing: "0.12em",
      padding: "3px 10px", border: `1px solid ${color}`,
      borderRadius: 2, color, background: `${color}18`,
    }}>
      {level} RISK
    </span>
  );
}

function SeverityDot({ severity }: { severity: string }) {
  const color = severity === "critical" ? "var(--accent-red)"
              : severity === "high"     ? "var(--accent-amber)"
              :                           "var(--accent-green)";
  return (
    <span className="mono" style={{ fontSize: 9, padding: "2px 6px", border: `1px solid ${color}`, borderRadius: 2, color, fontWeight: 700 }}>
      {severity.toUpperCase()}
    </span>
  );
}

function CopyButton({ text, label = "Copy" }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={async () => {
        await navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }}
      style={{ display: "flex", alignItems: "center", gap: 4, background: "none", border: "1px solid var(--border-subtle)", borderRadius: 2, color: copied ? "var(--accent-green)" : "var(--text-muted)", fontSize: 10, padding: "3px 8px", cursor: "pointer", transition: "color 150ms" }}
    >
      {copied ? <Check size={10} strokeWidth={2} /> : <Copy size={10} strokeWidth={1.5} />}
      {copied ? "Copied" : label}
    </button>
  );
}

function Section({ title, children, delay = 0, reduced }: { title: string; children: React.ReactNode; delay?: number; reduced: boolean | null }) {
  return (
    <motion.div
      variants={reduced ? undefined : cardVariants}
      transition={reduced ? undefined : { delay }}
      style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 4, padding: "20px 24px" }}
    >
      <div style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 14, borderBottom: "1px solid var(--border-subtle)", paddingBottom: 8 }}>
        {title}
      </div>
      {children}
    </motion.div>
  );
}

export default function ReportDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const reduced = useReducedMotion();
  const [report, setReport] = useState<ReportDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [streamText, setStreamText] = useState("");
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const sseRef = useRef<EventSource | null>(null);

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        const data = await getReport(params.id);
        if (!mounted) return;
        setReport(data);
        setLoading(false);

        if (data.status === "generating") {
          const es = new EventSource(`${API_BASE}/reports/${params.id}/stream`);
          sseRef.current = es;
          es.addEventListener("chunk", (e) => {
            if (mounted) setStreamText((prev) => prev + (e as MessageEvent).data);
          });
          es.addEventListener("done", () => {
            es.close();
            getReport(params.id).then((d) => { if (mounted) { setReport(d); setStreamText(""); } });
          });
          es.addEventListener("error", () => {
            es.close();
            pollRef.current = setInterval(async () => {
              try {
                const updated = await getReport(params.id);
                if (!mounted) return;
                if (updated.status !== "generating") {
                  clearInterval(pollRef.current!);
                  setReport(updated);
                }
              } catch { /* ignore */ }
            }, 2000);
          });
        }
      } catch (e) {
        console.error(e);
        if (mounted) setLoading(false);
      }
    }

    load();
    return () => {
      mounted = false;
      if (pollRef.current) clearInterval(pollRef.current);
      if (sseRef.current) sseRef.current.close();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.id]);

  const motionProps = reduced ? {} : { initial: "hidden", animate: "visible", variants: containerVariants };

  if (loading) {
    return (
      <div>
        <TopBar title="Loading Report..." subtitle="" />
        <div style={{ padding: "40px 32px", display: "flex", flexDirection: "column", gap: 16 }}>
          {[120, 80, 180, 100].map((h, i) => (
            <div key={i} style={{ height: h, background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 4 }} />
          ))}
        </div>
      </div>
    );
  }

  if (!report) return <div style={{ padding: 32, color: "var(--text-muted)" }}>Report not found.</div>;

  const { sections } = report;

  return (
    <div>
      <div style={{ position: "sticky", top: 0, zIndex: 50, background: "var(--bg-base)", borderBottom: "1px solid var(--border-subtle)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "12px 32px" }}>
          <button
            onClick={() => router.push("/reports")}
            style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", display: "flex", alignItems: "center", gap: 5, fontSize: 12 }}
          >
            <ArrowLeft size={13} strokeWidth={1.5} /> Reports
          </button>
          <span style={{ color: "var(--border-subtle)" }}>|</span>
          <RiskBadge level={report.risk_level} />
          <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)", flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {report.title ?? "Investigation Brief"}
          </span>
          <span className="mono" style={{ fontSize: 9, color: "var(--text-muted)", flexShrink: 0 }}>
            {new Date(report.created_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })}
          </span>
          {report.status === "ready" && (
            <button
              onClick={() => exportReportPdf(report.id)}
              style={{ display: "flex", alignItems: "center", gap: 6, background: "var(--bg-elevated)", border: "1px solid var(--border-subtle)", borderRadius: 2, color: "var(--text-secondary)", fontSize: 11, padding: "6px 12px", cursor: "pointer" }}
            >
              <Download size={12} strokeWidth={1.5} /> Export PDF
            </button>
          )}
        </div>
      </div>

      {report.status === "generating" && (
        <div style={{ padding: "40px 32px" }}>
          <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 4, padding: "28px 28px" }}>
            <div className="mono" style={{ fontSize: 11, color: "var(--accent-amber)", marginBottom: 12, letterSpacing: "0.06em" }}>
              GENERATING INVESTIGATION BRIEF
              <span style={{ animation: "blink 1s step-end infinite", marginLeft: 2 }}>_</span>
            </div>
            {streamText ? (
              <pre style={{ fontSize: 11, color: "var(--text-secondary)", whiteSpace: "pre-wrap", wordBreak: "break-word", fontFamily: "JetBrains Mono, monospace", lineHeight: 1.6, maxHeight: 400, overflow: "hidden", margin: 0 }}>
                {streamText.slice(-1200)}
              </pre>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {[80, 65, 90, 70].map((w, i) => (
                  <div key={i} style={{ height: 10, width: `${w}%`, background: "var(--bg-elevated)", borderRadius: 2, animation: "pulse 1.5s ease-in-out infinite", animationDelay: `${i * 200}ms` }} />
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {report.status === "failed" && (
        <div style={{ padding: "40px 32px" }}>
          <div style={{ display: "flex", gap: 12, color: "var(--accent-red)", alignItems: "center", fontSize: 13 }}>
            <AlertTriangle size={16} /> Report generation failed. Please try generating again.
          </div>
        </div>
      )}

      {report.status === "ready" && sections && (
        <motion.div
          {...motionProps}
          style={{ padding: "28px 32px", display: "flex", flexDirection: "column", gap: 14, maxWidth: 920 }}
        >
          <Section title="Executive Summary" delay={0} reduced={reduced}>
            <p style={{ fontSize: 14, color: "var(--text-primary)", lineHeight: 1.7, margin: 0 }}>
              {sections.executive_summary}
            </p>
          </Section>

          <Section title="Red Flags Identified" delay={0.08} reduced={reduced}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                  {["Flag", "Severity", "Evidence"].map((h) => (
                    <th key={h} style={{ textAlign: "left", padding: "5px 10px 8px", fontSize: 9, fontWeight: 700, color: "var(--text-muted)", letterSpacing: "0.07em", textTransform: "uppercase" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sections.red_flags.map((f: RedFlag, i: number) => (
                  <tr key={i} style={{ borderBottom: i < sections.red_flags.length - 1 ? "1px solid var(--border-subtle)" : "none" }}>
                    <td style={{ padding: "10px 10px", fontSize: 12, fontWeight: 600, color: "var(--text-primary)", whiteSpace: "nowrap" }}>{f.flag}</td>
                    <td style={{ padding: "10px 10px" }}><SeverityDot severity={f.severity} /></td>
                    <td style={{ padding: "10px 10px", fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.5 }}>{f.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Section>

          <Section title="Evidence Analysis" delay={0.16} reduced={reduced}>
            {sections.evidence_analysis.split("\n\n").filter(Boolean).map((para, i) => (
              <p key={i} style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.75, margin: "0 0 12px" }}>{para}</p>
            ))}
          </Section>

          <Section title="Comparative Analysis" delay={0.24} reduced={reduced}>
            <div className="mono" style={{ fontSize: 11, color: "var(--text-secondary)", lineHeight: 1.7, borderLeft: "3px solid var(--accent-red)", paddingLeft: 14, background: "var(--bg-elevated)", padding: "12px 16px" }}>
              {sections.comparative_analysis}
            </div>
          </Section>

          <Section title="RTI Questions to File" delay={0.32} reduced={reduced}>
            <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 10 }}>
              <CopyButton text={sections.rti_questions.map((q: string, i: number) => `${i + 1}. ${q}`).join("\n\n")} label="Copy all" />
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {sections.rti_questions.map((q: string, i: number) => (
                <div key={i} style={{ display: "flex", gap: 12, alignItems: "flex-start", padding: "10px 14px", border: "1px solid var(--border-subtle)", borderRadius: 2, background: "var(--bg-elevated)" }}>
                  <span className="mono" style={{ fontSize: 10, color: "var(--accent-red)", fontWeight: 700, flexShrink: 0, marginTop: 2 }}>{i + 1}.</span>
                  <span style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.55, flex: 1 }}>{q}</span>
                  <CopyButton text={q} />
                </div>
              ))}
            </div>
          </Section>

          <Section title="Recommended Actions" delay={0.4} reduced={reduced}>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {sections.recommended_actions.map((a: string, i: number) => (
                <div key={i} style={{ display: "flex", gap: 12, alignItems: "flex-start", padding: "8px 0", borderBottom: i < sections.recommended_actions.length - 1 ? "1px solid var(--border-subtle)" : "none" }}>
                  <div style={{ width: 16, height: 16, border: "1px solid var(--border-active)", borderRadius: 2, flexShrink: 0, marginTop: 2 }} />
                  <span style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.55 }}>{a}</span>
                </div>
              ))}
            </div>
          </Section>

          {sections.estimated_loss && (
            <Section title="Estimated Public Money at Risk" delay={0.48} reduced={reduced}>
              <div className="mono" style={{ fontSize: 22, fontWeight: 700, color: "var(--accent-red)" }}>
                {sections.estimated_loss}
              </div>
            </Section>
          )}
        </motion.div>
      )}

      <style>{`
        @keyframes blink { 50% { opacity: 0; } }
        @keyframes pulse { 0%, 100% { opacity: 0.4; } 50% { opacity: 0.8; } }
      `}</style>
    </div>
  );
}