"use client";

import { useEffect, useRef } from "react";
import * as d3 from "d3";
import type { VendorNetwork, NetworkNode, NetworkEdge } from "@/lib/api";

interface Props {
  data: VendorNetwork;
  width?: number;
  height?: number;
}

interface SimNode extends NetworkNode, d3.SimulationNodeDatum {}
interface SimLink extends d3.SimulationLinkDatum<SimNode> {
  type: string;
}

export default function D3ForceGraph({ data, width = 560, height = 380 }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const svg = d3.select(svgRef.current!);
    svg.selectAll("*").remove();

    const nodes: SimNode[] = data.nodes.map((n) => ({ ...n }));
    const nodeById = new Map(nodes.map((n) => [n.id, n]));

    const links: SimLink[] = data.edges
      .map((e) => ({
        source: nodeById.get(e.source) ?? e.source,
        target: nodeById.get(e.target) ?? e.target,
        type: e.type,
      }))
      .filter((l) => l.source && l.target);

    const sim = d3
      .forceSimulation<SimNode>(nodes)
      .force("link", d3.forceLink<SimNode, SimLink>(links).id((d) => d.id).distance(90))
      .force("charge", d3.forceManyBody().strength(-260))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide(28));

    const container = svg
      .attr("width", width)
      .attr("height", height)
      .attr("viewBox", `0 0 ${width} ${height}`)
      .style("background", "var(--bg-elevated)")
      .style("border-radius", "8px");

    const linkEl = container
      .append("g")
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke", "var(--border-active)")
      .attr("stroke-width", 1.5)
      .attr("stroke-opacity", 0.7);

    function nodeColor(n: SimNode): string {
      if (n.type === "director") return "var(--accent-blue)";
      switch (n.risk_level) {
        case "critical": return "var(--accent-red)";
        case "high": return "var(--accent-amber)";
        case "medium": return "var(--accent-amber)";
        default: return "var(--accent-green)";
      }
    }

    const nodeEl = container
      .append("g")
      .selectAll("g")
      .data(nodes)
      .join("g")
      .style("cursor", "pointer");

    nodeEl
      .append("circle")
      .attr("r", (d) => (d.type === "vendor" ? 20 : 14))
      .attr("fill", nodeColor)
      .attr("fill-opacity", 0.15)
      .attr("stroke", nodeColor)
      .attr("stroke-width", 2);

    nodeEl
      .append("text")
      .text((d) => (d.type === "vendor" ? "V" : "D"))
      .attr("text-anchor", "middle")
      .attr("dominant-baseline", "central")
      .attr("fill", nodeColor)
      .attr("font-size", 11)
      .attr("font-family", "JetBrains Mono, monospace")
      .attr("font-weight", "700");

    nodeEl
      .append("title")
      .text((d) => `${d.label}${d.din ? ` (DIN: ${d.din})` : ""}${d.risk_level ? ` — ${d.risk_level}` : ""}`);

    const labelEl = container
      .append("g")
      .selectAll("text")
      .data(nodes)
      .join("text")
      .text((d) => (d.label.length > 18 ? d.label.slice(0, 16) + "…" : d.label))
      .attr("text-anchor", "middle")
      .attr("fill", "var(--text-secondary)")
      .attr("font-size", 9)
      .attr("font-family", "Space Grotesk, sans-serif")
      .attr("pointer-events", "none");

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const dragBehavior = d3.drag<SVGGElement, SimNode>()
      .on("start", (event, d) => {
        if (!event.active) sim.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on("drag", (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on("end", (event, d) => {
        if (!event.active) sim.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });
    nodeEl.call(dragBehavior as any);

    sim.on("tick", () => {
      linkEl
        .attr("x1", (d) => (d.source as SimNode).x ?? 0)
        .attr("y1", (d) => (d.source as SimNode).y ?? 0)
        .attr("x2", (d) => (d.target as SimNode).x ?? 0)
        .attr("y2", (d) => (d.target as SimNode).y ?? 0);

      nodeEl.attr("transform", (d) => `translate(${d.x ?? 0},${d.y ?? 0})`);
      labelEl
        .attr("x", (d) => d.x ?? 0)
        .attr("y", (d) => (d.y ?? 0) + (d.type === "vendor" ? 32 : 24));
    });

    return () => {
      sim.stop();
    };
  }, [data, width, height]);

  return <svg ref={svgRef} style={{ display: "block", width: "100%", height }} />;
}
