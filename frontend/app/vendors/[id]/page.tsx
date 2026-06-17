"use client";

import { useEffect, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { useParams, useRouter } from "next/navigation";
import { getVendor, getVendorNetwork, formatRupees, riskLevelColor } from "@/lib/api";
import type { VendorProfile, VendorNetwork } from "@/lib/api";
import { pageVariants, cardVariants, containerVariants } from "@/lib/motion";
import { RiskRing } from "@/components/ui/RiskRing";
import { RiskBadge } from "@/components/ui/RiskBadge";
import D3ForceGraph from "@/components/ui/D3ForceGraph";
import { TopBar } from "@/components/layout/TopBar";
import { Skeleton } from "@/components/ui/Skeleton";
import { ArrowLeft, Building2, Shield, Share2 } from "lucide-react";

export default function VendorProfilePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [vendor, setVendor] = useState<VendorProfile | null>(null);
  const [network, setNetwork] = useState<VendorNetwork | null>(null);
  const [networkLoading, setNetworkLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const reduced = useReducedMotion();

  useEffect(() => {
    getVendor(id)
      .then(setVendor)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    if (!id) return;
    setNetworkLoading(true);
    getVendorNetwork(id)
      .then(setNetwork)
      .catch(console.error)
      .finally(() => setNetworkLoading(false));
  }, [id]);

  const motionProps = reduced ? {} : { initial: "hidden", animate: "visible", variants: pageVariants };

  return (
    <motion.div {...motionProps}>
      <TopBar title={loading ? "Vendor Profile" : (vendor?.name ?? "Vendor Profile")} subtitle="Contract history and risk profile" />

      <div style={{ padding: "24px 32px", display: "flex", flexDirection: "column", gap: 20 }}>
        <button
          onClick={() => router.push("/vendors")}
          style={{ display: "flex", alignItems: "center", gap: 6, background: "none", border: "none", color: "var(--text-muted)", fontSize: 12, cursor: "pointer", padding: 0, width: "fit-content" }}
        >
          <ArrowLeft size={14} strokeWidth={1.5} /> Back to vendors
        </button>

        {/* Profile card */}
        <motion.div
          variants={reduced ? undefined : cardVariants}
          style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 4, padding: "20px 24px", display: "grid", gridTemplateColumns: "1fr auto", gap: 24 }}
        >
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {loading ? (
              <>
                <Skeleton width={240} height={20} />
                <Skeleton width={160} height={12} />
                <Skeleton width={200} height={12} />
              </>
            ) : vendor ? (
              <>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <Building2 size={18} strokeWidth={1.5} color="var(--text-muted)" />
                  <span style={{ fontSize: 18, fontWeight: 600, color: "var(--text-primary)" }}>{vendor.name}</span>
                </div>
                <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
                  <Info label="GSTIN" value={vendor.gstin ?? "Not registered"} mono />
                  <Info label="State" value={vendor.state ?? "Unknown"} />
                  <Info label="Incorporated" value={vendor.incorporation_date ?? "Unknown"} />
                  <Info label="MCA Verified" value={vendor.mca_verified ? "Yes" : "No"} color={vendor.mca_verified ? "var(--accent-green)" : "var(--text-muted)"} />
                </div>
                <div style={{ display: "flex", gap: 24, flexWrap: "wrap", marginTop: 4 }}>
                  <Info label="Total Wins" value={String(vendor.total_wins)} mono />
                  <Info label="Total Value" value={formatRupees(vendor.total_value)} mono />
                  <Info
                    label="Win Rate"
                    value={vendor.win_rate > 100 ? "100%+ (monopoly)" : `${vendor.win_rate.toFixed(1)}%`}
                    mono
                    color={vendor.win_rate > 100 ? "var(--accent-red)" : undefined}
                  />
                </div>
              </>
            ) : (
              <span style={{ color: "var(--text-muted)" }}>Vendor not found</span>
            )}
          </div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
            {vendor && (
              <>
                <span className="mono" style={{ fontSize: 9, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>Risk Level</span>
                <span className="mono" style={{ fontSize: 16, fontWeight: 700, color: riskLevelColor(vendor.risk_level), textTransform: "uppercase" }}>
                  {vendor.risk_level}
                </span>
                <Shield size={24} strokeWidth={1.5} color={riskLevelColor(vendor.risk_level)} />
              </>
            )}
          </div>
        </motion.div>

        {/* Director network */}
        <motion.div
          variants={reduced ? undefined : cardVariants}
          style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 4, padding: "16px 20px" }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
            <Share2 size={14} strokeWidth={1.5} color="var(--text-muted)" />
            <span style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
              Director Network
            </span>
          </div>
          {networkLoading ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 8, padding: "8px 0" }}>
              <Skeleton width="100%" height={300} />
            </div>
          ) : network && network.nodes.length > 0 ? (
            <>
              <D3ForceGraph data={network} height={340} />
              <div style={{ display: "flex", gap: 20, marginTop: 12, flexWrap: "wrap" }}>
                <Legend color="var(--accent-green)" label="Vendor (low)" />
                <Legend color="var(--accent-amber)" label="Vendor (medium/high)" />
                <Legend color="var(--accent-red)" label="Vendor (critical)" />
                <Legend color="var(--accent-blue)" label="Director" />
              </div>
            </>
          ) : (
            <div style={{ padding: "32px 0", textAlign: "center" }}>
              <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Network data unavailable</span>
            </div>
          )}
        </motion.div>

        {/* Contract history */}
        <motion.div
          variants={reduced ? undefined : cardVariants}
          style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 4, overflow: "hidden" }}
        >
          <div style={{ padding: "14px 20px", borderBottom: "1px solid var(--border-subtle)" }}>
            <span style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
              Recent Contracts (last 10)
            </span>
          </div>
          <motion.div variants={reduced ? undefined : containerVariants} initial={reduced ? undefined : "hidden"} animate={reduced ? undefined : "visible"}>
            {loading
              ? Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} style={{ padding: "14px 20px", borderBottom: "1px solid var(--border-subtle)", display: "flex", gap: 12, alignItems: "center" }}>
                    <Skeleton width="60%" height={13} />
                    <Skeleton width={80} height={13} />
                    <Skeleton width={40} height={13} />
                  </div>
                ))
              : vendor?.recent_contracts.length === 0
              ? (
                <div style={{ padding: "32px 20px", textAlign: "center", color: "var(--text-muted)", fontSize: 13 }}>No contracts found</div>
              )
              : vendor?.recent_contracts.map((c) => (
                  <motion.div
                    key={c.tender_id}
                    variants={reduced ? undefined : cardVariants}
                    style={{ padding: "14px 20px", borderBottom: "1px solid var(--border-subtle)", display: "grid", gridTemplateColumns: "1fr auto auto auto auto", gap: 16, alignItems: "center", transition: "background 150ms" }}
                    onMouseEnter={(e) => ((e.currentTarget as HTMLDivElement).style.background = "var(--bg-elevated)")}
                    onMouseLeave={(e) => ((e.currentTarget as HTMLDivElement).style.background = "transparent")}
                  >
                    <span style={{ fontSize: 12, color: "var(--text-secondary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={c.title}>{c.title}</span>
                    <span className="mono" style={{ fontSize: 11, color: "var(--text-muted)" }}>{c.date}</span>
                    <span className="mono" style={{ fontSize: 12, color: "var(--text-primary)" }}>{formatRupees(c.value)}</span>
                    <RiskRing score={c.risk_score} size={32} />
                    <div style={{ display: "flex", gap: 4 }}>
                      {c.anomaly_flags.map((f) => <RiskBadge key={f} flag={f} />)}
                    </div>
                  </motion.div>
                ))}
          </motion.div>
        </motion.div>
      </div>
    </motion.div>
  );
}

function Info({ label, value, mono, color }: { label: string; value: string; mono?: boolean; color?: string }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <span style={{ fontSize: 10, color: "var(--text-muted)", letterSpacing: "0.06em", textTransform: "uppercase" }}>{label}</span>
      <span className={mono ? "mono" : ""} style={{ fontSize: 13, color: color ?? "var(--text-secondary)" }}>{value}</span>
    </div>
  );
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <div style={{ width: 10, height: 10, borderRadius: "50%", border: `2px solid ${color}`, background: color + "26" }} />
      <span style={{ fontSize: 10, color: "var(--text-muted)" }}>{label}</span>
    </div>
  );
}
