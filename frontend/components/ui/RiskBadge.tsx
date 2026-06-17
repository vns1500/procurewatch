const FLAG_CONFIG: Record<string, { label: string; color: string }> = {
  single_bid: { label: "SINGLE BID", color: "var(--accent-red)" },
  rushed_timeline: { label: "RUSHED", color: "var(--accent-amber)" },
  bid_splitting: { label: "BID SPLIT", color: "var(--accent-red)" },
  price_inflation: { label: "PRICE ↑", color: "var(--accent-amber)" },
  default: { label: "FLAGGED", color: "var(--accent-amber)" },
};

interface RiskBadgeProps {
  flag: string;
}

export function RiskBadge({ flag }: RiskBadgeProps) {
  const config = FLAG_CONFIG[flag] ?? FLAG_CONFIG.default;

  return (
    <span
      className="mono"
      style={{
        display: "inline-block",
        fontSize: 9,
        fontWeight: 600,
        letterSpacing: "0.06em",
        padding: "2px 6px",
        border: `1px solid ${config.color}`,
        borderRadius: 2,
        color: config.color,
        whiteSpace: "nowrap",
      }}
    >
      {config.label}
    </span>
  );
}
