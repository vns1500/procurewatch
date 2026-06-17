"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FileText,
  Building2,
  AlertTriangle,
  BarChart3,
  Bell,
  CreditCard,
} from "lucide-react";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/tenders", label: "Tenders", icon: FileText },
  { href: "/vendors", label: "Vendors", icon: Building2 },
  { href: "/anomalies", label: "Anomalies", icon: AlertTriangle },
  { href: "/reports", label: "Reports", icon: BarChart3 },
  { href: "/alerts", label: "Alerts", icon: Bell },
  { href: "/pricing", label: "Pricing", icon: CreditCard },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside
      style={{
        width: 220,
        minHeight: "100vh",
        background: "var(--bg-surface)",
        borderRight: "1px solid var(--border-subtle)",
        display: "flex",
        flexDirection: "column",
        flexShrink: 0,
      }}
    >
      <div
        style={{
          padding: "24px 20px 20px",
          borderBottom: "1px solid var(--border-subtle)",
        }}
      >
        <span
          style={{
            fontFamily: "'Space Grotesk', sans-serif",
            fontWeight: 700,
            fontSize: 15,
            color: "var(--accent-red)",
            letterSpacing: "0.06em",
          }}
        >
          PROCUREWATCH
        </span>
      </div>

      <nav style={{ flex: 1, padding: "12px 0" }}>
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "9px 20px",
                fontSize: 13,
                fontWeight: 500,
                color: active ? "var(--text-primary)" : "var(--text-muted)",
                borderLeft: active
                  ? "3px solid var(--accent-red)"
                  : "3px solid transparent",
                background: active ? "var(--bg-elevated)" : "transparent",
                textDecoration: "none",
                transition: "color 150ms, background 150ms",
              }}
              onMouseEnter={(e) => {
                if (!active) {
                  (e.currentTarget as HTMLAnchorElement).style.color =
                    "var(--text-secondary)";
                }
              }}
              onMouseLeave={(e) => {
                if (!active) {
                  (e.currentTarget as HTMLAnchorElement).style.color =
                    "var(--text-muted)";
                }
              }}
            >
              <Icon size={16} strokeWidth={1.5} />
              {label}
            </Link>
          );
        })}
      </nav>

      <div
        style={{
          padding: "16px 20px",
          borderTop: "1px solid var(--border-subtle)",
        }}
      >
        <span
          className="mono"
          style={{
            fontSize: 10,
            color: "var(--text-muted)",
            letterSpacing: "0.04em",
          }}
        >
          v1.0.0-alpha
        </span>
      </div>
    </aside>
  );
}
