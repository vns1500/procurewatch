"use client";

import { useEffect, useRef } from "react";
import { useMotionValue, useSpring, useReducedMotion } from "framer-motion";
import { motion } from "framer-motion";
import { cardVariants } from "@/lib/motion";

type AccentColor = "red" | "amber" | "green" | "blue";

const COLOR_MAP: Record<AccentColor, string> = {
  red: "var(--accent-red)",
  amber: "var(--accent-amber)",
  green: "var(--accent-green)",
  blue: "var(--accent-blue)",
};

interface StatCardProps {
  label: string;
  value: number;
  unit?: string;
  trend?: number;
  color: AccentColor;
  prefix?: string;
  formatter?: (v: number) => string;
}

function AnimatedNumber({
  value,
  prefix = "",
  formatter,
}: {
  value: number;
  prefix?: string;
  formatter?: (v: number) => string;
}) {
  const reduced = useReducedMotion();
  const motionVal = useMotionValue(0);
  const spring = useSpring(motionVal, { stiffness: 60, damping: 20, mass: 0.8 });
  const ref = useRef<HTMLSpanElement>(null);

  const format = (v: number) =>
    formatter ? formatter(v) : `${prefix}${Math.round(v).toLocaleString("en-IN")}`;

  useEffect(() => {
    if (reduced) {
      if (ref.current) ref.current.textContent = format(value);
      return;
    }
    motionVal.set(0);
    spring.set(0);
    const timeout = setTimeout(() => motionVal.set(value), 50);

    const unsub = spring.on("change", (v) => {
      if (ref.current) {
        ref.current.textContent = format(v);
      }
    });

    return () => {
      clearTimeout(timeout);
      unsub();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, motionVal, spring, reduced, prefix, formatter]);

  return (
    <span ref={ref} className="mono" style={{ fontSize: 28, fontWeight: 600, lineHeight: 1 }}>
      {prefix}0
    </span>
  );
}

export function StatCard({ label, value, unit, trend, color, prefix = "", formatter }: StatCardProps) {
  const accentColor = COLOR_MAP[color];

  return (
    <motion.div
      variants={cardVariants}
      style={{
        background: "var(--bg-surface)",
        border: "1px solid var(--border-subtle)",
        borderRadius: 4,
        padding: "20px 24px",
        display: "flex",
        flexDirection: "column",
        gap: 8,
        flex: 1,
        minWidth: 0,
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
        {label}
      </span>
      <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
        <AnimatedNumber value={value} prefix={prefix} formatter={formatter} />
        {unit && (
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>{unit}</span>
        )}
      </div>
      {trend !== undefined && (
        <span
          style={{
            fontSize: 11,
            color: trend >= 0 ? "var(--accent-red)" : "var(--accent-green)",
          }}
        >
          {trend >= 0 ? "↑" : "↓"} {Math.abs(trend)}% vs last month
        </span>
      )}
      <div
        style={{
          height: 2,
          background: accentColor,
          borderRadius: 1,
          opacity: 0.6,
          marginTop: 4,
        }}
      />
    </motion.div>
  );
}
