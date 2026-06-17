"use client";

import { useEffect, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { getDashboardStats, getTenders, runDetection, formatRupees } from "@/lib/api";
import type { DashboardStats, Tender } from "@/lib/api";
import { pageVariants, containerVariants, cardVariants } from "@/lib/motion";
import { StatCard } from "@/components/ui/StatCard";
import { RiskRing } from "@/components/ui/RiskRing";
import { RiskBadge } from "@/components/ui/RiskBadge";
import { TopBar } from "@/components/layout/TopBar";
import { StatCardSkeleton, TableRowSkeleton } from "@/components/ui/Skeleton";
import { Play } from "lucide-react";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [tenders, setTenders] = useState<Tender[]>([]);
  const [loading, setLoading] = useState(true);
  const [detectRunning, setDetectRunning] = useState(false);
  const [detectMsg, setDetectMsg] = useState("");
  const reduced = useReducedMotion();

  const handleRunDetection = async () => {
    setDetectRunning(true);
    try {
      const res = await runDetection();
      setDetectMsg(`Pipeline queued: ${res.task_id.slice(0, 8)}`);
    } catch {
      setDetectMsg("Failed to start");
    } finally {
      setDetectRunning(false);
      setTimeout(() => setDetectMsg(""), 5000);
    }
  };

  useEffect(() => {
    async function load() {
      try {
        const [statsData, tendersData] = await Promise.all([
          getDashboardStats(),
          getTenders({ risk_min: 30, limit: 10 }),
        ]);
        setStats(statsData);
        setTenders(tendersData.tenders);
      } catch (err) {
        console.error("Failed to load dashboard:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const motionProps = reduced
    ? {}
    : { initial: "hidden", animate: "visible", variants: pageVariants };

  return (
    <motion.div {...motionProps}>
      <TopBar
        title="Intelligence Dashboard"
        subtitle="Real-time procurement anomaly monitoring"
        action={
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            {detectMsg && <span className="mono" style={{ fontSize: 11, color: "var(--accent-green)" }}>{detectMsg}</span>}
            <button
              onClick={handleRunDetection}
              disabled={detectRunning}
              style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, background: detectRunning ? "var(--bg-surface)" : "var(--accent-red)", border: `1px solid var(--accent-red)`, borderRadius: 2, color: detectRunning ? "var(--accent-red)" : "var(--bg-base)", padding: "6px 12px", cursor: detectRunning ? "default" : "pointer", fontFamily: "JetBrains Mono, monospace", letterSpacing: "0.04em" }}
            >
              <Play size={11} strokeWidth={2} /> {detectRunning ? "Running…" : "Run Detection"}
            </button>
          </div>
        }
      />

      <div style={{ padding: "24px 32px", display: "flex", flexDirection: "column", gap: 24 }}>
        {/* Stat Cards Row */}
        <motion.div
          style={{ display: "flex", gap: 16 }}
          variants={reduced ? undefined : containerVariants}
          initial={reduced ? undefined : "hidden"}
          animate={reduced ? undefined : "visible"}
        >
          {loading ? (
            <>
              <StatCardSkeleton />
              <StatCardSkeleton />
              <StatCardSkeleton />
              <StatCardSkeleton />
            </>
          ) : stats ? (
            <>
              <StatCard
                label="Flagged This Month"
                value={stats.flagged_this_month}
                color="red"
                unit="tenders"
              />
              <StatCard
                label="Suspicious Value"
                value={Math.round(stats.suspicious_value / 100)}
                color="amber"
                formatter={(v) =>
                  v >= 1_00_00_000
                    ? `₹${Math.round(v / 1_00_00_000).toLocaleString("en-IN")}Cr`
                    : v >= 1_00_000
                    ? `₹${(v / 1_00_000).toFixed(1)}L`
                    : `₹${Math.round(v).toLocaleString("en-IN")}`
                }
              />
              <StatCard
                label="New Anomalies Today"
                value={stats.new_anomalies_today}
                color="red"
              />
              <StatCard
                label="Total Scanned"
                value={stats.total_tenders_scanned}
                color="blue"
                unit="tenders"
              />
            </>
          ) : null}
        </motion.div>

        {/* Two-column: ministry breakdown + anomaly types */}
        {stats && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <motion.div
              variants={reduced ? undefined : cardVariants}
              style={{
                background: "var(--bg-surface)",
                border: "1px solid var(--border-subtle)",
                borderRadius: 4,
                padding: "16px 20px",
              }}
            >
              <div
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                  color: "var(--text-muted)",
                  letterSpacing: "0.08em",
                  textTransform: "uppercase",
                  marginBottom: 14,
                }}
              >
                Top Risky Ministries
              </div>
              {stats.top_risky_ministries.map((m, i) => (
                <div
                  key={m.ministry}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "7px 0",
                    borderBottom: i < stats.top_risky_ministries.length - 1
                      ? "1px solid var(--border-subtle)"
                      : "none",
                  }}
                >
                  <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>
                    {m.ministry.replace("Ministry of ", "Min. of ")}
                  </span>
                  <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                    <span className="mono" style={{ fontSize: 11, color: "var(--text-muted)" }}>
                      {formatRupees(m.total_value)}
                    </span>
                    <span
                      className="mono"
                      style={{
                        fontSize: 11,
                        color: "var(--accent-red)",
                        minWidth: 24,
                        textAlign: "right",
                      }}
                    >
                      {m.count}
                    </span>
                  </div>
                </div>
              ))}
            </motion.div>

            <motion.div
              variants={reduced ? undefined : cardVariants}
              style={{
                background: "var(--bg-surface)",
                border: "1px solid var(--border-subtle)",
                borderRadius: 4,
                padding: "16px 20px",
              }}
            >
              <div
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                  color: "var(--text-muted)",
                  letterSpacing: "0.08em",
                  textTransform: "uppercase",
                  marginBottom: 14,
                }}
              >
                Anomaly Breakdown
              </div>
              {stats.anomaly_breakdown.map((a, i) => {
                const maxCount = stats.anomaly_breakdown[0]?.count ?? 1;
                const pct = (a.count / maxCount) * 100;
                const aColor =
                  a.type === "single_bid"
                    ? "var(--accent-red)"
                    : a.type === "bid_splitting"
                    ? "var(--accent-red)"
                    : "var(--accent-amber)";
                return (
                  <div
                    key={a.type}
                    style={{
                      padding: "7px 0",
                      borderBottom: i < stats.anomaly_breakdown.length - 1
                        ? "1px solid var(--border-subtle)"
                        : "none",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        marginBottom: 4,
                      }}
                    >
                      <span className="mono" style={{ fontSize: 11, color: "var(--text-secondary)" }}>
                        {a.type}
                      </span>
                      <span className="mono" style={{ fontSize: 11, color: aColor }}>
                        {a.count}
                      </span>
                    </div>
                    <div
                      style={{
                        height: 2,
                        background: "var(--border-subtle)",
                        borderRadius: 1,
                        overflow: "hidden",
                      }}
                    >
                      <div
                        style={{
                          height: "100%",
                          width: `${pct}%`,
                          background: aColor,
                          borderRadius: 1,
                          transition: "width 0.6s ease",
                        }}
                      />
                    </div>
                  </div>
                );
              })}

            </motion.div>
          </div>
        )}

        {/* State Risk Table */}
        {stats && stats.state_risk_map.length > 0 && (
          <motion.div
            variants={reduced ? undefined : cardVariants}
            style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 4, overflow: "hidden" }}
          >
            <div style={{ padding: "14px 20px", borderBottom: "1px solid var(--border-subtle)" }}>
              <span style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
                State Risk Heatmap
              </span>
            </div>
            <div style={{ padding: "16px 20px", display: "flex", flexWrap: "wrap", gap: 8 }}>
              {stats.state_risk_map
                .sort((a, b) => b.risk_score - a.risk_score)
                .map((s) => {
                  const intensity = Math.min(s.risk_score / 100, 1);
                  const r = Math.round(232 * intensity);
                  const g = Math.round(48 + (246 * (1 - intensity)));
                  const b2 = Math.round(74 * intensity);
                  const bg = `rgba(${r}, ${g}, ${b2}, ${0.08 + intensity * 0.22})`;
                  const border = `rgba(${r}, ${g}, ${b2}, ${0.3 + intensity * 0.5})`;
                  return (
                    <div
                      key={s.state}
                      title={`${s.state}: avg risk ${s.risk_score}, ${s.flagged_count} flagged`}
                      style={{ padding: "6px 10px", borderRadius: 3, border: `1px solid ${border}`, background: bg, cursor: "default" }}
                    >
                      <div className="mono" style={{ fontSize: 10, color: "var(--text-primary)", fontWeight: intensity > 0.5 ? 700 : 400 }}>
                        {s.state}
                      </div>
                      <div className="mono" style={{ fontSize: 9, color: "var(--text-muted)", marginTop: 2 }}>
                        {s.flagged_count} flagged · {Number(s.risk_score).toFixed(1)}pts
                      </div>
                    </div>
                  );
                })}
            </div>
          </motion.div>
        )}

        {/* Top risky tenders table */}
        <motion.div
          variants={reduced ? undefined : cardVariants}
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border-subtle)",
            borderRadius: 4,
            overflow: "hidden",
          }}
        >
          <div
            style={{
              padding: "14px 20px",
              borderBottom: "1px solid var(--border-subtle)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <span
              style={{
                fontSize: 11,
                fontWeight: 600,
                color: "var(--text-muted)",
                letterSpacing: "0.08em",
                textTransform: "uppercase",
              }}
            >
              Highest Risk Tenders
            </span>
            <a
              href="/tenders"
              style={{
                fontSize: 11,
                color: "var(--accent-blue)",
                textDecoration: "none",
              }}
            >
              View all →
            </a>
          </div>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                {["ID", "Ministry", "State", "Value", "Bids", "Risk", "Flags"].map((h) => (
                  <th
                    key={h}
                    style={{
                      padding: "8px 12px",
                      textAlign: "left",
                      fontSize: 10,
                      fontWeight: 600,
                      color: "var(--text-muted)",
                      letterSpacing: "0.06em",
                      textTransform: "uppercase",
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading
                ? Array.from({ length: 5 }).map((_, i) => (
                    <TableRowSkeleton key={i} cols={7} />
                  ))
                : tenders.map((t) => (
                    <tr
                      key={t.id}
                      style={{
                        borderBottom: "1px solid var(--border-subtle)",
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
                      <td style={{ padding: "10px 12px" }}>
                        <span
                          className="mono"
                          style={{
                            fontSize: 10,
                            color: "var(--text-muted)",
                            display: "block",
                            maxWidth: 100,
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                          }}
                        >
                          {t.gem_id}
                        </span>
                      </td>
                      <td style={{ padding: "10px 12px" }}>
                        <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>
                          {t.ministry.replace("Ministry of ", "Min. of ")}
                        </span>
                      </td>
                      <td style={{ padding: "10px 12px" }}>
                        <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>
                          {t.state}
                        </span>
                      </td>
                      <td style={{ padding: "10px 12px" }}>
                        <span className="mono" style={{ fontSize: 12, color: "var(--text-primary)" }}>
                          {formatRupees(t.value)}
                        </span>
                      </td>
                      <td style={{ padding: "10px 12px" }}>
                        <span className="mono" style={{ fontSize: 12, color: "var(--text-muted)" }}>
                          {t.bid_count}
                        </span>
                      </td>
                      <td style={{ padding: "10px 12px" }}>
                        <RiskRing score={t.risk_score} size={32} />
                      </td>
                      <td style={{ padding: "10px 12px" }}>
                        <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                          {(t.anomaly_flags ?? []).map((f) => (
                            <RiskBadge key={f} flag={f} />
                          ))}
                        </div>
                      </td>
                    </tr>
                  ))}
            </tbody>
          </table>
        </motion.div>
      </div>
    </motion.div>
  );
}
