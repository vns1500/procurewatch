"use client";

import { useEffect, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { useRouter } from "next/navigation";
import { getReports, generateReport, deleteReport, getTenders } from "@/lib/api";
import type { ReportSummary, Tender } from "@/lib/api";
import { pageVariants, containerVariants, cardVariants } from "@/lib/motion";
import { TopBar } from "@/components/layout/TopBar";
import { Skeleton } from "@/components/ui/Skeleton";
import { FileText, Plus, Clock, CheckCircle, XCircle, Trash2 } from "lucide-react";

function RiskLevelBadge({ level }: { level: string | null }) {
  if (!level) return null;
  const color =
    level === "CRITICAL" ? "var(--accent-red)" :
    level === "HIGH"     ? "var(--accent-amber)" :
                           "var(--accent-green)";
  return (
    <span className="mono" style={{
      fontSize: 9, fontWeight: 700, letterSpacing: "0.1em",
      padding: "2px 6px", border: `1px solid ${color}`,
      borderRadius: 2, color,
    }}>
      {level}
    </span>
  );
}

export default function ReportsPage() {
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [flaggedTenders, setFlaggedTenders] = useState<Tender[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const router = useRouter();
  const reduced = useReducedMotion();

  async function loadReports() {
    try {
      const data = await getReports();
      setReports(data);
    } catch (e) { console.error(e); } finally { setLoading(false); }
  }

  useEffect(() => { loadReports(); }, []);

  async function openModal() {
    setShowModal(true);
    setSelected(new Set());
    try {
      const data = await getTenders({ risk_min: 30, limit: 50 });
      setFlaggedTenders(data.tenders);
    } catch (e) { console.error(e); }
  }

  async function handleGenerate() {
    if (selected.size === 0) return;
    setGenerating(true);
    try {
      const result = await generateReport([...selected], "full");
      setShowModal(false);
      router.push(`/reports/${result.report_id}`);
    } catch (e) { console.error(e); } finally { setGenerating(false); }
  }

  async function handleDelete(id: string, e: React.MouseEvent) {
    e.stopPropagation();
    setDeletingId(id);
    try {
      await deleteReport(id);
      setReports((prev) => prev.filter((r) => r.id !== id));
    } catch (e) { console.error(e); } finally { setDeletingId(null); }
  }

  function toggleSelect(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }

  const motionProps = reduced ? {} : { initial: "hidden", animate: "visible", variants: pageVariants };

  return (
    <motion.div {...motionProps}>
      <TopBar
        title="Intelligence Reports"
        subtitle="AI-generated investigative briefs"
        action={
          <button
            onClick={openModal}
            style={{
              display: "flex", alignItems: "center", gap: 6,
              background: "var(--accent-red)", border: "none", borderRadius: 2,
              color: "var(--bg-base)", fontSize: 11, fontWeight: 700,
              padding: "6px 14px", cursor: "pointer",
              fontFamily: "JetBrains Mono, monospace", letterSpacing: "0.04em",
            }}
          >
            <Plus size={12} strokeWidth={2.5} /> New Report
          </button>
        }
      />

      <div style={{ padding: "24px 32px", display: "flex", flexDirection: "column", gap: 16 }}>
        {loading ? (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 12 }}>
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 4, padding: "18px 20px" }}>
                <Skeleton width={180} height={12} /><div style={{ height: 8 }} /><Skeleton width="90%" height={10} /><div style={{ height: 6 }} /><Skeleton width={100} height={9} />
              </div>
            ))}
          </div>
        ) : reports.length === 0 ? (
          <motion.div
            variants={reduced ? undefined : cardVariants}
            style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 4, padding: "80px 0", textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center", gap: 14 }}
          >
            <FileText size={36} strokeWidth={1} color="var(--text-muted)" />
            <span style={{ fontSize: 14, color: "var(--text-muted)" }}>No reports yet</span>
            <span style={{ fontSize: 12, color: "var(--text-muted)", opacity: 0.5 }}>Select flagged tenders and generate an AI investigative brief</span>
            <button onClick={openModal} style={{ marginTop: 8, display: "flex", alignItems: "center", gap: 6, background: "var(--accent-red)", border: "none", borderRadius: 2, color: "var(--bg-base)", fontSize: 12, fontWeight: 700, padding: "8px 18px", cursor: "pointer" }}>
              <Plus size={12} strokeWidth={2.5} /> Generate First Report
            </button>
          </motion.div>
        ) : (
          <motion.div
            variants={reduced ? undefined : containerVariants}
            initial={reduced ? undefined : "hidden"}
            animate={reduced ? undefined : "visible"}
            style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 12 }}
          >
            {reports.map((r) => (
              <motion.div
                key={r.id}
                variants={reduced ? undefined : cardVariants}
                onClick={() => r.status === "ready" && router.push(`/reports/${r.id}`)}
                style={{
                  background: "var(--bg-surface)",
                  border: "1px solid var(--border-subtle)",
                  borderLeft: r.risk_level === "CRITICAL" ? "3px solid var(--accent-red)"
                             : r.risk_level === "HIGH"    ? "3px solid var(--accent-amber)"
                             : "3px solid var(--border-subtle)",
                  borderRadius: 4, padding: "16px 18px",
                  cursor: r.status === "ready" ? "pointer" : "default",
                  transition: "background 150ms", position: "relative",
                }}
                onMouseEnter={(e) => r.status === "ready" && ((e.currentTarget as HTMLDivElement).style.background = "var(--bg-elevated)")}
                onMouseLeave={(e) => ((e.currentTarget as HTMLDivElement).style.background = "var(--bg-surface)")}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                  {r.status === "ready"      && <CheckCircle size={13} strokeWidth={1.5} color="var(--accent-green)" />}
                  {r.status === "generating" && <Clock size={13} strokeWidth={1.5} color="var(--accent-amber)" />}
                  {r.status === "failed"     && <XCircle size={13} strokeWidth={1.5} color="var(--accent-red)" />}
                  <RiskLevelBadge level={r.risk_level} />
                  <span className="mono" style={{ fontSize: 9, color: "var(--text-muted)", marginLeft: "auto" }}>
                    {r.tender_count} tender{r.tender_count !== 1 ? "s" : ""}
                  </span>
                  <button
                    onClick={(e) => handleDelete(r.id, e)}
                    disabled={deletingId === r.id}
                    style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", padding: "2px 4px", display: "flex", opacity: 0.5 }}
                    onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.opacity = "1"; }}
                    onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.opacity = "0.5"; }}
                  >
                    <Trash2 size={12} strokeWidth={1.5} />
                  </button>
                </div>
                <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)", marginBottom: 6, lineHeight: 1.35, display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                  {r.title ?? (r.status === "generating" ? "Generating investigation brief…" : `Report — ${r.tender_count} tender(s)`)}
                </div>
                {r.summary_preview && (
                  <p style={{ fontSize: 11, color: "var(--text-secondary)", margin: "0 0 8px", lineHeight: 1.5, display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                    {r.summary_preview}
                  </p>
                )}
                <span className="mono" style={{ fontSize: 9, color: "var(--text-muted)" }}>
                  {new Date(r.created_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" })}
                </span>
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>

      {showModal && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.75)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 200 }}>
          <div style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-active)", borderRadius: 4, padding: "24px", width: 620, maxHeight: "82vh", display: "flex", flexDirection: "column", gap: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <div style={{ fontSize: 14, fontWeight: 700, color: "var(--text-primary)" }}>Select Tenders for AI Brief</div>
                <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 3 }}>Flagged tenders (risk 30+). Claude will analyse all selected.</div>
              </div>
              <button onClick={() => setShowModal(false)} style={{ background: "none", border: "none", color: "var(--text-muted)", fontSize: 20, cursor: "pointer", lineHeight: 1 }}>x</button>
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <button onClick={() => setSelected(new Set(flaggedTenders.map(t => t.id)))} style={{ fontSize: 10, background: "none", border: "1px solid var(--border-subtle)", borderRadius: 2, color: "var(--text-muted)", padding: "4px 10px", cursor: "pointer" }}>
                Select all ({flaggedTenders.length})
              </button>
              <button onClick={() => setSelected(new Set())} style={{ fontSize: 10, background: "none", border: "1px solid var(--border-subtle)", borderRadius: 2, color: "var(--text-muted)", padding: "4px 10px", cursor: "pointer" }}>Clear</button>
              <span className="mono" style={{ fontSize: 10, color: "var(--accent-red)", marginLeft: "auto", alignSelf: "center" }}>{selected.size} selected</span>
            </div>
            <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 5, maxHeight: 380 }}>
              {flaggedTenders.map((t) => (
                <label key={t.id} style={{ display: "flex", alignItems: "center", gap: 10, padding: "9px 12px", background: selected.has(t.id) ? "var(--bg-surface)" : "transparent", borderRadius: 2, cursor: "pointer", border: `1px solid ${selected.has(t.id) ? "var(--accent-red)" : "var(--border-subtle)"}`, transition: "all 120ms" }}>
                  <input type="checkbox" checked={selected.has(t.id)} onChange={() => toggleSelect(t.id)} style={{ accentColor: "var(--accent-red)", flexShrink: 0 }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 12, color: "var(--text-primary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{t.title}</div>
                    <div className="mono" style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 2 }}>{t.ministry} - Risk {t.risk_score}/100</div>
                  </div>
                </label>
              ))}
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, borderTop: "1px solid var(--border-subtle)", paddingTop: 14 }}>
              <button onClick={() => setShowModal(false)} style={{ background: "none", border: "1px solid var(--border-subtle)", borderRadius: 2, color: "var(--text-muted)", fontSize: 12, padding: "7px 16px", cursor: "pointer" }}>Cancel</button>
              <button onClick={handleGenerate} disabled={selected.size === 0 || generating} style={{ background: selected.size === 0 ? "var(--border-subtle)" : "var(--accent-red)", border: "none", borderRadius: 2, color: selected.size === 0 ? "var(--text-muted)" : "var(--bg-base)", fontSize: 12, fontWeight: 700, padding: "7px 20px", cursor: selected.size === 0 ? "default" : "pointer" }}>
                {generating ? "Queuing…" : `Generate AI Brief (${selected.size})`}
              </button>
            </div>
          </div>
        </div>
      )}
    </motion.div>
  );
}
