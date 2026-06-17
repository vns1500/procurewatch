import type { CSSProperties } from "react";

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  borderRadius?: number;
  style?: CSSProperties;
}

export function Skeleton({ width = "100%", height = 16, borderRadius = 2, style }: SkeletonProps) {
  return (
    <div
      className="skeleton"
      style={{
        width,
        height,
        borderRadius,
        ...style,
      }}
    />
  );
}

export function StatCardSkeleton() {
  return (
    <div
      style={{
        background: "var(--bg-surface)",
        border: "1px solid var(--border-subtle)",
        borderRadius: 4,
        padding: "20px 24px",
        flex: 1,
        minWidth: 0,
        display: "flex",
        flexDirection: "column",
        gap: 10,
      }}
    >
      <Skeleton width={80} height={10} />
      <Skeleton width={120} height={32} />
      <Skeleton width={60} height={10} />
      <Skeleton height={2} />
    </div>
  );
}

export function TableRowSkeleton({ cols = 8 }: { cols?: number }) {
  return (
    <tr>
      {Array.from({ length: cols }).map((_, i) => (
        <td key={i} style={{ padding: "10px 12px" }}>
          <Skeleton width={i === 0 ? 100 : i === cols - 1 ? 40 : "80%"} height={12} />
        </td>
      ))}
    </tr>
  );
}
