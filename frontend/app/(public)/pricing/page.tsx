"use client";

import { useState } from "react";
import { useReducedMotion, motion } from "framer-motion";
import { TopBar } from "@/components/layout/TopBar";
import { createCheckoutSession } from "@/lib/api";
import { Check } from "lucide-react";

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.1 } },
};
const cardVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.28, ease: "easeOut" } },
};

const PLANS = [
  {
    id: "free",
    name: "FREE",
    price: "0",
    period: null,
    tagline: "For individual researchers",
    features: [
      "10 AI reports per month",
      "Anomaly detection dashboard",
      "Vendor network analysis",
      "State heatmap",
      "CSV export",
    ],
    cta: "Current Plan",
    featured: false,
    disabled: true,
  },
  {
    id: "pro",
    name: "PRO",
    price: "2,999",
    period: "/ month",
    tagline: "For journalists and activists",
    features: [
      "Unlimited AI reports",
      "PDF export with branding",
      "Priority anomaly alerts via email",
      "RTI question auto-generation",
      "Comparative analysis across ministries",
      "API access",
    ],
    cta: "Upgrade to Pro",
    featured: true,
    disabled: false,
  },
  {
    id: "enterprise",
    name: "ENTERPRISE",
    price: "Custom",
    period: null,
    tagline: "For NGOs and institutions",
    features: [
      "Everything in Pro",
      "Dedicated data pipeline",
      "Custom ministry/state scope",
      "Team accounts",
      "SLA guarantee",
      "On-premise option",
    ],
    cta: "Contact Us",
    featured: false,
    disabled: false,
  },
] as const;

const FAQS = [
  { q: "Is this real-time data?", a: "ProcureWatch scrapes Government e-Marketplace (GeM) and CPPP data daily. Detection runs within 24 hours of new tender publication." },
  { q: "How are AI reports generated?", a: "Reports use Claude AI to analyze tender patterns, vendor histories, and anomaly clusters. Each report is generated fresh from your selected tenders — not a template." },
  { q: "What is RTI?", a: "The Right to Information Act 2005 allows Indian citizens to request government documents. Our reports generate targeted RTI questions based on detected anomalies." },
  { q: "Can I cancel anytime?", a: "Yes. Pro is month-to-month. Cancel from your account settings and you retain access until end of the billing period." },
  { q: "Is my data shared?", a: "No. Your reports and queries are private. We only store aggregate statistics to improve detection models." },
];

export default function PricingPage() {
  const reduced = useReducedMotion();
  const [loading, setLoading] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [emailError, setEmailError] = useState("");

  async function handlePro() {
    if (!email.trim() || !email.includes("@")) {
      setEmailError("Enter your email to continue");
      return;
    }
    setEmailError("");
    setLoading("pro");
    try {
      const { checkout_url } = await createCheckoutSession({
        plan: "pro",
        email: email.trim(),
        success_url: `${window.location.origin}/reports?upgraded=1`,
        cancel_url: `${window.location.origin}/pricing`,
      });
      window.location.href = checkout_url;
    } catch (e) {
      console.error(e);
      setLoading(null);
    }
  }

  function handleEnterprise() {
    window.location.href = "mailto:officialchidakash@gmail.com?subject=ProcureWatch Enterprise";
  }

  const motionProps = reduced ? {} : { initial: "hidden" as const, animate: "visible" as const, variants: containerVariants };

  return (
    <div>
      <TopBar title="Pricing" subtitle="Choose the plan that fits your investigation needs" />

      <div style={{ padding: "36px 32px" }}>
        {/* Plans */}
        <motion.div
          {...motionProps}
          style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 16, maxWidth: 900, marginBottom: 48 }}
        >
          {PLANS.map((plan) => (
            <motion.div
              key={plan.id}
              variants={reduced ? undefined : cardVariants}
              style={{
                background: plan.featured ? "var(--bg-surface)" : "var(--bg-base)",
                border: plan.featured ? "1px solid var(--accent-red)" : "1px solid var(--border-subtle)",
                borderRadius: 4,
                padding: "24px 24px 20px",
                display: "flex", flexDirection: "column",
                position: "relative",
              }}
            >
              {plan.featured && (
                <div className="mono" style={{ position: "absolute", top: -1, left: 24, fontSize: 9, fontWeight: 700, color: "var(--bg-base)", background: "var(--accent-red)", padding: "2px 8px", letterSpacing: "0.08em" }}>
                  RECOMMENDED
                </div>
              )}

              <div className="mono" style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.12em", color: plan.featured ? "var(--accent-red)" : "var(--text-muted)", marginBottom: 8, marginTop: plan.featured ? 6 : 0 }}>
                {plan.name}
              </div>

              <div style={{ display: "flex", alignItems: "baseline", gap: 4, marginBottom: 4 }}>
                {plan.price === "Custom" ? (
                  <span className="mono" style={{ fontSize: 24, fontWeight: 700, color: "var(--text-primary)" }}>Custom</span>
                ) : (
                  <>
                    <span className="mono" style={{ fontSize: 11, color: "var(--text-muted)", alignSelf: "flex-start", marginTop: 6 }}>₹</span>
                    <span className="mono" style={{ fontSize: 28, fontWeight: 700, color: "var(--text-primary)" }}>{plan.price}</span>
                    {plan.period && <span className="mono" style={{ fontSize: 11, color: "var(--text-muted)" }}>{plan.period}</span>}
                  </>
                )}
              </div>

              <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 20 }}>{plan.tagline}</div>

              <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 10, marginBottom: 24 }}>
                {plan.features.map((f) => (
                  <div key={f} style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                    <Check size={11} strokeWidth={2.5} style={{ color: plan.featured ? "var(--accent-red)" : "var(--accent-green)", flexShrink: 0, marginTop: 2 }} />
                    <span style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.4 }}>{f}</span>
                  </div>
                ))}
              </div>

              {plan.id === "pro" && (
                <div style={{ marginBottom: 10 }}>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="your@email.com"
                    style={{ width: "100%", background: "var(--bg-elevated)", border: emailError ? "1px solid var(--accent-red)" : "1px solid var(--border-subtle)", borderRadius: 2, color: "var(--text-primary)", fontSize: 12, padding: "8px 10px", outline: "none", boxSizing: "border-box", fontFamily: "JetBrains Mono, monospace" }}
                  />
                  {emailError && <div style={{ fontSize: 10, color: "var(--accent-red)", marginTop: 4 }}>{emailError}</div>}
                </div>
              )}

              <button
                onClick={plan.id === "pro" ? handlePro : plan.id === "enterprise" ? handleEnterprise : undefined}
                disabled={plan.disabled || loading === plan.id}
                style={{ background: plan.featured ? "var(--accent-red)" : "var(--bg-elevated)", border: plan.featured ? "none" : "1px solid var(--border-subtle)", borderRadius: 2, color: plan.featured ? "#fff" : "var(--text-secondary)", fontSize: 11, fontWeight: 700, letterSpacing: "0.06em", padding: "10px 16px", cursor: plan.disabled ? "default" : "pointer", opacity: plan.disabled ? 0.45 : 1, transition: "opacity 150ms" }}
              >
                {loading === plan.id ? "REDIRECTING..." : plan.cta.toUpperCase()}
              </button>
            </motion.div>
          ))}
        </motion.div>

        {/* FAQ */}
        <div style={{ maxWidth: 640 }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 16, borderBottom: "1px solid var(--border-subtle)", paddingBottom: 8 }}>
            Frequently Asked Questions
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
            {FAQS.map((item, i) => (
              <div key={i} style={{ borderBottom: "1px solid var(--border-subtle)", padding: "16px 0" }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)", marginBottom: 6 }}>{item.q}</div>
                <div style={{ fontSize: 12, color: "var(--text-muted)", lineHeight: 1.6 }}>{item.a}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}