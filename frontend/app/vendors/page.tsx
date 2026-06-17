"use client";

import { useEffect, useState, useCallback } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { useRouter } from "next/navigation";
import { getVendors, formatRupees, riskLevelColor } from "@/lib/api";
import type { VendorSummary } from "@/lib/api";
import { pageVariants, containerVariants, tableRowVariants } from "@/lib/motion";
import { TopBar } from "@/components/layout/TopBar";
import { TableRowSkeleton } from "@/components/ui/Skeleton";

const RISK_LEVELS = ["", "critical", "high", "medium", "low"];

export default function VendorsPage() {
  const [vendors, setVendors] = useState<VendorSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [riskFilter, setRiskFilter] = useState("");
  const [stateFilter, setStateFilter] = useState("");
  const router = useRouter();
  const reduced = useReducedMotion();
  const PAGE_SIZE = 25;

  const load = useCallback(async (p: number, risk: string, state: string) => {
    setLoading(true);
    try {
      const data = await getVendors({ page: p, limit: PAGE_SIZE, risk_level: risk || undefined, state: state || undefined });
      setVendors(data.vendors);
      setTotal(data.total);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(page, riskFilter, stateFilter); }, [page, riskFilter, stateFilter, load]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  const motionProps = reduced ? {} : { initial: "hidden", animate: "visible", variants: pageVariants };

  return (
    <motion.div {...motionProps}>
      <TopBar title="Vendor Registry" subtitle={`${total.toLocaleString("en-IN")} vendors indexed`} />

      {/* Filters */}
      <div style={{ padding: "14px 32px", borderBottom: "1px solid var(--border-subtle)", display: "flex", gap: 10 }}>
        <input
          placeholder="Filter state…"
          onChange={(e) => { setStateFilter(e.target.value); setPage(1); }}
          style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 2, color: "var(--text-primary)", fontSize: 12, padding: "6px 10px", outline: "none", width: 180 }}
        />
        <select
          value={riskFilter}
          onChange={(e) => { setRiskFilter(e.target.value); setPage(1); }}
          style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 2, color: riskFilter ? riskLevelColor(riskFilter) : "var(--text-muted)", fontSize: 12, padding: "6px 10px", outline: "none" }}
        >
          {RISK_LEVELS.map((r) => (
            <option key={r} value={r} style={{ color: r ? riskLevelColor(r) : "var(--text-muted)", background: "var(--bg-surface)" }}>
              {r ? r.charAt(0).toUpperCase() + r.slice(1) : "All risk levels"}
            </option>
          ))}
        </select>
      </div>

      <div style={{ padding: "0 32px 24px" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", marginTop: 8 }}>
          <thead>
            <tr>
              {["Name", "GSTIN", "State", "Total Wins", "Total Value", "Win Rate", "Risk Level"].map((h) => (
                <th key={h} style={{ padding: "10px 12px", textAlign: "left", fontSize: 10, fontWeight: 600, color: "var(--text-muted)", letterSpacing: "0.06em", textTransform: "uppercase", borderBottom: "1px solid var(--border-subtle)" }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <motion.tbody
            variants={reduced ? undefined : containerVariants}
            initial={reduced ? undefined : "hidden"}
            animate={reduced ? undefined : "visible"}
          >
            {loading
              ? Array.from({ length: 8 }).map((_, i) => <TableRowSkeleton key={i} cols={7} />)
              : vendors.map((v) => (
                  <motion.tr
                    key={v.id}
                    variants={reduced ? undefined : tableRowVariants}
                    onClick={() => router.push(`/vendors/${v.id}`)}
                    style={{ borderBottom: "1px solid var(--border-subtle)", height: 44, cursor: "pointer", transition: "background 150ms" }}
                    onMouseEnter={(e) => ((e.currentTarget as HTMLTableRowElement).style.background = "var(--bg-elevated)")}
                    onMouseLeave={(e) => ((e.currentTarget as HTMLTableRowElement).style.background = "transparent")}
                  >
                    <td style={{ padding: "0 12px" }}>
                      <span style={{ fontSize: 13, color: "var(--text-primary)", fontWeight: 500 }}>{v.name}</span>
                    </td>
                    <td style={{ padding: "0 12px" }}>
                      <span className="mono" style={{ fontSize: 10, color: "var(--text-muted)" }}>{v.gstin ?? "—"}</span>
                    </td>
                    <td style={{ padding: "0 12px" }}>
                      <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>{v.state ?? "—"}</span>
                    </td>
                    <td style={{ padding: "0 12px" }}>
                      <span className="mono" style={{ fontSize: 13, color: "var(--text-primary)" }}>{v.total_wins}</span>
                    </td>
                    <td style={{ padding: "0 12px" }}>
                      <span className="mono" style={{ fontSize: 12, color: "var(--text-primary)" }}>{formatRupees(v.total_value)}</span>
                    </td>
                    <td style={{ padding: "0 12px" }}>
                      <span className="mono" style={{ fontSize: 12, color: v.win_rate > 100 ? "var(--accent-red)" : "var(--text-muted)" }}>
                        {v.win_rate > 100 ? "100%+ (monopoly)" : `${v.win_rate.toFixed(1)}%`}
                      </span>
                    </td>
                    <td style={{ padding: "0 12px" }}>
                      <RiskLevelBadge level={v.risk_level} />
                    </td>
                  </motion.tr>
                ))}
          </motion.tbody>
        </table>

        {!loading && totalPages > 1 && (
          <div style={{ display: "flex", justifyContent: "center", gap: 4, padding: "16px 0", alignItems: "center" }}>
            <PageButton onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1} label="← Prev" />
            <span className="mono" style={{ fontSize: 11, color: "var(--text-muted)", padding: "0 8px" }}>{page} / {totalPages}</span>
            <PageButton onClick={() => setPage(Math.min(totalPages, page + 1))} disabled={page === totalPages} label="Next →" />
          </div>
        )}
      </div>
    </motion.div>
  );
}

function RiskLevelBadge({ level }: { level: string }) {
  const color = riskLevelColor(level);
  return (
    <span className="mono" style={{ fontSize: 9, fontWeight: 600, letterSpacing: "0.06em", padding: "2px 7px", border: `1px solid ${color}`, borderRadius: 2, color, textTransform: "uppercase" }}>
      {level}
    </span>
  );
}

function PageButton({ onClick, disabled, label }: { onClick: () => void; disabled: boolean; label: string }) {
  return (
    <button onClick={onClick} disabled={disabled} style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", color: disabled ? "var(--text-muted)" : "var(--text-primary)", borderRadius: 2, padding: "5px 12px", fontSize: 12, cursor: disabled ? "default" : "pointer" }}>
      {label}
    </button>
  );
}
