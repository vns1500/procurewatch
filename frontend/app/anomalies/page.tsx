"use client";

import type { CSSProperties } from "react";
import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion, useReducedMotion } from "framer-motion";
import { getAnomalies, patchAnomaly, generateReport, severityBorderColor, formatRupees } from "@/lib/api";
import type { AnomalyDetail } from "@/lib/api";
import { pageVariants, containerVariants, cardVariants } from "@/lib/motion";
import { RiskRing } from "@/components/ui/RiskRing";
import { TopBar } from "@/components/layout/TopBar";
import { Skeleton } from "@/components/ui/Skeleton";
import { FileText } from "lucide-react";

const ANOMALY_TYPES = [
  "", "single_bid", "rushed_timeline", "bid_splitting",
  "shell_vendor", "repeat_monopoly", "post_award_inflation",
  "inflated_pricing", "spec_tailoring", "geo_mismatch",
];

const SEVERITIES = ["", "critical", "high", "medium", "low"];

const TYPE_LABELS: Record<string, string> = {
  single_bid: "SINGLE BID",
  rushed_timeline: "RUSHED TIMELINE",
  bid_splitting: "BID SPLITTING",
  shell_vendor: "SHELL VENDOR",
  repeat_monopoly: "REPEAT MONOPOLY",
  post_award_inflation: "POST-AWARD INFLATION",
  inflated_pricing: "INFLATED PRICING",
  spec_tailoring: "SPEC TAILORING",
  geo_mismatch: "GEO MISMATCH",
  director_overlap: "DIRECTOR OVERLAP",
};

const SEVERITY_COLORS: Record<string, string> = {
  critical: "var(--accent-red)",
  high: "var(--accent-red)",
  medium: "var(--accent-amber)",
  low: "var(--accent-green)",
};

const SEVERITY_ORDER = ["critical", "high", "medium", "low"];

export default function AnomaliesPage() {
  const [anomalies, setAnomalies] = useState<AnomalyDetail[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState("");
  const [severityFilter, setSeverityFilter] = useState("");
  const [ministryFilter, setMinistryFilter] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [reportGenerating, setReportGenerating] = useState(false);
  const reduced = useReducedMotion();
  const router = useRouter();
  const PAGE_SIZE = 50;

  const load = useCallback(async (p: number, type: string, severity: string, ministry: string) => {
    setLoading(true);
    try {
      const data = await getAnomalies({
        type: type || undefined,
        severity: severity || undefined,
        ministry: ministry || undefined,
        page: p,
        limit: PAGE_SIZE,
      });
      setAnomalies(data.anomalies);
      setTotal(data.total);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(page, typeFilter, severityFilter, ministryFilter); }, [page, typeFilter, severityFilter, ministryFilter, load]);

  const markFalsePositive = async (id: string) => {
    try {
      await patchAnomaly(id, "false_positive");
      setAnomalies((prev) => prev.map((a) => a.id === id ? { ...a, status: "false_positive" } : a));
    } catch (e) {
      console.error(e);
    }
  };

  const handleGenerateReport = async () => {
    if (selected.size === 0) return;
    const tenderIds = anomalies
      .filter((a) => selected.has(a.id))
      .map((a) => a.tender_id);
    const uniqueTenderIds = [...new Set(tenderIds)];
    setReportGenerating(true);
    try {
      const res = await generateReport(uniqueTenderIds);
      setSelected(new Set());
      router.push(`/reports/${res.report_id}`);
    } catch (e) {
      console.error(e);
    } finally {
      setReportGenerating(false);
    }
  };

  const toggleSelect = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const selectAll = () => setSelected(new Set(anomalies.map((a) => a.id)));
  const clearSelected = () => setSelected(new Set());

  // Group by severity
  const grouped: Record<string, AnomalyDetail[]> = {};
  for (const a of anomalies) {
    if (!grouped[a.severity]) grouped[a.severity] = [];
    grouped[a.severity].push(a);
  }
  const severityKeys = SEVERITY_ORDER.filter((s) => grouped[s]?.length);

  const totalPages = Math.ceil(total / PAGE_SIZE);
  const motionProps = reduced ? {} : { initial: "hidden", animate: "visible", variants: pageVariants };

  return (
    <motion.div {...motionProps}>
      <TopBar title="Anomaly Feed" subtitle={`${total.toLocaleString("en-IN")} anomalies detected`} />

      {/* Filters */}
      <div style={{ padding: "14px 32px", borderBottom: "1px solid var(--border-subtle)", display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
        <select
          value={typeFilter}
          onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}
          style={selectStyle}
        >
          {ANOMALY_TYPES.map((t) => (
            <option key={t} value={t} style={{ background: "var(--bg-surface)", color: "var(--text-secondary)" }}>
              {t ? TYPE_LABELS[t] ?? t : "All anomaly types"}
            </option>
          ))}
        </select>
        <select
          value={severityFilter}
          onChange={(e) => { setSeverityFilter(e.target.value); setPage(1); }}
          style={{ ...selectStyle, color: severityFilter ? SEVERITY_COLORS[severityFilter] : "var(--text-muted)" }}
        >
          {SEVERITIES.map((s) => (
            <option key={s} value={s} style={{ background: "var(--bg-surface)", color: s ? SEVERITY_COLORS[s] : "var(--text-muted)" }}>
              {s ? s.charAt(0).toUpperCase() + s.slice(1) : "All severities"}
            </option>
          ))}
        </select>
        <input
          placeholder="Filter ministry…"
          onChange={(e) => { setMinistryFilter(e.target.value); setPage(1); }}
          style={{ ...selectStyle, width: 200 }}
        />

        {/* Bulk select controls */}
        <div style={{ marginLeft: "auto", display: "flex", gap: 8, alignItems: "center" }}>
          {selected.size > 0 && (
            <>
              <span className="mono" style={{ fontSize: 11, color: "var(--text-muted)" }}>{selected.size} selected</span>
              <button onClick={handleGenerateReport} disabled={reportGenerating} style={actionBtnStyle(false)}>
                <FileText size={12} strokeWidth={1.5} /> Generate Report
              </button>
              <button onClick={clearSelected} style={actionBtnStyle(true)}>Clear</button>
            </>
          )}
          {selected.size === 0 && anomalies.length > 0 && (
            <button onClick={selectAll} style={actionBtnStyle(true)}>Select All</button>
          )}
        </div>
      </div>

      {/* Severity-grouped feed */}
      <div style={{ padding: "20px 32px", display: "flex", flexDirection: "column", gap: 24 }}>
        {loading ? (
          <motion.div variants={reduced ? undefined : containerVariants} initial={reduced ? undefined : "hidden"} animate={reduced ? undefined : "visible"} style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderLeft: "3px solid var(--border-active)", borderRadius: 4, padding: "16px 20px", display: "flex", flexDirection: "column", gap: 8 }}>
                <div style={{ display: "flex", gap: 12 }}><Skeleton width={100} height={12} /><Skeleton width={60} height={12} /></div>
                <Skeleton width="70%" height={14} />
                <Skeleton width="40%" height={11} />
              </div>
            ))}
          </motion.div>
        ) : anomalies.length === 0 ? (
          <div style={{ padding: "48px 0", textAlign: "center", color: "var(--text-muted)", fontSize: 13 }}>
            No anomalies match the current filters
          </div>
        ) : (
          severityKeys.map((sev) => (
            <div key={sev}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
                <div style={{ width: 8, height: 8, borderRadius: "50%", background: SEVERITY_COLORS[sev] }} />
                <span className="mono" style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.1em", color: SEVERITY_COLORS[sev], textTransform: "uppercase" }}>
                  {sev}
                </span>
                <span className="mono" style={{ fontSize: 10, color: "var(--text-muted)" }}>({grouped[sev].length})</span>
                <div style={{ flex: 1, height: 1, background: "var(--border-subtle)" }} />
              </div>
              <motion.div
                variants={reduced ? undefined : containerVariants}
                initial={reduced ? undefined : "hidden"}
                animate={reduced ? undefined : "visible"}
                style={{ display: "flex", flexDirection: "column", gap: 8 }}
              >
                {grouped[sev].map((a) => (
                  <AnomalyCard
                    key={a.id}
                    anomaly={a}
                    reduced={!!reduced}
                    selected={selected.has(a.id)}
                    onToggleSelect={() => toggleSelect(a.id)}
                    onMarkFalsePositive={() => markFalsePositive(a.id)}
                  />
                ))}
              </motion.div>
            </div>
          ))
        )}

        {!loading && totalPages > 1 && (
          <div style={{ display: "flex", justifyContent: "center", gap: 4, padding: "8px 0", alignItems: "center" }}>
            <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1} style={pageBtnStyle(page === 1)}>← Prev</button>
            <span className="mono" style={{ fontSize: 11, color: "var(--text-muted)", padding: "0 8px" }}>{page} / {totalPages}</span>
            <button onClick={() => setPage(Math.min(totalPages, page + 1))} disabled={page === totalPages} style={pageBtnStyle(page === totalPages)}>Next →</button>
          </div>
        )}
      </div>
    </motion.div>
  );
}

function AnomalyCard({
  anomaly: a,
  reduced,
  selected,
  onToggleSelect,
  onMarkFalsePositive,
}: {
  anomaly: AnomalyDetail;
  reduced: boolean;
  selected: boolean;
  onToggleSelect: () => void;
  onMarkFalsePositive: () => void;
}) {
  const borderColor = severityBorderColor(a.severity);
  const sevColor = SEVERITY_COLORS[a.severity] ?? "var(--text-muted)";
  const isFp = a.status === "false_positive";

  return (
    <motion.div
      variants={reduced ? undefined : cardVariants}
      style={{
        background: selected ? "var(--bg-elevated)" : "var(--bg-surface)",
        border: `1px solid ${selected ? "var(--border-active)" : "var(--border-subtle)"}`,
        borderLeft: `3px solid ${isFp ? "var(--text-muted)" : borderColor}`,
        borderRadius: 4,
        padding: "14px 16px",
        display: "grid",
        gridTemplateColumns: "20px 1fr auto",
        gap: 14,
        alignItems: "start",
        opacity: isFp ? 0.55 : 1,
        transition: "background 150ms, border-color 150ms",
      }}
    >
      {/* Checkbox */}
      <div
        onClick={onToggleSelect}
        style={{ width: 16, height: 16, border: `2px solid ${selected ? borderColor : "var(--border-active)"}`, borderRadius: 2, background: selected ? borderColor : "transparent", cursor: "pointer", marginTop: 2, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}
      >
        {selected && <span style={{ fontSize: 10, color: "var(--bg-base)", fontWeight: 700 }}>✓</span>}
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 7, minWidth: 0 }}>
        {/* Header row */}
        <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
          <span className="mono" style={{ fontSize: 9, fontWeight: 700, letterSpacing: "0.08em", padding: "2px 7px", border: `1px solid ${isFp ? "var(--text-muted)" : borderColor}`, borderRadius: 2, color: isFp ? "var(--text-muted)" : borderColor }}>
            {TYPE_LABELS[a.type] ?? a.type.toUpperCase()}
          </span>
          <span className="mono" style={{ fontSize: 9, color: isFp ? "var(--text-muted)" : sevColor, fontWeight: 600, textTransform: "uppercase" }}>
            {a.severity}
          </span>
          <span className="mono" style={{ fontSize: 10, color: "var(--text-muted)" }}>
            {new Date(a.detected_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })}
          </span>
          <span className="mono" style={{ fontSize: 9, padding: "1px 5px", border: "1px solid var(--border-active)", borderRadius: 2, color: isFp ? "var(--accent-amber)" : "var(--text-muted)", textTransform: "uppercase" }}>
            {a.status}
          </span>
          {!isFp && (
            <button
              onClick={onMarkFalsePositive}
              style={{ marginLeft: "auto", fontSize: 9, background: "none", border: "1px solid var(--border-active)", borderRadius: 2, color: "var(--text-muted)", padding: "2px 7px", cursor: "pointer", fontFamily: "JetBrains Mono, monospace", letterSpacing: "0.04em" }}
            >
              Mark False Positive
            </button>
          )}
        </div>

        {/* Tender title */}
        <span style={{ fontSize: 12, fontWeight: 500, color: isFp ? "var(--text-muted)" : "var(--text-primary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {a.tender_title}
        </span>

        {/* Ministry */}
        <span style={{ fontSize: 11, color: "var(--text-muted)" }}>{a.ministry}</span>

        {/* Evidence summary */}
        {a.evidence && (
          <div style={{ display: "flex", gap: 14, flexWrap: "wrap", marginTop: 2 }}>
            {Object.entries(a.evidence).slice(0, 4).filter(([k]) => !k.endsWith("_ids") && !k.endsWith("_scores") && !k.endsWith("_paise")).map(([k, v]) => (
              <div key={k} style={{ display: "flex", flexDirection: "column", gap: 1 }}>
                <span style={{ fontSize: 9, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>{k.replace(/_/g, " ")}</span>
                <span className="mono" style={{ fontSize: 11, color: "var(--text-secondary)" }}>
                  {typeof v === "number" && k.includes("rupees")
                    ? formatRupees(v as number)
                    : typeof v === "number"
                    ? v.toLocaleString("en-IN")
                    : String(v).slice(0, 40)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      <RiskRing score={a.risk_score} size={40} />
    </motion.div>
  );
}

const selectStyle: CSSProperties = {
  background: "var(--bg-surface)",
  border: "1px solid var(--border-subtle)",
  borderRadius: 2,
  color: "var(--text-secondary)",
  fontSize: 12,
  padding: "6px 10px",
  outline: "none",
};

function actionBtnStyle(muted: boolean): CSSProperties {
  return {
    display: "flex",
    alignItems: "center",
    gap: 5,
    fontSize: 11,
    background: muted ? "var(--bg-surface)" : "var(--accent-red)",
    border: `1px solid ${muted ? "var(--border-active)" : "var(--accent-red)"}`,
    borderRadius: 2,
    color: muted ? "var(--text-secondary)" : "var(--bg-base)",
    padding: "5px 10px",
    cursor: "pointer",
    fontFamily: "JetBrains Mono, monospace",
    letterSpacing: "0.04em",
  };
}

function pageBtnStyle(disabled: boolean): CSSProperties {
  return { background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", color: disabled ? "var(--text-muted)" : "var(--text-primary)", borderRadius: 2, padding: "5px 12px", fontSize: 12, cursor: disabled ? "default" : "pointer" };
}
