"use client";

import { useEffect, useRef } from "react";
import { useReducedMotion } from "framer-motion";

interface RiskRingProps {
  score: number;
  size?: number;
}

function scoreColor(score: number): string {
  if (score > 70) return "var(--accent-red)";
  if (score > 40) return "var(--accent-amber)";
  return "var(--accent-green)";
}

export function RiskRing({ score, size = 48 }: RiskRingProps) {
  const reduced = useReducedMotion();
  const circleRef = useRef<SVGCircleElement>(null);

  const radius = (size - 6) / 2;
  const circumference = 2 * Math.PI * radius;
  const targetDash = (score / 100) * circumference;
  const color = scoreColor(score);

  useEffect(() => {
    const circle = circleRef.current;
    if (!circle) return;

    if (reduced) {
      circle.style.strokeDashoffset = String(circumference - targetDash);
      return;
    }

    circle.style.strokeDashoffset = String(circumference);
    const raf = requestAnimationFrame(() => {
      circle.style.transition = "stroke-dashoffset 0.8s cubic-bezier(0.4, 0, 0.2, 1)";
      circle.style.strokeDashoffset = String(circumference - targetDash);
    });
    return () => cancelAnimationFrame(raf);
  }, [score, circumference, targetDash, reduced]);

  return (
    <svg width={size} height={size} style={{ transform: "rotate(-90deg)", flexShrink: 0 }}>
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="var(--border-subtle)"
        strokeWidth={3}
      />
      <circle
        ref={circleRef}
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth={3}
        strokeDasharray={circumference}
        strokeDashoffset={circumference}
        strokeLinecap="round"
      />
      <text
        x={size / 2}
        y={size / 2}
        textAnchor="middle"
        dominantBaseline="central"
        style={{
          transform: "rotate(90deg)",
          transformOrigin: `${size / 2}px ${size / 2}px`,
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: size <= 32 ? 9 : 13,
          fontWeight: 600,
          fill: color,
        }}
      >
        {score}
      </text>
    </svg>
  );
}
