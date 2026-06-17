"use client";

import type { ReactNode } from "react";

interface TopBarProps {
  title: string;
  subtitle?: string;
  action?: ReactNode;
}

export function TopBar({ title, subtitle, action }: TopBarProps) {
  return (
    <div
      style={{
        padding: "20px 32px",
        borderBottom: "1px solid var(--border-subtle)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        background: "var(--bg-base)",
      }}
    >
      <div>
        <h1
          style={{
            fontSize: 18,
            fontWeight: 600,
            color: "var(--text-primary)",
            margin: 0,
          }}
        >
          {title}
        </h1>
        {subtitle && (
          <p
            style={{
              fontSize: 12,
              color: "var(--text-muted)",
              margin: "2px 0 0",
            }}
          >
            {subtitle}
          </p>
        )}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        {action}
        <span
          className="mono"
          style={{
            fontSize: 10,
            color: "var(--mono-accent)",
            padding: "3px 8px",
            border: "1px solid var(--mono-accent)",
            borderRadius: 2,
            opacity: 0.7,
          }}
        >
          LIVE
        </span>
      </div>
    </div>
  );
}
