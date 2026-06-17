"use client";

import type { FormEvent } from "react";
import { useEffect, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { getAlerts, subscribeAlert, patchAlert, deleteAlert } from "@/lib/api";
import type { AlertSummary } from "@/lib/api";
import { pageVariants, containerVariants, cardVariants } from "@/lib/motion";
import { TopBar } from "@/components/layout/TopBar";
import { Skeleton } from "@/components/ui/Skeleton";
import { Bell, BellOff, Plus, X, Trash2 } from "lucide-react";

function timeAgo(iso: string | null): string {
  if (!iso) return "Never";
  const diffMs = Date.now() - new Date(iso).getTime();
  const diffH = Math.floor(diffMs / 36e5);
  if (diffH < 1) return "Less than 1 hour ago";
  if (diffH < 24) return `${diffH}h ago`;
  const diffD = Math.floor(diffH / 24);
  return `${diffD}d ago`;
}

const MINISTRY_OPTIONS = [
  "Ministry of Defence", "Ministry of Railways", "Ministry of Health and Family Welfare",
  "Ministry of Road Transport and Highways", "Ministry of Education", "Ministry of Finance",
  "Ministry of Electronics and Information Technology", "Ministry of Jal Shakti",
  "Ministry of Power", "Ministry of Agriculture and Farmers Welfare",
  "Ministry of Home Affairs", "Ministry of Coal",
];

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const reduced = useReducedMotion();

  // Form state
  const [selectedMinistries, setSelectedMinistries] = useState<string[]>([]);
  const [keywordInput, setKeywordInput] = useState("");
  const [keywords, setKeywords] = useState<string[]>([]);
  const [email, setEmail] = useState("");
  const [formError, setFormError] = useState("");

  async function loadAlerts() {
    try {
      const data = await getAlerts();
      setAlerts(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadAlerts(); }, []);

  function toggleMinistry(m: string) {
    setSelectedMinistries((prev) => prev.includes(m) ? prev.filter((x) => x !== m) : [...prev, m]);
  }

  function addKeyword() {
    const kw = keywordInput.trim();
    if (kw && !keywords.includes(kw)) {
      setKeywords((prev) => [...prev, kw]);
    }
    setKeywordInput("");
  }

  function removeKeyword(kw: string) {
    setKeywords((prev) => prev.filter((k) => k !== kw));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setFormError("");
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setFormError("Please enter a valid email address.");
      return;
    }
    if (selectedMinistries.length === 0 && keywords.length === 0) {
      setFormError("Select at least one ministry or keyword.");
      return;
    }
    setSubmitting(true);
    try {
      await subscribeAlert({ ministries: selectedMinistries, keywords, email });
      setSuccess(true);
      setSelectedMinistries([]);
      setKeywords([]);
      setEmail("");
      setTimeout(() => setSuccess(false), 3000);
      await loadAlerts();
    } catch (e) {
      setFormError("Failed to create alert. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  async function toggleAlertStatus(id: string, current: string) {
    const next = current === "active" ? "paused" : "active";
    try {
      const updated = await patchAlert(id, next);
      setAlerts((prev) => prev.map((a) => a.id === id ? updated : a));
    } catch (e) {
      console.error(e);
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteAlert(id);
      setAlerts((prev) => prev.filter((a) => a.id !== id));
      setDeleteConfirm(null);
    } catch (e) {
      console.error(e);
    }
  }

  const motionProps = reduced ? {} : { initial: "hidden", animate: "visible", variants: pageVariants };

  return (
    <motion.div {...motionProps}>
      <TopBar title="Alert Subscriptions" subtitle="Get notified when procurement anomalies match your criteria" />

      <div style={{ padding: "24px 32px", display: "grid", gridTemplateColumns: "1fr 360px", gap: 24, alignItems: "start" }}>
        {/* Active alerts list */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 4 }}>
            Active Subscriptions ({alerts.length})
          </div>
          <motion.div
            variants={reduced ? undefined : containerVariants}
            initial={reduced ? undefined : "hidden"}
            animate={reduced ? undefined : "visible"}
            style={{ display: "flex", flexDirection: "column", gap: 8 }}
          >
            {loading ? (
              Array.from({ length: 3 }).map((_, i) => (
                <div key={i} style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 4, padding: "16px 20px", display: "flex", flexDirection: "column", gap: 8 }}>
                  <Skeleton width={200} height={12} /><Skeleton width={160} height={10} /><Skeleton width={120} height={10} />
                </div>
              ))
            ) : alerts.length === 0 ? (
              <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 4, padding: "48px 0", textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>
                <Bell size={28} strokeWidth={1} color="var(--text-muted)" />
                <span style={{ fontSize: 13, color: "var(--text-muted)" }}>No alerts configured</span>
                <span style={{ fontSize: 12, color: "var(--text-muted)", opacity: 0.6 }}>Use the form to subscribe to anomaly alerts</span>
              </div>
            ) : alerts.map((a) => (
              <motion.div
                key={a.id}
                variants={reduced ? undefined : cardVariants}
                style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderLeft: `3px solid ${a.status === "active" ? "var(--accent-green)" : "var(--border-active)"}`, borderRadius: 4, padding: "14px 18px" }}
              >
                <div style={{ display: "grid", gridTemplateColumns: "1fr auto", alignItems: "flex-start", gap: 12 }}>
                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span style={{ fontSize: 12, color: "var(--text-primary)", fontWeight: 500 }}>{a.email}</span>
                      {a.trigger_count > 0 && (
                        <span className="mono" style={{ fontSize: 9, padding: "1px 5px", background: "var(--accent-red)", color: "#fff", borderRadius: 2 }}>
                          {a.trigger_count} fired
                        </span>
                      )}
                    </div>
                    {a.ministries.length > 0 && (
                      <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                        {a.ministries.map((m) => (
                          <span key={m} className="mono" style={{ fontSize: 9, padding: "1px 5px", border: "1px solid var(--border-active)", borderRadius: 2, color: "var(--text-muted)" }}>
                            {m.replace("Ministry of ", "Min. ")}
                          </span>
                        ))}
                      </div>
                    )}
                    {a.keywords.length > 0 && (
                      <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                        {a.keywords.map((k) => (
                          <span key={k} className="mono" style={{ fontSize: 9, padding: "1px 5px", border: "1px solid var(--accent-blue)", borderRadius: 2, color: "var(--accent-blue)" }}>
                            #{k}
                          </span>
                        ))}
                      </div>
                    )}
                    <span className="mono" style={{ fontSize: 10, color: "var(--text-muted)" }}>
                      Last triggered: {timeAgo(a.last_triggered)} &middot; Created {new Date(a.created_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })}
                    </span>
                  </div>
                  <div style={{ display: "flex", gap: 6 }}>
                    <button
                      onClick={() => toggleAlertStatus(a.id, a.status)}
                      title={a.status === "active" ? "Pause alert" : "Resume alert"}
                      style={{ background: "none", border: "1px solid var(--border-subtle)", borderRadius: 2, color: a.status === "active" ? "var(--accent-green)" : "var(--text-muted)", padding: "6px 8px", cursor: "pointer", display: "flex", alignItems: "center", gap: 5, fontSize: 11, transition: "all 150ms" }}
                      onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "var(--bg-elevated)")}
                      onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "none")}
                    >
                      {a.status === "active" ? <BellOff size={13} strokeWidth={1.5} /> : <Bell size={13} strokeWidth={1.5} />}
                      {a.status === "active" ? "Pause" : "Resume"}
                    </button>
                    {deleteConfirm === a.id ? (
                      <div style={{ display: "flex", gap: 4 }}>
                        <button
                          onClick={() => handleDelete(a.id)}
                          style={{ background: "var(--accent-red)", border: "none", borderRadius: 2, color: "#fff", padding: "6px 8px", cursor: "pointer", fontSize: 10, fontWeight: 700 }}
                        >
                          Confirm
                        </button>
                        <button
                          onClick={() => setDeleteConfirm(null)}
                          style={{ background: "none", border: "1px solid var(--border-subtle)", borderRadius: 2, color: "var(--text-muted)", padding: "6px 8px", cursor: "pointer", fontSize: 10 }}
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => setDeleteConfirm(a.id)}
                        title="Delete alert"
                        style={{ background: "none", border: "1px solid var(--border-subtle)", borderRadius: 2, color: "var(--text-muted)", padding: "6px 8px", cursor: "pointer", display: "flex", alignItems: "center", transition: "all 150ms" }}
                        onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.color = "var(--accent-red)"; (e.currentTarget as HTMLButtonElement).style.background = "var(--bg-elevated)"; }}
                        onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.color = "var(--text-muted)"; (e.currentTarget as HTMLButtonElement).style.background = "none"; }}
                      >
                        <Trash2 size={13} strokeWidth={1.5} />
                      </button>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>

        {/* Subscribe form */}
        <motion.div
          variants={reduced ? undefined : cardVariants}
          style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 4, padding: "20px", position: "sticky", top: 20, display: "flex", flexDirection: "column", gap: 16 }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Plus size={14} strokeWidth={2} color="var(--accent-red)" />
            <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>New Alert</span>
          </div>

          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {/* Ministry multiselect */}
            <div>
              <label style={{ fontSize: 10, color: "var(--text-muted)", letterSpacing: "0.06em", textTransform: "uppercase", display: "block", marginBottom: 6 }}>Ministries</label>
              <div style={{ maxHeight: 180, overflowY: "auto", display: "flex", flexDirection: "column", gap: 4, border: "1px solid var(--border-subtle)", borderRadius: 2, padding: "6px" }}>
                {MINISTRY_OPTIONS.map((m) => (
                  <label key={m} style={{ display: "flex", alignItems: "center", gap: 8, padding: "4px 6px", borderRadius: 2, cursor: "pointer", background: selectedMinistries.includes(m) ? "var(--bg-elevated)" : "transparent", transition: "background 150ms" }}>
                    <input type="checkbox" checked={selectedMinistries.includes(m)} onChange={() => toggleMinistry(m)} style={{ accentColor: "var(--accent-red)" }} />
                    <span style={{ fontSize: 11, color: "var(--text-secondary)" }}>{m.replace("Ministry of ", "Min. of ")}</span>
                  </label>
                ))}
              </div>
              {selectedMinistries.length > 0 && (
                <span style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 4, display: "block" }}>{selectedMinistries.length} selected</span>
              )}
            </div>

            {/* Keywords */}
            <div>
              <label style={{ fontSize: 10, color: "var(--text-muted)", letterSpacing: "0.06em", textTransform: "uppercase", display: "block", marginBottom: 6 }}>Keywords</label>
              <div style={{ display: "flex", gap: 6 }}>
                <input
                  value={keywordInput}
                  onChange={(e) => setKeywordInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addKeyword())}
                  placeholder="ventilator, CCTV…"
                  style={{ flex: 1, background: "var(--bg-elevated)", border: "1px solid var(--border-subtle)", borderRadius: 2, color: "var(--text-primary)", fontSize: 12, padding: "6px 8px", outline: "none" }}
                />
                <button type="button" onClick={addKeyword} style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-subtle)", borderRadius: 2, color: "var(--text-muted)", padding: "6px 10px", cursor: "pointer", fontSize: 13 }}>+</button>
              </div>
              {keywords.length > 0 && (
                <div style={{ display: "flex", gap: 4, flexWrap: "wrap", marginTop: 6 }}>
                  {keywords.map((k) => (
                    <span key={k} style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 10, padding: "2px 6px", border: "1px solid var(--accent-blue)", borderRadius: 2, color: "var(--accent-blue)" }}>
                      #{k}
                      <X size={9} strokeWidth={2} onClick={() => removeKeyword(k)} style={{ cursor: "pointer" }} />
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Email */}
            <div>
              <label style={{ fontSize: 10, color: "var(--text-muted)", letterSpacing: "0.06em", textTransform: "uppercase", display: "block", marginBottom: 6 }}>Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="investigator@example.gov.in"
                style={{ width: "100%", background: "var(--bg-elevated)", border: "1px solid var(--border-subtle)", borderRadius: 2, color: "var(--text-primary)", fontSize: 12, padding: "7px 10px", outline: "none", boxSizing: "border-box" }}
              />
            </div>

            {formError && <span style={{ fontSize: 11, color: "var(--accent-red)" }}>{formError}</span>}
            {success && <span style={{ fontSize: 11, color: "var(--accent-green)" }}>Alert created successfully.</span>}

            <button
              type="submit"
              disabled={submitting}
              style={{ background: submitting ? "var(--border-subtle)" : "var(--accent-red)", border: "none", borderRadius: 2, color: "var(--text-primary)", fontSize: 13, fontWeight: 600, padding: "9px 0", cursor: submitting ? "default" : "pointer", width: "100%" }}
            >
              {submitting ? "Subscribing…" : "Subscribe to Alerts"}
            </button>
          </form>
        </motion.div>
      </div>
    </motion.div>
  );
}
