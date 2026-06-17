"use client";

import { useEffect, useState, useCallback } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { getTenders, formatRupees } from "@/lib/api";
import type { Tender, TenderFilters } from "@/lib/api";
import { pageVariants, containerVariants, tableRowVariants } from "@/lib/motion";
import { RiskRing } from "@/components/ui/RiskRing";
import { RiskBadge } from "@/components/ui/RiskBadge";
import { TopBar } from "@/components/layout/TopBar";
import { TableRowSkeleton } from "@/components/ui/Skeleton";

const PAGE_SIZE = 25;

export default function TendersPage() {
  const [tenders, setTenders] = useState<Tender[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const reduced = useReducedMotion();

  const [filters, setFilters] = useState<TenderFilters>({
    page: 1,
    limit: PAGE_SIZE,
  });

  const load = useCallback(async (f: TenderFilters) => {
    setLoading(true);
    try {
      const data = await getTenders(f);
      setTenders(data.tenders);
      setTotal(data.total);
    } catch (err) {
      console.error("Failed to load tenders:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load(filters);
  }, [filters, load]);

  function applyFilter(key: keyof TenderFilters, value: string | number | undefined) {
    setFilters((prev) => ({ ...prev, [key]: value, page: 1 }));
    setPage(1);
  }

  function goPage(p: number) {
    setPage(p);
    setFilters((prev) => ({ ...prev, page: p }));
  }

  const totalPages = Math.ceil(total / PAGE_SIZE);

  const motionProps = reduced
    ? {}
    : { initial: "hidden", animate: "visible", variants: pageVariants };

  return (
    <motion.div {...motionProps}>
      <TopBar
        title="Tender Registry"
        subtitle={`${total.toLocaleString("en-IN")} tenders indexed`}
      />

      {/* Filters */}
      <div
        style={{
          padding: "14px 32px",
          borderBottom: "1px solid var(--border-subtle)",
          display: "flex",
          gap: 10,
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        {(
          [
            { key: "ministry", placeholder: "Filter ministry…" },
            { key: "state", placeholder: "Filter state…" },
            { key: "anomaly_type", placeholder: "Anomaly type…" },
          ] as const
        ).map(({ key, placeholder }) => (
          <input
            key={key}
            placeholder={placeholder}
            onChange={(e) => applyFilter(key, e.target.value || undefined)}
            style={{
              background: "var(--bg-surface)",
              border: "1px solid var(--border-subtle)",
              borderRadius: 2,
              color: "var(--text-primary)",
              fontSize: 12,
              padding: "6px 10px",
              outline: "none",
              width: 180,
            }}
            onFocus={(e) =>
              ((e.target as HTMLInputElement).style.borderColor = "var(--border-active)")
            }
            onBlur={(e) =>
              ((e.target as HTMLInputElement).style.borderColor = "var(--border-subtle)")
            }
          />
        ))}

        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Risk</span>
          <input
            type="number"
            placeholder="Min"
            min={0}
            max={100}
            onChange={(e) => applyFilter("risk_min", e.target.value ? Number(e.target.value) : undefined)}
            style={{
              background: "var(--bg-surface)",
              border: "1px solid var(--border-subtle)",
              borderRadius: 2,
              color: "var(--text-primary)",
              fontSize: 12,
              padding: "6px 8px",
              outline: "none",
              width: 60,
            }}
          />
          <span style={{ color: "var(--text-muted)", fontSize: 11 }}>–</span>
          <input
            type="number"
            placeholder="Max"
            min={0}
            max={100}
            onChange={(e) => applyFilter("risk_max", e.target.value ? Number(e.target.value) : undefined)}
            style={{
              background: "var(--bg-surface)",
              border: "1px solid var(--border-subtle)",
              borderRadius: 2,
              color: "var(--text-primary)",
              fontSize: 12,
              padding: "6px 8px",
              outline: "none",
              width: 60,
            }}
          />
        </div>
      </div>

      {/* Table */}
      <div style={{ padding: "0 32px 24px" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", marginTop: 8 }}>
          <thead>
            <tr>
              {["ID", "Ministry", "State", "Value (₹)", "Bids", "Risk", "Flags", "Date"].map(
                (h) => (
                  <th
                    key={h}
                    style={{
                      padding: "10px 12px",
                      textAlign: "left",
                      fontSize: 10,
                      fontWeight: 600,
                      color: "var(--text-muted)",
                      letterSpacing: "0.06em",
                      textTransform: "uppercase",
                      borderBottom: "1px solid var(--border-subtle)",
                    }}
                  >
                    {h}
                  </th>
                )
              )}
            </tr>
          </thead>
          <motion.tbody
            variants={reduced ? undefined : containerVariants}
            initial={reduced ? undefined : "hidden"}
            animate={reduced ? undefined : "visible"}
          >
            {loading
              ? Array.from({ length: 8 }).map((_, i) => (
                  <TableRowSkeleton key={i} cols={8} />
                ))
              : tenders.map((t) => (
                  <motion.tr
                    key={t.id}
                    variants={reduced ? undefined : tableRowVariants}
                    style={{
                      borderBottom: "1px solid var(--border-subtle)",
                      height: 44,
                      cursor: "default",
                      transition: "background 150ms",
                    }}
                    onMouseEnter={(e) =>
                      ((e.currentTarget as HTMLTableRowElement).style.background =
                        "var(--bg-elevated)")
                    }
                    onMouseLeave={(e) =>
                      ((e.currentTarget as HTMLTableRowElement).style.background = "transparent")
                    }
                  >
                    <td style={{ padding: "0 12px" }}>
                      <span
                        className="mono"
                        style={{
                          fontSize: 10,
                          color: "var(--text-muted)",
                          display: "block",
                          maxWidth: 120,
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                        title={t.gem_id}
                      >
                        {t.gem_id}
                      </span>
                    </td>
                    <td style={{ padding: "0 12px", maxWidth: 160 }}>
                      <span
                        style={{
                          fontSize: 12,
                          color: "var(--text-secondary)",
                          display: "block",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                        title={t.ministry}
                      >
                        {t.ministry.replace("Ministry of ", "Min. ")}
                      </span>
                    </td>
                    <td style={{ padding: "0 12px" }}>
                      <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>
                        {t.state}
                      </span>
                    </td>
                    <td style={{ padding: "0 12px" }}>
                      <span
                        className="mono"
                        style={{ fontSize: 12, color: "var(--text-primary)", whiteSpace: "nowrap" }}
                      >
                        {formatRupees(t.value)}
                      </span>
                    </td>
                    <td style={{ padding: "0 12px" }}>
                      <span
                        className="mono"
                        style={{
                          fontSize: 12,
                          color:
                            t.bid_count === 1
                              ? "var(--accent-red)"
                              : "var(--text-muted)",
                        }}
                      >
                        {t.bid_count}
                      </span>
                    </td>
                    <td style={{ padding: "0 12px" }}>
                      <RiskRing score={t.risk_score} size={32} />
                    </td>
                    <td style={{ padding: "0 12px" }}>
                      <div style={{ display: "flex", gap: 3, flexWrap: "wrap" }}>
                        {(t.anomaly_flags ?? []).map((f) => (
                          <RiskBadge key={f} flag={f} />
                        ))}
                      </div>
                    </td>
                    <td style={{ padding: "0 12px" }}>
                      <span
                        className="mono"
                        style={{ fontSize: 10, color: "var(--text-muted)" }}
                      >
                        {t.tender_date}
                      </span>
                    </td>
                  </motion.tr>
                ))}
          </motion.tbody>
        </table>

        {/* Pagination */}
        {!loading && totalPages > 1 && (
          <div
            style={{
              display: "flex",
              justifyContent: "center",
              gap: 4,
              padding: "16px 0",
              alignItems: "center",
            }}
          >
            <button
              onClick={() => goPage(Math.max(1, page - 1))}
              disabled={page === 1}
              style={{
                background: "var(--bg-surface)",
                border: "1px solid var(--border-subtle)",
                color: page === 1 ? "var(--text-muted)" : "var(--text-primary)",
                borderRadius: 2,
                padding: "5px 12px",
                fontSize: 12,
                cursor: page === 1 ? "default" : "pointer",
              }}
            >
              ← Prev
            </button>
            <span
              className="mono"
              style={{ fontSize: 11, color: "var(--text-muted)", padding: "0 8px" }}
            >
              {page} / {totalPages}
            </span>
            <button
              onClick={() => goPage(Math.min(totalPages, page + 1))}
              disabled={page === totalPages}
              style={{
                background: "var(--bg-surface)",
                border: "1px solid var(--border-subtle)",
                color: page === totalPages ? "var(--text-muted)" : "var(--text-primary)",
                borderRadius: 2,
                padding: "5px 12px",
                fontSize: 12,
                cursor: page === totalPages ? "default" : "pointer",
              }}
            >
              Next →
            </button>
          </div>
        )}
      </div>
    </motion.div>
  );
}
